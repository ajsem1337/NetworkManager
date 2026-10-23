"""Security regressions; no real network commands or privileged writes."""
import contextlib
import importlib
import io
import os
from pathlib import Path
import stat
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]


@contextlib.contextmanager
def variant(platform):
    directory = ROOT / ('source_code_' + platform)
    names = {p.stem for p in directory.glob('*.py')}
    previous = {name: sys.modules.pop(name) for name in names if name in sys.modules}
    sys.path.insert(0, str(directory))
    try:
        yield importlib.import_module
    finally:
        sys.path.remove(str(directory))
        for name in names:
            sys.modules.pop(name, None)
        sys.modules.update(previous)


@contextlib.contextmanager
def data_directory(config, directory):
    data = Path(directory) / 'core_data'
    with patch.multiple(config, DB_DIR=str(data), REPORTS_DIR=str(Path(directory) / 'Reports'),
                        DB_IP=str(data / 'ip_registry.sys'), DB_WOL=str(data / 'wol_registry.sys'),
                        DB_WIFI=str(data / 'wifi_vault.dat'), FIRST_RUN_FLAG=str(data / 'installed.flag')):
        yield


class SecurityTests(unittest.TestCase):
    def setUp(self):
        self.output = contextlib.redirect_stdout(io.StringIO())
        self.output.__enter__()

    def tearDown(self):
        self.output.__exit__(None, None, None)

    def test_validators_reject_commands_options_and_control_characters(self):
        for platform in ('linux', 'windows'):
            with self.subTest(platform=platform), variant(platform) as load:
                security = load('security_utils')
                for host in ('example.com', 'localhost', '192.0.2.1', '2001:db8::1'):
                    self.assertTrue(security.validate_hostname(host), host)
                for host in ('example.com;id', 'example.com & whoami', '-n', 'bad..host',
                             'example.com\n', 'fe80::1%eth0\ninjected', '../../hosts'):
                    self.assertFalse(security.validate_hostname(host), host)
                for interface in ('-x', '.', '..', 'eth0;id', 'eth0\n'):
                    self.assertFalse(security.validate_interface_name(interface), interface)
                self.assertTrue(security.validate_interface_name('enp3s0.10'))
                self.assertTrue(security.validate_netmask('255.255.255.0'))
                self.assertFalse(security.validate_netmask('255.0.255.0'))
                self.assertFalse(security.validate_netmask('0.0.0.255'))

    def test_report_paths_stay_inside_reports_and_do_not_overwrite(self):
        for platform in ('linux', 'windows'):
            with self.subTest(platform=platform), variant(platform) as load, tempfile.TemporaryDirectory() as tmp:
                config = load('core_config')
                reports = load('core_report')
                with data_directory(config, tmp), patch.object(reports.time, 'strftime', return_value='fixed'):
                    paths = [reports.save('secret', prefix) for prefix in
                             ('../../outside', r'C:\Windows\hosts', '/tmp/absolute', '../../outside')]
                    self.assertEqual(len(set(paths)), 4)
                    for path in paths:
                        self.assertEqual(Path(path).parent, Path(config.REPORTS_DIR))
                        self.assertEqual(Path(path).read_text(), 'secret')
                        if os.name == 'posix':
                            self.assertEqual(stat.S_IMODE(os.stat(path).st_mode), 0o600)
                    if os.name == 'posix':
                        self.assertEqual(stat.S_IMODE(os.stat(config.REPORTS_DIR).st_mode), 0o700)
                        self.assertEqual(stat.S_IMODE(os.stat(config.DB_IP).st_mode), 0o600)

    @unittest.skipUnless(os.name == 'posix', 'POSIX symlink and permissions checks')
    def test_existing_permissions_are_tightened_and_symlinks_rejected(self):
        for platform in ('linux', 'windows'):
            with self.subTest(platform=platform), variant(platform) as load, tempfile.TemporaryDirectory() as tmp:
                config = load('core_config')
                with data_directory(config, tmp):
                    config.init()
                    os.chmod(config.DB_DIR, 0o755)
                    os.chmod(config.DB_WOL, 0o644)
                    config.init()
                    self.assertEqual(stat.S_IMODE(os.stat(config.DB_DIR).st_mode), 0o700)
                    self.assertEqual(stat.S_IMODE(os.stat(config.DB_WOL).st_mode), 0o600)
                    target = Path(tmp) / 'untouched'
                    target.write_text('original')
                    Path(config.DB_IP).unlink()
                    Path(config.DB_IP).symlink_to(target)
                    with self.assertRaises(OSError):
                        config.init()
                    self.assertEqual(target.read_text(), 'original')
                    Path(config.DB_IP).unlink()
                    Path(config.REPORTS_DIR).rmdir()
                    Path(config.REPORTS_DIR).symlink_to(tmp, target_is_directory=True)
                    with self.assertRaises(OSError):
                        config.init()

    def test_invalid_windows_ping_and_dns_never_spawn_processes(self):
        for module_name, entry, answers in (
            ('diag_ping', 'run_menu', ['3', 'example.com & whoami', '', '0']),
            ('diag_dns', 'run', ['1', '-debug', '', '0']),
            ('diag_tracert', 'run', ['example.com\nwhoami', '', '0']),
        ):
            with self.subTest(module=module_name), variant('windows') as load:
                module = load(module_name)
                with patch('builtins.input', side_effect=answers), patch.object(module.os, 'system'), \
                        patch.object(module.subprocess, 'run') as run, patch.object(module.subprocess, 'Popen') as popen:
                    getattr(module, entry)()
                    run.assert_not_called()
                    popen.assert_not_called()

    def test_windows_ping_passes_valid_target_as_a_single_argument(self):
        with variant('windows') as load:
            module = load('diag_ping')
            with patch('builtins.input', side_effect=['3', 'example.com', '', '0']), \
                    patch.object(module.os, 'system'), patch.object(module.subprocess, 'run') as run:
                module.run_menu()
                run.assert_called_once_with(['ping', 'example.com'])

    def test_wifi_profile_is_data_and_export_requires_opt_in(self):
        for consent in ('n', 't'):
            with self.subTest(consent=consent), variant('windows') as load:
                module = load('diag_wifi')
                profile = 'Home" & whoami & "'
                with patch.object(module.os, 'system'), patch('builtins.input', side_effect=[consent, '']), \
                        patch.object(module.subprocess, 'run', side_effect=[
                            Mock(stdout='All User Profile : ' + profile),
                            Mock(stdout='Authentication : WPA2\nKey Content : secret')]) as run, \
                        patch.object(module.core_report, 'save') as save:
                    module.run()
                    self.assertEqual(run.call_args.args[0],
                                     ['netsh', 'wlan', 'show', 'profile', 'name=' + profile, 'key=clear'])
                    self.assertFalse(run.call_args.kwargs.get('shell', False))
                    self.assertEqual(save.call_count, int(consent == 't'))

    def test_windows_adapter_names_are_literal_powershell_strings(self):
        with variant('windows') as load:
            commands = load('windows_commands')
            module = load('net_card_menu')
            adapter = "Ethernet'; Write-Output PWNED; '$(whoami)&"
            with patch.object(module.subprocess, 'check_output', return_value=b'') as run:
                module.get_adapter_info(adapter)
                args = run.call_args.args[0]
                self.assertIsInstance(args, list)
                self.assertIn(commands.literal(adapter), args[-1])
                # Removing PowerShell single-quoted literals leaves no injected command.
                import re
                outside_literals = re.sub(r"'(?:[^']|'')*'", "''", args[-1])
                self.assertNotIn('PWNED', outside_literals)
                self.assertNotIn('whoami', outside_literals)
                self.assertFalse(run.call_args.kwargs.get('shell', False))

    def test_invalid_ip_profiles_cannot_change_network_configuration(self):
        for platform, function in (('linux', 'apply_config'), ('windows', 'apply_ip_config')):
            with self.subTest(platform=platform), variant(platform) as load:
                module = load('net_card_menu')
                with patch.object(module.subprocess, 'run') as run, \
                        patch.object(module.subprocess, 'call') as call, \
                        patch.object(module.subprocess, 'check_output') as check:
                    getattr(module, function)('eth0', '192.0.2.1', '255.0.255.0', '-', '-', '-')
                    getattr(module, function)('eth0', '192.0.2.1 & whoami', '255.255.255.0', '-', '-', '-')
                    run.assert_not_called()
                    call.assert_not_called()
                    check.assert_not_called()

    def test_windows_valid_profile_uses_netsh_arguments_without_shell(self):
        with variant('windows') as load:
            module = load('net_card_menu')
            with patch.object(module.subprocess, 'run') as run, patch.object(module, 'wait_for_ip'):
                module.apply_ip_config('Ethernet & "name"', '192.0.2.1', '255.255.255.0', '-', '1.1.1.1', '-')
                self.assertEqual(run.call_args_list[0].args[0], [
                    'netsh', 'interface', 'ip', 'set', 'address', 'name=Ethernet & "name"',
                    'static', '192.0.2.1', '255.255.255.0', 'none'])
                for call in run.call_args_list:
                    self.assertFalse(call.kwargs.get('shell', False))

    def test_linux_config_reads_text_output_without_losing_existing_profile(self):
        with variant('linux') as load:
            module = load('net_card_menu')
            with patch.object(module.subprocess, 'check_output', side_effect=[
                'Existing profile:eth0\n', 'inet 192.0.2.10/24 brd 192.0.2.255\n',
                'default via 192.0.2.1 dev eth0\n', 'IP4.DNS[1]: 1.1.1.1\n']):
                self.assertEqual(module.get_connection_profile('eth0'), 'Existing profile')
                cfg = module.get_current_config('eth0')
                self.assertEqual(cfg['ip'], '192.0.2.10')
                self.assertEqual(cfg['mask'], '255.255.255.0')
                self.assertEqual(cfg['gw'], '192.0.2.1')
                self.assertEqual(cfg['dns1'], '1.1.1.1')

    def test_geoip_uses_https_timeout_and_new_response_format(self):
        for platform in ('linux', 'windows'):
            with self.subTest(platform=platform), variant(platform) as load:
                module = load('diag_geo_ip')
                response = Mock()
                response.json.return_value = dict(success=True, ip='192.0.2.1', country='Poland',
                    country_code='PL', city='Warsaw', region='Mazovia', connection={'isp': 'ISP'})
                with patch.object(module.os, 'system'), patch('builtins.input', side_effect=['n', '']), \
                        patch.object(module.requests, 'get', return_value=response) as get:
                    module.run()
                    get.assert_called_once_with('https://ipwho.is/', timeout=5)
                    response.raise_for_status.assert_called_once()
                    response.json.assert_called_once()

    def test_wol_does_not_expose_or_resave_unused_passwords(self):
        for platform in ('linux', 'windows'):
            with self.subTest(platform=platform), variant(platform) as load, tempfile.TemporaryDirectory() as tmp:
                module = load('db_wol')
                path = Path(tmp) / 'wol_registry.sys'
                path.write_text('PC;00:11:22:33:44:55;192.0.2.255;old-secret\n')
                with patch.object(module, 'DB_PATH', str(path)):
                    profiles = module.load_wol_profiles()
                    self.assertEqual(profiles[0][3], '-')
                    module.save_wol_profiles([['PC', '00:11:22:33:44:55', '192.0.2.255', 'new-secret']])
                    self.assertNotIn('secret', path.read_text())


if __name__ == '__main__':
    unittest.main()

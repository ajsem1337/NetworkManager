# NetworkMaster

![Made with AI](https://raw.githubusercontent.com/ajsem1337/ajsem1337/main/assets/made-with-ai.svg)

A console tool for network diagnostics and configuration on Linux and Windows, with separate implementations in the NetworkManager repository's `source_code_linux` and `source_code_windows` directories.

## Features

- Ping, traceroute, DNS lookup, WHOIS/RDAP and TLS certificate checks.
- Port scanning, LAN device discovery and MAC vendor lookup.
- Dashboard, traffic and WiFi signal monitoring, and a subnet calculator.
- IP, DHCP and DNS configuration, a profile database, and Wake-on-LAN.
- Hosts file editing, DNS cache flushing and network configuration resets.
- Saved WiFi password retrieval and text report export.

“DNS Benchmark” measures ICMP latency to DNS servers, rather than name resolution
time. The LAN scanner checks a `/24` range based on the local address, rather than
every possible subnet.

## Getting started

Requires Python 3.11 or newer and `requests`. Run the code from a directory in
your own user account where the application can write its data.

### Linux

```sh
git clone https://github.com/ajsem1337/NetworkManager.git
cd NetworkManager
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python source_code_linux/main.py
```

Individual modules use system tools: `ip`, `ping`, `tracepath`, `nslookup`, `ss`,
`nmcli`, `iwconfig`, `ethtool`, `lspci`, `lsusb` and `nano`. The graphical editor
requires `nm-connection-editor`. Network reset also uses `systemctl` and `dhclient`.
Package names vary by distribution; a missing tool limits the corresponding feature.

Routine diagnostics work without root. Configuration changes use `sudo`; reading
WiFi passwords on Linux requires root privileges. Do not run the entire application
as root for routine diagnostics. Data directories belong to the user who created
them; mixing normal and root runs can cause permission errors.

### Windows

In PowerShell, after downloading or cloning the repository:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe source_code_windows\main.py
```

The Windows version uses system tools including Windows PowerShell, `netsh`,
`ipconfig`, `ping`, `tracert` and `nslookup`. Configuration changes, hosts file
editing and some WiFi queries require a terminal running as Administrator.
Some output parsers support Polish and English messages; other system languages
may require adjustments.

## Data and security

- `core_data/` beside each platform's code contains the first-run flag and plain
  text IP and WOL profile databases. The `.sys` extension does not imply a system
  file or encryption.
- Reports go to `Reports/` beside each platform's code. Filenames are sanitized
  and given a random suffix to avoid overwriting existing files.
- On Linux, data and report directories have permissions `700`; database files
  and new reports use `600`. On Windows, access protection depends on the user
  directory's ACLs. Data is not encrypted.
- The WiFi audit displays available passwords; saving a report requires an
  explicit choice. Reports containing passwords remain plain text. Older reports
  are not automatically deleted or given updated permissions.
- WOL sends a standard Magic Packet and does not use SSH/RPC passwords. The legacy
  fourth database field is ignored and replaced with `-` when saved. Old passwords
  remain in existing files until those files are saved again; backups are unchanged.
- GeoIP connects to `ipwho.is` over HTTPS; the
  [service documentation](https://ipwhois.io/documentation) describes its API
  response. WHOIS uses `rdap.org`, and MAC Lookup uses `api.macvendors.com`.
  These services receive the connection's public IP address and, where applicable,
  the queried domain or MAC address.
- Diagnostic commands send traffic to the selected hosts and servers. Reports may
  contain addresses, device names and passwords; review them before sharing.

Network resets, DHCP, IP changes and disabling an adapter can interrupt the
connection. The existing [Phase 1 report](SECURITY_FIXES_PHASE1.md) is historical
and does not confirm a complete audit of the current code.

## Verification

```sh
python -m unittest discover -s tests -v
python -m compileall -q source_code_linux source_code_windows
```

Regression tests cover input validation, process argument handling, safe report
writing, symlink protection and the removal of automatic WiFi password exports.
Network and administrative calls are mocked; tests do not change network
configuration. System tools need separate verification on the target platform.

Additional documentation: [NetworkMaster Technical Documentation PL](NetworkMaster_Technical_Documentation_PL.pdf)
(in Polish). The PDF may describe an earlier version.

## License

[GNU GPLv3](LICENSE.md).

---

<p align="center"><sub>Built by <a href="https://github.com/ajsem1337">ajsem</a> with AI assistance.</sub></p>

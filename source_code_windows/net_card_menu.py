import os, subprocess, time, db_ip, security_utils
from windows_commands import powershell, literal

# Definicje kolorów (zgodne z main.py)
G, R, C, Y, RESET = '\033[92m', '\033[91m', '\033[96m', '\033[93m', '\033[0m'

def get_adapter_info(adapter_name):
    try:
        cmd = powershell(f'Get-NetAdapter | Where-Object {{ $_.Name -eq {literal(adapter_name)} }} | Select-Object Status, LinkSpeed, MacAddress | ConvertTo-Csv -NoTypeInformation')
        out = subprocess.check_output(cmd, timeout=15).decode('utf-8', errors='ignore').splitlines()
        if len(out) >= 2:
            d = out[1].replace('"', '').split(',')
            raw_st = d[0].strip().upper()
            st = f"{G}UP{RESET}" if raw_st == "UP" else f"{R}DOWN{RESET}"
            sp = d[1].strip() if raw_st == "UP" else "--"
            return st, sp, d[2].strip()
    except: pass
    return f"{R}DOWN{RESET}", "--", "00-00-00-00-00-00"

def get_full_current_config(adapter_name):
    cfg = {"ip": "-", "mask": "-", "gw": "-", "dns1": "-", "dns2": "-"}
    try:
        # IP i MASKA
        cmd_ip = powershell(f'Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue | Where-Object {{ $_.InterfaceAlias -eq {literal(adapter_name)} }} | Select-Object IPAddress, PrefixLength')
        out_ip = subprocess.check_output(cmd_ip, timeout=15).decode('utf-8', errors='ignore').strip().splitlines()
        
        for line in out_ip:
            if "." in line:
                parts = line.split()
                if len(parts) >= 2:
                    cfg["ip"] = parts[0]
                    # Konwersja prefiksu na maskę (np. 24 -> 255.255.255.0)
                    try:
                        prefix = int(parts[1])
                        mask_long = (0xffffffff << (32 - prefix)) & 0xffffffff
                        cfg["mask"] = ".".join([str((mask_long >> i) & 0xff) for i in [24, 16, 8, 0]])
                    except:
                        cfg["mask"] = f"/{parts[1]}"
                break
        
        # BRAMA
        cmd_gw = powershell(f"(Get-NetRoute -DestinationPrefix '0.0.0.0/0' | Where-Object {{ $_.InterfaceAlias -eq {literal(adapter_name)} }}).NextHop")
        res_gw = subprocess.run(cmd_gw, capture_output=True, text=True, timeout=15).stdout.strip()
        if res_gw: cfg["gw"] = res_gw

        # DNS
        cmd_dns = powershell(f'(Get-DnsClientServerAddress -AddressFamily IPv4 | Where-Object {{ $_.InterfaceAlias -eq {literal(adapter_name)} }}).ServerAddresses')
        res_dns = subprocess.run(cmd_dns, capture_output=True, text=True, timeout=15).stdout.strip().splitlines()
        if len(res_dns) > 0: cfg["dns1"] = res_dns[0]
        if len(res_dns) > 1: cfg["dns2"] = res_dns[1]
    except: pass
    return cfg

def wait_for_ip(adapter_name):
    print(" [i] Aplikowanie konfiguracji...", end="", flush=True)
    for _ in range(4): time.sleep(1); print(".", end="", flush=True)
    print(" OK")

def set_interface_state(adapter_name, state):
    """state: enable | disable"""
    print(f" [i] Zmieniam stan karty na: {state}...")
    if state not in ('enable', 'disable'):
        raise ValueError('Nieprawidłowy stan karty')
    subprocess.run(['netsh', 'interface', 'set', 'interface', 'name=' + adapter_name, 'admin=' + state], timeout=15)
    time.sleep(2)

def apply_ip_config(adapter_name, ip, m, g, d1, d2):
    if not security_utils.validate_ipv4(ip) or not security_utils.validate_netmask(m):
        print(" [!] Nieprawidłowy adres IP lub maska.")
        return
    if any(value not in (None, '', '-') and not security_utils.validate_ipv4(value) for value in (g, d1, d2)):
        print(" [!] Nieprawidłowa brama lub DNS.")
        return
    print(f"\n [i] Ustawianie: IP {ip} | Maska {m} | Brama {g}")
    cmd_ip = ['netsh', 'interface', 'ip', 'set', 'address', 'name=' + adapter_name, 'static', ip, m]
    cmd_ip += [g, '1'] if g not in (None, '', '-') else ['none']
    subprocess.run(cmd_ip, check=True, timeout=15)
    if d1 not in (None, '', '-'):
        subprocess.run(['netsh', 'interface', 'ip', 'set', 'dns', 'name=' + adapter_name, 'static', d1, 'validate=no'], check=True, timeout=15)
    if d2 not in (None, '', '-'):
        subprocess.run(['netsh', 'interface', 'ip', 'add', 'dns', 'name=' + adapter_name, d2, 'index=2', 'validate=no'], check=True, timeout=15)
    wait_for_ip(adapter_name)


def snapshot_to_db(cfg):
    print(f"\n{Y}--- SNAPSHOT DO BAZY ---{RESET}")
    if cfg['ip'] == "-" or not cfg['ip']:
        print(f" {R}[BŁĄD] Brak aktywnego adresu IP do zapisania!{RESET}"); time.sleep(2); return

    name = input(" Podaj nazwę dla tego profilu: ").strip()
    if not name: return

    # Format bazy: [Nazwa, IP, Maska, Brama, DNS1, DNS2]
    new_entry = [
        name,
        cfg['ip'],
        cfg['mask'],
        cfg['gw'] if cfg['gw'] else "-",
        cfg['dns1'] if cfg['dns1'] else "8.8.8.8",
        cfg['dns2'] if cfg['dns2'] else "-"
    ]
    
    profiles = db_ip.load_all_profiles()
    profiles.append(new_entry)
    db_ip.save_all(profiles)
    print(f" {G}[SUKCES] Zapisano obecną konfigurację w bazie.{RESET}")
    time.sleep(1.5)

def run(adapter_name):
    while True:
        os.system('cls')
        status, speed, mac = get_adapter_info(adapter_name)
        cfg = get_full_current_config(adapter_name)
        
        # --- TWOJA SEKCJA WIZUALNA (1:1) ---
        print(f"{C}================================================================{RESET}")
        print(f"        KARTA: {Y}{adapter_name}{RESET}  |  MAC: {mac}")
        print(f"        STATUS: {status:<19} PREDKOSC: {speed}")
        print(f"        IP: {cfg['ip']:<15} MASKA: {cfg['mask']}")
        print(f"        GW: {cfg['gw']:<15} DNS: {cfg['dns1']}, {cfg['dns2']}")
        print(f"{C}================================================================{RESET}")
        
        print(f" [{G}1{RESET}] DHCP (Auto)")
        print(f" [{G}2{RESET}] Ustaw ręcznie IP")
        print(f" [{G}3{RESET}] Baza Profili")
        print(f" [{G}4{RESET}] Restart (Down/Up)")
        print(f" [{G}ON{RESET}] Włącz kartę        [{R}OFF{RESET}] Wyłącz kartę")
        print(f" [{G}5{RESET}] Snapshot do bazy")
        print(f" [{G}7{RESET}] Odśwież")
        print(f"\n [{R}0{RESET}] Powrót")
        
        c = input("\n Wybór: ").strip().lower()
        
        if c == '0': break
        
        elif c == '1':
            print("\n [i] Przywracanie DHCP...")
            subprocess.run(['netsh', 'interface', 'ip', 'set', 'address', 'name=' + adapter_name, 'source=dhcp'], check=True, timeout=15)
            subprocess.run(['netsh', 'interface', 'ip', 'set', 'dns', 'name=' + adapter_name, 'source=dhcp'], check=True, timeout=15)
            wait_for_ip(adapter_name)
            
        elif c == '2':
            data = db_ip.manual_input_profile()
            if data:
                _, ip, m, g, d1, d2 = data
                apply_ip_config(adapter_name, ip, m, g, d1, d2)
                
        elif c == '3':
            p = db_ip.select_profile_menu(mode="SELECT")
            if p:
                n, ip, m, g, d1, d2 = p
                apply_ip_config(adapter_name, ip, m, g, d1, d2)
                
        elif c == '4':
            set_interface_state(adapter_name, "disable")
            set_interface_state(adapter_name, "enable")
            
        elif c == 'on':
            set_interface_state(adapter_name, "enable")
            
        elif c == 'off':
            set_interface_state(adapter_name, "disable")
            
        elif c == '5':
            snapshot_to_db(cfg)
            
        elif c == '7':
            continue # Tylko odświeża pętlę
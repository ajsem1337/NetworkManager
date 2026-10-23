import os
import subprocess
import concurrent.futures
import time
import core_report
import core_mac_lookup
import core_config
import db_wol
import security_utils

def wake_up_ip(ip):
    if not security_utils.validate_ipv4(ip):
        return
    subprocess.run(["ping", "-n", "1", "-w", "100", ip], capture_output=True, timeout=3)

def get_local_ip_prefix():
    try:
        cmd = 'powershell "(Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.PrefixOrigin -ne \'WellKnown\' }).IPAddress"'
        res = subprocess.run(cmd, capture_output=True, text=True, shell=True).stdout.strip()
        main_ip = res.split()[0]
        return ".".join(main_ip.split(".")[:-1]) + "."
    except: return "192.168.1."

def run():
    os.system('cls')
    prefix = get_local_ip_prefix()
    print(f" [*] Skanowanie sieci {prefix}0/24...")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as ex:
        ex.map(wake_up_ip, [f"{prefix}{i}" for i in range(1, 255)])

    cmd = 'powershell "Get-NetNeighbor -AddressFamily IPv4 | Select-Object IPAddress, LinkLayerAddress | Format-Table -HideTableHeaders"'
    raw = subprocess.run(cmd, capture_output=True, text=True, shell=True).stdout
    
    found = []
    print(f"\n {'ID':<4} | {'IP':<15} | {'MAC ADDRESS':<18} | {'PRODUCENT'}")
    print("-" * 80)
    
    for line in raw.strip().split('\n'):
        p = line.split()
        if len(p) >= 2 and p[1] != "00-00-00-00-00-00" and p[0].startswith(prefix):
            mac = p[1].replace("-", ":").upper()
            vendor = core_mac_lookup.get_vendor(mac)
            idx = len(found) + 1
            print(f" [{idx:02}] | {p[0]:<15} | {mac:<18} | {vendor[:30]}")
            found.append({"ip": p[0], "mac": mac, "vendor": vendor})

    print("\n [A] Dodaj do bazy WOL   [0] Powrót")
    choice = input("\n Wybór: ").lower()
    
    if choice == 'a':
        try:
            idx = int(input(" Podaj ID urządzenia: ")) - 1
            if 0 <= idx < len(found):
                t = found[idx]
                print(f"\n --- DODAWANIE DO WOL: {t['ip']} ---")
                name = input(f" Nazwa (Enter dla {t['vendor'][:15]}): ") or t['vendor'][:15]
                
                current_db = db_wol.load_wol_profiles()
                
                # Ostatnie pole pozostaje puste dla zgodności ze starszą bazą.
                current_db.append([name, t['mac'], t['ip'], "-"])
                db_wol.save_wol_profiles(current_db)
                
                print(" [V] Dodano profil do bazy."); time.sleep(1.5)
        except Exception as e: 
            print(f" [!] Błąd: {e}"); time.sleep(2)
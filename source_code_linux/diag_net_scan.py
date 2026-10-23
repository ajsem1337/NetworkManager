#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, subprocess, concurrent.futures, time
import core_report, core_mac_lookup, core_config, db_wol
import security_utils

def wake_up_ip(ip):
    # Linux ping: -c (count), -W (timeout sec)
    if not security_utils.validate_ipv4(ip):
        return
    subprocess.run(["ping", "-c", "1", "-W", "1", ip], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=3)

def get_local_ip_prefix():
    try:
        # Pobieramy src IP trasy domyślnej
        route = subprocess.check_output(["ip", "route", "get", "1.1.1.1"], text=True, timeout=5).split()
        source_ip = route[route.index("src") + 1]
        if security_utils.validate_ipv4(source_ip):
            return ".".join(source_ip.split(".")[:-1]) + "."
        return "192.168.1."
    except: return "192.168.1."

def run():
    core_config.clear_screen()
    prefix = get_local_ip_prefix()
    print(f" [*] Skanowanie sieci {prefix}0/24 (ARP + Ping Sweep)...")
    
    # Pingowanie w tle
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as ex:
        ex.map(wake_up_ip, [f"{prefix}{i}" for i in range(1, 255)])

    # Odczyt tablicy ARP (ip neigh)
    try:
        raw = subprocess.check_output(["ip", "neigh"], timeout=5).decode()
    except: raw = ""
    
    found = []
    print(f"\n {'ID':<4} | {'IP':<15} | {'MAC ADDRESS':<18} | {'PRODUCENT'}")
    print("-" * 80)
    
    # Format ip neigh: "192.168.1.1 dev eth0 lladdr aa:bb:cc... REACHABLE"
    lines = raw.strip().split('\n')
    idx = 1
    for line in lines:
        parts = line.split()
        if len(parts) >= 5 and "lladdr" in parts:
            ip = parts[0]
            if not ip.startswith(prefix): continue
            
            mac_idx = parts.index("lladdr") + 1
            mac = parts[mac_idx].upper()
            
            vendor = core_mac_lookup.get_vendor(mac)
            print(f" [{idx:02}] | {ip:<15} | {mac:<18} | {vendor[:30]}")
            found.append({"ip": ip, "mac": mac, "vendor": vendor})
            idx += 1

    print("\n [A] Dodaj do bazy WOL   [0] Powrót")
    choice = input("\n Wybór: ").lower()
    
    if choice == 'a':
        try:
            sel = int(input(" ID urządzenia: ")) - 1
            if 0 <= sel < len(found):
                t = found[sel]
                name = input(f" Nazwa (Enter={t['vendor'][:10]}): ") or t['vendor'][:10]
                
                db = db_wol.load_wol_profiles()
                db.append([name, t['mac'], t['ip'], "-"])
                db_wol.save_wol_profiles(db)
                print(" [OK] Dodano."); time.sleep(1)
        except: pass
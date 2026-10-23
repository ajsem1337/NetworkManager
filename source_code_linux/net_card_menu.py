#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import subprocess
import time
import db_ip
import core_config
import ipaddress
import security_utils

G, R, C, Y, RESET = '\033[92m', '\033[91m', '\033[96m', '\033[93m', '\033[0m'


def get_connection_profile(iface):
    """Znajduje nazwę profilu (np. 'Wired connection 1') przypisaną do interfejsu."""
    try:
        out = subprocess.check_output(
            ["nmcli", "-t", "-f", "NAME,DEVICE", "con", "show"],
            text=True,
            stderr=subprocess.DEVNULL
        )
        for line in out.splitlines():
            parts = line.split(":")
            if len(parts) > 1 and parts[1] == iface:
                return parts[0]
    except: 
        pass
    return None


def get_adapter_status(iface):
    try:
        with open(f"/sys/class/net/{iface}/operstate") as f:
            state = f.read().strip()
        with open(f"/sys/class/net/{iface}/address") as f:
            mac = f.read().strip()
        st_color = G if state == "up" else R
        return f"{st_color}{state.upper()}{RESET}", mac
    except: 
        return f"{R}DOWN{RESET}", "00:00:00:00:00:00"


def get_current_config(iface):
    cfg = {"ip": "-", "mask": "-", "gw": "-", "dns1": "-", "dns2": "-"}
    try:
        # 1. IP i Maska
        out = subprocess.check_output(
            ["ip", "-4", "addr", "show", "dev", iface],
            text=True,
            stderr=subprocess.DEVNULL
        )
        for line in out.splitlines():
            if "inet " in line:
                parts = line.strip().split()
                ip_cidr = parts[1]
                if "/" in ip_cidr:
                    ip_obj = ipaddress.IPv4Interface(ip_cidr)
                    cfg['ip'] = str(ip_obj.ip)
                    cfg['mask'] = str(ip_obj.netmask)
                else:
                    cfg['ip'] = ip_cidr
                break
        
        # 2. Brama
        out_gw = subprocess.check_output(["ip", "route"], text=True, stderr=subprocess.DEVNULL)
        for line in out_gw.splitlines():
            if "default" in line and iface in line:
                cfg['gw'] = line.split()[2]
                break

        # 3. DNS
        out_dns = subprocess.check_output(
            ["nmcli", "dev", "show", iface],
            text=True,
            stderr=subprocess.DEVNULL
        )
        dns_list = []
        for line in out_dns.splitlines():
            if "DNS" in line and ":" in line:
                dns_list.append(line.split(":")[1].strip())
        if len(dns_list) > 0: 
            cfg['dns1'] = dns_list[0]
        if len(dns_list) > 1: 
            cfg['dns2'] = dns_list[1]
    except: 
        pass
    return cfg


def mask_to_cidr(mask):
    try: 
        return ipaddress.IPv4Network(f"0.0.0.0/{mask}", strict=False).prefixlen
    except: 
        return 24


def apply_config(iface, ip, mask, gw, d1, d2):
    """Apply network configuration with proper validation and no shell injection."""
    if not security_utils.validate_interface_name(iface) or not security_utils.validate_netmask(mask):
        print(f" {R}[BŁĄD]{RESET} Nieprawidłowy interfejs lub maska")
        return
    if not security_utils.validate_ipv4(ip):
        print(f" {R}[BŁĄD]{RESET} Nieprawidłowy adres IP")
        return
    
    if gw and gw not in ["-", "", "None", "0.0.0.0"] and not security_utils.validate_ipv4(gw):
        print(f" {R}[BŁĄD]{RESET} Nieprawidłowa brama")
        return
    
    if d1 and d1 not in ["-", ""] and not security_utils.validate_ipv4(d1):
        print(f" {R}[BŁĄD]{RESET} Nieprawidłowy DNS 1")
        return
    
    if d2 and d2 not in ["-", ""] and not security_utils.validate_ipv4(d2):
        print(f" {R}[BŁĄD]{RESET} Nieprawidłowy DNS 2")
        return
    
    con = get_connection_profile(iface)
    if not con:
        print(f" {Y}[INFO]{RESET} Brak profilu dla {iface}. Tworzę nowy...")
        con = f"Wired connection {iface}"
        try:
            subprocess.run(
                ["sudo", "nmcli", "con", "add", "type", "ethernet", 
                 "con-name", con, "ifname", iface],
                check=False,
                timeout=5
            )
            time.sleep(1)
        except Exception as e:
            print(f" {R}[BŁĄD]{RESET} Nie udało się utworzyć profilu: {e}")
            return

    cidr = mask_to_cidr(mask)
    print(f" [i] Konfiguracja profilu '{con}'...")
    
    dns_list = []
    if d1 and d1 not in ["-", ""]: 
        dns_list.append(d1)
    if d2 and d2 not in ["-", ""]: 
        dns_list.append(d2)
    dns_str = ' '.join(dns_list) if dns_list else ''

    cmd = ["sudo", "nmcli", "con", "mod", con, 
           f"ipv4.addresses", f"{ip}/{cidr}",
           "ipv4.method", "manual"]
    
    if gw and gw not in ["-", "", "None", "0.0.0.0"]:
        cmd.extend(["ipv4.gateway", gw])
    
    if dns_str:
        cmd.extend(["ipv4.dns", dns_str])
    
    try:
        if subprocess.call(cmd, timeout=5) == 0:
            print(" [i] Restartowanie interfejsu...")
            subprocess.run(
                ["sudo", "nmcli", "con", "down", con],
                timeout=5,
                stderr=subprocess.DEVNULL,
                check=False
            )
            subprocess.run(
                ["sudo", "nmcli", "con", "up", con],
                timeout=5,
                check=False
            )
            print(f" {G}[SUKCES]{RESET} Ustawiono IP: {ip}/{cidr}")
        else:
            print(f" {R}[BŁĄD]{RESET} Nie udało się zapisać zmian.")
    except subprocess.TimeoutExpired:
        print(f" {R}[BŁĄD]{RESET} Timeout przy konfiguracji")
    except Exception as e:
        print(f" {R}[BŁĄD]{RESET} {e}")
    time.sleep(2)


def set_dhcp(iface):
    """Set interface to DHCP with proper validation."""
    con = get_connection_profile(iface)
    if not con: 
        print(f" {R}[BŁĄD]{RESET} Nie znaleziono profilu połączenia.")
        return

    print(f" [i] Ustawianie DHCP dla '{con}'...")
    try:
        cmd = ["sudo", "nmcli", "con", "mod", con,
               "ipv4.method", "auto",
               "ipv4.addresses", "",
               "ipv4.gateway", "",
               "ipv4.dns", ""]
        
        if subprocess.call(cmd, timeout=5) == 0:
            subprocess.run(
                ["sudo", "nmcli", "con", "down", con],
                timeout=5,
                stderr=subprocess.DEVNULL,
                check=False
            )
            subprocess.run(
                ["sudo", "nmcli", "con", "up", con],
                timeout=5,
                check=False
            )
            print(f" {G}[SUKCES]{RESET} DHCP Aktywne.")
        else:
            print(f" {R}[BŁĄD]{RESET} Nie udało się ustawić DHCP")
    except subprocess.TimeoutExpired:
        print(f" {R}[BŁĄD]{RESET} Timeout")
    except Exception as e:
        print(f" {R}[BŁĄD]{RESET} {e}")
    time.sleep(2)


def toggle_iface(iface, state):
    """Inteligentne włączanie/wyłączanie karty."""
    if not security_utils.validate_interface_name(iface):
        print(f" {R}[BŁĄD]{RESET} Nieprawidłowa nazwa interfejsu")
        return
    
    print(f" [i] Zmieniam stan {iface} na: {state.upper()}...")
    
    try:
        if state == "down":
            subprocess.run(
                ["sudo", "nmcli", "dev", "disconnect", iface],
                timeout=5,
                stderr=subprocess.DEVNULL,
                check=False
            )
            subprocess.run(
                ["sudo", "ip", "link", "set", iface, "down"],
                timeout=5,
                check=False
            )
        else:
            subprocess.run(
                ["sudo", "ip", "link", "set", iface, "up"],
                timeout=5,
                check=False
            )
            time.sleep(0.5)
            subprocess.run(
                ["sudo", "nmcli", "dev", "connect", iface],
                timeout=5,
                check=False
            )
    except subprocess.TimeoutExpired:
        print(f" {R}[BŁĄD]{RESET} Timeout")
    except Exception as e:
        print(f" {R}[BŁĄD]{RESET} {e}")
    
    time.sleep(1.5)


def run(iface):
    if not security_utils.validate_interface_name(iface):
        print(f" {R}[BŁĄD]{RESET} Nieprawidłowa nazwa interfejsu: {iface}")
        return
    
    while True:
        core_config.clear_screen()
        status, mac = get_adapter_status(iface)
        cfg = get_current_config(iface)
        
        print(f"{C}================================================================{RESET}")
        print(f"        KARTA: {Y}{iface}{RESET}  |  MAC: {mac}")
        print(f"        STATUS: {status:<19}")
        print(f"        IP: {cfg['ip']:<15} MASKA: {cfg['mask']}")
        print(f"        GW: {cfg['gw']:<15} DNS: {cfg['dns1']}, {cfg['dns2']}")
        print(f"{C}================================================================{RESET}")
        
        print(f" [{G}1{RESET}] DHCP (Auto)")
        print(f" [{G}2{RESET}] Ustaw ręcznie IP")
        print(f" [{G}3{RESET}] Baza Profili")
        print(f" [{G}4{RESET}] Restart (Down/Up)")
        print(f" [{G}ON{RESET}] Włącz kartę        [{R}OFF{RESET}] Wyłącz kartę")
        print(f" [{G}5{RESET}] Snapshot do bazy")
        print(f"\n [{R}0{RESET}] Powrót")
        
        c = input("\n Wybór: ").strip().lower()
        
        if c == '0': 
            break
        elif c == '1': 
            set_dhcp(iface)
        elif c == '2':
            d = db_ip.manual_input_profile()
            if d: 
                apply_config(iface, d[1], d[2], d[3], d[4], d[5])
        elif c == '3':
            p = db_ip.select_profile_menu(mode="SELECT")
            if p: 
                apply_config(iface, p[1], p[2], p[3], p[4], p[5])
        elif c == '4':
            toggle_iface(iface, "down")
            toggle_iface(iface, "up")
        elif c == 'on': 
            toggle_iface(iface, "up")
        elif c == 'off': 
            toggle_iface(iface, "down")
        elif c == '5':
            name = input(" Nazwa profilu: ").strip()
            if name and security_utils.validate_profile_name(name):
                snap_gw = cfg['gw'] if cfg['gw'] else "-"
                snap_d1 = cfg['dns1'] if cfg['dns1'] else "8.8.8.8"
                snap_d2 = cfg['dns2'] if cfg['dns2'] else "-"
                db_ip.save_all(db_ip.load_all_profiles() + [[name, cfg['ip'], cfg['mask'], snap_gw, snap_d1, snap_d2]])
                print(f" {G}Zapisano.{RESET}")
                time.sleep(1)
            else:
                print(f" {R}[!] Nieprawidłowa nazwa profilu{RESET}")
                input("\nEnter...")


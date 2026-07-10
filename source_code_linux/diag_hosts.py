#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import subprocess
import time
import core_config
import security_utils

PATH = "/etc/hosts"


def run():
    while True:
        core_config.clear_screen()
        print("=== EDYTOR /ETC/HOSTS ===")
        print(" [1] Wyświetl")
        print(" [2] Dodaj wpis (sudo)")
        print(" [3] Edytuj w nano (sudo)")
        print(" [0] Powrót")
        
        c = input("\n Wybór: ")
        if c == '0': 
            break
        elif c == '1':
            try:
                with open(PATH, 'r') as f:
                    print(f.read())
            except PermissionError:
                print(" [!] Brak uprawnień do czytania /etc/hosts")
            except Exception as e:
                print(f" [!] Błąd: {e}")
            input("\n Enter...")
        elif c == '2':
            ip = input(" IP: ").strip()
            dom = input(" Domena: ").strip()
            
            if not ip or not dom:
                print(" [!] IP i domena nie mogą być puste")
                input("\nEnter...")
                continue
            
            if not security_utils.validate_ipv4(ip):
                print(" [!] Nieprawidłowy adres IP")
                input("\nEnter...")
                continue
            
            if not security_utils.validate_hostname(dom):
                print(" [!] Nieprawidłowa domena")
                input("\nEnter...")
                continue
            
            entry = f"{ip} {dom}\n"
            try:
                proc = subprocess.run(
                    ["sudo", "tee", "-a", PATH],
                    input=entry,
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if proc.returncode == 0:
                    print(" [OK] Dodano.")
                else:
                    print(f" [!] Błąd: {proc.stderr}")
            except subprocess.TimeoutExpired:
                print(" [!] Timeout przy dodawaniu wpisu")
            except Exception as e:
                print(f" [!] Błąd: {e}")
            time.sleep(1)
        elif c == '3':
            try:
                subprocess.run(["sudo", "nano", PATH])
            except FileNotFoundError:
                print(" [!] Polecenie 'nano' nie znalezione")
            except Exception as e:
                print(f" [!] Błąd: {e}")
            input("\nEnter...")
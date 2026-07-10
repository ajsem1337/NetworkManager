#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import subprocess
import core_config
import security_utils


def run_menu():
    while True:
        core_config.clear_screen()
        print("=== MENU PING (LINUX) ===\n [1] Google (x4)\n [2] Google (Ciągły)\n [3] Własny (x4)\n [4] Własny (Ciągły)")
        print(" [0] Powrót")
        
        c = input("\n Wybór: ")
        if c == '0': 
            break
        
        try:
            if c == '1': 
                subprocess.run(["ping", "-c", "4", "8.8.8.8"])
            elif c == '2': 
                subprocess.run(["ping", "8.8.8.8"])
            elif c == '3': 
                adr = input(" Adres: ").strip()
                if not adr:
                    print(" [!] Pusty adres!")
                    input("\nEnter...")
                    continue
                if not security_utils.validate_hostname(adr):
                    print(" [!] Nieprawidłowy adres (IP lub domena)")
                    input("\nEnter...")
                    continue
                subprocess.run(["ping", "-c", "4", adr])
            elif c == '4': 
                adr = input(" Adres: ").strip()
                if not adr:
                    print(" [!] Pusty adres!")
                    input("\nEnter...")
                    continue
                if not security_utils.validate_hostname(adr):
                    print(" [!] Nieprawidłowy adres (IP lub domena)")
                    input("\nEnter...")
                    continue
                subprocess.run(["ping", adr])
            
            input("\n[KONIEC] Enter...")
        except KeyboardInterrupt: 
            pass
        except FileNotFoundError:
            print(" [!] Polecenie 'ping' nie znalezione")
            input("\nEnter...")
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import subprocess
import sys
import core_config
import security_utils


def run():
    while True:
        core_config.clear_screen()
        print("================================================================")
        print("                ŚLEDZENIE TRASY (TRACEPATH) ")
        print("================================================================")
        
        target = input("\n Podaj adres IP lub domenę (np. google.com) lub [0] aby wrócić: ").strip()
        
        if target == '0' or not target: 
            break
        
        if not security_utils.validate_hostname(target):
            print(" [!] Nieprawidłowy adres (IP lub domena)")
            input("\nEnter...")
            continue

        print(f"\n [!] Rozpoczynam śledzenie drogi do: {target}")
        print(" [!] Używam narzędzia 'tracepath' (Linux standard).\n")
        print("-" * 64)

        try:
            process = subprocess.Popen(
                ['tracepath', target], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT, 
                text=True
            )

            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                if line:
                    print(f" {line.strip()}")
                    sys.stdout.flush()

        except KeyboardInterrupt:
            print("\n\n [!] Przerwano przez użytkownika.")
            if process: 
                process.terminate()
        except FileNotFoundError:
             print("\n [!] Nie znaleziono polecenia 'tracepath'. Zainstaluj: sudo apt install iputils-tracepath")
        except Exception as e:
            print(f"\n [!] Wystąpił błąd: {e}")
        
        print("-" * 64)
        input("\n Koniec. Enter...")
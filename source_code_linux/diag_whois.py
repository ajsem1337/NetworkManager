#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests, core_report, core_config, security_utils

def run():
    while True:
        core_config.clear_screen()
        print("=== WHOIS / REJESTRACJA DOMENY (RDAP) ===\n")
        domain = input(" Podaj domenę (np. google.com) lub [0] aby wrócić: ").strip()
        
        if not domain or domain == '0': break
        
        if not security_utils.validate_hostname(domain):
            print(" [!] Nieprawidłowa domena.")
            input(" Enter...")
            continue

        print(f"\n [i] Pobieranie danych dla: {domain}...")
        
        try:
            headers = {
                "User-Agent": "NetworkMaster"
            }
            
            # Używamy API, które lepiej radzi sobie z przekierowaniami
            r = requests.get(f"https://rdap.org/domain/{domain}", headers=headers, timeout=10)
            
            if r.status_code == 200:
                data = r.json()
                
                events = data.get('events', [])
                created = "Brak danych"
                expired = "Brak danych"
                
                for e in events:
                    if e.get('eventAction') == 'registration': created = e.get('eventDate')
                    if e.get('eventAction') == 'expiration': expired = e.get('eventDate')
                
                output = f"\n WYNIK DLA: {domain.upper()}\n"
                output += f" {'-'*40}\n"
                output += f" REJESTRACJA: {created[:10]}\n"
                output += f" WYGASA:      {expired[:10]}\n"
                output += f" HANDLE:      {data.get('handle', 'N/A')}\n"
                
                # Wyciąganie statusów w czytelniejszy sposób
                statuses = data.get('status', [])
                output += f" STATUS:      {', '.join(statuses)}\n"
                output += f" {'-'*40}\n"
                
                print(output)
                
                if input(" [?] Zapisać raport? (t/n): ").lower() == 't':
                    core_report.save(output, f"Whois_{domain}")
            
            elif r.status_code == 404:
                print(f" [!] Domena {domain} prawdopodobnie jest WOLNA lub nie istnieje.")
            elif r.status_code == 403:
                print(" [!] Dostęp zabroniony (403). Serwer zablokował zapytanie.")
            elif r.status_code == 429:
                print(" [!] Zbyt wiele zapytań (Rate Limit). Odczekaj chwilę.")
            else:
                print(f" [!] Błąd API: {r.status_code}")
                
        except Exception as e:
            print(f" [!] Błąd połączenia: {e}")
        
        input("\n Enter...")

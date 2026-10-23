#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, requests, core_report, core_config

def run():
    core_config.clear_screen()
    print("=== LOKALIZACJA GEOGRAFICZNA IP ===\n")
    print(" [i] Pobieranie danych...")
    
    try:
        response = requests.get("https://ipwho.is/", timeout=5)
        response.raise_for_status()
        response = response.json()
        if response.get('success') is True:
            data = f"""
 ADRES IP:    {response['ip']}
 KRAJ:        {response['country']} ({response['country_code']})
 MIASTO:      {response['city']}
 REGION:      {response['region']}
 DOSTAWCA:    {response['connection']['isp']}
"""
            print(data)
            print("-" * 40)
            if input(" [?] Zapisać raport? (t/n): ").lower() == 't':
                core_report.save(data, "Raport_GeoIP")
        else:
            print(" [!] Błąd API.")
    except Exception as e:
        print(f" [!] Błąd połączenia: {e}")
        
    input("\n Enter...")
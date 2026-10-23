import os, requests, core_report

def run():
    os.system('cls')
    print("=== LOKALIZACJA GEOGRAFICZNA IP ===\n")
    print(" [i] Pobieranie danych o Twoim publicznym adresie IP...")
    
    try:
        # GeoIP przez HTTPS; format odpowiedzi: https://ipwhois.io/documentation
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
                print(" [OK] Zapisano.")
        else:
            print(" [!] Nie udało się pobrać danych.")
            
    except Exception as e:
        print(f" [!] Błąd połączenia z serwerem GeoIP: {e}")
        print(" [i] Upewnij się, że masz połączenie z internetem.")
        
    input("\n Naciśnij Enter, aby wrócić...")
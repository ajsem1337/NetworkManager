import os, subprocess, re, core_report

def run():
    os.system('cls')
    print("="*90)
    print("                WIFI SECURITY AUDITOR - NETWORK MASTER")
    print("="*90)
    
    try:
        # Pobieranie listy profili (obsługa wersji PL i EN)
        raw = subprocess.run(["netsh", "wlan", "show", "profiles"], capture_output=True, text=True, encoding='cp852', timeout=15).stdout
        profiles = re.findall(r"(?:All User Profile|Profil wszystkich użytkowników)\s*:\s*(.*)", raw)
        
        data, max_l = [], 15
        for p in [x.strip() for x in profiles]:
            out = subprocess.run(["netsh", "wlan", "show", "profile", "name=" + p, "key=clear"], capture_output=True, text=True, encoding='cp852', timeout=15).stdout
            
            # Wyciąganie typu zabezpieczeń
            auth_match = re.search(r"(?:Authentication|Uwierzytelnianie)\s*:\s*(.*)", out)
            auth = auth_match.group(1).strip() if auth_match else "Nieznane"
            
            # Wyciąganie hasła
            pwd_match = re.search(r"(?:Key Content|Zawartość klucza)\s*:\s*(.*)", out)
            pwd_raw = pwd_match.group(1).strip() if pwd_match else None
            
            # Logika statusu dla WPA3 i zwykłych haseł
            if "WPA3" in auth or "SAE" in auth:
                pwd = pwd_raw if pwd_raw else "[CHRONIONE WPA3-SAE]"
            elif pwd_raw:
                pwd = pwd_raw
            else:
                pwd = "-"
                
            data.append((p, auth, pwd))
            max_l = max(max_l, len(p))
        
        # Formatowanie tabeli z nową kolumną TYP
        fmt = f"%-{max_l}s | %-20s | %s"
        header = fmt % ("NAZWA SIECI", "TYP ZABEZPIECZEŃ", "HASŁO / STATUS")
        print(header)
        print("-" * (max_l + 45))
        
        res_txt = header + "\n" + ("-" * (max_l + 45)) + "\n"
        
        for n, t, k in data:
            line = fmt % (n, t, k)
            print(line)
            res_txt += line + "\n"
            
        if input("\n Zapisać raport z hasłami WiFi? (t/n): ").strip().lower() == "t":
            core_report.save(res_txt, "WiFi_Security_Audit")
        
    except Exception as e: 
        print(f" [!] Błąd odczytu WiFi: {e}")
        
    # Odczyt zależy od uprawnień i sposobu przechowywania klucza w systemie.
    print("\n" + "="*90)
    print(" INFO: Raport może zawierać hasła WiFi w jawnym tekście.")
    print(" Status [CHRONIONE] oznacza, że system operacyjny ukrył klucz dla bezpieczeństwa.")
    print("="*90)
    
    input("\nNaciśnij Enter, aby wrócić...")
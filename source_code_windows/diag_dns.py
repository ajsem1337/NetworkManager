# diag_dns.py
import os, subprocess, core_report, re, security_utils

G, R, C, Y, RESET = '\033[92m', '\033[91m', '\033[96m', '\033[93m', '\033[0m'

DNS_SERVERS = {
    "Google": "8.8.8.8",
    "Cloudflare": "1.1.1.1",
    "OpenDNS": "208.67.222.222",
    "Quad9": "9.9.9.9"
}

def run():
    while True:
        os.system('cls')
        print(f"{C}=== SPRAWDZANIE ADRESÓW WWW (DNS) ==={RESET}")
        print(f" [{G}1{RESET}] Szybkie sprawdzenie (domyślny serwer 8.8.8.8)")
        print(f" [{G}2{RESET}] Test propagacji DNS (wiele serwerów globalnych)")
        print(f" [{R}0{RESET}] Powrót")
        
        c = input("\nWybór: ")
        if c == '0': break
        
        if c == '1':
            dom = input(" Podaj nazwę (np. wp.pl): ").strip()
            if not security_utils.validate_hostname(dom):
                print(" [!] Nieprawidłowy host lub adres IP.")
                input(" Enter...")
                continue
            res = subprocess.run(["nslookup", dom, "8.8.8.8"], capture_output=True, text=True, timeout=15, encoding='cp852').stdout
            print(f"\nOdpowiedź serwera:\n{res}")
            core_report.save(res, f"DNS_{dom}")
            input("\nNaciśnij Enter...")
        
        elif c == '2':
            dom = input(" Podaj domenę do testu propagacji: ").strip()
            if not security_utils.validate_hostname(dom):
                print(" [!] Nieprawidłowy host lub adres IP.")
                input(" Enter...")
                continue
            print(f"\n {Y}[i] Sprawdzanie propagacji dla: {dom}{RESET}\n")
            
            results = f"Test propagacji DNS dla: {dom}\n"
            results += "-" * 50 + "\n"
            
            for name, ip in DNS_SERVERS.items():
                print(f" [*] Odpytywanie {name:<11} ({ip:<15})...", end="", flush=True)
                # Używamy nslookup, aby faktycznie zapytać konkretny serwer (ChatGPT użył lokalnego cache)
                try:
                    res = subprocess.run(["nslookup", dom, ip], capture_output=True, text=True, timeout=15, encoding='cp852').stdout
                    ips = re.findall(r'Address(?:es)?:\s+((?:\d{1,3}\.){3}\d{1,3})', res)
                    
                    # Odrzucamy IP samego serwera DNS
                    valid_ips = [i for i in ips if i != ip]
                    
                    if valid_ips:
                        print(f" {G}OK{RESET} -> {', '.join(valid_ips)}")
                        results += f"{name:12} ({ip:15}) -> {', '.join(valid_ips)}\n"
                    else:
                        print(f" {R}BRAK REKORDU{RESET}")
                        results += f"{name:12} ({ip:15}) -> BRAK REKORDU\n"
                except Exception as e:
                    print(f" {R}BŁĄD{RESET}")
                    results += f"{name:12} ({ip:15}) -> BŁĄD ({e})\n"
                    
            print("-" * 55)
            if input(" [?] Zapisać raport? (t/n): ").lower() == 't':
                core_report.save(results, f"DNS_Propagacja_{dom}")
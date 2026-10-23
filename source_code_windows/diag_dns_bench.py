import os
import subprocess
import re
import time
import core_report
import security_utils

G, R, C, Y, RESET = '\033[92m', '\033[91m', '\033[96m', '\033[93m', '\033[0m'

# Baza popularnych publicznych serwerów DNS
DNS_SERVERS = {
    "Cloudflare": "1.1.1.1",
    "Google": "8.8.8.8",
    "Quad9": "9.9.9.9",
    "OpenDNS": "208.67.222.222",
    "AdGuard": "94.140.14.14",
    "Control D": "76.76.2.0",
    "Mullvad": "194.242.2.2"
}

def ping_server(ip):
    """Wykonuje 3 pingi do serwera i zwraca średni czas w ms. Zwraca 9999 jeśli błąd."""
    try:
        # -n 3: trzy pakiety, -w 1000: timeout 1 sekunda na pakiet
        if not security_utils.validate_ipv4(ip):
            return 9999
        cmd = ["ping", "-n", "3", "-w", "1000", ip]
        # Używamy cp852 dla polskiego Windowsa, ignorujemy błędy znaków
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=8, encoding='cp852', errors='ignore').stdout
        
        # Szukamy wartości "Średnio = X ms" lub "Average = Xms"
        # Regex łapie formaty: Średnio = 15 ms, Srednio=15ms, Average = 15ms
        match = re.search(r"(?:Average|rednio|Średnio|srednio)\s*=\s*(\d+)", res)
        
        if match:
            return int(match.group(1))
        else:
            return 9999 # Brak odpowiedzi lub 100% loss
    except Exception:
        return 9999

def draw_bar(latency):
    """Rysuje pasek wydajności (im krótszy czas, tym zieleńszy/lepszy pasek)."""
    if latency == 9999:
        return f"{R}[ BRAK ODPOWIEDZI ]{RESET}"
        
    bar_length = 20
    # Zakładamy, że 100ms to bardzo wolno (cały pasek wypełniony na czerwono)
    filled = min(int((latency / 100) * bar_length), bar_length)
    
    if latency < 20:
        color = G
    elif latency < 50:
        color = Y
    else:
        color = R
        
    bar = "█" * filled + "░" * (bar_length - filled)
    return f"{color}[{bar}] {latency} ms{RESET}"

def run():
    while True:
        os.system('cls')
        print(f"{C}================================================================{RESET}")
        print(f"                {Y}DNS BENCHMARK (TEST SZYBKOŚCI){RESET}")
        print(f"{C}================================================================{RESET}")
        print(" [i] Program przetestuje najpopularniejsze serwery DNS, aby pomóc")
        print("     Ci wybrać ten o najniższym opóźnieniu dla Twojego łącza.")
        print("----------------------------------------------------------------")
        
        if input("\n Rozpocząć test? (t/n): ").strip().lower() != 't':
            break

        print("\n [*] Testowanie serwerów w toku (to zajmie kilkanaście sekund)...\n")
        
        results = []
        for name, ip in DNS_SERVERS.items():
            print(f"     > Pingowanie: {name:<12} ({ip})...", end="", flush=True)
            latency = ping_server(ip)
            results.append({"name": name, "ip": ip, "latency": latency})
            if latency == 9999:
                print(f" {R}TIMEOUT{RESET}")
            else:
                print(f" {G}{latency} ms{RESET}")
                
        # Sortowanie od najszybszego
        results.sort(key=lambda x: x["latency"])
        
        os.system('cls')
        print(f"{C}================================================================{RESET}")
        print(f"                  {Y}WYNIKI TESTU SERWERÓW DNS{RESET}")
        print(f"{C}================================================================{RESET}")
        print(f" {'DOSTAWCA':<12} | {'ADRES IP':<15} | {'OPÓŹNIENIE (LATENCJA)'}")
        print("-" * 64)
        
        report_text = "RAPORT DNS BENCHMARK\n---------------------------------\n"
        
        for idx, res in enumerate(results, 1):
            name, ip, lat = res["name"], res["ip"], res["latency"]
            bar = draw_bar(lat)
            
            # Najszybszy dostaje koronę/gwiazdkę
            mark = f"{Y}*{RESET}" if idx == 1 and lat != 9999 else " "
            
            print(f" {mark}{name:<11} | {ip:<15} | {bar}")
            
            # Format tekstowy do raportu
            lat_txt = "TIMEOUT" if lat == 9999 else f"{lat} ms"
            report_text += f"{idx}. {name} ({ip}) - {lat_txt}\n"
            
        print("-" * 64)
        print(f" {Y}[*] Najszybszy serwer dla Twojej lokalizacji to: {results[0]['name']}{RESET}")
        print("\n [?] Zapisać wyniki do pliku?")
        
        if input(" Wybór (t/n): ").strip().lower() == 't':
            core_report.save(report_text, "DNS_Benchmark")
            
        input("\n Naciśnij Enter, aby powrócić do menu głównego...")
        break
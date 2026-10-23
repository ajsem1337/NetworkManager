import os, ssl, socket
from datetime import datetime
import core_report

G, R, C, Y, RESET = '\033[92m', '\033[91m', '\033[96m', '\033[93m', '\033[0m'

def run():
    while True:
        os.system('clear')
        print(f"{C}================================================================{RESET}")
        print(f"                  {Y}AUDYT CERTYFIKATÓW SSL/TLS{RESET}")
        print(f"{C}================================================================{RESET}")
        
        host = input("\n Podaj hosta (np. google.com) lub [0] aby wrócić: ").strip()
        
        if host == '0' or not host:
            break
            
        print(f"\n [i] Pobieranie certyfikatu z {host}:443 ...")
        
        try:
            ctx = ssl.create_default_context()
            ctx.minimum_version = ssl.TLSVersion.TLSv1_2
            with ctx.wrap_socket(socket.socket(), server_hostname=host) as s:
                s.settimeout(5)
                s.connect((host, 443))
                cert = s.getpeercert()

                issuer = dict(x[0] for x in cert['issuer'])
                issuer_name = issuer.get('organizationName', 'Nieznany')
                
                subject = dict(x[0] for x in cert['subject'])
                subject_name = subject.get('commonName', 'Nieznany')

                exp = cert['notAfter']
                exp_date = datetime.strptime(exp, "%b %d %H:%M:%S %Y %Z")
                days_left = (exp_date - datetime.utcnow()).days

                print(f"\n {G}>>> DANE CERTYFIKATU:{RESET}")
                print(f" ----------------------------------------------------------------")
                print(f" WYSTAWIONY DLA: {C}{subject_name}{RESET}")
                print(f" WYSTAWCA (CA):  {C}{issuer_name}{RESET}")
                print(f" DATA WAŻNOŚCI:  {Y}{exp_date.strftime('%Y-%m-%d %H:%M:%S')} UTC{RESET}")
                
                if days_left < 10:
                    print(f" STATUS:         {R}KRYTYCZNY ({days_left} DNI DO KOŃCA){RESET}")
                elif days_left < 30:
                    print(f" STATUS:         {Y}OSTRZEŻENIE ({days_left} DNI DO KOŃCA){RESET}")
                else:
                    print(f" STATUS:         {G}PRAWIDŁOWY ({days_left} DNI DO KOŃCA){RESET}")
                print(f" ----------------------------------------------------------------")
                
                report_txt = f"AUDYT SSL DLA: {host}\nWygaśnięcie: {exp_date}\nPozostało dni: {days_left}\nWystawca: {issuer_name}"
                if input("\n [?] Zapisać wyniki do pliku? (t/n): ").strip().lower() == 't':
                    core_report.save(report_txt, f"SSL_{host}")
                    
        except socket.gaierror:
            print(f" {R}[BŁĄD] Nie można rozwiązać nazwy hosta.{RESET}")
        except ssl.SSLError as e:
            print(f" {R}[BŁĄD SSL] Błąd weryfikacji certyfikatu: {e}{RESET}")
        except Exception as e:
            print(f" {R}[BŁĄD] Wystąpił problem: {e}{RESET}")
            
        input("\n Naciśnij Enter, aby sprawdzić inny adres...")
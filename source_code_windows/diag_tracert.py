import os
import subprocess
import sys
import security_utils

def run():
    while True:
        os.system('cls')
        print("================================================================")
        print("                ŚLEDZENIE TRASY (TRACEROUTE) ")
        print("================================================================")
        
        target = input("\n Podaj adres IP lub domenę (np. google.com) lub [0] aby wrócić: ").strip()
        
        if target == '0' or not target:
            break

        if not security_utils.validate_hostname(target):
            print(" [!] Nieprawidłowy host lub adres IP.")
            input(" Enter...")
            continue

        print(f"\n [!] Rozpoczynam śledzenie drogi do: {target}")
        print(" [!] To może potrwać kilka minut. Każdy skok pojawi się poniżej:\n")
        print("-" * 64)

        try:
            # Uruchamiamy proces tracert z parametrem -d (szybsze, bez DNS) lub bez niego
            # stdout=subprocess.PIPE pozwala nam "przechwycić" tekst w locie
            process = subprocess.Popen(
                ['tracert', '-d', target], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT, 
                text=True
            )

            # Czytamy wynik linia po linii w czasie rzeczywistym
            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                if line:
                    print(f" {line.strip()}")
                    sys.stdout.flush() # Wymuszamy natychmiastowe wypisanie na ekranie

        except KeyboardInterrupt:
            print("\n\n [!] Śledzenie przerwane przez użytkownika.")
            if process:
                process.terminate()
        except Exception as e:
            print(f"\n [!] Wystąpił błąd: {e}")
        
        print("-" * 64)
        input("\n Koniec trasowania. Naciśnij Enter, aby kontynuować...")
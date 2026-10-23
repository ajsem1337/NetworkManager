# NetworkMaster

![Made with AI](https://img.shields.io/badge/Made%20with-AI-76ddcf)

Konsolowe narzędzie do diagnostyki i konfiguracji sieci na Linuxie i Windowsie. Repozytorium NetworkManager zawiera dwie osobne wersje aplikacji: `source_code_linux` i `source_code_windows`.

## Funkcje

- Ping, traceroute, DNS lookup, WHOIS/RDAP i sprawdzanie certyfikatów TLS.
- Skanowanie portów, wykrywanie urządzeń w LAN i odczyt producenta karty po MAC.
- Dashboard, monitor ruchu i sygnału WiFi, kalkulator podsieci.
- Konfiguracja IP, DHCP i DNS, baza profili, Wake-on-LAN.
- Edytor pliku hosts, czyszczenie DNS i reset konfiguracji sieci.
- Odczyt zapisanych haseł WiFi oraz eksport raportów tekstowych.

„DNS Benchmark” mierzy opóźnienie ICMP do serwerów DNS; nie mierzy czasu rozwiązywania nazw. Skaner LAN sprawdza zakres `/24` wybrany na podstawie lokalnego adresu, a nie wszystkie możliwe podsieci.

## Uruchomienie

Wymagany jest Python 3.11 lub nowszy oraz pakiet `requests`. Uruchamiaj kod z własnego katalogu użytkownika, w którym aplikacja może zapisywać dane.

### Linux

```bash
git clone https://github.com/ajsem1337/NetworkManager.git
cd NetworkManager
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python source_code_linux/main.py
```

Poszczególne moduły korzystają z narzędzi systemowych: `ip`, `ping`, `tracepath`, `nslookup`, `ss`, `nmcli`, `iwconfig`, `ethtool`, `lspci`, `lsusb` i `nano`. Edytor graficzny wymaga `nm-connection-editor`. Reset sieci używa również `systemctl` i `dhclient`. Nazwy pakietów zależą od dystrybucji; brak danego narzędzia ogranicza odpowiednią funkcję.

Zwykła diagnostyka działa bez roota. Zmiany konfiguracji używają `sudo`; odczyt haseł WiFi na Linuxie wymaga uruchomienia z uprawnieniami roota. Nie uruchamiaj całej aplikacji jako root do zwykłej diagnostyki. Katalogi danych są przypisane do użytkownika, który je utworzył — mieszanie uruchomień zwykłych i jako root może spowodować odmowę dostępu.

### Windows

W PowerShellu, po pobraniu lub sklonowaniu repozytorium:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe source_code_windows\main.py
```

Wersja Windows używa narzędzi systemowych, w tym Windows PowerShell, `netsh`, `ipconfig`, `ping`, `tracert` i `nslookup`. Zmiany konfiguracji, edycja hosts i część odczytów WiFi wymagają terminala uruchomionego jako administrator. Parsery części wyników obsługują polskie i angielskie komunikaty; inne języki systemu mogą wymagać dostosowania.

## Dane i bezpieczeństwo

- `core_data/` przy odpowiedniej wersji kodu zawiera flagę pierwszego uruchomienia oraz tekstowe bazy profili IP i WOL. Rozszerzenie `.sys` nie oznacza pliku systemowego ani szyfrowania.
- Raporty trafiają do `Reports/` przy odpowiedniej wersji kodu. Nazwy są oczyszczane i otrzymują losowy sufiks, żeby zapisy nie nadpisywały istniejących plików.
- Na Linuxie katalogi danych i raportów mają uprawnienia `700`, bazy danych i nowe raporty `600`. Na Windowsie ochrona dostępu zależy od ACL katalogu użytkownika. Dane nie są szyfrowane.
- Audyt WiFi wyświetla dostępne hasła; zapis raportu wymaga wyboru użytkownika. Raport z hasłami pozostaje jawnym tekstem. Starsze raporty nie są automatycznie usuwane ani zabezpieczane ponownie.
- WOL wysyła standardowy Magic Packet i nie korzysta z haseł SSH/RPC. Dawne czwarte pole bazy jest ignorowane, a przy zapisie zastępowane `-`. Stare hasła pozostają w istniejącym pliku do jego ponownego zapisania; kopie zapasowe pozostają bez zmian.
- GeoIP łączy się z `ipwho.is` przez HTTPS; [dokumentacja usługi](https://ipwhois.io/documentation) opisuje odpowiedź API. WHOIS korzysta z `rdap.org`, a MAC Lookup z `api.macvendors.com`. Usługi otrzymują publiczny adres IP połączenia oraz odpowiednio domenę lub adres MAC z zapytania.
- Polecenia diagnostyczne wysyłają ruch do wybranych hostów i serwerów. Raporty mogą zawierać adresy, nazwy urządzeń i hasła — sprawdź je przed udostępnieniem.

Reset sieci, DHCP, zmiana IP i wyłączenie karty mogą przerwać połączenie. Dotychczasowy [raport Phase 1](SECURITY_FIXES_PHASE1.md) jest historyczny; nie stanowi potwierdzenia pełnego audytu aktualnego kodu.

## Weryfikacja

```bash
python -m unittest discover -s tests -v
python -m compileall -q source_code_linux source_code_windows
```

Testy regresji sprawdzają walidację danych, przekazywanie argumentów procesom, bezpieczny zapis raportów, ochronę przed dowiązaniami i rezygnację z automatycznego eksportu haseł WiFi. Wywołania sieciowe i administracyjne są w testach zastępowane atrapami; testy nie zmieniają konfiguracji sieci. Działanie narzędzi systemowych wymaga osobnego sprawdzenia na docelowym systemie.

Dodatkowa dokumentacja: [NetworkMaster Technical Documentation PL](NetworkMaster_Technical_Documentation_PL.pdf). PDF może opisywać wcześniejszą wersję programu.

## Licencja

[GNU GPLv3](LICENSE.md).

## AI assistance

**Made with AI.** This project was developed with AI assistance, including code, documentation, and testing.

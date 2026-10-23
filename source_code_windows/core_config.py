import os
import sys
import subprocess
import security_utils
from windows_commands import powershell

# --- 1. USTALANIE ŚCIEŻKI GŁÓWNEJ ---
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- 2. GŁÓWNE FOLDERY ---
DB_DIR = os.path.join(BASE_DIR, "core_data")
REPORTS_DIR = os.path.join(BASE_DIR, "Reports")

# --- 3. DANE APLIKACJI ---
APP_ID = "NetworkMaster"
APP_PLATFORM = "windows"

# --- 4. ŚCIEŻKI PLIKÓW DANYCH ---
FIRST_RUN_FLAG = os.path.join(DB_DIR, "installed.flag")
DB_IP = os.path.join(DB_DIR, "ip_registry.sys")
DB_WOL = os.path.join(DB_DIR, "wol_registry.sys") 
DB_WIFI = os.path.join(DB_DIR, "wifi_vault.dat")  

# --- FUNKCJE POMOCNICZE ---
def init():
    """Tworzy niezbędne foldery przy starcie."""
    for directory in (DB_DIR, REPORTS_DIR):
        if os.path.islink(directory):
            raise OSError("Katalog danych nie może być dowiązaniem: " + directory)
        os.makedirs(directory, mode=0o700, exist_ok=True)
        if os.name == 'posix':
            if os.stat(directory).st_uid != os.geteuid():
                raise PermissionError("Katalog danych należy do innego użytkownika: " + directory)
            os.chmod(directory, 0o700)
    
    for f in (DB_IP, DB_WOL, DB_WIFI, FIRST_RUN_FLAG):
        if os.path.islink(f):
            raise OSError("Plik danych nie może być dowiązaniem: " + f)
        if f in (DB_IP, DB_WOL) and not os.path.exists(f):
            fd = os.open(f, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            os.close(fd)
        if os.name == 'posix' and os.path.exists(f):
            os.chmod(f, 0o600)

def clear_screen():
    os.system('cls')

def get_adapters_info():
    """Pobiera informacje o kartach sieciowych (używane w GUI)."""
    cmd = powershell('Get-NetAdapter | Select-Object Name, Status, LinkSpeed | ConvertTo-Csv -NoTypeInformation')
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=15).stdout
        info = {}
        lines = res.strip().split('\n')
        if len(lines) > 1:
            for line in lines[1:]:
                parts = line.replace('"', '').split(',')
                if len(parts) >= 3:
                    name = parts[0]
                    status = parts[1]
                    speed = parts[2]
                    is_up = status.strip().upper() == "UP"
                    info[name] = {"status": "UP" if is_up else "DOWN", "speed": speed.strip() if is_up else "--", "up": is_up}
        return info
    except:
        return {}
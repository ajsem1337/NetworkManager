import os
import sys
import subprocess
import security_utils
import re

# --- 1. FUNKCJE SYSTEMOWE ---
def clear_screen():
    os.system('clear')

# --- 2. USTALANIE ŚCIEŻKI GŁÓWNEJ ---
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(os.path.realpath(sys.executable))
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- 3. GŁÓWNE FOLDERY ---
DB_DIR = os.path.join(BASE_DIR, "core_data")
REPORTS_DIR = os.path.join(BASE_DIR, "Reports")

# --- 4. DANE APLIKACJI ---
APP_ID = "NetworkMaster"
APP_PLATFORM = "linux"

# --- 5. ŚCIEŻKI PLIKÓW ---
FIRST_RUN_FLAG = os.path.join(DB_DIR, "installed.flag")
DB_IP = os.path.join(DB_DIR, "ip_registry.sys")
DB_WOL = os.path.join(DB_DIR, "wol_registry.sys") 
DB_WIFI = os.path.join(DB_DIR, "wifi_vault.dat")  

# --- FUNKCJE POMOCNICZE ---
def init():
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

def get_linux_speed(interface_name):
    if not security_utils.validate_interface_name(interface_name):
        return "--"
    try:
        res = subprocess.check_output(["iwconfig", interface_name], stderr=subprocess.DEVNULL).decode()
        match = re.search(r"Bit Rate[=:]\s*([0-9\.]+.*?/s)", res)
        if match: return match.group(1).strip()
    except: pass
    try:
        cmd = ["nmcli", "-t", "-f", "WIFI-PROPERTIES.RATE", "dev", "show", interface_name]
        res = subprocess.check_output(cmd, stderr=subprocess.DEVNULL).decode().strip()
        if res and "--" not in res: return res.replace("Mbit/s", "Mb/s")
    except: pass
    try:
        res = subprocess.check_output(["ethtool", interface_name], stderr=subprocess.DEVNULL).decode()
        if "Speed:" in res: 
            val = res.split("Speed:")[1].splitlines()[0].strip()
            if "Unknown" in val: return "1000 Mb/s"
            return val
    except: pass
    try:
        with open(f"/sys/class/net/{interface_name}/speed", "r") as f:
            val = f.read().strip()
            if val.isdigit() and int(val) > 0: return f"{val} Mb/s"
    except: pass
    return "--"

def get_adapters_info():
    info = {}
    try:
        interfaces = os.listdir('/sys/class/net/')
        for iface in interfaces:
            if iface == 'lo' or not security_utils.validate_interface_name(iface): continue
            try:
                with open(f'/sys/class/net/{iface}/operstate', 'r') as f:
                    st = f.read().strip().lower()
                    status = "UP" if st in ["up", "unknown"] else "DOWN"
            except: status = "DOWN"
            is_up = status == "UP"
            speed = get_linux_speed(iface) if is_up else "--"
            ip_addr = "---"
            try:
                cmd = ["ip", "-4", "-o", "addr", "show", "dev", iface]
                res = subprocess.check_output(cmd, stderr=subprocess.DEVNULL).decode()
                if "inet" in res:
                    ip_addr = res.split()[3].split('/')[0]
            except: pass
            info[iface] = {
                "status": status, 
                "speed": speed, 
                "up": is_up,
                "ip": ip_addr
            }
        return info
    except: return {}
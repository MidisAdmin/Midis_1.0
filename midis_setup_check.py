import subprocess
import sys
import os
import time

def is_wifi_configured():
    try:
        from midis_config import WIFI_SSID, WIFI_PASSWORD
        return bool(WIFI_SSID and WIFI_PASSWORD)
    except ImportError:
        return False

def start_hotspot():
    # Unblock WiFi
    subprocess.run(['sudo', 'rfkill', 'unblock', 'wifi'])
    
    # Stop NetworkManager from managing wlan0
    subprocess.run(['sudo', 'nmcli', 'device', 'disconnect', 'wlan0'], capture_output=True)
    
    # Write hostapd config
    subprocess.run(['sudo', 'bash', '-c', '''
cat > /etc/hostapd/hostapd.conf << EOF
interface=wlan0
driver=nl80211
ssid=Midis Setup
hw_mode=g
channel=7
wmm_enabled=0
auth_algs=1
ignore_broadcast_ssid=0
EOF
'''])

    # Write dnsmasq config
    subprocess.run(['sudo', 'bash', '-c', '''
cat > /etc/dnsmasq.conf << EOF
interface=wlan0
dhcp-range=192.168.4.2,192.168.4.20,255.255.255.0,24h
address=/#/192.168.4.1
EOF
'''])

    # Set static IP
    subprocess.run(['sudo', 'ip', 'addr', 'flush', 'dev', 'wlan0'])
    subprocess.run(['sudo', 'ip', 'addr', 'add', '192.168.4.1/24', 'dev', 'wlan0'])
    subprocess.run(['sudo', 'ip', 'link', 'set', 'wlan0', 'up'])
    
    # Start hostapd and dnsmasq
    subprocess.run(['sudo', 'systemctl', 'restart', 'hostapd'])
    time.sleep(2)
    subprocess.run(['sudo', 'systemctl', 'restart', 'dnsmasq'])
    time.sleep(1)
    
    # Start the setup portal
    subprocess.run(['sudo', 'python3', '/home/pi/Midis_1.0/midis_setup_portal.py'])

if not is_wifi_configured():
    print("No WiFi configured — starting setup mode")
    start_hotspot()
    sys.exit(0)
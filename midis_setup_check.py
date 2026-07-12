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

def show_setup_screen():
    try:
        from rgbmatrix import RGBMatrix, RGBMatrixOptions
        from rgbmatrix import graphics

        options = RGBMatrixOptions()
        options.rows = 32
        options.cols = 64
        options.hardware_mapping = 'adafruit-hat'
        options.gpio_slowdown = 4
        options.disable_hardware_pulsing = True
        options.drop_privileges = 0

        matrix = RGBMatrix(options=options)
        canvas = matrix.CreateFrameCanvas()

        medium_font = graphics.Font()
        medium_font.LoadFont("/usr/local/share/midis-fonts/6x10.bdf")
        small_font = graphics.Font()
        small_font.LoadFont("/usr/local/share/midis-fonts/5x8.bdf")

        canvas.Clear()
        green  = graphics.Color(0, 255, 0)
        orange = graphics.Color(255, 140, 0)
        pink   = graphics.Color(255, 121, 253)

        graphics.DrawText(canvas, medium_font, 1, 10, green,  "SETUP MODE")
        graphics.DrawText(canvas, small_font,  1, 20, orange, "Connect to wifi:")
        graphics.DrawText(canvas, small_font,  1, 29, pink,   "Midis Setup")

        canvas = matrix.SwapOnVSync(canvas)
        return matrix

    except Exception as e:
        print(f"Display error: {e}")
        return None

def start_hotspot(matrix=None):
    rfkill_cmd = ['rfkill', 'unblock', 'wifi']
    subprocess.run(rfkill_cmd)
    subprocess.run(['nmcli', 'device', 'disconnect', 'wlan0'], capture_output=True)
    subprocess.run(['bash', '-c', '''
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
    subprocess.run(['bash', '-c', '''
cat > /etc/dnsmasq.conf << EOF
interface=wlan0
dhcp-range=192.168.4.2,192.168.4.20,255.255.255.0,24h
address=/#/192.168.4.1
EOF
'''])
    subprocess.run(['ip', 'addr', 'flush', 'dev', 'wlan0'])
    subprocess.run(['ip', 'addr', 'add', '192.168.4.1/24', 'dev', 'wlan0'])
    subprocess.run(['ip', 'link', 'set', 'wlan0', 'up'])
    subprocess.run(['systemctl', 'restart', 'hostapd'])
    time.sleep(2)
    subprocess.run(['systemctl', 'restart', 'dnsmasq'])
    time.sleep(1)
    subprocess.run(['python3', '/home/pi/Midis_1.0/midis_setup_portal.py'])
    if matrix:
        matrix.Clear()

if not is_wifi_configured():
    print("No WiFi configured — starting setup mode")
    matrix = show_setup_screen()
    start_hotspot(matrix)
    sys.exit(1)
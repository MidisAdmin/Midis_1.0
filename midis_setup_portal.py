import subprocess
import os
import time
from flask import Flask, request, render_template_string, redirect

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Midis Setup</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 400px; margin: 40px auto; padding: 20px; background: #111; color: #fff; }
        h1 { color: #FFA500; }
        input { width: 100%; padding: 10px; margin: 8px 0; background: #222; color: #fff; border: 1px solid #444; border-radius: 5px; box-sizing: border-box; }
        button { width: 100%; padding: 12px; background: #FFA500; color: #000; border: none; border-radius: 5px; font-size: 16px; font-weight: bold; cursor: pointer; }
        .label { color: #aaa; font-size: 14px; margin-top: 10px; }
        .success { color: #00cc00; font-size: 18px; text-align: center; }
    </style>
</head>
<body>
    <h1>Midis Setup</h1>
    {% if success %}
    <p class="success">✓ Connected! Your Midis is restarting...</p>
    {% else %}
    <form method="POST" action="/setup">
        <p class="label">WiFi Network Name</p>
        <input type="text" name="ssid" placeholder="Your WiFi name" required>
        <p class="label">WiFi Password</p>
        <input type="password" name="password" placeholder="Your WiFi password" required>
        <br><br>
        <button type="submit">Connect Midis</button>
    </form>
    {% endif %}
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML, success=False)

@app.route('/setup', methods=['POST'])
def setup():
    ssid = request.form.get('ssid')
    password = request.form.get('password')

    # Read existing config
    config_path = '/home/pi/Midis_1.0/midis_config.py'
    with open(config_path, 'r') as f:
        content = f.read()

    # Update WiFi fields
    import re
    content = re.sub(r'WIFI_SSID = ".*"', f'WIFI_SSID = "{ssid}"', content)
    content = re.sub(r'WIFI_PASSWORD = ".*"', f'WIFI_PASSWORD = "{password}"', content)

    with open(config_path, 'w') as f:
        f.write(content)

    # Connect to WiFi
    subprocess.run(['sudo', 'nmcli', 'device', 'wifi', 'connect', ssid, 'password', password])
    time.sleep(5)

    # Stop hotspot
    subprocess.run(['sudo', 'systemctl', 'stop', 'hostapd'])
    subprocess.run(['sudo', 'systemctl', 'stop', 'dnsmasq'])

    # Reboot
    subprocess.Popen(['sudo', 'shutdown', '-r', 'now'])

    return render_template_string(HTML, success=True)

# Captive portal detection endpoints
@app.route('/hotspot-detect.html')
@app.route('/generate_204')
@app.route('/ncsi.txt')
@app.route('/connecttest.txt')
def captive_check():
    return redirect('http://192.168.4.1/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=False)
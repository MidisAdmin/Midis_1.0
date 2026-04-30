import subprocess
import os
import time
from flask import Flask, request, render_template_string

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
        <p class="label">Your City or ZIP Code</p>
        <input type="text" name="location" placeholder="e.g. San Diego, CA or 92115" required>
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
    location = request.form.get('location')

    # Get coordinates from location
    lat, lon, timezone, airport = get_location_data(location)

    # Write midis_config.py
    config = f"""# Midis Configuration
LAT = {lat}
LON = {lon}
TIMEZONE = "{timezone}"
HOME_AIRPORT = "{airport}"
HOME_LAT = {lat}
HOME_LON = {lon}
"""
    with open('/home/pi/midis_config.py', 'w') as f:
        f.write(config)

    # Connect to WiFi
    subprocess.Popen(['sudo', 'nmcli', 'device', 'wifi', 'connect', ssid, 'password', password])

    # Schedule reboot
    subprocess.Popen(['sudo', 'shutdown', '-r', '+1'])

    return render_template_string(HTML, success=True)

def get_location_data(location):
    try:
        import urllib.request
        import json
        query = location.replace(' ', '+')
        url = f"https://nominatim.openstreetmap.org/search?q={query}&format=json&limit=1"
        req = urllib.request.Request(url, headers={"User-Agent": "MidisSetup/1.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
            if data:
                lat = round(float(data[0]['lat']), 6)
                lon = round(float(data[0]['lon']), 6)
                return lat, lon, "America/Los_Angeles", "SAN"
    except:
        pass
    return 32.787253, -117.215941, "America/Los_Angeles", "SAN"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=False)
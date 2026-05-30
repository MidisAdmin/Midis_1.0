cat > ~/midis_flights.py << 'ENDOFFILE'
import time
import math
import threading
import urllib.request
import json
import requests
from rgbmatrix import graphics

try:
    from midis_config import HOME_LAT, HOME_LON, HOME_AIRPORT, FR24_API_KEY
except ImportError:
    HOME_LAT = 32.7336
    HOME_LON = -117.1897
    HOME_AIRPORT = "SAN"
    FR24_API_KEY = ""

SEARCH_RADIUS = 0.3

flight_list = []
current_flight = 0
last_fetch = 0
last_switch = 0
FLIGHT_DURATION = 45
is_fetching = False
origin_cache = {}

route_font = None

COMMERCIAL_AIRLINES = {
    "AAL", "UAL", "DAL", "SWA", "ASA", "SKW", "JBU", "FFT", "HAL",
    "WJA", "ACA", "BAW", "AFR", "DLH", "KLM", "UAE", "QFA", "SIA",
    "CPA", "JAL", "ANA", "KAL", "CSN", "CCA", "AMX", "VOI", "VIV",
    "RPA", "AWI", "ENY", "GJS", "TSC", "WEN"
}

def init_fonts():
    global route_font
    route_font = graphics.Font()
    route_font.LoadFont("/usr/local/share/midis-fonts/6x13B.bdf")

def calculate_distance_km(lat1, lon1, lat2, lon2):
    R = 6371
    lat1_r = math.radians(lat1)
    lat2_r = math.radians(lat2)
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (math.sin(d_lat/2)**2 + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(d_lon/2)**2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

def get_origin_fr24(callsign):
    if not FR24_API_KEY:
        return "???"
    try:
        url = "https://fr24api.flightradar24.com/api/live/flight-positions/full?callsigns=" + callsign
        headers = {
            "Accept": "application/json",
            "Accept-Version": "v1",
            "Authorization": "Bearer " + FR24_API_KEY
        }
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code in [402, 429]:
            return "???"
        data = r.json()
        for f in data.get("data", []):
            origin = f.get("orig_iata", "") or "???"
            if origin.startswith("K") and len(origin) == 4:
                origin = origin[1:]
            return origin
    except:
        pass
    return "???"

def fetch_flights_thread():
    global flight_list, last_fetch, is_fetching, origin_cache
    is_fetching = True
    try:
        lat_min = HOME_LAT - SEARCH_RADIUS
        lat_max = HOME_LAT + SEARCH_RADIUS
        lon_min = HOME_LON - SEARCH_RADIUS
        lon_max = HOME_LON + SEARCH_RADIUS

        url = "https://opensky-network.org/api/states/all?lamin=" + str(lat_min) + "&lomin=" + str(lon_min) + "&lamax=" + str(lat_max) + "&lomax=" + str(lon_max)
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read())

        found = []
        if data.get("states"):
            for s in data["states"]:
                callsign = (s[1] or "").strip()
                altitude = round(s[7] * 3.28084) if s[7] else 0
                speed = round(s[9] * 2.23694) if s[9] else 0
                on_ground = s[8]
                lat = s[6] or HOME_LAT
                lon = s[5] or HOME_LON

                if not callsign or on_ground or altitude < 1000:
                    continue

                airline = ''.join(c for c in callsign if c.isalpha())
                number = ''.join(c for c in callsign if c.isdigit())
                if len(airline) != 3 or not number:
                    continue
                if airline not in COMMERCIAL_AIRLINES:
                    continue

                if callsign not in origin_cache:
                    print("Looking up origin for " + callsign + " via FR24")
                    result = get_origin_fr24(callsign)
                    origin_cache[callsign] = result
                    time.sleep(0.5)

                origin = origin_cache[callsign]
                dist = calculate_distance_km(HOME_LAT, HOME_LON, lat, lon)

                found.append({
                    "callsign": callsign,
                    "origin": origin,
                    "altitude": altitude,
                    "speed": speed,
                    "distance_mi": round(dist * 0.621371, 1)
                })

        flight_list = sorted(found, key=lambda f: f["distance_mi"])
        last_fetch = time.time()
        print("Found " + str(len(flight_list)) + " flights near " + HOME_AIRPORT)
    except Exception as e:
        print("Flight error: " + str(e))
    is_fetching = False

def get_flights():
    t = threading.Thread(target=fetch_flights_thread, daemon=True)
    t.start()

def format_altitude(alt):
    if alt >= 10000:
        return str(round(alt/1000)) + "kft"
    return str(alt) + "ft"

def draw(canvas, font, small_font):
    global flight_list, current_flight, last_fetch, last_switch, route_font, is_fetching

    if route_font is None:
        init_fonts()

    if not is_fetching and time.time() - last_fetch > 180:
        get_flights()

    if is_fetching and not flight_list:
        graphics.DrawText(canvas, small_font, 2, 12, graphics.Color(255, 160, 0), "Fetching")
        graphics.DrawText(canvas, small_font, 2, 22, graphics.Color(180, 180, 180), "flights...")
        return

    if flight_list and time.time() - last_switch > FLIGHT_DURATION:
        current_flight = (current_flight + 1) % len(flight_list)
        last_switch = time.time()

    if not flight_list:
        try:
            from PIL import Image
            img = Image.open("/usr/local/share/midis-icons/flightless.png").convert('RGB')
            x_offset = (64 - 32) // 2
            for y in range(32):
                for x in range(32):
                    r, g, b = img.getpixel((x, y))
                    canvas.SetPixel(x_offset + x, y, r, g, b)
        except:
            graphics.DrawText(canvas, small_font, 2, 16, graphics.Color(255, 160, 0), "No flights")
        return

    f = flight_list[current_flight % len(flight_list)]

    x = 2
    for char in f["callsign"]:
        graphics.DrawText(canvas, route_font, x, 10, graphics.Color(148, 0, 211), char)
        x += 7

    x = 2
    for char in f["origin"] + ">" + HOME_AIRPORT:
        graphics.DrawText(canvas, route_font, x, 22, graphics.Color(255, 160, 0), char)
        x += 7

    alt_str = format_altitude(f["altitude"])
    spd_str = str(f["speed"]) + "kt"
    stats = alt_str + " " + spd_str
    graphics.DrawText(canvas, small_font, 2, 31, graphics.Color(0, 200, 0), stats)
ENDOFFILE
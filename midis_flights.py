import time
import math
import threading
from rgbmatrix import graphics
from secrets import HOME_LAT, HOME_LON, HOME_AIRPORT

try:
    from FlightRadar24 import FlightRadar24API
    fr_api = FlightRadar24API()
except Exception as e:
    print(f"FlightRadar24 error: {e}")
    fr_api = None

SEARCH_RADIUS = 2.0

flight_list = []
current_flight = 0
last_fetch = 0
last_switch = 0
FLIGHT_DURATION = 45
is_fetching = False

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

def lookup_flight(flight, results):
    try:
        details = fr_api.get_flight_details(flight)
        flight.set_flight_details(details)
        dest = flight.destination_airport_iata or ""
        if dest != HOME_AIRPORT:
            return
        callsign = (flight.callsign or "").strip()
        if not callsign:
            return
        airline = ''.join(c for c in callsign if c.isalpha())
        number = ''.join(c for c in callsign if c.isdigit())
        if len(airline) != 3 or not number:
            return
        if airline not in COMMERCIAL_AIRLINES:
            return
        origin = flight.origin_airport_iata or "???"
        if origin.startswith("K") and len(origin) == 4:
            origin = origin[1:]
        dist = calculate_distance_km(HOME_LAT, HOME_LON, flight.latitude, flight.longitude)
        results.append({
            "callsign": callsign,
            "origin": origin,
            "altitude": flight.altitude,
            "speed": flight.ground_speed or 0,
            "distance_mi": round(dist * 0.621371, 1)
        })
    except:
        pass

def fetch_flights_thread():
    global flight_list, last_fetch, fr_api, is_fetching
    is_fetching = True
    try:
        bounds = "{},{},{},{}".format(
            HOME_LAT + SEARCH_RADIUS,
            HOME_LAT - SEARCH_RADIUS,
            HOME_LON - SEARCH_RADIUS,
            HOME_LON + SEARCH_RADIUS
        )
        flights = fr_api.get_flights(bounds=bounds)
        airborne = [f for f in flights if f.altitude > 0 and f.latitude != 0]

        results = []
        threads = []
        for flight in airborne:
            t = threading.Thread(target=lookup_flight, args=(flight, results), daemon=True)
            threads.append(t)
            t.start()

        for t in threads:
            t.join(timeout=10)

        flight_list = sorted(results, key=lambda f: f["distance_mi"])
        last_fetch = time.time()
        print(f"Found {len(flight_list)} {HOME_AIRPORT} arrivals")
    except Exception as e:
        print(f"Flight error: {e}")
    is_fetching = False

def get_flights():
    t = threading.Thread(target=fetch_flights_thread, daemon=True)
    t.start()

def format_altitude(alt):
    if alt >= 10000:
        return f"{round(alt/1000)}kft"
    return f"{alt}ft"

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
        graphics.DrawText(canvas, small_font, 2, 10, graphics.Color(255, 160, 0), "No flights")
        graphics.DrawText(canvas, small_font, 2, 20, graphics.Color(180, 180, 180), f"near {HOME_AIRPORT}")
        return

    f = flight_list[current_flight % len(flight_list)]

    x = 2
    for char in f["callsign"]:
        graphics.DrawText(canvas, route_font, x, 10, graphics.Color(148, 0, 211), char)
        x += 7

    x = 2
    for char in f"{f['origin']}>{HOME_AIRPORT}":
        graphics.DrawText(canvas, route_font, x, 22, graphics.Color(255, 160, 0), char)
        x += 7

    alt_str = format_altitude(f["altitude"])
    spd_str = f"{f['speed']}kt"
    stats = f"{alt_str} {spd_str}"
    graphics.DrawText(canvas, small_font, 2, 31, graphics.Color(0, 200, 0), stats)

import requests
import urllib.request
import json
import time
from rgbmatrix import graphics

last_fetch = 0
commute_data = None
last_weather_fetch = 0
weather_data = None
FETCH_INTERVAL = 900  # 15 minutes
WEATHER_INTERVAL = 1800  # 30 minutes

med_font = None

def init_fonts():
    global med_font
    med_font = graphics.Font()
    med_font.LoadFont("/usr/local/share/midis-fonts/7x14B.bdf")

def is_commute_hours():
    return True  # TEMP: remove for production
    t = time.localtime()
    if t.tm_wday >= 5:
        return False
    hour = t.tm_hour
    return 7 <= hour < 8

def should_show():
    return is_commute_hours()

def get_commute():
    global commute_data, last_fetch
    try:
        from midis_config import COMMUTE_ORIGIN, COMMUTE_DESTINATION, DISTANCEMATRIX_API_KEY
        url = "https://api.distancematrix.ai/maps/api/distancematrix/json"
        params = {
            "origins": COMMUTE_ORIGIN,
            "destinations": COMMUTE_DESTINATION,
            "key": DISTANCEMATRIX_API_KEY,
            "mode": "driving",
            "traffic_model": "best_guess",
            "departure_time": "now"
        }
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
        element = data["rows"][0]["elements"][0]
        if element["status"] == "OK":
            duration = element.get("duration_in_traffic", element["duration"])
            minutes = round(duration["value"] / 60)
            commute_data = minutes
            last_fetch = time.time()
    except Exception as e:
        print(f"Commute error: {e}")

def get_weather():
    global weather_data, last_weather_fetch
    try:
        from midis_config import LAT, LON, TIMEZONE
        url = f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}&daily=temperature_2m_max,temperature_2m_min&temperature_unit=fahrenheit&timezone={TIMEZONE}&forecast_days=1"
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read())
            high = round(data["daily"]["temperature_2m_max"][0])
            low = round(data["daily"]["temperature_2m_min"][0])
            weather_data = (high, low)
            last_weather_fetch = time.time()
    except Exception as e:
        print(f"Commute weather error: {e}")

def draw(canvas, font, small_font):
    global commute_data, last_fetch, weather_data, last_weather_fetch, med_font

    if med_font is None:
        init_fonts()

    if commute_data is None or time.time() - last_fetch > FETCH_INTERVAL:
        get_commute()

    if weather_data is None or time.time() - last_weather_fetch > WEATHER_INTERVAL:
        get_weather()

    # LINE 1: COMMUTE label
    graphics.DrawText(canvas, small_font, 2, 8, graphics.Color(255, 160, 0), "COMMUTE")

    # LINE 2: ETA
    if commute_data is not None:
        eta_str = f"ETA {commute_data} MINS"
        graphics.DrawText(canvas, small_font, 2, 16, graphics.Color(0, 220, 0), eta_str)
    else:
        graphics.DrawText(canvas, small_font, 2, 16, graphics.Color(180, 180, 180), "Fetching...")

    # LINE 3: Weather high/low
    if weather_data is not None:
        high, low = weather_data
        graphics.DrawText(canvas, small_font, 2, 24, graphics.Color(255, 60, 60), f"H:{high}")
        graphics.DrawText(canvas, small_font, 32, 24, graphics.Color(0, 100, 255), f"L:{low}")

    # LINE 4: Current time right aligned
    time_str = time.strftime("%-I:%M%p").lower()
    x = 64 - len(time_str) * 5 - 2
    graphics.DrawText(canvas, small_font, x, 32, graphics.Color(255, 255, 255), time_str)
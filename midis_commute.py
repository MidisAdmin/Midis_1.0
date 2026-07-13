import requests
import time
from rgbmatrix import graphics

last_fetch = 0
commute_data = None
FETCH_INTERVAL = 900  # 15 minutes

med_font = None

def init_fonts():
    global med_font
    med_font = graphics.Font()
    med_font.LoadFont("/usr/local/share/midis-fonts/7x14B.bdf")

def is_commute_hours():
    t = time.localtime()
    if t.tm_wday >= 5:
        return False
    hour = t.tm_hour
    return (6 <= hour < 10) or (15 <= hour < 20)

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

def draw(canvas, font, small_font):
    global commute_data, last_fetch, med_font

    if not is_commute_hours():
        return

    if med_font is None:
        init_fonts()

    if commute_data is None or time.time() - last_fetch > FETCH_INTERVAL:
        get_commute()

    if commute_data is not None:
        graphics.DrawText(canvas, small_font, 2, 8, graphics.Color(255, 160, 0), "COMMUTE")
        time_str = f"{commute_data} min"
        graphics.DrawText(canvas, med_font, 2, 22, graphics.Color(0, 200, 255), time_str)

        if commute_data <= 20:
            status = "Clear"
            color = graphics.Color(0, 220, 0)
        elif commute_data <= 35:
            status = "Moderate"
            color = graphics.Color(255, 160, 0)
        else:
            status = "Heavy"
            color = graphics.Color(255, 40, 40)

        graphics.DrawText(canvas, small_font, 2, 31, color, status)
    else:
        graphics.DrawText(canvas, small_font, 2, 16, graphics.Color(180, 180, 180), "No data")
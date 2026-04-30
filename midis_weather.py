import urllib.request
import json
import time
from PIL import Image
from rgbmatrix import graphics
from midis_config import LAT, LON, TIMEZONE

ICON_DIR = "/usr/local/share/midis-icons"

weather_data = None
last_fetch = 0

def get_weather():
    global weather_data, last_fetch
    url = f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}&current=temperature_2m,weathercode&daily=temperature_2m_max,temperature_2m_min&temperature_unit=fahrenheit&timezone={TIMEZONE}&forecast_days=1"
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read())
            weather_data = (
                round(data["current"]["temperature_2m"]),
                round(data["daily"]["temperature_2m_max"][0]),
                round(data["daily"]["temperature_2m_min"][0]),
                data["current"]["weathercode"]
            )
            last_fetch = time.time()
    except:
        pass

def temp_color(temp):
    if temp <= 50: return (255, 255, 255)
    elif temp <= 65: return (100, 150, 255)
    elif temp <= 75: return (255, 220, 0)
    elif temp <= 90: return (255, 140, 0)
    else: return (255, 30, 0)

def code_to_icon(code):
    if code == 0: return "sun"
    elif code in [1, 2, 3]: return "cloud"
    elif code in [45, 48]: return "fog"
    elif code in [51,53,55,61,63,65,80,81,82]: return "rain"
    elif code in [71,73,75]: return "snow"
    elif code in [95,96,99]: return "thunder"
    else: return "sun"

def draw_icon(canvas, icon_name, x, y):
    try:
        img = Image.open(f"{ICON_DIR}/{icon_name}.png").convert('RGB')
        for iy in range(img.size[1]):
            for ix in range(img.size[0]):
                r, g, b = img.getpixel((ix, iy))
                if r > 20 or g > 20 or b > 20:
                    canvas.SetPixel(x + ix, y + iy, r, g, b)
    except:
        pass

def draw(canvas, font, small_font):
    global weather_data, last_fetch

    if weather_data is None or time.time() - last_fetch > 600:
        get_weather()

    if weather_data is not None:
        temp, high, low, code = weather_data
        temp_str = f"{temp}"
        r, g, b = temp_color(temp)
        graphics.DrawText(canvas, font, 3, 19, graphics.Color(r, g, b), temp_str)
        dot_x = 3 + len(temp_str) * 10
        dot_y = 4
        for dx, dy in [(1,0),(2,0),(0,1),(3,1),(0,2),(3,2),(1,3),(2,3)]:
            canvas.SetPixel(dot_x + dx, dot_y + dy, r, g, b)
        draw_icon(canvas, code_to_icon(code), 42, 5)
        graphics.DrawText(canvas, small_font, 3, 30, graphics.Color(255, 60, 60), f"H:{high}")
        graphics.DrawText(canvas, small_font, 26, 30, graphics.Color(100, 150, 255), f"L:{low}")
    else:
        graphics.DrawText(canvas, small_font, 2, 16, graphics.Color(255, 0, 0), "No signal")

import time
import urllib.request
import json
from rgbmatrix import graphics
from secrets import LAT, LON, TIMEZONE

forecast_data = None
last_fetch = 0
sunset_hour = 19

med_font = None

def init_fonts():
    global med_font
    med_font = graphics.Font()
    med_font.LoadFont("/usr/local/share/midis-fonts/7x14B.bdf")

def get_forecast():
    global forecast_data, last_fetch, sunset_hour
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}&hourly=temperature_2m&daily=sunset,uv_index_max&temperature_unit=fahrenheit&timezone={TIMEZONE}&forecast_days=1"
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read())
            temps = data["hourly"]["temperature_2m"]
            now_hour = time.localtime().tm_hour
            t_now = round(temps[now_hour])
            t_3hr = round(temps[min(now_hour + 3, 23)])
            t_6hr = round(temps[min(now_hour + 6, 23)])
            sunset_str = data["daily"]["sunset"][0]
            sunset_hour = int(sunset_str.split("T")[1].split(":")[0])
            uv = round(data["daily"]["uv_index_max"][0])
            forecast_data = (t_now, t_3hr, t_6hr, now_hour, uv)
            last_fetch = time.time()
    except Exception as e:
        print(f"Forecast error: {e}")

def temp_color(hour, brightness):
    if hour >= sunset_hour:
        return (0, int(100 * brightness), int(255 * brightness))
    else:
        return (int(255 * brightness), int(160 * brightness), 0)

def draw(canvas, font, small_font):
    global forecast_data, last_fetch, med_font

    if med_font is None:
        init_fonts()

    if forecast_data is None or time.time() - last_fetch > 600:
        get_forecast()

    if forecast_data is None:
        graphics.DrawText(canvas, small_font, 2, 16, graphics.Color(255, 0, 0), "No data")
        return

    t_now, t_3hr, t_6hr, now_hour, uv = forecast_data

    r, g, b = temp_color(now_hour, 1.0)
    graphics.DrawText(canvas, font, 2, 21, graphics.Color(r, g, b), str(t_now))

    r, g, b = temp_color(now_hour + 3, 0.7)
    graphics.DrawText(canvas, med_font, 26, 20, graphics.Color(r, g, b), str(t_3hr))

    r, g, b = temp_color(now_hour + 6, 0.5)
    graphics.DrawText(canvas, med_font, 46, 20, graphics.Color(r, g, b), str(t_6hr))

    uv_str = f"UV{uv}"
    uv_x = 64 - len(uv_str) * 5 - 2
    graphics.DrawText(canvas, small_font, uv_x, 8, graphics.Color(100, 100, 100), uv_str)

    graphics.DrawText(canvas, small_font, 4, 30, graphics.Color(100, 100, 100), "NOW")
    graphics.DrawText(canvas, small_font, 28, 30, graphics.Color(100, 100, 100), "3H")
    graphics.DrawText(canvas, small_font, 48, 30, graphics.Color(100, 100, 100), "6H")

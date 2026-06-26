import time
from rgbmatrix import graphics

bold_font = None

def init_fonts():
    global bold_font
    bold_font = graphics.Font()
    bold_font.LoadFont("/usr/local/share/midis-fonts/9x18B.bdf")

def get_clock_color():
    try:
        import midis_forecast
        sunset_hour, sunrise_hour = midis_forecast.get_sunset_sunrise()
    except:
        sunset_hour = 19
        sunrise_hour = 6

    hour = time.localtime().tm_hour
    minute = time.localtime().tm_min
    time_decimal = hour + minute / 60.0

    sunset_plus_30 = sunset_hour + 0.5

    if 22 <= time_decimal or time_decimal < 3:
        return (148, 0, 211)      # purple 10pm-3am
    elif 3 <= time_decimal < 9:
        return (255, 160, 0)      # orange 3am-9am
    elif 9 <= time_decimal < 16:
        return (255, 220, 50)     # warm yellow 9am-4pm
    elif 16 <= time_decimal < sunset_plus_30:
        return (200, 0, 0)        # red 4pm-30min after sunset
    else:
        return (0, 180, 255)      # blue sunset+30 until 10pm
    
def draw(canvas, font, small_font):
    global bold_font
    if bold_font is None:
        init_fonts()

    t = time.localtime()
    progress = (t.tm_sec + time.time() % 1) / 60.0
    bar_width = int(progress * 64)

    color = get_clock_color()

    for x in range(bar_width):
        canvas.SetPixel(x, 30, *color)
        canvas.SetPixel(x, 31, *color)

    time_str = time.strftime("%I:%M").lstrip("0")
    ampm_str = time.strftime("%p").lower()
    text_width = len(time_str) * 9
    x = (64 - text_width) // 2
    graphics.DrawText(canvas, bold_font, x, 20, graphics.Color(*color), time_str)
    graphics.DrawText(canvas, small_font, 50, 26, graphics.Color(*color), ampm_str)
import subprocess
import time
from rgbmatrix import RGBMatrix, RGBMatrixOptions
from rgbmatrix import graphics
import midis_clock
import midis_flights
import midis_forecast
import midis_baseball
import midis_weather
import midis_stocks
import midis_art

subprocess.run(["sudo", "python3", "/home/pi/midis_splash.py"])

options = RGBMatrixOptions()
options.rows = 32
options.cols = 64
options.hardware_mapping = 'adafruit-hat'
options.gpio_slowdown = 4
options.disable_hardware_pulsing = True

matrix = RGBMatrix(options=options)
canvas = matrix.CreateFrameCanvas()
font = graphics.Font()
font.LoadFont("/usr/local/share/midis-fonts/10x20.bdf")
small_font = graphics.Font()
small_font.LoadFont("/usr/local/share/midis-fonts/5x8.bdf")

FEATURES = [
    (midis_clock, 15),
    (midis_weather, 20),
    (midis_flights, 20),
    (midis_stocks, 10),
    (midis_art, 20),
    (midis_forecast, 30),
    (midis_flights, 20),
]

current = 0
screen_start = time.time()

def get_brightness():
    try:
        sunset_hour, sunrise_hour = midis_forecast.get_sunset_sunrise()
        now_hour = time.localtime().tm_hour
        dim_start = sunset_hour + 1
        dim_end = sunrise_hour - 1
        if now_hour >= dim_start or now_hour < dim_end:
            return 50
        return 100
    except:
        return 100

last_brightness = None

try:
    while True:
        now = time.time()

        brightness = get_brightness()
        if brightness != last_brightness:
            matrix.brightness = brightness
            last_brightness = brightness

        if midis_baseball.games_active():
            canvas.Clear()
            midis_baseball.draw(canvas, font, small_font)
            canvas = matrix.SwapOnVSync(canvas)
            time.sleep(0.05)
            continue

        feature, duration = FEATURES[current]
        if now - screen_start >= duration:
            current = (current + 1) % len(FEATURES)
            screen_start = now

        canvas.Clear()
        feature.draw(canvas, font, small_font)
        canvas = matrix.SwapOnVSync(canvas)
        time.sleep(0.05)

except KeyboardInterrupt:
    matrix.Clear()
import subprocess
import os
import sys

# Check WiFi BEFORE importing rgbmatrix (which drops privileges)
result = subprocess.run(
    ['sudo', 'python3', '/home/pi/Midis_1.0/midis_setup_check.py'],
    capture_output=False
)
if result.returncode != 0:
    sys.exit(0)

# Only reach here if WiFi is configured
import time
import importlib
from rgbmatrix import RGBMatrix, RGBMatrixOptions
from rgbmatrix import graphics
from midis_config import MODULES
import midis_forecast
import midis_baseball

subprocess.run(["sudo", "python3", "/home/pi/Midis_1.0/midis_splash.py"])

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

# Dynamically load modules from config
FEATURES = []
for module_name, duration in MODULES:
    try:
        mod = importlib.import_module(f"midis_{module_name}")
        FEATURES.append((mod, duration))
    except ImportError:
        print(f"Module midis_{module_name} not found, skipping")

current = 0
screen_start = time.time()

brightness_last_check = 0
brightness_cached = 100

def get_brightness():
    global brightness_last_check, brightness_cached
    if time.time() - brightness_last_check < 300:
        return brightness_cached
    brightness_last_check = time.time()
    try:
        sunset_hour, sunrise_hour = midis_forecast.get_sunset_sunrise()
        now_hour = time.localtime().tm_hour
        dim_start = sunset_hour + 1
        dim_end = sunrise_hour - 1
        if now_hour >= dim_start or now_hour < dim_end:
            brightness_cached = 50
        else:
            brightness_cached = 100
    except:
        brightness_cached = 100
    return brightness_cached

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

        if not FEATURES:
            time.sleep(1)
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
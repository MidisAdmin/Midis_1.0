import time
import random
import os
from PIL import Image
from rgbmatrix import graphics

ART_DIR = "/home/pi/Midis_1.0/icons/midis-icons/Art"

IMAGES = [
    os.path.join(ART_DIR, f)
    for f in os.listdir(ART_DIR)
    if f.lower().endswith('.png')
] if os.path.exists(ART_DIR) else []

current_image = random.randint(0, max(len(IMAGES) - 1, 0)) if IMAGES else 0
last_switch = 0
IMAGE_DURATION = 30

def draw(canvas, font, small_font):
    global current_image, last_switch

    if not IMAGES:
        graphics.DrawText(canvas, small_font, 2, 16, graphics.Color(255, 0, 0), "No art")
        return

    now = time.time()
    if now - last_switch > IMAGE_DURATION:
        current_image = random.randint(0, len(IMAGES) - 1)
        last_switch = now

    try:
        img = Image.open(IMAGES[current_image]).convert('RGB').resize((64, 32), Image.LANCZOS)
        for y in range(32):
            for x in range(64):
                r, g, b = img.getpixel((x, y))
                canvas.SetPixel(x, y, r, g, b)
    except Exception as e:
        print(f"Art error: {e}")
        graphics.DrawText(canvas, small_font, 2, 16, graphics.Color(255, 0, 0), "No image")
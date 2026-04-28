import time
import random
from PIL import Image
from rgbmatrix import graphics

IMAGES = [
    "/usr/local/share/midis-icons/starrynight.png",
    "/usr/local/share/midis-icons/framed.png",
    "/usr/local/share/midis-icons/house.png",
    "/usr/local/share/midis-icons/moonrise.png",
]

current_image = random.randint(0, len(IMAGES) - 1)
last_switch = 0
IMAGE_DURATION = 30

def draw(canvas, font, small_font):
    global current_image, last_switch

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

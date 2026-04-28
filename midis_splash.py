import time
from rgbmatrix import RGBMatrix, RGBMatrixOptions
from rgbmatrix import graphics

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

# Single loop border pixels (one pass around outermost edge)
def get_border_pixels():
    pixels = []
    for x in range(64): pixels.append((x, 0))
    for y in range(1, 32): pixels.append((63, y))
    for x in range(62, -1, -1): pixels.append((x, 31))
    for y in range(30, 0, -1): pixels.append((0, y))
    return pixels

border_pixels = get_border_pixels()
total_pixels = len(border_pixels)

start = time.time()
DURATION = 10

try:
    while True:
        elapsed = time.time() - start
        if elapsed >= DURATION:
            break

        progress = elapsed / DURATION
        pixels_to_draw = int(progress * total_pixels)

        canvas.Clear()

        for i in range(pixels_to_draw):
            x, y = border_pixels[i]
            # Always 3 pixels wide inward
            canvas.SetPixel(x, y, 0, 100, 0)
            if y == 0: canvas.SetPixel(x, 1, 0, 100, 0); canvas.SetPixel(x, 2, 0, 100, 0)
            elif y == 31: canvas.SetPixel(x, 30, 0, 100, 0); canvas.SetPixel(x, 29, 0, 100, 0)
            elif x == 63: canvas.SetPixel(62, y, 0, 100, 0); canvas.SetPixel(61, y, 0, 100, 0)
            elif x == 0: canvas.SetPixel(1, y, 0, 100, 0); canvas.SetPixel(2, y, 0, 100, 0)

        graphics.DrawText(canvas, small_font, 7, 12, graphics.Color(148, 0, 211), "MY")
        graphics.DrawText(canvas, font, 7, 26, graphics.Color(255, 160, 0), "MIDIS")

        canvas = matrix.SwapOnVSync(canvas)
        time.sleep(0.05)
finally:
    matrix.Clear()

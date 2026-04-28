import time
from rgbmatrix import graphics

bold_font = None

def init_fonts():
    global bold_font
    bold_font = graphics.Font()
    bold_font.LoadFont("/usr/local/share/midis-fonts/9x18B.bdf")

def draw(canvas, font, small_font):
    global bold_font
    if bold_font is None:
        init_fonts()

    t = time.localtime()
    progress = (t.tm_sec + time.time() % 1) / 60.0
    bar_width = int(progress * 64)

    for x in range(bar_width):
        canvas.SetPixel(x, 30, 200, 0, 0)
        canvas.SetPixel(x, 31, 200, 0, 0)

    time_str = time.strftime("%I:%M").lstrip("0")
    ampm_str = time.strftime("%p").lower()
    text_width = len(time_str) * 9
    x = (64 - text_width) // 2
    graphics.DrawText(canvas, bold_font, x, 20, graphics.Color(255, 160, 0), time_str)
    graphics.DrawText(canvas, small_font, 50, 26, graphics.Color(255, 160, 0), ampm_str)

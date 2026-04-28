import urllib.request
import json
import time
from rgbmatrix import graphics

SYMBOL = "^GSPC"
stock_data = None
last_fetch = 0

med_font = None
change_font = None

def init_fonts():
    global med_font, change_font
    med_font = graphics.Font()
    med_font.LoadFont("/usr/local/share/midis-fonts/7x14B.bdf")
    change_font = graphics.Font()
    change_font.LoadFont("/usr/local/share/midis-fonts/6x12.bdf")

def get_stock():
    global stock_data, last_fetch
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{SYMBOL}?interval=1d&range=2d"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read())
            result = data["chart"]["result"][0]
            closes = result["indicators"]["quote"][0]["close"]
            prev_close = closes[-2]
            current = closes[-1]
            change = current - prev_close
            stock_data = (round(current, 2), round(change, 2))
            last_fetch = time.time()
    except Exception as e:
        print(f"Stock error: {e}")

def is_trading_hours():
    t = time.gmtime()
    if t.tm_wday >= 5:
        return False
    minutes = t.tm_hour * 60 + t.tm_min
    return 14 * 60 + 30 <= minutes <= 21 * 60

def draw(canvas, font, small_font):
    global stock_data, last_fetch, med_font, change_font

    if med_font is None:
        init_fonts()

    interval = 300 if is_trading_hours() else 3600
    if stock_data is None or time.time() - last_fetch > interval:
        get_stock()

    if stock_data is not None:
        price, change = stock_data

        # Ticker in blue
        graphics.DrawText(canvas, small_font, 2, 8, graphics.Color(255, 160, 0), "S&P 500")

        # Price in warm white, left side
        price_str = f"{price:,.2f}"
        graphics.DrawText(canvas, med_font, 2, 21, graphics.Color(255, 220, 180), price_str)

        # Change right aligned with 2px buffer
        if change >= 0:
            change_str = f"+{change:.2f}"
            color = graphics.Color(0, 220, 0)
        else:
            change_str = f"{change:.2f}"
            color = graphics.Color(255, 40, 40)

        change_width = len(change_str) * 6
        x = 64 - change_width - 2
        graphics.DrawText(canvas, change_font, x, 31, color, change_str)
    else:
        graphics.DrawText(canvas, small_font, 2, 16, graphics.Color(255, 0, 0), "No data")

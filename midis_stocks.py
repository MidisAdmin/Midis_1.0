import urllib.request
import json
import time
from rgbmatrix import graphics

try:
    from midis_config import STOCK_SYMBOLS
    SYMBOLS = STOCK_SYMBOLS
except ImportError:
    try:
        from midis_config import STOCK_SYMBOL
        SYMBOLS = [STOCK_SYMBOL]
    except ImportError:
        SYMBOLS = ["^GSPC"]

stock_data = {}
last_fetch = {}
last_switch = 0
current_symbol = 0

med_font = None
change_font = None

def init_fonts():
    global med_font, change_font
    med_font = graphics.Font()
    med_font.LoadFont("/usr/local/share/midis-fonts/7x14B.bdf")
    change_font = graphics.Font()
    change_font.LoadFont("/usr/local/share/midis-fonts/6x12.bdf")

def get_stock(symbol):
    global stock_data, last_fetch
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=2d"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read())
            result = data["chart"]["result"][0]
            closes = result["indicators"]["quote"][0]["close"]
            prev_close = closes[-2]
            current = closes[-1]
            change = current - prev_close
            pct_change = (change / prev_close) * 100
            stock_data[symbol] = (round(current, 2), round(pct_change, 2))
            last_fetch[symbol] = time.time()
    except Exception as e:
        print(f"Stock error ({symbol}): {e}")

def is_trading_hours():
    t = time.localtime()
    if t.tm_wday >= 5:
        return False
    minutes = t.tm_hour * 60 + t.tm_min
    return 14 * 60 + 30 <= minutes <= 21 * 60

def should_show():
    return time.localtime().tm_wday < 5

def draw(canvas, font, small_font):
    global stock_data, last_fetch, med_font, change_font, current_symbol, last_switch

    if time.localtime().tm_wday >= 5:
        return

    if med_font is None:
        init_fonts()

    # Rotate symbol every 4 seconds
    if time.time() - last_switch > 4:
        current_symbol = (current_symbol + 1) % len(SYMBOLS)
        last_switch = time.time()

    symbol = SYMBOLS[current_symbol]

    interval = 300 if is_trading_hours() else 3600
    if symbol not in stock_data or time.time() - last_fetch.get(symbol, 0) > interval:
        get_stock(symbol)

    if symbol in stock_data:
        price, change = stock_data[symbol]

        graphics.DrawText(canvas, small_font, 2, 8, graphics.Color(255, 160, 0), symbol)

        price_str = f"{price:,.2f}"
        graphics.DrawText(canvas, med_font, 2, 21, graphics.Color(255, 220, 180), price_str)

        if change >= 0:
            change_str = f"+{change:.2f}%"
            color = graphics.Color(0, 220, 0)
        else:
            change_str = f"{change:.2f}%"
            color = graphics.Color(255, 40, 40)

        change_width = len(change_str) * 6
        x = 64 - change_width - 2
        graphics.DrawText(canvas, change_font, x, 31, color, change_str)
    else:
        graphics.DrawText(canvas, small_font, 2, 16, graphics.Color(255, 0, 0), "No data")
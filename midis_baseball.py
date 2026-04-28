import time
import statsapi
from datetime import datetime, timezone
from rgbmatrix import graphics

PADRES_ID = 135
DODGERS_ID = 119

game_data = []
last_fetch = 0
current_game = 0
last_switch = 0
SWITCH_DURATION = 60

med_font = None

TEAM_COLORS = {
    "SD":  (255, 184, 46),
    "LAD": (0, 90, 200),
    "LAA": (200, 0, 0),
    "SF":  (253, 90, 30),
    "AZ":  (167, 25, 48),
    "COL": (51, 0, 111),
    "SEA": (0, 92, 92),
    "TEX": (0, 50, 200),
    "HOU": (235, 110, 31),
    "ATH": (0, 100, 60),
    "CHC": (14, 51, 134),
    "CWS": (180, 180, 180),
    "NYY": (0, 48, 135),
    "NYM": (0, 45, 114),
    "BOS": (200, 0, 0),
    "ATL": (206, 17, 38),
    "PHI": (200, 0, 0),
    "MIA": (0, 163, 224),
    "WSH": (200, 0, 0),
    "STL": (196, 30, 58),
    "MIL": (18, 40, 75),
    "CIN": (198, 1, 31),
    "PIT": (253, 184, 39),
    "MIN": (0, 43, 92),
    "CLE": (0, 56, 100),
    "DET": (12, 35, 64),
    "KC":  (0, 70, 135),
    "TB":  (9, 44, 92),
    "BAL": (252, 76, 2),
    "TOR": (19, 74, 142),
}

TEAM_ABBR = {
    "San Diego Padres": "SD",
    "Los Angeles Dodgers": "LAD",
    "Los Angeles Angels": "LAA",
    "San Francisco Giants": "SF",
    "Arizona Diamondbacks": "AZ",
    "Colorado Rockies": "COL",
    "Seattle Mariners": "SEA",
    "Texas Rangers": "TEX",
    "Houston Astros": "HOU",
    "Oakland Athletics": "OAK",
    "Athletics": "ATH",
    "Chicago Cubs": "CHC",
    "Chicago White Sox": "CWS",
    "New York Yankees": "NYY",
    "New York Mets": "NYM",
    "Boston Red Sox": "BOS",
    "Atlanta Braves": "ATL",
    "Philadelphia Phillies": "PHI",
    "Miami Marlins": "MIA",
    "Washington Nationals": "WSH",
    "St. Louis Cardinals": "STL",
    "Milwaukee Brewers": "MIL",
    "Cincinnati Reds": "CIN",
    "Pittsburgh Pirates": "PIT",
    "Minnesota Twins": "MIN",
    "Cleveland Guardians": "CLE",
    "Detroit Tigers": "DET",
    "Kansas City Royals": "KC",
    "Tampa Bay Rays": "TB",
    "Baltimore Orioles": "BAL",
    "Toronto Blue Jays": "TOR",
}

def init_fonts():
    global med_font
    med_font = graphics.Font()
    med_font.LoadFont("/usr/local/share/midis-fonts/7x14B.bdf")

def get_game(team_id):
    try:
        games = statsapi.schedule(team=team_id)
        for game in games:
            status = game.get("status", "")
            relevant = ["In Progress", "Live", "Scheduled", "Warmup", "Final", "Game Over", "Completed Early"]
            if not any(s in status for s in relevant):
                continue

            home_name = game.get("home_name", "")
            away_name = game.get("away_name", "")
            home_score = game.get("home_score", 0)
            away_score = game.get("away_score", 0)
            inning = game.get("current_inning", "")
            inning_state = game.get("inning_state", "")
            outs = game.get("current_inning_ordinal", "")
            game_datetime = game.get("game_datetime", "")

            # Get outs from live game data
            try:
                game_id = game.get("game_id")
                linescore = statsapi.get('game', {'gamePk': game_id, 'fields': 'liveData,linescore,outs'})
                outs = linescore.get('liveData', {}).get('linescore', {}).get('outs', 0)
            except:
                outs = 0

            home_abbr = TEAM_ABBR.get(home_name, home_name[:3].upper())
            away_abbr = TEAM_ABBR.get(away_name, away_name[:3].upper())

            if any(s in status for s in ["Final", "Game Over", "Completed"]):
                inning_text = "FINAL"
            elif inning:
                if "Top" in inning_state:
                    inning_text = f"T{inning}"
                elif "Bot" in inning_state or "Bottom" in inning_state:
                    inning_text = f"B{inning}"
                elif "Mid" in inning_state:
                    inning_text = f"M{inning}"
                else:
                    inning_text = f"{inning}"
            else:
                try:
                    import pytz
                    gt = datetime.fromisoformat(game_datetime.replace("Z", "+00:00"))
                    pt = gt.astimezone(pytz.timezone("America/Los_Angeles"))
                    inning_text = pt.strftime("%-I:%M%p").lower()
                except:
                    inning_text = "SOON"

            return {
                "home": home_abbr,
                "away": away_abbr,
                "home_score": home_score,
                "away_score": away_score,
                "inning": inning_text,
                "outs": outs,
                "status": status,
                "game_datetime": game_datetime,
            }
    except Exception as e:
        print(f"Baseball error: {e}")
    return None

def is_game_relevant(game):
    if game is None:
        return False
    status = game.get("status", "")

    if any(s in status for s in ["In Progress", "Live", "Warmup"]):
        return True

    if any(s in status for s in ["Final", "Game Over", "Completed"]):
        try:
            game_dt = datetime.fromisoformat(game.get("game_datetime", "").replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            estimated_end = game_dt.replace(hour=min(game_dt.hour + 3, 23))
            minutes_since_end = (now - estimated_end).total_seconds() / 60
            return minutes_since_end <= 30
        except:
            return True

    try:
        game_dt = datetime.fromisoformat(game.get("game_datetime", "").replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        minutes_until = (game_dt - now).total_seconds() / 60
        return minutes_until <= 15
    except:
        return False

def fetch_games():
    global game_data, last_fetch
    games = []
    for team_id in [PADRES_ID, DODGERS_ID]:
        g = get_game(team_id)
        if g and is_game_relevant(g):
            games.append(g)
    game_data = games
    last_fetch = time.time()

def games_active():
    if time.time() - last_fetch > 60:
        fetch_games()
    return len(game_data) > 0

def draw(canvas, font, small_font):
    global game_data, last_fetch, current_game, last_switch, med_font

    if med_font is None:
        init_fonts()

    if time.time() - last_fetch > 60:
        fetch_games()

    if len(game_data) > 1 and time.time() - last_switch > SWITCH_DURATION:
        current_game = (current_game + 1) % len(game_data)
        last_switch = time.time()
        canvas.Clear()

    if not game_data:
        graphics.DrawText(canvas, small_font, 2, 16, graphics.Color(180, 180, 180), "No games today")
        return

    g = game_data[current_game % len(game_data)]

    away = g["away"]
    home = g["home"]
    away_score = g["away_score"]
    home_score = g["home_score"]
    inning = g["inning"]
    outs = g["outs"]

    away_color = TEAM_COLORS.get(away, (255, 255, 255))
    home_color = TEAM_COLORS.get(home, (255, 255, 255))

    graphics.DrawText(canvas, med_font, 2, 11, graphics.Color(*away_color), away)
    graphics.DrawText(canvas, med_font, 44, 11, graphics.Color(*away_color), str(away_score))
    graphics.DrawText(canvas, med_font, 2, 23, graphics.Color(*home_color), home)
    graphics.DrawText(canvas, med_font, 44, 23, graphics.Color(*home_color), str(home_score))

# Inning + outs on bottom line
    if inning == "FINAL":
        graphics.DrawText(canvas, small_font, 2, 30, graphics.Color(255, 60, 60), "FINAL")
    else:
        graphics.DrawText(canvas, small_font, 2, 30, graphics.Color(255, 60, 60), inning)
        # Draw 3 circles for outs
        for i in range(3):
            cx = 30 + i * 6
            cy = 27
            filled = i < outs
            if filled:
                for dx in range(-1, 2):
                    for dy in range(-1, 2):
                        canvas.SetPixel(cx + dx, cy + dy, 255, 60, 60)
            else:
                for dx, dy in [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(1,-1),(-1,1),(1,1)]:
                    canvas.SetPixel(cx + dx, cy + dy, 150, 50, 50)

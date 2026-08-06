import time
import requests
from datetime import datetime, timezone
from rgbmatrix import graphics

try:
    from midis_config import HOCKEY_TEAMS
except ImportError:
    HOCKEY_TEAMS = [25]  # LA Kings default

game_data = []
last_fetch = 0
current_game = 0
last_switch = 0
SWITCH_DURATION = 60

med_font = None

TEAM_COLORS = {
    "LAK": (162, 170, 173),
    "ANA": (252, 76, 2),
    "SJS": (0, 109, 117),
    "VGK": (185, 151, 91),
    "SEA": (0, 153, 153),
    "ARI": (140, 38, 51),
    "COL": (111, 38, 61),
    "DAL": (0, 104, 71),
    "MIN": (2, 73, 48),
    "STL": (0, 47, 135),
    "CHI": (207, 10, 44),
    "NSH": (255, 184, 28),
    "WPG": (4, 30, 66),
    "EDM": (4, 30, 66),
    "CGY": (210, 0, 28),
    "VAN": (0, 32, 91),
    "NYR": (0, 56, 168),
    "NYI": (0, 83, 155),
    "NJD": (206, 17, 38),
    "PHI": (247, 73, 2),
    "PIT": (252, 181, 20),
    "WSH": (4, 30, 66),
    "BOS": (252, 181, 20),
    "BUF": (0, 48, 135),
    "TOR": (0, 32, 91),
    "MTL": (175, 30, 45),
    "OTT": (198, 146, 20),
    "DET": (206, 17, 38),
    "CBJ": (0, 38, 84),
    "CAR": (206, 17, 38),
    "FLA": (4, 30, 66),
    "TBL": (0, 40, 104),
}

def init_fonts():
    global med_font
    med_font = graphics.Font()
    med_font.LoadFont("/usr/local/share/midis-fonts/7x14B.bdf")

def get_game(team_id):
    try:
        url = f"https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/teams/{team_id}/schedule"
        r = requests.get(url, timeout=10)
        data = r.json()
        events = data.get("events", [])
        now = datetime.now(timezone.utc)

        for event in events:
            competitions = event.get("competitions", [])
            if not competitions:
                continue
            comp = competitions[0]
            status = comp.get("status", {})
            state = status.get("type", {}).get("state", "")
            game_time = event.get("date", "")

            competitors = comp.get("competitors", [])
            if len(competitors) < 2:
                continue

            home = next((c for c in competitors if c.get("homeAway") == "home"), competitors[0])
            away = next((c for c in competitors if c.get("homeAway") == "away"), competitors[1])

            home_abbr = home.get("team", {}).get("abbreviation", "???")
            away_abbr = away.get("team", {}).get("abbreviation", "???")
            home_score = home.get("score", "0")
            away_score = away.get("score", "0")

            try:
                game_dt = datetime.fromisoformat(game_time.replace("Z", "+00:00"))
                minutes_until = (game_dt - now).total_seconds() / 60
                minutes_since = (now - game_dt).total_seconds() / 60
            except:
                minutes_until = 999
                minutes_since = 0

            if state == "in":
                period = status.get("period", 1)
                clock = status.get("displayClock", "")
                period_text = f"OT" if period > 3 else f"P{period}"
                status_text = f"{period_text} {clock}"
            elif state == "post":
                if minutes_since > 60:
                    continue
                status_text = "FINAL"
            elif state == "pre":
                if minutes_until > 15:
                    continue
                status_text = "SOON"
            else:
                continue

            return {
                "home": home_abbr,
                "away": away_abbr,
                "home_score": int(home_score) if home_score else 0,
                "away_score": int(away_score) if away_score else 0,
                "status": status_text,
                "state": state,
            }
    except Exception as e:
        print(f"Hockey error: {e}")
    return None

def fetch_games():
    global game_data, last_fetch
    games = []
    for team_id in HOCKEY_TEAMS:
        g = get_game(team_id)
        if g:
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
    status = g["status"]

    away_color = TEAM_COLORS.get(away, (255, 255, 255))
    home_color = TEAM_COLORS.get(home, (255, 255, 255))

    graphics.DrawText(canvas, med_font, 2, 11, graphics.Color(*away_color), away)
    graphics.DrawText(canvas, med_font, 44, 11, graphics.Color(*away_color), str(away_score))
    graphics.DrawText(canvas, med_font, 2, 23, graphics.Color(*home_color), home)
    graphics.DrawText(canvas, med_font, 44, 23, graphics.Color(*home_color), str(home_score))
    graphics.DrawText(canvas, small_font, 2, 30, graphics.Color(100, 200, 255), status)
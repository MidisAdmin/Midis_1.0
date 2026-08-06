import time
import requests
from datetime import datetime, timezone
from rgbmatrix import graphics

try:
    from midis_config import FOOTBALL_TEAMS, TIMEZONE
except ImportError:
    FOOTBALL_TEAMS = [14]  # LA Rams default
    TIMEZONE = "America/Los_Angeles"

game_data = []
last_fetch = 0
current_game = 0
last_switch = 0
SWITCH_DURATION = 60

med_font = None

TEAM_COLORS = {
    "LAC": (0, 128, 198),
    "LAR": (0, 53, 148),
    "KC":  (227, 24, 55),
    "SF":  (170, 0, 0),
    "DAL": (0, 53, 148),
    "NE":  (0, 34, 68),
    "GB":  (24, 48, 40),
    "CHI": (11, 22, 42),
    "MIA": (0, 142, 151),
    "BUF": (0, 51, 141),
    "PHI": (0, 76, 84),
    "NYG": (1, 35, 82),
    "NYJ": (18, 87, 64),
    "WAS": (63, 16, 16),
    "ATL": (167, 25, 48),
    "CAR": (0, 133, 202),
    "NO":  (211, 188, 141),
    "TB":  (213, 10, 10),
    "ARI": (151, 35, 63),
    "SEA": (0, 34, 68),
    "DEN": (251, 79, 20),
    "LV":  (165, 172, 175),
    "BAL": (26, 25, 95),
    "CLE": (49, 29, 0),
    "PIT": (255, 182, 18),
    "CIN": (251, 79, 20),
    "HOU": (3, 32, 47),
    "TEN": (75, 146, 219),
    "IND": (0, 44, 95),
    "JAX": (0, 103, 120),
    "MIN": (79, 38, 131),
    "DET": (0, 118, 182),
}

def init_fonts():
    global med_font
    med_font = graphics.Font()
    med_font.LoadFont("/usr/local/share/midis-fonts/7x14B.bdf")

def get_game(team_id):
    try:
        url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/{team_id}/schedule"
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
                status_text = f"Q{period} {clock}"
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
        print(f"Football error: {e}")
    return None

def fetch_games():
    global game_data, last_fetch
    games = []
    for team_id in FOOTBALL_TEAMS:
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
    graphics.DrawText(canvas, small_font, 2, 30, graphics.Color(255, 60, 60), status)
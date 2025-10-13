# app.py
import os
import requests
import logging
from flask import Flask, render_template, jsonify, request
from dotenv import load_dotenv
from telegram import Bot
from datetime import datetime, timedelta

load_dotenv()

# config
FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY")
THEODDS_API_KEY = os.getenv("THEODDS_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not all([FOOTBALL_API_KEY, THEODDS_API_KEY, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]):
    logging.warning("Alguma variável de ambiente importante não está definida.")

bot = Bot(token=TELEGRAM_TOKEN)
app = Flask(__name__, template_folder="templates")

# helpers
def clean_name(name: str) -> str:
    """Normalize team name for matching (lowercase, basic char replacements)."""
    if not name:
        return ""
    s = name.lower()
    s = s.replace("f.c.", "").replace("fc", "")
    s = s.replace(".", "").replace("'", "").replace("´", "").replace("`", "")
    s = s.replace("à", "a").replace("á", "a").replace("ã", "a").replace("â", "a")
    s = s.replace("é", "e").replace("ê", "e")
    s = s.replace("í", "i").replace("ó", "o").replace("ô", "o").replace("õ", "o")
    s = s.replace("ú", "u").replace("ç", "c")
    s = " ".join(s.split())
    return s.strip()

def get_matches_from_football_data():
    """Get today's matches from football-data.org (v4)."""
    url = "https://api.football-data.org/v4/matches"
    headers = {"X-Auth-Token": FOOTBALL_API_KEY}
    today = datetime.utcnow().date().isoformat()
    params = {"dateFrom": today, "dateTo": today}
    try:
        r = requests.get(url, headers=headers, params=params, timeout=12)
        r.raise_for_status()
        data = r.json()
        matches = data.get("matches", [])
        return matches
    except Exception as e:
        logging.exception("Erro ao buscar jogos na Football-data:")
        return []

def get_odds_from_theodds(sport_key="soccer"):
    """
    Query TheOddsAPI for odds. Returns list of games with bookmakers and markets.
    Uses region=eu and markets=spreads,totals by default.
    """
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds"
    params = {
        "regions": "eu",           # bookmakers/regions
        "markets": "spreads,totals",
        "oddsFormat": "decimal",
        "dateFormat": "iso",
        "apiKey": THEODDS_API_KEY
    }
    try:
        r = requests.get(url, params=params, timeout=12)
        r.raise_for_status()
        return r.json()  # list of games
    except Exception as e:
        logging.exception("Erro ao buscar odds na TheOddsAPI:")
        return []

def find_matching_odds(match, odds_list):
    """
    Try to find a matching odds entry for the football-data match.
    Matching by team name (cleaned) and start time +- 2 hours tolerance.
    Returns odds entry or None.
    """
    match_home = clean_name(match.get("homeTeam", {}).get("name", ""))
    match_away = clean_name(match.get("awayTeam", {}).get("name", ""))
    match_time_str = match.get("utcDate")  # ISO
    try:
        match_time = datetime.fromisoformat(match_time_str.replace("Z", "+00:00"))
    except Exception:
        match_time = None

    for odds_game in odds_list:
        teams = odds_game.get("teams") or []
        if len(teams) < 2:
            continue
        odds_home = clean_name(teams[0])
        odds_away = clean_name(teams[1])

        # Compare names by containment (try both orders)
        name_match = False
        if match_home and match_away:
            if match_home in odds_home or odds_home in match_home:
                if match_away in odds_away or odds_away in match_away:
                    name_match = True
            if not name_match:
                # try swapped
                if match_home in odds_away or odds_away in match_home:
                    if match_away in odds_home or odds_home in match_away:
                        name_match = True

        time_ok = True
        if match_time and "commence_time" in odds_game:
            try:
                otime = datetime.fromisoformat(odds_game["commence_time"].replace("Z", "+00:00"))
                diff = abs((otime - match_time).total_seconds())
                # allow up to 3 hours difference
                time_ok = diff < (3 * 3600)
            except Exception:
                time_ok = True

        if name_match and time_ok:
            return odds_game
    return None

def extract_lines_from_odds_entry(odds_entry):
    """
    Parse TheOddsAPI entry and extract a sensible set of lines:
    - handicap (spreads) best bookmaker first
    - totals (over/under)
    """
    result = {
        "handicap": None,
        "handicap_odd": None,
        "over_line": None,
        "over_odd": None,
    }
    if not odds_entry:
        return result

    bookmakers = odds_entry.get("bookmakers", []) or []
    # iterate bookmakers and markets to find spreads and totals
    for bm in bookmakers:
        markets = bm.get("markets", []) or []
        for m in markets:
            if m.get("key") == "spreads" and m.get("outcomes"):
                # take first outcome as sample
                outcomes = m["outcomes"]
                # pick the outcome that favors home team (heuristic)
                # outcomes typically contain something like {name: 'Team A', point: -1.5, price: 1.95}
                # we'll pick outcome with point != 0
                if outcomes:
                    # prioritize negative point (home favorite)
                    chosen = None
                    for o in outcomes:
                        if o.get("point") is not None:
                            chosen = o
                            break
                    if chosen:
                        result["handicap"] = chosen.get("point")
                        result["handicap_odd"] = chosen.get("price")
            if m.get("key") == "totals" and m.get("outcomes"):
                # find over outcome name contains "Over" or positive relation
                for o in m["outcomes"]:
                    if o.get("name") and "over" in o.get("name").lower():
                        result["over_line"] = o.get("point")
                        result["over_odd"] = o.get("price")
                        break
        # if we already have main lines, break
        if result["handicap"] is not None or result["over_line"] is not None:
            break
    return result

def simulate_setpiece_and_shots(match):
    """
    football-data doesn't give per-game setpiece/shots in free tier; simulate heuristics:
    Use recent form if available (not available here) — so use defaults.
    Return escanteios, finalizacoes_1t, finalizacoes_2t and a confidence metric.
    """
    # sensible defaults
    return {
        "escanteios": 8.5,
        "finalizacoes_1t": 4.5,
        "finalizacoes_2t": 3.5,
        "conf": 0.65
    }

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/buscar", methods=["POST"])
def buscar():
    try:
        # 1) get matches of today
        matches = get_matches_from_football_data()
        if not matches:
            return jsonify({"erro": "Nenhum jogo encontrado hoje."}), 404

        # 2) get odds from TheOddsAPI
        odds_list = get_odds_from_theodds(sport_key="soccer")
        # fallback: sometimes endpoint uses 'soccer' variants; do not fail if empty

        bilhetes = []
        for match in matches:
            home = match.get("homeTeam", {}).get("name")
            away = match.get("awayTeam", {}).get("name")
            comp = match.get("competition", {}).get("name")
            hora = match.get("utcDate", "")[11:16] if match.get("utcDate") else ""

            odds_entry = find_matching_odds(match, odds_list)
            lines = extract_lines_from_odds_entry(odds_entry) if odds_entry else {}
            sim = simulate_setpiece_and_shots(match)

            favorito = home  # simplificação: time da casa como favorito (pode ser melhorado)
            confidence = sim.get("conf", 0.6)
            # slightly bump confidence if lines exist
            if lines.get("handicap") is not None:
                confidence += 0.07
            if lines.get("over_line") is not None:
                confidence += 0.05
            if confidence > 0.92: confidence = 0.92

            # build bilhete text
            bilhete_lines = []
            bilhete_lines.append(f"⚽ {home} vs {away} ({hora})")
            bilhete_lines.append(f"🏆 {comp}")
            bilhete_lines.append(f"🏅 Sugestão: Vitória ou Empate do favorito: {favorito}")
            if lines.get("handicap") is not None:
                bilhete_lines.append(f"📈 Handicap {favorito} {lines['handicap']} @{lines['handicap_odd']}")
            else:
                bilhete_lines.append(f"📈 Handicap {favorito} -0.5 @ (sem linha)")

            if lines.get("over_line") is not None:
                bilhete_lines.append(f"🔢 Over {lines['over_line']} gols @{lines['over_odd']}")
            else:
                bilhete_lines.append(f"🔢 Over 1.5 gols @ (sem linha)")

            bilhete_lines.append(f"🔢 Escanteios do {favorito}: +{sim['escanteios']}")
            bilhete_lines.append(f"🎯 Finalizações {favorito}: 1T +{sim['finalizacoes_1t']} | 2T +{sim['finalizacoes_2t']}")
            bilhete_lines.append(f"💡 Confiança: {confidence*100:.0f}%")
            bilhete_text = "\n".join(bilhete_lines)

            # send to telegram (guardado em try to avoid entire run breaking)
            try:
                bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=bilhete_text)
            except Exception as e:
                logging.exception("Erro ao enviar mensagem Telegram:")

            bilhetes.append(bilhete_text)

        return jsonify({"dados": bilhetes})

    except Exception as e:
        logging.exception("Erro na rota /buscar:")
        return jsonify({"erro": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

import os
import logging
from datetime import datetime
from difflib import SequenceMatcher

import requests
from flask import Flask, render_template, jsonify, request
from telegram import Bot
from dotenv import load_dotenv

load_dotenv()

# --- Config / env ---
FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY")
THEODDS_API_KEY = os.getenv("THEODDS_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# basic checks
if not all([FOOTBALL_API_KEY, THEODDS_API_KEY, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]):
    logging.warning("Alguma variável de ambiente importante não está definida.")

# --- App & bot ---
app = Flask(__name__, template_folder="templates")
bot = Bot(token=TELEGRAM_TOKEN)

# --- Helpers ---
def clean_name(s: str) -> str:
    if not s:
        return ""
    s = s.lower()
    for a, b in [("f.c.", ""), ("fc", ""), (".", ""), ("'", ""), ("´", ""), ("`", "")]:
        s = s.replace(a, b)
    s = s.replace("à", "a").replace("á", "a").replace("ã", "a").replace("â", "a")
    s = s.replace("é", "e").replace("ê", "e")
    s = s.replace("í", "i").replace("ó", "o").replace("ô", "o").replace("õ", "o")
    s = s.replace("ú", "u").replace("ç", "c")
    return " ".join(s.split()).strip()

def similar(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()

def get_football_matches():
    url = "https://api.football-data.org/v4/matches"
    headers = {"X-Auth-Token": FOOTBALL_API_KEY}
    today = datetime.utcnow().date().isoformat()
    params = {"dateFrom": today, "dateTo": today}
    try:
        r = requests.get(url, headers=headers, params=params, timeout=12)
        r.raise_for_status()
        data = r.json()
        return data.get("matches", [])
    except requests.RequestException as e:
        logging.exception("Erro ao buscar na Football-data:")
        return []

def get_theodds_odds(sport_key="soccer"):
    # TheOddsAPI v4
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds"
    params = {
        "regions": "eu",
        "markets": "spreads,totals",
        "oddsFormat": "decimal",
        "dateFormat": "iso",
        "apiKey": THEODDS_API_KEY,
        "bookmakers": "all"
    }
    try:
        r = requests.get(url, params=params, timeout=12)
        r.raise_for_status()
        return r.json()  # list
    except requests.RequestException:
        logging.exception("Erro ao buscar odds na TheOddsAPI:")
        return []

def match_odds_entry(match, odds_list):
    # match: football-data match object
    home = clean_name(match.get("homeTeam", {}).get("name", ""))
    away = clean_name(match.get("awayTeam", {}).get("name", ""))
    match_time = None
    try:
        match_time = datetime.fromisoformat(match.get("utcDate").replace("Z", "+00:00"))
    except Exception:
        match_time = None

    best_score = 0.0
    best_entry = None
    for entry in odds_list:
        teams = entry.get("teams", [])
        if len(teams) < 2:
            continue
        e_home = clean_name(teams[0])
        e_away = clean_name(teams[1])
        score = (similar(home, e_home) + similar(away, e_away)) / 2.0
        # also try swapped order
        score_swapped = (similar(home, e_away) + similar(away, e_home)) / 2.0
        score = max(score, score_swapped)

        # time check (allow +/- 3h)
        time_ok = True
        if match_time and entry.get("commence_time"):
            try:
                e_time = datetime.fromisoformat(entry["commence_time"].replace("Z", "+00:00"))
                diff = abs((e_time - match_time).total_seconds())
                time_ok = diff < 3 * 3600
            except Exception:
                time_ok = True

        # prefer entries with reasonable similarity and time_ok
        if score > best_score and score > 0.5 and time_ok:
            best_score = score
            best_entry = entry
    return best_entry

def extract_lines(odds_entry):
    # returns dict with 'handicap' (point) and 'handicap_odd', 'over_line', 'over_odd'
    result = {"handicap": None, "handicap_odd": None, "over_line": None, "over_odd": None}
    if not odds_entry:
        return result
    for bm in odds_entry.get("bookmakers", [])[:6]:  # check several bookmakers but limit
        for m in bm.get("markets", []):
            if m.get("key") == "spreads":
                # outcomes example: [{'name':'Home','point':-1.5,'price':1.95}, ...]
                outs = m.get("outcomes", []) or []
                if outs:
                    # pick outcome with non-zero point and best (heuristic)
                    chosen = sorted(outs, key=lambda o: (abs(o.get("point", 0)), -o.get("price", 0)), reverse=True)[0]
                    result["handicap"] = chosen.get("point")
                    result["handicap_odd"] = chosen.get("price")
            if m.get("key") == "totals":
                outs = m.get("outcomes", []) or []
                for o in outs:
                    if o.get("name") and "over" in o.get("name").lower():
                        result["over_line"] = o.get("point")
                        result["over_odd"] = o.get("price")
                        break
        if result["handicap"] is not None or result["over_line"] is not None:
            break
    return result

def simulate_setpieces_and_shots(match):
    # If no per-game stats are available, use reasonable defaults / heuristics
    return {"escanteios": 8.5, "shots_1t": 4.5, "shots_2t": 3.5, "conf": 0.65}

# --- Routes ---
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/buscar", methods=["POST"])
def buscar():
    try:
        matches = get_football_matches()
        if not matches:
            logging.info("Nenhum jogo encontrado hoje (Football-data retornou vazio).")
            return jsonify({"erro": "Nenhum jogo encontrado hoje."}), 404

        odds_list = get_theodds_odds()
        bilhetes = []

        for match in matches:
            home = match.get("homeTeam", {}).get("name", "Casa")
            away = match.get("awayTeam", {}).get("name", "Fora")
            comp = match.get("competition", {}).get("name", "")
            hora = match.get("utcDate", "")[11:16] if match.get("utcDate") else ""

            odds_entry = match_odds_entry(match, odds_list)
            lines = extract_lines(odds_entry) if odds_entry else {}
            sim = simulate_setpieces_and_shots(match)

            favorito = home  # heurística simples (pode melhorar com odds)
            conf = sim.get("conf", 0.6)
            if lines.get("handicap") is not None:
                conf += 0.07
            if lines.get("over_line") is not None:
                conf += 0.05
            conf = min(conf, 0.95)

            parts = [
                f"⚽ {home} vs {away} ({hora})",
                f"🏆 {comp}",
                f"✔ Sugestão: Vitória ou empate do favorito — {favorito}"
            ]
            if lines.get("handicap") is not None:
                parts.append(f"📈 Handicap {favorito} {lines['handicap']} @{lines.get('handicap_odd')}")
            else:
                parts.append(f"📈 Handicap {favorito} -0.5 @ (sem linha)")

            if lines.get("over_line") is not None:
                parts.append(f"🔢 Over {lines['over_line']} gols @{lines.get('over_odd')}")
            else:
                parts.append("🔢 Over 1.5 gols @ (sem linha)")

            parts.append(f"🚩 Escanteios do {favorito}: +{sim['escanteios']}")
            parts.append(f"🎯 Finalizações {favorito}: 1T +{sim['shots_1t']} | 2T +{sim['shots_2t']}")
            parts.append(f"💡 Confiança: {conf*100:.0f}%")

            text = "\n".join(parts)
            bilhetes.append(text)

            # send to telegram but don't crash entire loop on failure
            try:
                bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=text)
                logging.info("Mensagem enviada ao Telegram para %s vs %s", home, away)
            except Exception:
                logging.exception("Falha ao enviar mensagem Telegram para jogo %s vs %s", home, away)

        return jsonify({"dados": bilhetes}), 200

    except Exception:
        logging.exception("Erro inesperado na rota /buscar")
        return jsonify({"erro": "Erro interno no servidor"}), 500

# run
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

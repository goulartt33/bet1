import os
import requests
from flask import Flask, jsonify
from telegram import Bot
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY")

bot = Bot(token=TELEGRAM_TOKEN)
app = Flask(__name__)
HEADERS = {"X-Auth-Token": FOOTBALL_API_KEY}

# Função para pegar últimos 5 jogos de um time
def get_last_5_matches(team_id):
    url = f"https://api.football-data.org/v4/teams/{team_id}/matches?limit=5"
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        return []
    data = response.json()
    matches = []

    for match in data.get("matches", []):
        home = match["homeTeam"]["id"]
        away = match["awayTeam"]["id"]
        home_score = match["score"]["fullTime"]["home"]
        away_score = match["score"]["fullTime"]["away"]

        is_home = team_id == home
        matches.append({
            "goals_for": home_score if is_home else away_score,
            "goals_against": away_score if is_home else home_score,
            "corners": 3,  # Exemplo fixo, pode integrar API real de corners
            "shots": 5,    # Exemplo fixo
            "cards": 1     # Exemplo fixo
        })
    return matches

# Função para calcular médias e sugerir apostas
def analyze_team(team_id):
    last_matches = get_last_5_matches(team_id)
    if not last_matches:
        return {}

    total_goals = sum(m["goals_for"] for m in last_matches)
    total_corners = sum(m["corners"] for m in last_matches)
    total_shots = sum(m["shots"] for m in last_matches)
    total_cards = sum(m["cards"] for m in last_matches)

    avg_goals = total_goals / len(last_matches)
    avg_corners = total_corners / len(last_matches)
    avg_shots = total_shots / len(last_matches)
    avg_cards = total_cards / len(last_matches)

    return {
        "avg_goals": avg_goals,
        "avg_corners": avg_corners,
        "avg_shots": avg_shots,
        "avg_cards": avg_cards,
        "over_1_5_goals": avg_goals > 1.5,
        "over_2_5_corners": avg_corners > 2.5,
        "over_1_5_shots": avg_shots > 1.5,
        "high_card_risk": avg_cards > 1
    }

# Função para gerar bilhete completo
def generate_bet_ticket(matches):
    message = "🎯 Gerenciador FX - Bilhete Profissional\n\n"
    for match in matches:
        home_analysis = analyze_team(match["home_id"])
        away_analysis = analyze_team(match["away_id"])

        message += f"⚽ {match['home_name']} x {match['away_name']}\n"
        # Odds básicas
        message += f"🏆 {match['home_name']} | Odd {match['odds']['home']} | Prob {match['prob']['home']:.1f}%\n"
        message += f"🏆 {match['away_name']} | Odd {match['odds']['away']} | Prob {match['prob']['away']:.1f}%\n"
        message += f"🤝 Draw | Odd {match['odds']['draw']} | Prob {match['prob']['draw']:.1f}%\n"

        # Sugestões baseadas em estatísticas
        if home_analysis.get("over_1_5_goals") or away_analysis.get("over_1_5_goals"):
            message += "⚽ Over 1.5 gols\n"
        if home_analysis.get("over_2_5_corners") or away_analysis.get("over_2_5_corners"):
            message += "📏 Over 2.5 escanteios\n"
        if home_analysis.get("avg_goals") > away_analysis.get("avg_goals"):
            message += f"🤝 {match['home_name']} ou empate\n"
        elif away_analysis.get("avg_goals") > home_analysis.get("avg_goals"):
            message += f"🤝 {match['away_name']} ou empate\n"

        message += "\n"
    
    bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)

@app.route("/generate_ticket", methods=["GET"])
def generate_ticket_endpoint():
    # Exemplo de jogos - substitua com IDs reais da API
    matches = [
        {"home_id": 1, "away_id": 2, "home_name": "Arsenal FC", "away_name": "Olympiakos SFP",
         "odds": {"home": 1.72, "draw": 3.40, "away": 4.50}, "prob": {"home": 58.1, "draw": 29.4, "away": 12.5}},
        {"home_id": 3, "away_id": 4, "home_name": "Borussia Dortmund", "away_name": "Athletic Club",
         "odds": {"home": 1.95, "draw": 3.20, "away": 4.00}, "prob": {"home": 51.2, "draw": 25.0, "away": 23.8}}
    ]
    generate_bet_ticket(matches)
    return jsonify({"status": "success", "message": "Bilhete enviado via Telegram!"})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

from flask import Flask, jsonify
from flask_cors import CORS
import os
import requests
from telegram import Bot
from telegram.error import TelegramError
import random

# Flask app
app = Flask(__name__)
CORS(app)  # habilita CORS

# Variáveis de ambiente
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY")
PROB_MIN = float(os.getenv("PROB_MIN", 60))
ODD_MIN = float(os.getenv("ODD_MIN", 2.0))
COMPETITION_IDS = os.getenv("COMPETITION_IDS", "").split(",")

# Inicializar bot do Telegram
try:
    bot = Bot(token=TELEGRAM_TOKEN)
except TelegramError as e:
    print("Erro ao iniciar o bot do Telegram:", e)
    bot = None


@app.route("/")
def home():
    return "Bot de apostas está rodando! ⚽🏀"


@app.route("/api/games")
def get_games():
    headers = {"X-Auth-Token": FOOTBALL_API_KEY}
    games = []

    for comp in COMPETITION_IDS:
        url = f"https://api.football-data.org/v4/competitions/{comp}/matches?status=SCHEDULED"
        try:
            r = requests.get(url, headers=headers, timeout=10)
            data = r.json()
            for match in data.get("matches", []):
                games.append({
                    "competition": comp,
                    "home": match["homeTeam"]["name"],
                    "away": match["awayTeam"]["name"],
                    "utcDate": match["utcDate"]
                })
        except Exception as e:
            print(f"Erro ao buscar competição {comp}: {e}")

    return jsonify({"games": games, "count": len(games)})


@app.route("/generate", methods=["POST"])
def generate_bilhetes():
    headers = {"X-Auth-Token": FOOTBALL_API_KEY}
    bilhetes = []

    for comp in COMPETITION_IDS:
        url = f"https://api.football-data.org/v4/competitions/{comp}/matches?status=SCHEDULED"
        try:
            r = requests.get(url, headers=headers, timeout=10)
            data = r.json()
            for match in data.get("matches", []):
                prob = random.uniform(50, 90)  # simulação
                odd = round(random.uniform(1.5, 3.5), 2)  # simulação

                if prob >= PROB_MIN and odd >= ODD_MIN:
                    bilhete = f"{match['homeTeam']['name']} vs {match['awayTeam']['name']} | Odd: {odd} | Prob: {prob:.1f}%"
                    bilhetes.append(bilhete)
        except Exception as e:
            print(f"Erro ao buscar {comp}: {e}")

    status = "OK" if bilhetes else "Nenhum bilhete encontrado."

    # Envia para Telegram
    if bot and bilhetes:
        try:
            mensagem = "🎟️ *Bilhetes Gerados*\n\n" + "\n".join(bilhetes)
            bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=mensagem, parse_mode="Markdown")
        except TelegramError as e:
            print("Erro ao enviar para Telegram:", e)

    return jsonify({"bilhetes": bilhetes, "status": status})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

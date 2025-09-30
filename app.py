from flask import Flask, jsonify
from flask_cors import CORS
import os
import requests
from telegram import Bot
from telegram.error import TelegramError

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


@app.route("/send-test")
def send_test():
    if bot:
        try:
            bot.send_message(chat_id=TELEGRAM_CHAT_ID, text="Teste do bot funcionando ✅")
            return "Mensagem enviada com sucesso!"
        except TelegramError as e:
            return f"Erro ao enviar mensagem: {e}"
    else:
        return "Bot do Telegram não inicializado."


# ✅ Rota de teste simples para o navegador
@app.route("/api/teste")
def api_teste():
    return {"status": "ok", "msg": "API acessível via navegador ✅"}


# ✅ Rota para buscar jogos das competições configuradas
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


if __name__ == "__main__":
    # Porta 5000 local
    app.run(host="0.0.0.0", port=5000)

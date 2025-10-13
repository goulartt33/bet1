from flask import Flask, render_template, jsonify, request
import os
import requests
from dotenv import load_dotenv
from telegram import Bot

# Carrega variáveis do ambiente (.env)
load_dotenv()

# Configurações
FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

bot = Bot(token=TELEGRAM_TOKEN)
app = Flask(__name__)

# Página inicial
@app.route("/")
def index():
    return render_template("index.html")

# Buscar jogos e gerar bilhetes
@app.route("/buscar", methods=["POST"])
def buscar():
    try:
        url = "https://api.football-data.org/v4/matches"
        headers = {"X-Auth-Token": FOOTBALL_API_KEY}
        response = requests.get(url, headers=headers)
        data = response.json()

        if "matches" not in data:
            return jsonify({"erro": "Sem dados da API"}), 400

        bilhetes = []
        for match in data["matches"][:5]:
            home = match["homeTeam"]["name"]
            away = match["awayTeam"]["name"]
            comp = match["competition"]["name"]
            hora = match["utcDate"][11:16]

            bilhete = (
                f"⚽ {home} vs {away} ({hora})\n"
                f"🏆 {comp}\n"
                f"✅ Vitória ou empate do favorito: {home}\n"
                f"🔢 Escanteios do {home}: +5.5\n"
                f"🎯 Finalizações {home}: 1T +4.5 | 2T +3.5\n"
                f"📈 Over 1.5 gols (conf 0.72)\n"
                f"📈 Handicap -0.5 {home} (conf 0.68)"
            )

            bilhetes.append(bilhete)
            bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=bilhete)

        return jsonify({"dados": bilhetes})

    except Exception as e:
        return jsonify({"erro": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

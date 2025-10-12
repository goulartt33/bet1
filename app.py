# app.py
from flask import Flask, jsonify, request, send_from_directory
import os
import requests
from telegram import Bot
from datetime import datetime

app = Flask(__name__, static_folder="frontend", static_url_path="")

# Configurações do Telegram
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
bot = Bot(token=TELEGRAM_TOKEN)

# Configuração Football-Data API
FOOTBALL_API_KEY = os.environ.get("FOOTBALL_API_KEY")
BASE_URL = "https://api.football-data.org/v4/"

# Servir front-end
@app.route("/")
def index():
    return send_from_directory("frontend", "index.html")

# Função para obter jogos do dia
def get_todays_matches():
    today = datetime.utcnow().strftime("%Y-%m-%d")
    headers = {"X-Auth-Token": FOOTBALL_API_KEY}
    url = f"{BASE_URL}matches?dateFrom={today}&dateTo={today}"
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return []
    return response.json().get("matches", [])

# Função para gerar bilhete profissional
def generate_bilhetes():
    matches = get_todays_matches()
    bilhetes = []

    for match in matches:
        home = match["homeTeam"]["name"]
        away = match["awayTeam"]["name"]
        favorito = home  # simplificação: considerar o time da casa favorito
        jogo = f"{home} vs {away}"
        hora = datetime.strptime(match["utcDate"], "%Y-%m-%dT%H:%M:%SZ").strftime("%H:%M")

        # Simulação de estatísticas (você pode conectar a API real de estatísticas detalhadas)
        escanteios = 10
        finalizacoes_1T = 5
        finalizacoes_2T = 4
        conf = 0.7  # confiança baseada em histórico ou algoritmo

        bilhete = {
            "jogo": jogo,
            "data": hora,
            "favorito": favorito,
            "resultado": "Vitória ou Empate",
            "escanteios": escanteios,
            "finalizacoes_1T": finalizacoes_1T,
            "finalizacoes_2T": finalizacoes_2T,
            "conf": conf
        }
        bilhetes.append(bilhete)

    return bilhetes

# Endpoint para retornar bilhetes
@app.route("/bilhetes")
def bilhetes():
    try:
        bilhetes = generate_bilhetes()
        return jsonify(bilhetes)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Endpoint para enviar bilhetes ao Telegram
@app.route("/send-telegram", methods=["POST"])
def send_telegram():
    data = request.json
    if not data:
        return jsonify({"error": "Nenhum bilhete recebido"}), 400
    try:
        for b in data:
            message = (
                f"🎯 {b['resultado']} do favorito: {b['favorito']}\n"
                f"⚽ {b['jogo']} ({b['data']})\n"
                f"📊 Escanteios do time: {b['escanteios']}\n"
                f"🔢 Finalizações 1T: {b['finalizacoes_1T']} | 2T: {b['finalizacoes_2T']}\n"
                f"💡 Confiança: {b['conf']*100:.1f}%"
            )
            bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        return jsonify({"status": "Mensagens enviadas com sucesso"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

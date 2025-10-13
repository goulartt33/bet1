# app.py
import os
import requests
from flask import Flask, jsonify, render_template, request
from telegram import Bot
from datetime import datetime
from dotenv import load_dotenv

# Carregar variáveis do .env
load_dotenv()

FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

app = Flask(__name__)
bot = Bot(token=TELEGRAM_TOKEN)

# Função para buscar jogos do dia usando Football-data.org
def buscar_jogos():
    url = "https://api.football-data.org/v4/matches"
    headers = {"X-Auth-Token": FOOTBALL_API_KEY}
    params = {"dateFrom": datetime.now().strftime("%Y-%m-%d"),
              "dateTo": datetime.now().strftime("%Y-%m-%d")}
    response = requests.get(url, headers=headers, params=params)
    data = response.json()
    jogos = []

    for match in data.get("matches", []):
        time_casa = match["homeTeam"]["name"]
        time_fora = match["awayTeam"]["name"]
        horario = match["utcDate"].replace("T", " ").replace("Z", "")
        ligas = match["competition"]["name"]

        # Simulação básica de odds e sugestões (com base em tendências)
        bilhete = {
            "jogo": f"{time_casa} vs {time_fora}",
            "horario": horario,
            "liga": ligas,
            "sugestoes": [
                f"🏆 Vitória ou empate do favorito ({time_casa})",
                f"⚽ Over 1.5 gols",
                f"🚩 Escanteios +8.5 do {time_casa}",
                f"🎯 Finalizações do {time_casa} 1T +4.5 | 2T +3.5"
            ]
        }
        jogos.append(bilhete)
    return jogos

# Rota principal (frontend)
@app.route('/')
def index():
    return render_template('index.html')

# Rota para buscar oportunidades
@app.route('/buscar', methods=['POST'])
def buscar():
    try:
        jogos = buscar_jogos()
        if not jogos:
            return jsonify({"erro": "Nenhum jogo encontrado hoje."}), 404

        mensagens = []
        for jogo in jogos:
            msg = (
                f"⚽ {jogo['jogo']} ({jogo['horario']})\n"
                f"🏆 Liga: {jogo['liga']}\n\n"
                f"💡 Sugestões:\n"
                + "\n".join(jogo['sugestoes'])
            )
            mensagens.append(msg)
            bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg)

        return jsonify({"mensagem": "Bilhetes enviados com sucesso!", "dados": mensagens})
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)

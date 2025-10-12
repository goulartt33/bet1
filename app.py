# app.py
from flask import Flask, jsonify, request, send_from_directory
import os
import requests
from dotenv import load_dotenv
from telegram import Bot
from datetime import datetime

# Carregar variáveis de ambiente
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY")

bot = Bot(token=TELEGRAM_TOKEN)
app = Flask(__name__, static_folder='frontend')

# Serve front-end
@app.route('/')
def index():
    return send_from_directory('frontend', 'index.html')

# Função para buscar jogos de hoje
def buscar_jogos_hoje():
    url = "https://api.football-data.org/v4/matches?dateFrom=today&dateTo=today"
    headers = {"X-Auth-Token": FOOTBALL_API_KEY}
    resp = requests.get(url, headers=headers)
    bilhetes = []

    if resp.status_code == 200:
        jogos = resp.json().get("matches", [])

        for jogo in jogos:
            home = jogo['homeTeam']['name']
            away = jogo['awayTeam']['name']
            horario = datetime.fromisoformat(jogo['utcDate'].replace("Z", "+00:00")).strftime("%H:%M")

            # Simulação de análise profissional baseada em estatísticas recentes
            bilhete = {
                "jogo": f"{home} vs {away}",
                "data": horario,
                "resultado_fav": f"{home} ou Empate",  # Favorito simplificado
                "handicap": f"-0.5 {home}",
                "over_gols": "Over 2.5",
                "escanteios": 9,  # pode ser ajustado por estatísticas reais
                "finalizacoes_1T": 5,
                "finalizacoes_2T": 4,
                "conf": 0.75
            }
            bilhetes.append(bilhete)
    return bilhetes

# Rota para retornar bilhetes
@app.route('/bilhetes', methods=['GET'])
def bilhetes():
    bilhetes = buscar_jogos_hoje()
    return jsonify(bilhetes)

# Rota para enviar bilhetes ao Telegram
@app.route('/send-telegram', methods=['POST'])
def send_telegram():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Nenhum dado enviado"}), 400

    for b in data:
        mensagem = (
            f"⚽ {b['jogo']} ({b['data']})\n"
            f"🏆 Resultado favorito: {b['resultado_fav']}\n"
            f"📈 Handicap: {b['handicap']}\n"
            f"🔢 Over gols: {b['over_gols']}\n"
            f"📊 Escanteios do time: {b['escanteios']}\n"
            f"🎯 Finalizações 1T: {b['finalizacoes_1T']} | 2T: {b['finalizacoes_2T']}\n"
            f"💡 Confiança: {b['conf']*100:.1f}%"
        )
        try:
            bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=mensagem)
        except Exception as e:
            print("Erro ao enviar mensagem:", e)
    return jsonify({"status": "enviado"})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

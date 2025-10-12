# app.py
import os
from flask import Flask, render_template, request, jsonify
import requests
from telegram import Bot

# Configurações Flask
app = Flask(__name__, template_folder='frontend')

# Carregar variáveis de ambiente
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY")

bot = Bot(token=TELEGRAM_TOKEN)

# Função para buscar oportunidades reais (exemplo: últimas partidas e estatísticas)
def buscar_oportunidades():
    url = "https://api.football-data.org/v4/matches?status=SCHEDULED"  # Exemplo de endpoint
    headers = {"X-Auth-Token": FOOTBALL_API_KEY}
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return None
    
    data = response.json()
    bilhetes = []
    
    # Montar bilhetes de exemplo (você pode detalhar mais: escanteios, finalizações, etc.)
    for match in data.get("matches", [])[:5]:  # pegar apenas os 5 primeiros jogos
        home = match["homeTeam"]["name"]
        away = match["awayTeam"]["name"]
        time = home  # exemplo: favorito é o time da casa
        bilhete = (
            f"⚽ {home} vs {away} ({match['utcDate'][:16]} UTC)\n"
            f"🏆 Vitória ou Empate do favorito: {time}\n"
            f"🔢 Escanteios: +9.5\n"
            f"🎯 Finalizações 1T: +4.5 | 2T: +3.5\n"
        )
        bilhetes.append(bilhete)
    return bilhetes

# Rota principal
@app.route('/')
def home():
    return render_template('index.html')

# Rota para buscar oportunidades e enviar Telegram
@app.route('/buscar', methods=['POST'])
def buscar():
    bilhetes = buscar_oportunidades()
    if not bilhetes:
        return jsonify({"status": "erro", "msg": "Erro ao carregar bilhetes"}), 500
    
    try:
        for b in bilhetes:
            bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=b)
    except Exception as e:
        return jsonify({"status": "erro", "msg": f"Erro ao enviar Telegram: {e}"}), 500

    return jsonify({"status": "sucesso", "msg": "Bilhetes enviados com sucesso!"})

# Rodar app
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)

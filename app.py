# app.py
from flask import Flask, render_template, request, jsonify
import os
import requests
from telegram import Bot
from telegram.error import TelegramError

app = Flask(__name__)

# Carregar variáveis de ambiente
FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

bot = Bot(token=TELEGRAM_TOKEN)

# Endpoint da sua API real (substitua pelo endpoint correto)
API_URL = "https://api-da-superbet-ou-outra-free.com/jogos"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/buscar", methods=["POST"])
def buscar_jogos():
    try:
        # Requisição para sua API
        response = requests.get(f"{API_URL}?token={FOOTBALL_API_KEY}")
        response.raise_for_status()
        jogos = response.json()  # Assumindo que sua API retorna JSON

        bilhetes = []
        for jogo in jogos:
            # Montando o bilhete com base nos dados da API
            time_casa = jogo.get("time_casa")
            time_fora = jogo.get("time_fora")
            odds = jogo.get("odds")  # exemplo: {'over_1_5': 1.8, 'both_teams_score': 1.9}
            
            bilhete = f"🏟 {time_casa} vs {time_fora}\n"
            if odds:
                if "over_1_5" in odds:
                    bilhete += f"🔢 Mais de 1.5 gols @ {odds['over_1_5']}\n"
                if "both_teams_score" in odds:
                    bilhete += f"⚽ Ambas marcam @ {odds['both_teams_score']}\n"
                if "escanteios_over_4_5" in odds:
                    bilhete += f"🎯 Mais de 4.5 escanteios @ {odds['escanteios_over_4_5']}\n"

            bilhetes.append(bilhete)

        # Enviar cada bilhete para o Telegram
        for bilhete in bilhetes:
            try:
                bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=bilhete)
            except TelegramError as e:
                print(f"Erro ao enviar bilhete: {e}")

        return jsonify({"status": "sucesso", "bilhetes": bilhetes})
    
    except requests.RequestException as e:
        print(f"Erro ao buscar jogos: {e}")
        return jsonify({"status": "erro", "mensagem": str(e)}), 500

if __name__ == "__main__":
    # Configuração para Render
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

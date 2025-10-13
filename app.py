from flask import Flask, request, render_template, jsonify
import os
import requests
from telegram import Bot
from dotenv import load_dotenv

# Carrega variáveis do .env
load_dotenv()

app = Flask(__name__)

# Configurações do Telegram
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Inicializa bot
bot = Bot(token=TELEGRAM_TOKEN)

# URL da sua API real que retorna os bilhetes
API_BILHETES_URL = "https://sua-api-de-bilhetes.com/bilhetes"  # Substitua pela URL real da sua API

# Página principal
@app.route("/")
def index():
    return render_template("index.html")  # HTML na pasta templates

# Endpoint para buscar oportunidades
@app.route("/buscar", methods=["POST"])
def buscar_oportunidades():
    try:
        # Chama API real para gerar bilhetes
        response = requests.get(API_BILHETES_URL, timeout=10)
        if response.status_code != 200:
            return f"Erro ao acessar API de bilhetes: {response.status_code}", 500

        bilhetes_data = response.json()  # Deve retornar lista ou texto dos bilhetes

        # Formata os bilhetes em uma mensagem para Telegram
        mensagem = "🎯 Novos Bilhetes Gerados:\n\n"
        if isinstance(bilhetes_data, list):
            for i, bilhete in enumerate(bilhetes_data, 1):
                mensagem += f"{i}️⃣ {bilhete}\n"
        else:
            mensagem += str(bilhetes_data)

        # Envia mensagem para o Telegram
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=mensagem)

        return "Bilhetes enviados com sucesso! ✅"

    except requests.exceptions.RequestException as e:
        return f"Erro ao chamar API de bilhetes: {str(e)}", 500
    except Exception as e:
        return f"Erro ao enviar bilhetes: {str(e)}", 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=10000)

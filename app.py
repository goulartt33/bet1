from flask import Flask, render_template, request
import requests
from dotenv import load_dotenv
import os
from telegram import Bot

# Carrega variáveis de ambiente do .env
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

bot = Bot(token=TELEGRAM_TOKEN)

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/send-message', methods=['POST'])
def send_message():
    data = request.form
    message = data.get('message')
    if message:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        return "Mensagem enviada com sucesso!"
    return "Nenhuma mensagem para enviar."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

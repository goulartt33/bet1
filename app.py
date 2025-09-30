# app.py
from flask import Flask
import os
from telegram import Bot
from telegram.error import TelegramError

# Flask app
app = Flask(__name__)

# Carregar variáveis de ambiente
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

# Exemplo de envio de mensagem
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

if __name__ == "__main__":
    # Para testes locais, porta 5000
    app.run(host="0.0.0.0", port=5000)

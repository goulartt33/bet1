# app.py
from flask import Flask, request, jsonify
import os
import random
from telegram import Bot
from telegram.error import TelegramError
from dotenv import load_dotenv

# Carregar variáveis do arquivo .env (se estiver em ambiente local)
load_dotenv()

# Flask app
app = Flask(__name__)

# Variáveis de ambiente
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY")
PROB_MIN = float(os.getenv("PROB_MIN", 60))
ODD_MIN = float(os.getenv("ODD_MIN", 2.0))
COMPETITION_IDS = os.getenv("COMPETITION_IDS", "").split(",")

# Inicializar bot do Telegram
bot = None
if TELEGRAM_TOKEN:
    try:
        bot = Bot(token=TELEGRAM_TOKEN)
        print("✅ Bot do Telegram inicializado com sucesso!")
    except TelegramError as e:
        print("❌ Erro ao iniciar o bot do Telegram:", e)
else:
    print("⚠️ TELEGRAM_TOKEN não encontrado. Configure no Render ou no arquivo .env.")

@app.route("/")
def home():
    return "Bot de apostas está rodando! ⚽🏀"

# Rota de geração de bilhetes
@app.route("/gerar", methods=["POST"])
def gerar():
    matches = [
        {"homeTeam": {"name": "Flamengo"}, "awayTeam": {"name": "Palmeiras"}},
        {"homeTeam": {"name": "Barcelona"}, "awayTeam": {"name": "Real Madrid"}},
        {"homeTeam": {"name": "PSG"}, "awayTeam": {"name": "Marseille"}},
    ]

    bilhetes = []
    for match in matches:
        prob = random.uniform(PROB_MIN, 95)
        odd = round(random.uniform(ODD_MIN, 3.5), 2)
        bilhete = f"{match['homeTeam']['name']} vs {match['awayTeam']['name']} | Odd: {odd} | Prob: {prob:.1f}%"
        bilhetes.append(bilhete)

    if bot and bilhetes:
        try:
            mensagem = "🎟️ *Bilhetes Gerados:*\n\n" + "\n".join(bilhetes)
            bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=mensagem, parse_mode="Markdown")
            print("📨 Bilhetes enviados ao Telegram com sucesso!")
        except TelegramError as e:
            print("❌ Erro ao enviar mensagem para o Telegram:", e)

    return jsonify({
        "status": "ok",
        "bilhetes": bilhetes if bilhetes else ["Nenhum bilhete gerado."]
    })

# Rota de teste Telegram
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
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))

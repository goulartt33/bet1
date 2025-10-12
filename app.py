from flask import Flask, jsonify, request, render_template
import os
from telegram import Bot
from telegram.error import TelegramError

app = Flask(__name__)

# Carregar variáveis de ambiente
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

bot = Bot(token=TELEGRAM_TOKEN)

# Dados simulados de bilhetes (substitua pela sua lógica real)
bilhetes = [
    {
        "jogo": "Flamengo vs Palmeiras",
        "data": "12/10/2025 20:00",
        "spread": {"Flamengo": -1.5, "Palmeiras": 1.5},
        "total": {"over": 2.5, "under": 2.5},
        "conf": 0.85
    },
    {
        "jogo": "Atlético MG vs Santos",
        "data": "12/10/2025 21:00",
        "spread": {"Atlético MG": 0.0, "Santos": 0.0},
        "total": {"over": 1.5, "under": 1.5},
        "conf": 0.72
    }
]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/bilhetes')
def get_bilhetes():
    return jsonify(bilhetes)

@app.route('/enviar_telegram', methods=['POST'])
def enviar_telegram():
    data = request.get_json()
    bilhetes_enviar = data.get('bilhetes', [])
    mensagem = "📊 *Bilhetes Automáticos*\n\n"

    for b in bilhetes_enviar:
        mensagem += f"🏟️ {b['jogo']} ({b['data']})\n"
        mensagem += f"📈 Spread: {b['spread']}\n"
        mensagem += f"🔢 Total: {b['total']}\n"
        mensagem += f"💡 Confiança: {b['conf']}\n\n"

    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=mensagem, parse_mode="Markdown")
        return jsonify({"status": "success", "message": "Bilhetes enviados para o Telegram!"})
    except TelegramError as e:
        return jsonify({"status": "error", "message": f"Erro ao enviar Telegram: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))

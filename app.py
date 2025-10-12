from flask import Flask, render_template, jsonify
import os
import requests
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

app = Flask(__name__)

# Rota principal
@app.route('/')
def home():
    return render_template('index.html')

# Rota para buscar oportunidades e enviar Telegram
@app.route('/buscar', methods=['POST'])
def buscar_oportunidades():
    try:
        # Aqui você pode colocar a lógica real de busca de oportunidades
        mensagem = "⚽ Novas oportunidades de apostas disponíveis!"
        
        # Enviar mensagem para Telegram
        url_telegram = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": mensagem,
            "parse_mode": "HTML"
        }
        response = requests.post(url_telegram, data=payload)
        response.raise_for_status()
        
        return jsonify({"status": "sucesso", "mensagem": "Mensagem enviada para o Telegram!"})
    except Exception as e:
        return jsonify({"status": "erro", "mensagem": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)

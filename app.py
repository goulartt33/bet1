from flask import Flask, render_template, jsonify
import os
import requests
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
API_TOKEN = os.getenv("API_TOKEN")

app = Flask(__name__)

API_BASE_URL = "https://api.superbet.com.br/v1"  # Ajuste se necessário

def buscar_dados_reais():
    """
    Busca dados reais da API de apostas.
    Retorna lista de bilhetes com odds, times, handicaps, etc.
    """
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    
    endpoint = f"{API_BASE_URL}/games/today"
    response = requests.get(endpoint, headers=headers)
    response.raise_for_status()
    jogos = response.json()
    
    bilhetes = []
    for jogo in jogos:
        bilhete = f"🏟 {jogo['home_team']} vs {jogo['away_team']} ({jogo['start_time']})\n"
        bilhete += f"📈 Spread: {jogo.get('spread_home', 'N/A')} / {jogo.get('spread_away', 'N/A')}\n"
        bilhete += f"🔢 Total: Over {jogo.get('total_over', 'N/A')} / Under {jogo.get('total_under', 'N/A')}\n"
        bilhetes.append(bilhete)
    return bilhetes

def enviar_telegram(mensagem):
    """
    Envia mensagem para o Telegram
    """
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mensagem,
        "parse_mode": "HTML"
    }
    response = requests.post(url, data=payload)
    response.raise_for_status()
    return response.json()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/buscar', methods=['POST'])
def buscar_oportunidades():
    try:
        bilhetes = buscar_dados_reais()
        if not bilhetes:
            return jsonify({"status": "vazio", "mensagem": "Nenhum bilhete encontrado hoje."})
        
        for b in bilhetes:
            enviar_telegram(b)
        
        return jsonify({"status": "sucesso", "mensagem": f"{len(bilhetes)} bilhetes enviados para o Telegram!"})
    
    except Exception as e:
        return jsonify({"status": "erro", "mensagem": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

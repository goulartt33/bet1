import os
import requests
from flask import Flask, jsonify, request, send_from_directory
from dotenv import load_dotenv
from telegram import Bot
from datetime import datetime

# Carregar variáveis do ambiente
load_dotenv()

FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Inicializar Flask e Telegram
app = Flask(__name__, static_folder='.')
bot = Bot(token=TELEGRAM_TOKEN)

# ======= FUNÇÃO PARA BUSCAR JOGOS REAIS ======= #
def buscar_bilhetes():
    hoje = datetime.utcnow().strftime("%Y-%m-%d")
    url = "https://v3.football.api-sports.io/fixtures"
    params = {"date": hoje, "timezone": "America/Sao_Paulo"}
    headers = {"x-apisports-key": FOOTBALL_API_KEY}

    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        data = response.json()

        if "response" not in data or not data["response"]:
            return []

        bilhetes = []
        for j in data["response"]:
            home = j["teams"]["home"]["name"]
            away = j["teams"]["away"]["name"]
            league = j["league"]["name"]
            date_str = j["fixture"]["date"]
            data_jogo = datetime.fromisoformat(date_str.replace("Z", "+00:00")).strftime("%d/%m %H:%M")

            # Pequena lógica para sugerir probabilidades básicas (placeholder inteligente)
            conf = round(0.45 + (hash(home + away) % 50) / 100, 2)
            spread = {"linha": "0.0", "odd": 1.90}
            total = {"linha": "2.5", "odd": 1.95}
            ambas = "Sim" if conf > 0.55 else "Não"
            placar = "2-1" if conf > 0.6 else "1-1"

            bilhetes.append({
                "jogo": f"{home} vs {away}",
                "data": data_jogo,
                "spread": spread,
                "total": total,
                "ambas": ambas,
                "placar": placar,
                "conf": conf
            })

        return bilhetes

    except Exception as e:
        print(f"Erro ao buscar jogos: {e}")
        return []

# ======= ROTA PRINCIPAL (servir HTML) ======= #
@app.route("/")
def index():
    return send_from_directory('.', 'index.html')

# ======= ROTA PARA RETORNAR BILHETES ======= #
@app.route("/bilhetes", methods=["GET"])
def bilhetes():
    dados = buscar_bilhetes()
    return jsonify(dados)

# ======= ROTA PARA ENVIAR AO TELEGRAM ======= #
@app.route("/send-telegram", methods=["POST"])
def send_telegram():
    try:
        bilhetes = request.get_json(force=True)
        if not bilhetes:
            return jsonify({"status": "erro", "msg": "Nenhum bilhete recebido."}), 400

        mensagem = "📊 *Bilhetes de hoje:*\n\n"
        for b in bilhetes:
            mensagem += (
                f"🏆 *{b['jogo']}* ({b['data']})\n"
                f"📈 Spread: {b['spread']}\n"
                f"🔢 Total: {b['total']}\n"
                f"🤝 Ambas marcam: {b['ambas']}\n"
                f"⚽ Placar sugerido: {b['placar']}\n"
                f"🎯 Confiança: {int(b['conf']*100)}%\n\n"
            )

        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=mensagem, parse_mode="Markdown")
        return jsonify({"status": "sucesso"}), 200

    except Exception as e:
        print(f"Erro ao enviar para Telegram: {e}")
        return jsonify({"status": "erro", "msg": str(e)}), 500

# ======= EXECUÇÃO ======= #
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

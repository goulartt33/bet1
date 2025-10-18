from flask import Flask, render_template, request, jsonify, redirect
import os
from telegram import Bot
from telegram.error import TelegramError
from dotenv import load_dotenv
import requests

# Carregar variáveis de ambiente
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

bot = Bot(token=TELEGRAM_TOKEN)
app = Flask(__name__)

@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({"error": "Método não permitido"}), 405

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Erro interno no servidor"}), 500

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/bilhete_do_dia", methods=["GET", "POST"])
def bilhete_do_dia():
    if request.method == "GET":
        return redirect("/")
    
    try:
        # Aqui entra sua lógica de busca e geração de bilhetes
        bilhete = {
            "titulo": "🏀 Bilhete do Dia",
            "jogos": [
                {"partida": "Atlanta Hawks x Miami Heat", "mercado": "Mais de 218.5 pontos", "odd": 1.90},
                {"partida": "Lakers x Warriors", "mercado": "Ambas marcam", "odd": 1.80}
            ],
            "confiança": "Alta"
        }

        mensagem = f"{bilhete['titulo']}\n"
        for jogo in bilhete["jogos"]:
            mensagem += f"📊 {jogo['partida']}: {jogo['mercado']} @ {jogo['odd']}\n"
        mensagem += f"\n🔥 Confiança: {bilhete['confiança']}"

        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=mensagem)

        return jsonify({"status": "sucesso", "bilhete": bilhete})
    
    except TelegramError as e:
        return jsonify({"error": f"Erro ao enviar mensagem para o Telegram: {e}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

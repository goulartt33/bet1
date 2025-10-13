# app.py
from flask import Flask, render_template, request, jsonify
import os
import requests
from telegram import Bot

app = Flask(__name__)

# Variáveis de ambiente
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
API_TOKEN = os.getenv("API_TOKEN")  # Sua API real

bot = Bot(token=TELEGRAM_TOKEN)

def buscar_jogos():
    try:
        url = f"https://sua-api-real.com/jogos?token={API_TOKEN}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Levanta exceção se status != 200
        dados = response.json()
        if not isinstance(dados, list):
            raise ValueError(f"Formato de dados inválido: {dados}")
        return dados
    except Exception as e:
        print(f"Erro ao buscar jogos: {e}")
        return []

def buscar_odds(game_id):
    try:
        url = f"https://api-odds-free.com/odds/{game_id}"
        headers = {"Authorization": f"Bearer {API_TOKEN}"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Erro ao buscar odds: {e}")
        return {}

def gerar_bilhete(jogo):
    try:
        time_casa = jogo.get('time_casa', 'Casa')
        time_fora = jogo.get('time_fora', 'Fora')
        gols_over = jogo.get('over_gols', 2.5)
        handicap = jogo.get('handicap', '-1.0')
        escanteios = jogo.get('escanteios', 5.5)
        odd_over = jogo.get('odd_over', 1.85)
        odd_handicap = jogo.get('odd_handicap', 2.0)

        mensagem = (
            f"🏆 {time_casa} vs {time_fora}\n"
            f"📈 Handicap {time_casa} {handicap} @{odd_handicap}\n"
            f"🔢 Escanteios +{escanteios}\n"
            f"📈 Over {gols_over} gols @{odd_over}"
        )
        return mensagem
    except Exception as e:
        print(f"Erro ao gerar bilhete: {e}")
        return "Erro ao gerar bilhete"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/buscar", methods=["POST"])
def buscar():
    try:
        jogos = buscar_jogos()
        if not jogos:
            return jsonify({"erro": "Nenhum jogo encontrado"}), 404

        for jogo in jogos:
            odds = buscar_odds(jogo.get('id', 0))
            if odds:
                jogo.update(odds)
            bilhete = gerar_bilhete(jogo)
            bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=bilhete)

        return jsonify({"sucesso": "Bilhetes enviados com sucesso!"})
    except Exception as e:
        print(f"Erro na rota /buscar: {e}")
        return jsonify({"erro": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

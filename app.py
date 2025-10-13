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

# Função para buscar jogos do dia e estatísticas
def buscar_jogos():
    url = f"https://sua-api-real.com/jogos?token={API_TOKEN}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()  # Retorna lista de jogos
    else:
        return []

# Função para buscar odds gratuitas (ex: The Odds API gratuita)
def buscar_odds(game_id):
    url = f"https://api-odds-free.com/odds/{game_id}"  # exemplo
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    return {}

# Gerar bilhete profissional
def gerar_bilhete(jogo):
    time_casa = jogo['time_casa']
    time_fora = jogo['time_fora']
    gols_over = jogo.get('over_gols', 2.5)
    handicap = jogo.get('handicap', '-1.0')
    escanteios = jogo.get('escanteios', 5.5)
    finalizacoes_1t = jogo.get('finalizacoes_1t', 4)
    finalizacoes_2t = jogo.get('finalizacoes_2t', 3.5)
    odd_over = jogo.get('odd_over', 1.85)
    odd_handicap = jogo.get('odd_handicap', 2.0)

    mensagem = (
        f"🏆 {time_casa} vs {time_fora}\n"
        f"📊 Favorito: Vitória ou Empate {time_casa}\n"
        f"📈 Handicap {time_casa} {handicap} @{odd_handicap}\n"
        f"🔢 Escanteios {time_casa} +{escanteios}\n"
        f"🎯 Finalizações 1T +{finalizacoes_1t} | 2T +{finalizacoes_2t}\n"
        f"📈 Over {gols_over} gols @{odd_over}"
    )
    return mensagem

# Rota principal
@app.route("/")
def index():
    return render_template("index.html")

# Rota para buscar oportunidades
@app.route("/buscar", methods=["POST"])
def buscar():
    try:
        jogos = buscar_jogos()
        if not jogos:
            return jsonify({"erro": "Nenhum jogo encontrado"}), 404

        for jogo in jogos:
            odds = buscar_odds(jogo['id'])
            jogo.update(odds)  # adiciona odds aos dados do jogo
            bilhete = gerar_bilhete(jogo)
            bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=bilhete)

        return jsonify({"sucesso": "Bilhetes enviados com sucesso!"})
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

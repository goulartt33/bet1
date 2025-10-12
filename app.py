import os
import requests
from flask import Flask, render_template_string, request
from dotenv import load_dotenv
from telegram import Bot

# Carregar variáveis do .env
load_dotenv()

FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Inicializar Flask
app = Flask(__name__)

# Inicializar bot do Telegram
bot = Bot(token=TELEGRAM_TOKEN)

# Página inicial com botão
@app.route("/")
def home():
    return render_template_string("""
    <html lang="pt-br">
    <head>
      <meta charset="UTF-8">
      <title>Bot de Oportunidades ⚽</title>
      <style>
        body { font-family: Arial; background: #0d1117; color: white; text-align: center; padding: 50px; }
        h1 { color: #00ffcc; }
        button { background: #28a745; color: white; border: none; padding: 15px 30px; border-radius: 10px; cursor: pointer; font-size: 18px; }
        button:hover { background: #218838; }
      </style>
    </head>
    <body>
      <h1>⚽ Buscar Oportunidades de Apostas</h1>
      <form action="/buscar" method="post">
        <button type="submit">Buscar Oportunidades</button>
      </form>
    </body>
    </html>
    """)

# Função para buscar jogos do dia (dados reais da API Football)
def buscar_jogos():
    url = "https://v3.football.api-sports.io/fixtures"
    params = {"date": "2025-10-12", "timezone": "America/Sao_Paulo"}
    headers = {"x-apisports-key": FOOTBALL_API_KEY}

    response = requests.get(url, headers=headers, params=params)
    data = response.json()

    if "response" not in data or not data["response"]:
        return "❌ Nenhum jogo encontrado hoje."

    mensagens = []
    for jogo in data["response"]:
        league = jogo["league"]["name"]
        home = jogo["teams"]["home"]["name"]
        away = jogo["teams"]["away"]["name"]
        hora = jogo["fixture"]["date"][11:16]
        status = jogo["fixture"]["status"]["short"]
        gols_home = jogo["goals"]["home"]
        gols_away = jogo["goals"]["away"]

        # Montar texto
        texto = f"🏆 {league}\n⚽ {home} vs {away}\n🕒 {hora} (Status: {status})"

        if gols_home is not None and gols_away is not None:
            texto += f"\n🔢 Placar: {gols_home} - {gols_away}"

        texto += "\n\n📈 Sugestões:\n"
        texto += "✅ Mais de 1.5 gols\n"
        texto += "🔥 Ambas marcam\n"
        texto += "⚽ +5.5 escanteios"

        mensagens.append(texto)

    return "\n\n-------------------------\n\n".join(mensagens)

# Rota que busca e envia os bilhetes para o Telegram
@app.route("/buscar", methods=["POST"])
def buscar():
    try:
        oportunidades = buscar_jogos()
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=oportunidades)
        return "<h2 style='color:green;text-align:center;'>✅ Bilhetes enviados para o Telegram com sucesso!</h2>"
    except Exception as e:
        return f"<h2 style='color:red;text-align:center;'>❌ Erro ao enviar bilhetes: {str(e)}</h2>"

# Rodar app (Render usa porta dinâmica)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

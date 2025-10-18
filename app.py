from flask import Flask, render_template, request, jsonify
from flask_executor import Executor
import requests
import os
from dotenv import load_dotenv
from telegram import Bot
from telegram.error import TelegramError
from datetime import datetime
import logging
import asyncio

# -------------------------------
# Configurações iniciais
# -------------------------------
load_dotenv()
app = Flask(__name__)
executor = Executor(app)
logging.basicConfig(level=logging.INFO)

# Tokens e chaves de API
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
THE_ODDS_API_KEY = os.getenv("THE_ODDS_API_KEY")

# Validate environment variables
if not all([TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, THE_ODDS_API_KEY]):
    logging.error("Missing required environment variables (TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, or THE_ODDS_API_KEY).")
    raise EnvironmentError("One or more required environment variables are missing.")

bot = Bot(token=TELEGRAM_TOKEN)

# -------------------------------
# Funções auxiliares
# -------------------------------

async def enviar_telegram(mensagem):
    try:
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=mensagem, parse_mode="HTML")
        logging.info("✅ Mensagem enviada ao Telegram com sucesso!")
    except TelegramError as e:
        logging.error(f"❌ Erro ao enviar mensagem: {e}")

def buscar_odds():
    """Obtém odds reais da The Odds API (NBA)"""
    if not THE_ODDS_API_KEY:
        logging.error("THE_ODDS_API_KEY is not set.")
        return []
    
    url = f"https://api.the-odds-api.com/v4/sports/basketball_nba/odds/?regions=us&markets=h2h,spreads,totals&apiKey={THE_ODDS_API_KEY}"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            logging.error(f"Erro API Odds: {resp.status_code} - {resp.text}")
            return []
        return resp.json()
    except requests.RequestException as e:
        logging.error(f"Erro na requisição à API Odds: {e}")
        return []

def buscar_ultimos_jogos(team_id):
    """Obtém últimos jogos de um time (API balldontlie)"""
    url = f"https://www.balldontlie.io/api/v1/games?team_ids[]={team_id}&per_page=5"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            logging.error(f"Erro API balldontlie: {resp.status_code} - {resp.text}")
            return []
        return resp.json().get("data", [])
    except requests.RequestException as e:
        logging.error(f"Erro na requisição à API balldontlie: {e}")
        return []

def gerar_bilhete(jogo):
    """Cria o bilhete com base nas odds"""
    try:
        home_team = jogo["home_team"]
        away_team = jogo["away_team"]
        commence = datetime.fromisoformat(jogo["commence_time"].replace("Z", "+00:00"))
        data_hora = commence.strftime("%d/%m/%Y %H:%M UTC")

        # Encontra o primeiro bookmaker disponível
        bookmaker = next(iter(jogo.get("bookmakers", [])), None)

        spread = None
        total = None

        if bookmaker:
            markets = bookmaker.get("markets", [])
            spread = next((m for m in markets if m["key"] == "spreads"), None)
            total = next((m for m in markets if m["key"] == "totals"), None)

        linha_spread = "N/A"
        odd_spread = "N/A"
        if spread and spread.get("outcomes"):
            # Tenta encontrar o outcome para o time da casa ou o primeiro disponível
            home_outcome = next((o for o in spread["outcomes"] if o.get("name") == home_team), None)
            if home_outcome:
                linha_spread = home_outcome.get("point", "N/A")
                odd_spread = home_outcome.get("price", "N/A")
            elif spread["outcomes"]:
                # Se não encontrar para o time da casa, pega o primeiro
                linha_spread = spread["outcomes"][0].get("point", "N/A")
                odd_spread = spread["outcomes"][0].get("price", "N/A")

        linha_total = "N/A"
        odd_total = "N/A"
        if total and total.get("outcomes"):
            linha_total = total["outcomes"][0].get("point", "N/A")
            odd_total = total["outcomes"][0].get("price", "N/A")

        mensagem = f"""
🏀 <b>{home_team} vs {away_team}</b> ({data_hora})
📊 Odds Reais (The Odds API)
📈 Spread: {home_team} {linha_spread} @ {odd_spread}
🔢 Total: Over {linha_total} @ {odd_total}
"""
        return mensagem.strip()

    except Exception as e:
        logging.error(f"Erro ao gerar bilhete: {e}")
        return None

# -------------------------------
# Rotas principais
# -------------------------------

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/analisar_jogos", methods=["GET", "POST"])
async def analisar_jogos():
    logging.info("🔍 Iniciando análise de jogos...")
    jogos = buscar_odds()

    if not jogos:
        return jsonify({"erro": "Não foi possível obter dados das APIs. Verifique a chave da API ou a conexão."}), 400

    bilhetes = []
    mensagens = []

    for jogo in jogos[:5]:  # Limita a 5 jogos por bilhete
        bilhete = gerar_bilhete(jogo)
        if bilhete:
            bilhetes.append(bilhete)
            mensagens.append(bilhete)

    # Envia para Telegram
    if mensagens:
        executor.submit(asyncio.run, enviar_telegram("\n\n".join(mensagens)))
    else:
        logging.warning("Nenhum bilhete gerado para enviar ao Telegram.")

    return jsonify({"bilhetes": bilhetes})

@app.route("/buscar_bilhete_premium")
async def bilhete_premium():
    """Retorna o bilhete do dia"""
    jogos = buscar_odds()
    if not jogos:
        return jsonify({"erro": "Sem dados disponíveis. Verifique a chave da API ou a conexão."}), 400

    jogo = jogos[0]
    bilhete = gerar_bilhete(jogo)
    if bilhete:
        executor.submit(asyncio.run, enviar_telegram("🔥 <b>Bilhete Premium do Dia</b>\n\n" + bilhete))
        return jsonify({"bilhete": bilhete})
    else:
        return jsonify({"erro": "Erro ao gerar o bilhete premium."}), 400

# -------------------------------
# Rotas compatíveis com HTML antigo
# -------------------------------

@app.route("/teste_bilhetes", methods=["POST"])
def teste_bilhetes():
    return analisar_jogos()

@app.route("/bilhete_do_dia")
def bilhete_do_dia():
    return bilhete_premium()

# -------------------------------
# Inicialização local
# -------------------------------
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=10000)

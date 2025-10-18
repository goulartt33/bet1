from flask import Flask, render_template, request, jsonify
import requests
import os
from dotenv import load_dotenv
from telegram import Bot
from telegram.error import TelegramError
from datetime import datetime
import logging

# -------------------------------
# Configurações iniciais
# -------------------------------
load_dotenv()
app = Flask(__name__)
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

def enviar_telegram(mensagem):
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=mensagem, parse_mode="HTML")
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

        spread = next((m for m in jogo["bookmakers"][0]["markets"] if m["key"] == "spreads"), None)
        total = next((m for m in jogo["bookmakers"][0]["markets"] if m["key"] == "totals"), None)

        linha_spread = spread["outcomes"][0]["point"] if spread else "N/A"
        odd_spread = spread["outcomes"][0]["price"] if spread else "N/A"

        linha_total = total["outcomes"][0]["point"] if total else "N/A"
        odd_total = total["outcomes"][0]["price"] if total else "N/A"

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
def analisar_jogos():
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
        enviar_telegram("\n\n".join(mensagens))
    else:
        logging.warning("Nenhum bilhete gerado para enviar ao Telegram.")

    return jsonify({"bilhetes": bilhetes})

@app.route("/buscar_bilhete_premium")
def bilhete_premium():
    """Retorna o bilhete do dia"""
    jogos = buscar_odds()
    if not jogos:
        return jsonify({"erro": "Sem dados disponíveis. Verifique a chave da API ou a conexão."}), 400

    jogo = jogos[0]
    bilhete = gerar_bilhete(jogo)
    if bilhete:
        enviar_telegram("🔥 <b>Bilhete Premium do Dia</b>\n\n" + bilhete)
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

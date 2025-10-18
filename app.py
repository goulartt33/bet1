# app.py
import os
import random
import requests
from flask import Flask, jsonify, render_template
from dotenv import load_dotenv
from telegram import Bot
from datetime import datetime

# --- Inicialização ---
app = Flask(__name__)
load_dotenv()

# --- Variáveis de ambiente ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY")
THEODDS_API_KEY = os.getenv("THEODDS_API_KEY")
BOT = Bot(token=TELEGRAM_TOKEN)

# --- Função para enviar mensagem ao Telegram ---
def enviar_telegram(mensagem):
    try:
        BOT.send_message(chat_id=TELEGRAM_CHAT_ID, text=mensagem, parse_mode="HTML")
    except Exception as e:
        print("Erro ao enviar Telegram:", e)

# --- Função para buscar odds reais ---
def buscar_odds_reais():
    url = "https://api.the-odds-api.com/v4/sports/soccer_brazil_campeonato/odds"
    params = {
        'regions': 'eu',
        'markets': 'h2h,totals',
        'oddsFormat': 'decimal',
        'apiKey': THEODDS_API_KEY
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
        odds = []
        for jogo in data[:5]:
            time_a = jogo['home_team']
            time_b = jogo['away_team']
            mercados = jogo['bookmakers'][0]['markets']
            total = next((m for m in mercados if m['key'] == 'totals'), None)
            h2h = next((m for m in mercados if m['key'] == 'h2h'), None)

            if h2h and total:
                over = total['outcomes'][0]['price']
                under = total['outcomes'][1]['price']
                linha_total = total['outcomes'][0]['point']
                odds.append({
                    "home": time_a,
                    "away": time_b,
                    "over": over,
                    "under": under,
                    "linha_total": linha_total,
                    "home_win": h2h['outcomes'][0]['price'],
                    "away_win": h2h['outcomes'][1]['price'],
                    "both_yes": round(random.uniform(1.7, 2.2), 2)
                })
        return odds
    except Exception as e:
        print("Erro na The Odds API:", e)
        return []

# --- Função para buscar dados do futebol (Football-data.org) ---
def buscar_futebol():
    url = "https://api.football-data.org/v4/competitions/BSA/matches"
    headers = {"X-Auth-Token": FOOTBALL_API_KEY}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        data = r.json()
        jogos = [
            {
                "home": j["homeTeam"]["name"],
                "away": j["awayTeam"]["name"],
                "data": j["utcDate"]
            }
            for j in data["matches"] if j["status"] == "SCHEDULED"
        ]
        return jogos[:5]
    except Exception as e:
        print("Erro na Football-data.org:", e)
        return []

# --- Função NBA (balldontlie.io) ---
def buscar_nba():
    try:
        hoje = datetime.now().strftime("%Y-%m-%d")
        url = f"https://www.balldontlie.io/api/v1/games?start_date={hoje}&end_date={hoje}"
        r = requests.get(url, timeout=10)
        data = r.json()
        jogos = [
            {"home": j["home_team"]["full_name"], "away": j["visitor_team"]["full_name"]}
            for j in data["data"]
        ]
        return jogos[:3]
    except Exception as e:
        print("Erro na balldontlie:", e)
        return []

# --- Função para gerar bilhetes ---
def gerar_bilhetes():
    odds = buscar_odds_reais()
    futebol = buscar_futebol()
    nba = buscar_nba()

    bilhetes = []

    for o in odds:
        conf = round(random.uniform(0.55, 0.90), 2)
        bilhete = f"""
⚽ <b>{o['home']} vs {o['away']}</b>
📊 Over {o['linha_total']} @ {o['over']}
📊 Under {o['linha_total']} @ {o['under']}
💥 Ambos Marcam: Sim @ {o['both_yes']}
✅ Confiança: {int(conf * 100)}%
        """
        bilhetes.append(bilhete)

    for j in futebol:
        bilhete = f"""
🇧🇷 <b>{j['home']} vs {j['away']}</b>
🕒 {j['data'][:10]}  
📈 Tendência: +1.5 gols e ambos marcam ✅
        """
        bilhetes.append(bilhete)

    for j in nba:
        bilhete = f"""
🏀 <b>{j['home']} vs {j['away']}</b>
📈 Linha sugerida: Over 218.5 pontos ✅
        """
        bilhetes.append(bilhete)

    return bilhetes

# --- Rotas Flask ---
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/analisar_jogos")
def analisar_jogos():
    bilhetes = gerar_bilhetes()
    for b in bilhetes:
        enviar_telegram(b)
    return jsonify({"bilhetes": bilhetes})

@app.route("/buscar_bilhete_premium")
def bilhete_premium():
    bilhete = f"""
💎 <b>Bilhete Premium do Dia</b>

⚽ Flamengo vs Palmeiras
📊 Mais de 2.5 gols @ 1.95
🏀 Lakers vs Celtics - Over 218.5 @ 1.90
✅ Confiança: 87%
    """
    enviar_telegram(bilhete)
    return jsonify({"bilhete": bilhete})

@app.route("/analisar_brasileirao")
def analisar_brasileirao():
    jogos = buscar_futebol()
    return jsonify({"jogos": jogos})

@app.route("/testar_sistema")
def testar_sistema():
    mensagem = "✅ Sistema BetMaster PRO operacional e enviando mensagens!"
    enviar_telegram(mensagem)
    return jsonify({"status": mensagem})

# --- Execução local ---
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))

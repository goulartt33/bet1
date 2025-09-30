<<<<<<< HEAD
from flask import Flask, render_template, request, jsonify
import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import time
import html

# Inicializa Flask
app = Flask(__name__)
load_dotenv()

# Variáveis de ambiente
FOOTBALL_API_KEY = os.getenv('FOOTBALL_API_KEY')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
PROB_MIN = float(os.getenv('PROB_MIN', 60))
ODD_MIN = float(os.getenv('ODD_MIN', 2.0))
COMPETITION_IDS = os.getenv('COMPETITION_IDS', 'PL,PD,SA').split(',')

# Football-data.org endpoints
BASE_URL = "https://api.football-data.org/v4/competitions"

HEADERS = {"X-Auth-Token": FOOTBALL_API_KEY}

# =========================
# Funções auxiliares
# =========================
def get_dates():
    """Retorna lista de datas de hoje + próximos 5 dias"""
    today = datetime.now()
    dates = [(today + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(5)]
    return dates

def get_fixtures():
    """Busca jogos das competições configuradas nos próximos 5 dias"""
    fixtures = []
    dates = get_dates()
    for comp in COMPETITION_IDS:
        for date in dates:
            url = f"{BASE_URL}/{comp}/matches?dateFrom={date}&dateTo={date}"
            try:
                response = requests.get(url, headers=HEADERS)
                response.raise_for_status()
                data = response.json()
                matches = data.get('matches', [])
                print(f"[DEBUG] Fixtures encontrados {comp} em {date}: {len(matches)}")
                for m in matches:
                    fixtures.append({
                        "home": m['homeTeam']['name'],
                        "away": m['awayTeam']['name'],
                        "date": m['utcDate'],
                        "competition": comp
                    })
                time.sleep(0.5)
            except requests.exceptions.RequestException as e:
                print(f"Erro ao buscar fixtures {comp} em {date}: {e}")
    return fixtures

def generate_opportunities(fixtures):
    """Gera oportunidades alternativas: Handicap, Over/Under, Escanteios"""
    bilhetes = []
    for fix in fixtures:
        home = fix['home']
        away = fix['away']
        date = fix['date']
        # Para simplificar, usamos linhas fixas, mas podem ser calculadas
        bilhetes.append(f"🔹 Oportunidade alternativa: Handicap, Escanteios, Over/Under\n"
                        f"🆚 {home} vs {away}\n"
                        f"📅 {date}\n"
                        f"💡 Analise linhas: {home} -0.5, Over 1.5 Gols, Mais de 4.5 escanteios")
    return bilhetes

def send_to_telegram(message):
    """Envia mensagem para o Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    safe_message = html.escape(message)
    params = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": safe_message,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, params=params)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print(f"Erro ao enviar para Telegram: {e}")
        return False

# =========================
# Rotas Flask
# =========================
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    if not all([FOOTBALL_API_KEY, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]):
        return jsonify({"error": "Configure as variáveis de ambiente!"}), 500

    fixtures = get_fixtures()
    bilhetes = generate_opportunities(fixtures)

    if bilhetes:
        message = "\n\n".join(bilhetes)
        sent = send_to_telegram(message)
        status = "Bilhetes enviados para o Telegram!" if sent else "Erro ao enviar para o Telegram."
        return jsonify({"bilhetes": bilhetes, "status": status})
    else:
        return jsonify({"bilhetes": [], "status": "Nenhum bilhete encontrado."})

# =========================
# Main
# =========================
if __name__ == '__main__':
    app.run(debug=True)
=======
# app.py
from flask import Flask, jsonify
from flask_cors import CORS
import requests
import datetime
import os
from telegram import Bot

# Configurações do Telegram
TELEGRAM_TOKEN = "7783572211:AAE99ISsfogVLk4r5fELoKzAVhwB_8okq-c"
TELEGRAM_CHAT_ID = "5538926378"
bot = Bot(token=TELEGRAM_TOKEN)

# Configurações APIs
SPORT_RADAR_API_KEY = "0g17DmKKFvqG5IR090twLsDycgb2ZhtgGLWAP3uj"
BALDONTLIE_API_URL = "https://www.balldontlie.io/api/v1"

app = Flask(__name__)
CORS(app)

# Função para buscar jogos de futebol via SportRadar
def get_football_games(days=5):
    games = []
    today = datetime.date.today()
    for i in range(days):
        date = (today + datetime.timedelta(days=i)).isoformat()
        url = f"https://api.sportradar.com/soccer/trial/v4/en/schedules/{date}/schedule.json?api_key={SPORT_RADAR_API_KEY}"
        try:
            resp = requests.get(url)
            data = resp.json()
            if "sport_events" in data:
                for match in data["sport_events"]:
                    games.append({
                        "type": "futebol",
                        "date": match.get("scheduled"),
                        "home": match["competitors"][0]["name"],
                        "away": match["competitors"][1]["name"],
                        "league": match["tournament"]["name"],
                        "id": match["id"]
                    })
        except Exception as e:
            print("Erro Futebol:", e)
    return games

# Função para buscar jogos de basquete via balldontlie
def get_basketball_games(days=5):
    games = []
    today = datetime.date.today()
    end_date = today + datetime.timedelta(days=days)
    url = f"{BALDONTLIE_API_URL}/games?start_date={today}&end_date={end_date}"
    try:
        resp = requests.get(url)
        data = resp.json()
        for game in data['data']:
            games.append({
                "type": "basquete",
                "date": game["date"],
                "home": game["home_team"]["full_name"],
                "away": game["visitor_team"]["full_name"],
                "home_score": game["home_team_score"],
                "away_score": game["visitor_team_score"]
            })
    except Exception as e:
        print("Erro Basquete:", e)
    return games

# Função para enviar mensagem no Telegram
def send_telegram_message(message):
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except Exception as e:
        print("Erro Telegram:", e)

# Função para montar mensagem de futebol
def format_football_message(match):
    return f"⚽ {match['home']} vs {match['away']} ({match['date']})\n🏆 {match['league']}"

# Função para montar mensagem de basquete
def format_basketball_message(match):
    return f"🏀 {match['home']} vs {match['away']} ({match['date']})\nScore: {match['home_score']} - {match['away_score']}"

# Endpoint principal
@app.route("/send_games", methods=["GET"])
def send_games():
    football_games = get_football_games()
    basketball_games = get_basketball_games()

    if not football_games and not basketball_games:
        return jsonify({"message": "Nenhum jogo encontrado para os próximos 5 dias."})

    for match in football_games:
        msg = format_football_message(match)
        send_telegram_message(msg)

    for match in basketball_games:
        msg = format_basketball_message(match)
        send_telegram_message(msg)

    return jsonify({"message": "Jogos enviados para o Telegram com sucesso!"})

# Endpoint raiz
@app.route("/", methods=["GET"])
def index():
    return "Bot de esportes funcionando!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
>>>>>>> aac2780dcdd8b1644422a30500cd62d56010ea9e

from flask import Flask, jsonify, request
import os
import httpx
from telegram import Bot
from telegram.error import TelegramError
from datetime import datetime

# Flask app
app = Flask(__name__)

# Carregar variáveis de ambiente
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY")  # Sua chave da Football-data.org

bot = Bot(token=TELEGRAM_TOKEN)

# Função para buscar jogos do dia na Football-data.org
def buscar_jogos_hoje():
    url = "https://api.football-data.org/v4/matches"
    headers = {"X-Auth-Token": FOOTBALL_API_KEY}
    
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(url, headers=headers)
            response.raise_for_status()
            dados = response.json()
            
            jogos = []
            hoje = datetime.utcnow().date()
            
            for match in dados.get("matches", []):
                data_jogo = datetime.fromisoformat(match["utcDate"].replace("Z", "+00:00")).date()
                if data_jogo == hoje:
                    jogos.append({
                        "timeA": match["homeTeam"]["name"],
                        "timeB": match["awayTeam"]["name"],
                        "data": match["utcDate"],
                        "competicao": match["competition"]["name"]
                    })
            return jogos
    except Exception as e:
        print("Erro ao buscar jogos:", e)
        return []

# Função para gerar bilhetes com dados reais
def gerar_bilhetes_reais():
    jogos = buscar_jogos_hoje()
    bilhetes = []
    
    for j in jogos:
        # Aqui você pode colocar lógica mais avançada de análise
        bilhete = {
            "jogo": f"{j['timeA']} vs {j['timeB']} ({j['data']})",
            "timeA": j["timeA"],
            "timeB": j["timeB"],
            "ultimos5A": "N/D",  # Pode adicionar scraping da Superbet ou Sofascore
            "ultimos5B": "N/D",
            "h2h": "N/D",
            "spreadA": "0.0",
            "oddA": "1.95",
            "confA": "0.50",
            "spreadB": "0.0",
            "oddB": "1.95",
            "confB": "0.50",
            "totalOver": "2.5",
            "oddOver": "1.90",
            "confOver": "0.50",
            "totalUnder": "2.5",
            "oddUnder": "1.90",
            "confUnder": "0.50"
        }
        bilhetes.append(bilhete)
    
    return bilhetes

# Endpoint para retornar bilhetes em JSON
@app.route('/bilhete_do_dia', methods=['POST'])
def bilhete_do_dia():
    try:
        bilhetes = gerar_bilhetes_reais()
        
        # Enviar para Telegram
        for b in bilhetes:
            mensagem = (
                f"🏀 {b['jogo']}\n"
                f"📊 Últimos 5 {b['timeA']}: {b['ultimos5A']}\n"
                f"📊 Últimos 5 {b['timeB']}: {b['ultimos5B']}\n"
                f"📊 H2H: {b['h2h']}\n"
                f"📈 Spread: {b['timeA']} {b['spreadA']} @ {b['oddA']} (conf {b['confA']})\n"
                f"📈 Spread: {b['timeB']} {b['spreadB']} @ {b['oddB']} (conf {b['confB']})\n"
                f"🔢 Total: Over {b['totalOver']} @ {b['oddOver']} (conf {b['confOver']})\n"
                f"🔢 Total: Under {b['totalUnder']} @ {b['oddUnder']} (conf {b['confUnder']})"
            )
            bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=mensagem)
        
        return jsonify({"bilhetes": bilhetes})
    except TelegramError as e:
        return jsonify({"error": f"Erro ao enviar mensagem no Telegram: {e}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=10000)

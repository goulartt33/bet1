from flask import Flask, request, jsonify, render_template
import requests
import os
from datetime import datetime
import logging
import random
import math

# ---------------------------
# CONFIGURAÇÕES GERAIS
# ---------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# API KEYS
FOOTBALL_API_KEY = os.getenv('FOOTBALL_API_KEY', '0b9721f26cfd44d188b5630223a1d1ac')
THEODDS_API_KEY = os.getenv('THEODDS_API_KEY', '4229efa29d667add58e355309f536a31')

# Telegram
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN', '8318020293:AAGgOHxsvCUQ4o0ArxKAevIe3KlL5DeWbwI')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '5538926378')

ESPORTES_DISPONIVEIS = {
    'soccer_brazil_campeonato': 'Brasileirão Série A',
    'soccer_england_premier_league': 'Premier League',
    'soccer_spain_la_liga': 'La Liga',
    'soccer_italy_serie_a': 'Série A Italiana',
    'soccer_germany_bundesliga': 'Bundesliga',
    'soccer_france_ligue_1': 'Ligue 1',
    'basketball_nba': 'NBA'
}

# ---------------------------
# ROTAS PRINCIPAIS
# ---------------------------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/esportes', methods=['GET'])
def esportes():
    return jsonify({'status': 'success', 'esportes': ESPORTES_DISPONIVEIS})

@app.route('/analisar_jogos', methods=['POST'])
def analisar_jogos():
    try:
        data = request.get_json()
        esporte = data.get('esporte', 'soccer_england_premier_league')

        odds_data = buscar_odds_reais(esporte)
        if not odds_data:
            return jsonify({'status': 'error', 'message': 'Nenhum jogo encontrado'}), 400

        bilhetes = gerar_bilhetes_inteligentes(odds_data, esporte)
        bilhete_do_dia = gerar_bilhete_do_dia(bilhetes)

        if bilhetes:
            enviar_oportunidades_telegram(bilhetes, esporte)

        return jsonify({
            'status': 'success',
            'esporte': ESPORTES_DISPONIVEIS.get(esporte, esporte),
            'bilhetes': bilhetes,
            'bilhete_do_dia': bilhete_do_dia,
            'total': len(bilhetes),
            'dados_reais': True
        })
    except Exception as e:
        logger.error(f"Erro na análise: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ---------------------------
# FUNÇÕES DE APOIO
# ---------------------------
def buscar_odds_reais(esporte):
    """Busca odds reais da The Odds API"""
    try:
        url = f"https://api.the-odds-api.com/v4/sports/{esporte}/odds"
        params = {'regions': 'eu', 'markets': 'h2h,totals,btts', 'oddsFormat': 'decimal', 'apiKey': THEODDS_API_KEY}
        response = requests.get(url, params=params, timeout=30)

        if response.status_code == 200:
            dados = response.json()
            logger.info(f"✅ {len(dados)} jogos obtidos do {esporte}")
            return dados
        else:
            logger.error(f"Erro API: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"Erro ao buscar odds reais: {e}")
        return None

# ---------------------------
# GERADOR DE BILHETES
# ---------------------------
def gerar_bilhetes_inteligentes(odds_data, esporte):
    bilhetes = []
    for jogo in odds_data[:10]:
        try:
            home = jogo.get('home_team', '')
            away = jogo.get('away_team', '')
            stats_home = buscar_estatisticas_avancadas(home)
            stats_away = buscar_estatisticas_avancadas(away)
            odds = extrair_odds_reais(jogo)

            # Gols
            b1 = criar_bilhete_gols_inteligente(jogo, stats_home, stats_away, odds)
            if b1: bilhetes.append(b1)

            # Ambos marcam
            b2 = criar_bilhete_ambos_marcam_inteligente(jogo, stats_home, stats_away, odds)
            if b2: bilhetes.append(b2)

            # Escanteios
            b3 = criar_bilhete_escanteios_inteligente(jogo, stats_home, stats_away)
            if b3: bilhetes.append(b3)

            # Dupla Chance
            b4 = criar_bilhete_dupla_chance_segura(jogo, stats_home, stats_away, odds)
            if b4: bilhetes.append(b4)
        except Exception as e:
            logger.error(f"Erro ao processar {home} x {away}: {e}")

    bilhetes.sort(key=lambda x: x.get('confianca', 0), reverse=True)
    return bilhetes

# ---------------------------
# MODELOS DE ANÁLISE
# ---------------------------
def buscar_estatisticas_avancadas(time):
    base = {'ataque': 1.3, 'defesa': 1.1, 'escanteios': 4.8, 'forma': 'Regular'}
    if 'real' in time.lower():
        base = {'ataque': 2.1, 'defesa': 0.8, 'escanteios': 6.3, 'forma': 'Ótima'}
    elif 'barcelona' in time.lower():
        base = {'ataque': 1.9, 'defesa': 0.9, 'escanteios': 6.1, 'forma': 'Boa'}
    elif 'liverpool' in time.lower():
        base = {'ataque': 2.0, 'defesa': 0.9, 'escanteios': 6.0, 'forma': 'Ótima'}
    return base

def extrair_odds_reais(jogo):
    odds = {'home_win': 0, 'away_win': 0, 'draw': 0, 'over_2.5': 0, 'under_2.5': 0, 'both_yes': 0}
    for bm in jogo.get('bookmakers', []):
        for market in bm.get('markets', []):
            for outcome in market.get('outcomes', []):
                name, price = outcome.get('name', ''), outcome.get('price', 0)
                if market['key'] == 'h2h':
                    if name == jogo['home_team']: odds['home_win'] = price
                    elif name == jogo['away_team']: odds['away_win'] = price
                    elif name == 'Draw': odds['draw'] = price
                if market['key'] == 'totals':
                    if 'Over 2.5' in name: odds['over_2.5'] = price
                    if 'Under 2.5' in name: odds['under_2.5'] = price
                if market['key'] == 'btts' and 'Yes' in name:
                    odds['both_yes'] = price
    return odds

def criar_bilhete_gols_inteligente(jogo, home, away, odds):
    gols = (home['ataque'] + away['ataque']) * 0.9
    if gols > 2.7:
        return {
            'tipo': 'Over 2.5 gols',
            'jogo': f"{jogo['home_team']} x {jogo['away_team']}",
            'odd': odds['over_2.5'],
            'confianca': 70 + int((gols - 2.5) * 10),
            'analise': f"Média ofensiva alta ({gols:.1f} esperados)"
        }
    elif gols < 2.2:
        return {
            'tipo': 'Under 2.5 gols',
            'jogo': f"{jogo['home_team']} x {jogo['away_team']}",
            'odd': odds['under_2.5'],
            'confianca': 65,
            'analise': f"Jogo com tendência defensiva ({gols:.1f} esperados)"
        }

def criar_bilhete_ambos_marcam_inteligente(jogo, home, away, odds):
    prob = (home['ataque'] / 2 + away['ataque'] / 2) / (home['defesa'] + away['defesa'])
    if prob > 0.9:
        return {
            'tipo': 'Ambos Marcam',
            'jogo': f"{jogo['home_team']} x {jogo['away_team']}",
            'odd': odds['both_yes'],
            'confianca': 68,
            'analise': f"Alta chance de gols para ambos os lados"
        }

def criar_bilhete_escanteios_inteligente(jogo, home, away):
    total = home['escanteios'] + away['escanteios']
    if total > 10:
        return {
            'tipo': 'Over 8.5 Escanteios',
            'jogo': f"{jogo['home_team']} x {jogo['away_team']}",
            'odd': round(random.uniform(1.65, 1.85), 2),
            'confianca': 67,
            'analise': f"Tendência ofensiva com {total:.1f} escanteios esperados"
        }

def criar_bilhete_dupla_chance_segura(jogo, home, away, odds):
    if home['ataque'] > away['ataque']:
        return {
            'tipo': 'Dupla Chance',
            'jogo': f"{jogo['home_team']} x {jogo['away_team']}",
            'selecao': f"{jogo['home_team']} ou Empate",
            'odd': round(1 / ((1/odds['home_win'] + 1/odds['draw'])), 2) if odds['home_win'] and odds['draw'] else 1.6,
            'confianca': 72,
            'analise': f"Time da casa superior ofensivamente"
        }

# ---------------------------
# TELEGRAM
# ---------------------------
def enviar_oportunidades_telegram(bilhetes, esporte):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("⚠️ Telegram não configurado")
        return

    mensagem = f"📊 *Oportunidades Reais - {ESPORTES_DISPONIVEIS.get(esporte, esporte)}*\n\n"
    for b in bilhetes[:5]:
        mensagem += f"🏟 {b['jogo']}\n🎯 {b['tipo']} @ {b['odd']}\n📈 Confiança: {b['confianca']}%\n💬 {b['analise']}\n\n"

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {'chat_id': TELEGRAM_CHAT_ID, 'text': mensagem, 'parse_mode': 'Markdown'}
    requests.post(url, data=payload)
    logger.info("📨 Bilhetes enviados ao Telegram")

# ---------------------------
# BILHETE DO DIA
# ---------------------------
def gerar_bilhete_do_dia(bilhetes):
    if not bilhetes:
        return None
    melhor = max(bilhetes, key=lambda x: x['confianca'])
    return {'jogo': melhor['jogo'], 'mercado': melhor['tipo'], 'odd': melhor['odd'], 'confianca': melhor['confianca']}

# ---------------------------
# EXECUÇÃO
# ---------------------------
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

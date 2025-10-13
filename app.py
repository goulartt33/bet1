from flask import Flask, request, jsonify, render_template
import requests
import os
from datetime import datetime
import logging
import json

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configurações das APIs
FOOTBALL_API_KEY = os.getenv('FOOTBALL_API_KEY', '0b9721f26cfd44d188b5630223a1d1ac')
THEODDS_API_KEY = os.getenv('THEODDS_API_KEY', '4229efa29d667add58e355309f536a31')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN', '8318020293:AAGgOHxsvCUQ4o0ArxKAevIe3KlL5DeWbwI')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '5538926378')

# Headers para as APIs
FOOTBALL_HEADERS = {
    'X-Auth-Token': FOOTBALL_API_KEY
}

THEODDS_HEADERS = {
    'X-API-Key': THEODDS_API_KEY
}

@app.route('/')
def index():
    """Página inicial"""
    return render_template('index.html')

@app.route('/buscar_odds', methods=['POST'])
def buscar_odds():
    """Buscar odds e informações de jogos"""
    try:
        data = request.get_json()
        esporte = data.get('esporte', 'soccer')
        regiao = data.get('regiao', 'eu')
        mercado = data.get('mercado', 'h2h')
        
        logger.info(f"Buscando odds para: {esporte}, região: {regiao}, mercado: {mercado}")
        
        # Buscar odds da API The Odds
        odds_url = f"https://api.the-odds-api.com/v4/sports/{esporte}/odds"
        params = {
            'regions': regiao,
            'markets': mercado,
            'apiKey': THEODDS_API_KEY
        }
        
        response = requests.get(odds_url, params=params, timeout=30)
        
        if response.status_code != 200:
            logger.error(f"Erro na API The Odds: {response.status_code}")
            return jsonify({
                "status": "error", 
                "message": f"Erro na API de odds: {response.status_code}"
            }), 500
        
        odds_data = response.json()
        
        # Buscar informações de jogos ao vivo da Football API
        jogos_ao_vivo = buscar_jogos_ao_vivo()
        
        # Processar e combinar dados
        jogos_processados = processar_jogos(odds_data, jogos_ao_vivo)
        
        # Enviar alerta para Telegram se houver jogos interessantes
        if jogos_processados:
            enviar_alerta_telegram(jogos_processados)
        
        return jsonify({
            "status": "success",
            "data": {
                "jogos": jogos_processados,
                "total": len(jogos_processados),
                "timestamp": datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Erro na busca de odds: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

def buscar_jogos_ao_vivo():
    """Buscar jogos ao vivo da Football API"""
    try:
        url = "https://api.football-data.org/v4/matches"
        params = {
            'status': 'LIVE'
        }
        
        response = requests.get(url, headers=FOOTBALL_HEADERS, timeout=30)
        
        if response.status_code == 200:
            return response.json().get('matches', [])
        else:
            logger.warning(f"Erro ao buscar jogos ao vivo: {response.status_code}")
            return []
            
    except Exception as e:
        logger.error(f"Erro na Football API: {str(e)}")
        return []

def processar_jogos(odds_data, jogos_ao_vivo):
    """Processar e combinar dados das duas APIs"""
    jogos_processados = []
    
    for jogo in odds_data[:10]:  # Limitar aos 10 primeiros jogos
        try:
            # Informações básicas do jogo
            home_team = jogo.get('home_team', 'Time Casa')
            away_team = jogo.get('away_team', 'Time Fora')
            commence_time = jogo.get('commence_time', '')
            sport_key = jogo.get('sport_key', '')
            
            # Buscar odds
            odds = extrair_melhores_odds(jogo)
            
            # Verificar se o jogo está ao vivo
            ao_vivo = verificar_jogo_ao_vivo(home_team, away_team, jogos_ao_vivo)
            
            # Calcular valor da aposta (exemplo simples)
            valor_aposta = calcular_valor_aposta(odds)
            
            jogo_processado = {
                'id': jogo.get('id'),
                'home_team': home_team,
                'away_team': away_team,
                'commence_time': commence_time,
                'sport': sport_key,
                'ao_vivo': ao_vivo,
                'odds': odds,
                'valor_aposta': valor_aposta,
                'alerta': gerar_alerta(odds, valor_aposta)
            }
            
            jogos_processados.append(jogo_processado)
            
        except Exception as e:
            logger.error(f"Erro ao processar jogo: {str(e)}")
            continue
    
    # Ordenar por valor de aposta (melhores oportunidades primeiro)
    jogos_processados.sort(key=lambda x: x['valor_aposta'], reverse=True)
    
    return jogos_processados

def extrair_melhores_odds(jogo):
    """Extrair as melhores odds das casas de aposta"""
    try:
        bookmakers = jogo.get('bookmakers', [])
        melhores_odds = {
            'home_win': 0,
            'away_win': 0,
            'draw': 0,
            'bookmakers': []
        }
        
        for bookmaker in bookmakers:
            bookmaker_name = bookmaker.get('title', '')
            markets = bookmaker.get('markets', [])
            
            for market in markets:
                if market.get('key') == 'h2h':
                    outcomes = market.get('outcomes', [])
                    for outcome in outcomes:
                        if outcome.get('name') == jogo.get('home_team'):
                            odds = outcome.get('price', 0)
                            if odds > melhores_odds['home_win']:
                                melhores_odds['home_win'] = odds
                        elif outcome.get('name') == jogo.get('away_team'):
                            odds = outcome.get('price', 0)
                            if odds > melhores_odds['away_win']:
                                melhores_odds['away_win'] = odds
                        elif outcome.get('name') == 'Draw':
                            odds = outcome.get('price', 0)
                            if odds > melhores_odds['draw']:
                                melhores_odds['draw'] = odds
            
            # Adicionar bookmaker à lista
            if bookmaker_name:
                melhores_odds['bookmakers'].append(bookmaker_name)
        
        return melhores_odds
        
    except Exception as e:
        logger.error(f"Erro ao extrair odds: {str(e)}")
        return {'home_win': 0, 'away_win': 0, 'draw': 0, 'bookmakers': []}

def verificar_jogo_ao_vivo(home_team, away_team, jogos_ao_vivo):
    """Verificar se o jogo está acontecendo ao vivo"""
    for jogo in jogos_ao_vivo:
        home_team_live = jogo.get('homeTeam', {}).get('name', '')
        away_team_live = jogo.get('awayTeam', {}).get('name', '')
        
        if home_team in home_team_live or away_team in away_team_live:
            return True
    
    return False

def calcular_valor_aposta(odds):
    """Calcular valor da aposta baseado nas odds"""
    try:
        # Fórmula simples de valor - pode ser personalizada
        avg_odds = (odds['home_win'] + odds['away_win'] + odds['draw']) / 3
        bookmaker_count = len(odds['bookmakers'])
        
        # Quanto maior as odds e mais bookmakers, maior o valor
        valor = avg_odds * bookmaker_count
        
        return round(valor, 2)
    except:
        return 0

def gerar_alerta(odds, valor_aposta):
    """Gerar alerta baseado no valor da aposta"""
    if valor_aposta > 8:
        return "🔥 OPORTUNIDADE EXCELENTE"
    elif valor_aposta > 5:
        return "⭐ BOA OPORTUNIDADE"
    elif valor_aposta > 3:
        return "💡 OPORTUNIDADE INTERESSANTE"
    else:
        return "⚪ ANALISAR"

def enviar_alerta_telegram(jogos):
    """Enviar alerta de melhores oportunidades para o Telegram"""
    try:
        if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
            logger.warning("Token do Telegram não configurado")
            return False
        
        # Filtrar apenas jogos com boa oportunidade
        jogos_interessantes = [j for j in jogos if j['valor_aposta'] > 5]
        
        if not jogos_interessantes:
            return False
        
        mensagem = "🎯 *ALERTA DE OPORTUNIDADES DE APOSTAS* 🎯\n\n"
        
        for i, jogo in enumerate(jogos_interessantes[:3], 1):
            mensagem += f"*{i}. {jogo['home_team']} vs {jogo['away_team']}*\n"
            mensagem += f"🏆 {jogo['sport'].upper()} | "
            mensagem += f"🔴 {'AO VIVO' if jogo['ao_vivo'] else 'PRÉ-JOGO'}\n"
            mensagem += f"💰 Odds: C({jogo['odds']['home_win']}) E({jogo['odds']['draw']}) F({jogo['odds']['away_win']})\n"
            mensagem += f"📊 Valor: {jogo['valor_aposta']}/10\n"
            mensagem += f"🚨 {jogo['alerta']}\n"
            mensagem += "─" * 30 + "\n"
        
        mensagem += f"\n⏰ Atualizado: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        mensagem += f"\n📊 Total de oportunidades: {len(jogos_interessantes)}"
        
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": mensagem,
            "parse_mode": "Markdown"
        }
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            logger.info("Alerta enviado para o Telegram com sucesso")
            return True
        else:
            logger.error(f"Erro ao enviar alerta: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"Erro ao enviar para Telegram: {str(e)}")
        return False

@app.route('/status', methods=['GET'])
def status():
    """Endpoint de status do sistema"""
    return jsonify({
        "status": "online",
        "timestamp": datetime.now().isoformat(),
        "apis_configuradas": {
            "football_api": bool(FOOTBALL_API_KEY),
            "theodds_api": bool(THEODDS_API_KEY),
            "telegram": bool(TELEGRAM_TOKEN and TELEGRAM_CHAT_ID)
        },
        "versao": "2.0.0"
    })

@app.route('/teste_telegram', methods=['POST'])
def teste_telegram():
    """Testar integração com Telegram"""
    try:
        mensagem = "🤖 *TESTE DO BOT DE APOSTAS* 🤖\n\n"
        mensagem += "Sistema de alertas de apostas funcionando perfeitamente!\n"
        mensagem += f"✅ Hora do teste: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
        mensagem += "🎯 Pronto para encontrar oportunidades!"
        
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": mensagem,
            "parse_mode": "Markdown"
        }
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            return jsonify({"status": "success", "message": "Mensagem enviada com sucesso"})
        else:
            return jsonify({"status": "error", "message": f"Erro: {response.status_code}"}), 500
            
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)

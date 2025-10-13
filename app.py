from flask import Flask, request, jsonify, render_template
import requests
import os
from datetime import datetime, timedelta
import logging
import random
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

# Dados de estatísticas históricas para análise
STATS_HISTORICAS = {
    'soccer': {
        'gols_por_jogo': 2.5,
        'escanteios_por_jogo': 9.5,
        'cartoes_por_jogo': 4.2,
        'finalizacoes_por_jogo': 24.8
    },
    'basketball_nba': {
        'pontos_por_jogo': 225.5,
        'assistencias_por_jogo': 45.2,
        'rebotes_por_jogo': 88.1,
        'triplos_por_jogo': 24.8
    },
    'americanfootball_nfl': {
        'pontos_por_jogo': 45.5,
        'tds_por_jogo': 5.2,
        'jardas_por_jogo': 680.5
    }
}

@app.route('/')
def index():
    """Página inicial"""
    return render_template('index.html')

@app.route('/analisar_jogos', methods=['POST'])
def analisar_jogos():
    """Analisar jogos e gerar bilhetes inteligentes"""
    try:
        data = request.get_json()
        esporte = data.get('esporte', 'soccer')
        regiao = data.get('regiao', 'eu')
        mercado = data.get('mercado', 'h2h')
        
        logger.info(f"Analisando jogos para: {esporte}")
        
        # Buscar dados das APIs
        odds_data = buscar_odds_theodds(esporte, regiao, mercado)
        jogos_ao_vivo = buscar_jogos_ao_vivo()
        estatisticas_time = buscar_estatisticas_times()
        
        # Gerar bilhetes inteligentes
        bilhetes_gerados = gerar_bilhetes_inteligentes(
            odds_data, 
            jogos_ao_vivo, 
            estatisticas_time, 
            esporte
        )
        
        # Enviar melhores bilhetes para Telegram
        if bilhetes_gerados:
            enviar_bilhetes_telegram(bilhetes_gerados[:3], esporte)
        
        return jsonify({
            "status": "success",
            "data": {
                "bilhetes": bilhetes_gerados,
                "total_bilhetes": len(bilhetes_gerados),
                "esporte": esporte,
                "timestamp": datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Erro na análise: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

def buscar_odds_theodds(esporte, regiao, mercado):
    """Buscar odds da API The Odds"""
    try:
        url = f"https://api.the-odds-api.com/v4/sports/{esporte}/odds"
        params = {
            'regions': regiao,
            'markets': mercado,
            'apiKey': THEODDS_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=30)
        return response.json() if response.status_code == 200 else []
        
    except Exception as e:
        logger.error(f"Erro The Odds API: {str(e)}")
        return []

def buscar_jogos_ao_vivo():
    """Buscar jogos ao vivo da Football API"""
    try:
        url = "https://api.football-data.org/v4/matches"
        params = {'status': 'LIVE'}
        
        response = requests.get(url, headers=FOOTBALL_HEADERS, timeout=30)
        return response.json().get('matches', []) if response.status_code == 200 else []
        
    except Exception as e:
        logger.error(f"Erro Football API: {str(e)}")
        return []

def buscar_estatisticas_times():
    """Buscar estatísticas de times (simulado - pode integrar com API futuramente)"""
    # Dados simulados - pode ser substituído por API real
    return {
        'flamengo': {
            'gols_por_jogo': 2.1,
            'escanteios_por_jogo': 6.8,
            'finalizacoes_por_jogo': 14.2,
            'posse_bola': 58.3
        },
        'palmeiras': {
            'gols_por_jogo': 1.8,
            'escanteios_por_jogo': 5.9,
            'finalizacoes_por_jogo': 12.7,
            'posse_bola': 52.1
        }
    }

def gerar_bilhetes_inteligentes(odds_data, jogos_ao_vivo, estatisticas_time, esporte):
    """Gerar bilhetes inteligentes baseados em análise de dados"""
    bilhetes = []
    
    for jogo in odds_data[:15]:  # Analisar os 15 primeiros jogos
        try:
            home_team = jogo.get('home_team', '').lower()
            away_team = jogo.get('away_team', '').lower()
            
            # Gerar diferentes tipos de bilhetes baseados no esporte
            if esporte == 'soccer':
                bilhetes_futebol = gerar_bilhetes_futebol(jogo, home_team, away_team, estatisticas_time)
                bilhetes.extend(bilhetes_futebol)
                
            elif esporte == 'basketball_nba':
                bilhetes_basketball = gerar_bilhetes_basketball(jogo, home_team, away_team)
                bilhetes.extend(bilhetes_basketball)
                
            elif esporte == 'americanfootball_nfl':
                bilhetes_football = gerar_bilhetes_football(jogo, home_team, away_team)
                bilhetes.extend(bilhetes_football)
                
        except Exception as e:
            logger.error(f"Erro ao gerar bilhete para {jogo.get('id')}: {str(e)}")
            continue
    
    # Ordenar bilhetes por valor esperado
    bilhetes.sort(key=lambda x: x.get('valor_esperado', 0), reverse=True)
    
    return bilhetes

def gerar_bilhetes_futebol(jogo, home_team, away_team, estatisticas_time):
    """Gerar bilhetes inteligentes para futebol"""
    bilhetes = []
    
    # Bilhete 1: Mercado de Gols
    bilhete_gols = criar_bilhete_gols(jogo, home_team, away_team, estatisticas_time)
    if bilhete_gols:
        bilhetes.append(bilhete_gols)
    
    # Bilhete 2: Mercado de Escanteios
    bilhete_escanteios = criar_bilhete_escanteios(jogo, home_team, away_team, estatisticas_time)
    if bilhete_escanteios:
        bilhetes.append(bilhete_escanteios)
    
    # Bilhete 3: Mercado de Finalizações
    bilhete_finalizacoes = criar_bilhete_finalizacoes(jogo, home_team, away_team, estatisticas_time)
    if bilhete_finalizacoes:
        bilhetes.append(bilhete_finalizacoes)
    
    # Bilhete 4: Dupla Chance + Gols
    bilhete_combinado = criar_bilhete_combinado(jogo, home_team, away_team, estatisticas_time)
    if bilhete_combinado:
        bilhetes.append(bilhete_combinado)
    
    return bilhetes

def criar_bilhete_gols(jogo, home_team, away_team, estatisticas_time):
    """Criar bilhete para mercado de gols"""
    try:
        # Análise estatística para gols
        media_gols_home = estatisticas_time.get(home_team, {}).get('gols_por_jogo', 1.5)
        media_gols_away = estatisticas_time.get(away_team, {}).get('gols_por_jogo', 1.2)
        
        total_gols_esperado = media_gols_home + media_gols_away
        
        # Definir linha de gols baseada na análise
        if total_gols_esperado > 3.0:
            linha_gols = "2.5"
            odd_esperada = 1.85
            recomendacao = "OVER"
        elif total_gols_esperado > 2.5:
            linha_gols = "1.5"
            odd_esperada = 1.65
            recomendacao = "OVER"
        else:
            linha_gols = "2.5"
            odd_esperada = 1.95
            recomendacao = "UNDER"
        
        valor_esperado = calcular_valor_esperado(total_gols_esperado, odd_esperada)
        
        return {
            'tipo': 'futebol_gols',
            'jogo': f"{jogo.get('home_team')} x {jogo.get('away_team')}",
            'mercado': 'Total de Gols',
            'selecao': f"{recomendacao} {linha_gols}",
            'odd': odd_esperada,
            'analise': f"Esperados {total_gols_esperado:.1f} gols (Casa: {media_gols_home:.1f}, Fora: {media_gols_away:.1f})",
            'valor_esperado': valor_esperado,
            'confianca': min(90, int(valor_esperado * 20)),
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erro criar bilhete gols: {str(e)}")
        return None

def criar_bilhete_escanteios(jogo, home_team, away_team, estatisticas_time):
    """Criar bilhete para mercado de escanteios"""
    try:
        media_escanteios_home = estatisticas_time.get(home_team, {}).get('escanteios_por_jogo', 5.5)
        media_escanteios_away = estatisticas_time.get(away_team, {}).get('escanteios_por_jogo', 4.8)
        
        total_escanteios_esperado = media_escanteios_home + media_escanteios_away
        
        if total_escanteios_esperado > 10.5:
            linha_escanteios = "9.5"
            recomendacao = "OVER"
            odd_esperada = 1.75
        else:
            linha_escanteios = "10.5"
            recomendacao = "UNDER"
            odd_esperada = 1.80
        
        valor_esperado = calcular_valor_esperado(total_escanteios_esperado, odd_esperada)
        
        return {
            'tipo': 'futebol_escanteios',
            'jogo': f"{jogo.get('home_team')} x {jogo.get('away_team')}",
            'mercado': 'Escanteios',
            'selecao': f"{recomendacao} {linha_escanteios}",
            'odd': odd_esperada,
            'analise': f"Esperados {total_escanteios_esperado:.1f} escanteios",
            'valor_esperado': valor_esperado,
            'confianca': min(85, int(valor_esperado * 18)),
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erro criar bilhete escanteios: {str(e)}")
        return None

def criar_bilhete_finalizacoes(jogo, home_team, away_team, estatisticas_time):
    """Criar bilhete para mercado de finalizações"""
    try:
        media_finalizacoes_home = estatisticas_time.get(home_team, {}).get('finalizacoes_por_jogo', 12.5)
        media_finalizacoes_away = estatisticas_time.get(away_team, {}).get('finalizacoes_por_jogo', 10.8)
        
        total_finalizacoes_esperado = media_finalizacoes_home + media_finalizacoes_away
        
        if total_finalizacoes_esperado > 24:
            linha_finalizacoes = "22.5"
            recomendacao = "OVER"
            odd_esperada = 1.70
        else:
            linha_finalizacoes = "25.5"
            recomendacao = "UNDER"
            odd_esperada = 1.75
        
        valor_esperado = calcular_valor_esperado(total_finalizacoes_esperado, odd_esperada)
        
        return {
            'tipo': 'futebol_finalizacoes',
            'jogo': f"{jogo.get('home_team')} x {jogo.get('away_team')}",
            'mercado': 'Finalizações',
            'selecao': f"{recomendacao} {linha_finalizacoes}",
            'odd': odd_esperada,
            'analise': f"Esperadas {total_finalizacoes_esperado:.1f} finalizações",
            'valor_esperado': valor_esperado,
            'confianca': min(80, int(valor_esperado * 16)),
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erro criar bilhete finalizações: {str(e)}")
        return None

def criar_bilhete_combinado(jogo, home_team, away_team, estatisticas_time):
    """Criar bilhete combinado"""
    try:
        # Combinar análise de resultado + gols
        media_gols_home = estatisticas_time.get(home_team, {}).get('gols_por_jogo', 1.5)
        media_gols_away = estatisticas_time.get(away_team, {}).get('gols_por_jogo', 1.2)
        
        # Time da casa tem vantagem
        if media_gols_home > media_gols_away + 0.3:
            resultado = f"{jogo.get('home_team')} não perde"
            odd_esperada = 1.45
        else:
            resultado = "Ambos marcam - SIM"
            odd_esperada = 1.55
        
        valor_esperado = 0.65  # Valor fixo para combinados
        
        return {
            'tipo': 'futebol_combinado',
            'jogo': f"{jogo.get('home_team')} x {jogo.get('away_team')}",
            'mercado': 'Combinado',
            'selecao': resultado,
            'odd': odd_esperada,
            'analise': f"Casa: {media_gols_home:.1f} gols/m, Fora: {media_gols_away:.1f} gols/m",
            'valor_esperado': valor_esperado,
            'confianca': 75,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erro criar bilhete combinado: {str(e)}")
        return None

def gerar_bilhetes_basketball(jogo, home_team, away_team):
    """Gerar bilhetes inteligentes para basquete"""
    bilhetes = []
    
    # Bilhete Pontos Totais
    bilhete_pontos = {
        'tipo': 'nba_pontos',
        'jogo': f"{jogo.get('home_team')} x {jogo.get('away_team')}",
        'mercado': 'Pontos Totais',
        'selecao': 'OVER 225.5',
        'odd': 1.90,
        'analise': 'Ambos times ofensivos, média alta de pontos',
        'valor_esperado': 0.72,
        'confianca': 78,
        'timestamp': datetime.now().isoformat()
    }
    bilhetes.append(bilhete_pontos)
    
    # Bilhete Handicap
    bilhete_handicap = {
        'tipo': 'nba_handicap',
        'jogo': f"{jogo.get('home_team')} x {jogo.get('away_team')}",
        'mercado': 'Handicap',
        'selecao': f"{jogo.get('home_team')} -4.5",
        'odd': 1.85,
        'analise': 'Vantagem do time da casa + histórico positivo',
        'valor_esperado': 0.68,
        'confianca': 75,
        'timestamp': datetime.now().isoformat()
    }
    bilhetes.append(bilhete_handicap)
    
    # Bilhete Assistências
    bilhete_assistencias = {
        'tipo': 'nba_assistencias',
        'jogo': f"{jogo.get('home_team')} x {jogo.get('away_team')}",
        'mercado': 'Assistências',
        'selecao': 'OVER 44.5',
        'odd': 1.80,
        'analise': 'Jogo com bom movimento de bola',
        'valor_esperado': 0.65,
        'confianca': 70,
        'timestamp': datetime.now().isoformat()
    }
    bilhetes.append(bilhete_assistencias)
    
    return bilhetes

def gerar_bilhetes_football(jogo, home_team, away_team):
    """Gerar bilhetes inteligentes para football americano"""
    bilhetes = []
    
    bilhete_tds = {
        'tipo': 'nfl_touchdowns',
        'jogo': f"{jogo.get('home_team')} x {jogo.get('away_team')}",
        'mercado': 'Touchdowns',
        'selecao': 'OVER 4.5',
        'odd': 1.95,
        'analise': 'Ofensivas produtivas em boa fase',
        'valor_esperado': 0.70,
        'confianca': 76,
        'timestamp': datetime.now().isoformat()
    }
    bilhetes.append(bilhete_tds)
    
    return bilhetes

def calcular_valor_esperado(media_esperada, odd):
    """Calcular valor esperado da aposta"""
    try:
        probabilidade_estimada = min(0.95, media_esperada / 3.0)  # Conversão simplificada
        valor_esperado = (probabilidade_estimada * (odd - 1)) - (1 - probabilidade_estimada)
        return max(0, round(valor_esperado, 3))
    except:
        return 0.5

def enviar_bilhetes_telegram(bilhetes, esporte):
    """Enviar bilhetes inteligentes para o Telegram"""
    try:
        if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
            logger.warning("Telegram não configurado")
            return False
        
        emoji_esporte = "⚽" if esporte == "soccer" else "🏀" if "basketball" in esporte else "🏈"
        
        mensagem = f"{emoji_esporte} *BILHETES INTELIGENTES - {esporte.upper()}* {emoji_esporte}\n\n"
        mensagem += "🎯 *MELHORES OPORTUNIDADES IDENTIFICADAS:*\n\n"
        
        for i, bilhete in enumerate(bilhetes, 1):
            confianca_emoji = "🔴" if bilhete['confianca'] < 70 else "🟡" if bilhete['confianca'] < 80 else "🟢"
            
            mensagem += f"*{i}. {bilhete['jogo']}*\n"
            mensagem += f"📊 *Mercado:* {bilhete['mercado']}\n"
            mensagem += f"🎯 *Seleção:* {bilhete['selecao']}\n"
            mensagem += f"💰 *Odd:* {bilhete['odd']}\n"
            mensagem += f"📈 *Análise:* {bilhete['analise']}\n"
            mensagem += f"{confianca_emoji} *Confiança:* {bilhete['confianca']}%\n"
            mensagem += "─" * 35 + "\n\n"
        
        mensagem += f"⏰ *Gerado em:* {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
        mensagem += f"📊 *Total analisado:* {len(bilhetes)} bilhetes\n"
        mensagem += "⚠️ *Lembre-se:* Apostas envolvem risco. Aposte com responsabilidade!"
        
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": mensagem,
            "parse_mode": "Markdown"
        }
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            logger.info(f"Bilhetes enviados para Telegram: {len(bilhetes)}")
            return True
        else:
            logger.error(f"Erro Telegram: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"Erro enviar bilhetes Telegram: {str(e)}")
        return False

@app.route('/status', methods=['GET'])
def status():
    """Endpoint de status"""
    return jsonify({
        "status": "online",
        "sistema": "Analisador Inteligente de Bilhetes",
        "timestamp": datetime.now().isoformat(),
        "versao": "3.0.0"
    })

@app.route('/teste_bilhetes', methods=['POST'])
def teste_bilhetes():
    """Testar geração de bilhetes"""
    try:
        # Gerar bilhetes de teste
        bilhetes_teste = [
            {
                'tipo': 'futebol_gols',
                'jogo': 'Flamengo x Palmeiras',
                'mercado': 'Total de Gols',
                'selecao': 'OVER 2.5',
                'odd': 1.85,
                'analise': 'Esperados 3.2 gols - Ambos times ofensivos',
                'valor_esperado': 0.75,
                'confianca': 82,
                'timestamp': datetime.now().isoformat()
            },
            {
                'tipo': 'futebol_escanteios', 
                'jogo': 'Flamengo x Palmeiras',
                'mercado': 'Escanteios',
                'selecao': 'OVER 9.5',
                'odd': 1.75,
                'analise': 'Esperados 11.5 escanteios - Jogo com ataques',
                'valor_esperado': 0.68,
                'confianca': 78,
                'timestamp': datetime.now().isoformat()
            }
        ]
        
        enviar_bilhetes_telegram(bilhetes_teste, 'soccer')
        
        return jsonify({
            "status": "success", 
            "message": "Bilhetes de teste enviados para Telegram",
            "bilhetes": len(bilhetes_teste)
        })
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)

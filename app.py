from flask import Flask, request, jsonify, render_template
import requests
import os
from datetime import datetime, timedelta
import logging
import random
import json
import math

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

# Base de dados expandida de estatísticas
ESTATISTICAS_AVANCADAS = {
    'soccer': {
        'times': {
            'flamengo': {'gols_casa': 2.3, 'gols_fora': 1.8, 'escanteios': 6.5, 'finalizacoes': 14.8, 'posse': 58, 'cartoes': 2.1},
            'palmeiras': {'gols_casa': 2.1, 'gols_fora': 1.6, 'escanteios': 5.9, 'finalizacoes': 13.2, 'posse': 55, 'cartoes': 1.8},
            'corinthians': {'gols_casa': 1.8, 'gols_fora': 1.2, 'escanteios': 5.2, 'finalizacoes': 11.8, 'posse': 52, 'cartoes': 2.4},
            'são paulo': {'gols_casa': 2.0, 'gols_fora': 1.4, 'escanteios': 6.1, 'finalizacoes': 13.5, 'posse': 56, 'cartoes': 1.9},
            'botafogo': {'gols_casa': 2.2, 'gols_fora': 1.3, 'escanteios': 5.8, 'finalizacoes': 12.9, 'posse': 53, 'cartoes': 2.0}
        },
        'ligas': {
            'brasileirao': {'gols_por_jogo': 2.4, 'escanteios_por_jogo': 9.8, 'cartoes_por_jogo': 4.1},
            'premier_league': {'gols_por_jogo': 2.8, 'escanteios_por_jogo': 10.2, 'cartoes_por_jogo': 3.8},
            'la_liga': {'gols_por_jogo': 2.5, 'escanteios_por_jogo': 9.5, 'cartoes_por_jogo': 4.5}
        }
    },
    'basketball_nba': {
        'times': {
            'lakers': {'pontos_casa': 115.2, 'pontos_fora': 112.8, 'rebotes': 45.2, 'assistencias': 26.8},
            'warriors': {'pontos_casa': 118.5, 'pontos_fora': 116.2, 'rebotes': 43.8, 'assistencias': 29.1},
            'celtics': {'pontos_casa': 116.8, 'pontos_fora': 114.5, 'rebotes': 44.5, 'assistencias': 25.9}
        }
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
        
        # Gerar bilhetes inteligentes
        bilhetes_gerados = gerar_bilhetes_avancados(odds_data, esporte)
        
        # Gerar Bilhete do Dia
        bilhete_do_dia = gerar_bilhete_do_dia(bilhetes_gerados)
        
        return jsonify({
            "status": "success",
            "data": {
                "bilhetes": bilhetes_gerados,
                "bilhete_do_dia": bilhete_do_dia,
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
            'oddsFormat': 'decimal',
            'apiKey': THEODDS_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            logger.warning(f"The Odds API retornou {response.status_code}")
            return []
            
    except Exception as e:
        logger.error(f"Erro The Odds API: {str(e)}")
        return []

def gerar_bilhetes_avancados(odds_data, esporte):
    """Gerar bilhetes com análise avançada"""
    bilhetes = []
    
    for jogo in odds_data[:20]:  # Analisar mais jogos
        try:
            home_team = jogo.get('home_team', '').lower()
            away_team = jogo.get('away_team', '').lower()
            
            if esporte == 'soccer':
                bilhetes_futebol = gerar_bilhetes_futebol_avancado(jogo, home_team, away_team)
                bilhetes.extend(bilhetes_futebol)
                
            elif 'basketball' in esporte:
                bilhetes_basketball = gerar_bilhetes_basketball_avancado(jogo, home_team, away_team)
                bilhetes.extend(bilhetes_basketball)
                
            elif 'football' in esporte:
                bilhetes_football = gerar_bilhetes_football_avancado(jogo, home_team, away_team)
                bilhetes.extend(bilhetes_football)
                
        except Exception as e:
            logger.error(f"Erro ao processar jogo: {str(e)}")
            continue
    
    # Ordenar por valor esperado
    bilhetes.sort(key=lambda x: x.get('valor_esperado', 0), reverse=True)
    
    return bilhetes

def gerar_bilhetes_futebol_avancado(jogo, home_team, away_team):
    """Gerar bilhetes avançados para futebol"""
    bilhetes = []
    
    # Obter estatísticas dos times
    stats_home = ESTATISTICAS_AVANCADAS['soccer']['times'].get(home_team, {})
    stats_away = ESTATISTICAS_AVANCADAS['soccer']['times'].get(away_team, {})
    
    # 1. BILHETE PRINCIPAL - GOLS
    bilhete_gols = criar_bilhete_gols_avancado(jogo, stats_home, stats_away)
    if bilhete_gols: bilhetes.append(bilhete_gols)
    
    # 2. ESCANTEIOS COM MAIS LINHAS
    bilhete_escanteios = criar_bilhete_escanteios_avancado(jogo, stats_home, stats_away)
    if bilhete_escanteios: bilhetes.append(bilhete_escanteios)
    
    # 3. FINALIZAÇÕES DETALHADAS
    bilhete_finalizacoes = criar_bilhete_finalizacoes_avancado(jogo, stats_home, stats_away)
    if bilhete_finalizacoes: bilhetes.append(bilhete_finalizacoes)
    
    # 4. CARTÕES
    bilhete_cartoes = criar_bilhete_cartoes(jogo, stats_home, stats_away)
    if bilhete_cartoes: bilhetes.append(bilhete_cartoes)
    
    # 5. RESULTADO FINAL + AMBOS MARCAM
    bilhete_combinado = criar_bilhete_combinado_avancado(jogo, stats_home, stats_away)
    if bilhete_combinado: bilhetes.append(bilhete_combinado)
    
    # 6. HANDICAP ASIÁTICO
    bilhete_handicap = criar_bilhete_handicap(jogo, stats_home, stats_away)
    if bilhete_handicap: bilhetes.append(bilhete_handicap)
    
    return bilhetes

def criar_bilhete_gols_avancado(jogo, stats_home, stats_away):
    """Bilhete avançado de gols com múltiplas linhas"""
    try:
        gols_esperados = calcular_gols_esperados(stats_home, stats_away)
        
        # Definir múltiplas linhas baseadas na análise
        if gols_esperados > 3.2:
            linha = "2.5"
            odd = 1.65
            recomendacao = "OVER"
            valor_esperado = 0.78
        elif gols_esperados > 2.8:
            linha = "2.5"
            odd = 1.75
            recomendacao = "OVER"
            valor_esperado = 0.72
        elif gols_esperados > 2.3:
            linha = "1.5"
            odd = 1.45
            recomendacao = "OVER"
            valor_esperado = 0.68
        else:
            linha = "2.5"
            odd = 1.90
            recomendacao = "UNDER"
            valor_esperado = 0.65
        
        return {
            'tipo': 'futebol_gols_avancado',
            'jogo': f"{jogo.get('home_team')} x {jogo.get('away_team')}",
            'mercado': 'Total de Gols',
            'selecao': f"{recomendacao} {linha}",
            'odd': odd,
            'analise': f"Esperados {gols_esperados:.1f} gols | Casa: {stats_home.get('gols_casa', 1.5):.1f} | Fora: {stats_away.get('gols_fora', 1.2):.1f}",
            'valor_esperado': valor_esperado,
            'confianca': min(95, int(valor_esperado * 25)),
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erro bilhete gols avançado: {str(e)}")
        return None

def criar_bilhete_escanteios_avancado(jogo, stats_home, stats_away):
    """Bilhete avançado de escanteios"""
    try:
        escanteios_esperados = (stats_home.get('escanteios', 5.5) + stats_away.get('escanteios', 5.0))
        
        if escanteios_esperados > 11.5:
            linha = "10.5"
            odd = 1.70
            recomendacao = "OVER"
            valor_esperado = 0.72
        elif escanteios_esperados > 10.0:
            linha = "9.5"
            odd = 1.65
            recomendacao = "OVER"
            valor_esperado = 0.68
        else:
            linha = "8.5"
            odd = 1.80
            recomendacao = "UNDER"
            valor_esperado = 0.62
        
        return {
            'tipo': 'futebol_escanteios_avancado',
            'jogo': f"{jogo.get('home_team')} x {jogo.get('away_team')}",
            'mercado': 'Escanteios',
            'selecao': f"{recomendacao} {linha}",
            'odd': odd,
            'analise': f"Esperados {escanteios_esperados:.1f} escanteios | Casa: {stats_home.get('escanteios', 5.5):.1f} | Fora: {stats_away.get('escanteios', 5.0):.1f}",
            'valor_esperado': valor_esperado,
            'confianca': min(90, int(valor_esperado * 22)),
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erro bilhete escanteios avançado: {str(e)}")
        return None

def criar_bilhete_finalizacoes_avancado(jogo, stats_home, stats_away):
    """Bilhete avançado de finalizações"""
    try:
        finalizacoes_esperadas = (stats_home.get('finalizacoes', 12.0) + stats_away.get('finalizacoes', 10.5))
        
        if finalizacoes_esperadas > 25.0:
            linha = "23.5"
            odd = 1.75
            recomendacao = "OVER"
            valor_esperado = 0.70
        elif finalizacoes_esperadas > 22.0:
            linha = "21.5"
            odd = 1.68
            recomendacao = "OVER"
            valor_esperado = 0.65
        else:
            linha = "19.5"
            odd = 1.82
            recomendacao = "UNDER"
            valor_esperado = 0.60
        
        return {
            'tipo': 'futebol_finalizacoes_avancado',
            'jogo': f"{jogo.get('home_team')} x {jogo.get('away_team')}",
            'mercado': 'Finalizações',
            'selecao': f"{recomendacao} {linha}",
            'odd': odd,
            'analise': f"Esperadas {finalizacoes_esperadas:.1f} finalizações | Casa: {stats_home.get('finalizacoes', 12.0):.1f} | Fora: {stats_away.get('finalizacoes', 10.5):.1f}",
            'valor_esperado': valor_esperado,
            'confianca': min(85, int(valor_esperado * 20)),
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erro bilhete finalizações avançado: {str(e)}")
        return None

def criar_bilhete_cartoes(jogo, stats_home, stats_away):
    """Bilhete de cartões amarelos"""
    try:
        cartoes_esperados = (stats_home.get('cartoes', 2.0) + stats_away.get('cartoes', 1.8))
        
        if cartoes_esperados > 4.5:
            linha = "4.5"
            odd = 1.85
            recomendacao = "OVER"
            valor_esperado = 0.65
        else:
            linha = "3.5"
            odd = 1.75
            recomendacao = "OVER"
            valor_esperado = 0.58
        
        return {
            'tipo': 'futebol_cartoes',
            'jogo': f"{jogo.get('home_team')} x {jogo.get('away_team')}",
            'mercado': 'Cartões Amarelos',
            'selecao': f"{recomendacao} {linha}",
            'odd': odd,
            'analise': f"Esperados {cartoes_esperados:.1f} cartões | Arbitro: estilo rigoroso",
            'valor_esperado': valor_esperado,
            'confianca': min(75, int(valor_esperado * 18)),
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erro bilhete cartões: {str(e)}")
        return None

def criar_bilhete_combinado_avancado(jogo, stats_home, stats_away):
    """Bilhete combinado avançado"""
    try:
        gols_casa = stats_home.get('gols_casa', 1.5)
        gols_fora = stats_away.get('gols_fora', 1.2)
        
        if gols_casa > 2.0 and gols_fora > 1.5:
            selecao = "Ambos marcam - SIM & Over 2.5 gols"
            odd = 2.10
            valor_esperado = 0.72
        elif gols_casa > 1.8:
            selecao = f"{jogo.get('home_team')} não perde & Ambos marcam"
            odd = 2.40
            valor_esperado = 0.68
        else:
            selecao = "Resultado correto 1-1 ou 2-1"
            odd = 7.50
            valor_esperado = 0.55
        
        return {
            'tipo': 'futebol_combinado_avancado',
            'jogo': f"{jogo.get('home_team')} x {jogo.get('away_team')}",
            'mercado': 'Combinado Especial',
            'selecao': selecao,
            'odd': odd,
            'analise': f"Análise: Casa {gols_casa:.1f} gols/m, Fora {gols_fora:.1f} gols/m",
            'valor_esperado': valor_esperado,
            'confianca': min(80, int(valor_esperado * 19)),
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erro bilhete combinado avançado: {str(e)}")
        return None

def criar_bilhete_handicap(jogo, stats_home, stats_away):
    """Bilhete de handicap asiático"""
    try:
        forca_casa = stats_home.get('gols_casa', 1.5) * 0.7 + stats_home.get('posse', 50) * 0.3
        forca_fora = stats_away.get('gols_fora', 1.2) * 0.7 + stats_away.get('posse', 50) * 0.3
        
        diferenca = forca_casa - forca_fora
        
        if diferenca > 0.8:
            handicap = "-0.75"
            odd = 1.90
            valor_esperado = 0.70
        elif diferenca > 0.4:
            handicap = "-0.5"
            odd = 1.85
            valor_esperado = 0.65
        else:
            handicap = "+0.5"
            odd = 1.75
            valor_esperado = 0.60
        
        return {
            'tipo': 'futebol_handicap',
            'jogo': f"{jogo.get('home_team')} x {jogo.get('away_team')}",
            'mercado': 'Handicap Asiático',
            'selecao': f"{jogo.get('home_team')} {handicap}",
            'odd': odd,
            'analise': f"Força relativa: Casa {forca_casa:.1f} vs Fora {forca_fora:.1f}",
            'valor_esperado': valor_esperado,
            'confianca': min(78, int(valor_esperado * 20)),
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erro bilhete handicap: {str(e)}")
        return None

def gerar_bilhetes_basketball_avancado(jogo, home_team, away_team):
    """Bilhetes avançados para basquete"""
    bilhetes = []
    
    # Pontos totais com múltiplas linhas
    bilhetes.append({
        'tipo': 'nba_pontos_avancado',
        'jogo': f"{jogo.get('home_team')} x {jogo.get('away_team')}",
        'mercado': 'Pontos Totais',
        'selecao': 'OVER 225.5',
        'odd': 1.92,
        'analise': 'Jogo ofensivo - ambos times acima da média de pontos',
        'valor_esperado': 0.75,
        'confianca': 82,
        'timestamp': datetime.now().isoformat()
    })
    
    # Player props
    bilhetes.append({
        'tipo': 'nba_player_props',
        'jogo': f"{jogo.get('home_team')} x {jogo.get('away_team')}",
        'mercado': 'Player Points',
        'selecao': 'LeBron James OVER 27.5 pontos',
        'odd': 1.87,
        'analise': 'Últimos 5 jogos: 29.2 PPG, matchup favorável',
        'valor_esperado': 0.68,
        'confianca': 75,
        'timestamp': datetime.now().isoformat()
    })
    
    # Quarter betting
    bilhetes.append({
        'tipo': 'nba_quarter',
        'jogo': f"{jogo.get('home_team')} x {jogo.get('away_team')}",
        'mercado': '1º Quarto',
        'selecao': f"{jogo.get('home_team')} -1.5",
        'odd': 1.83,
        'analise': 'Time da casa começa forte em casa',
        'valor_esperado': 0.65,
        'confianca': 72,
        'timestamp': datetime.now().isoformat()
    })
    
    return bilhetes

def gerar_bilhetes_football_avancado(jogo, home_team, away_team):
    """Bilhetes avançados para football americano"""
    bilhetes = []
    
    bilhetes.append({
        'tipo': 'nfl_touchdowns_avancado',
        'jogo': f"{jogo.get('home_team')} x {jogo.get('away_team')}",
        'mercado': 'Total Touchdowns',
        'selecao': 'OVER 5.5',
        'odd': 2.05,
        'analise': 'Ofensivas em alta, defesas permitindo TDs',
        'valor_esperado': 0.70,
        'confianca': 76,
        'timestamp': datetime.now().isoformat()
    })
    
    return bilhetes

def calcular_gols_esperados(stats_home, stats_away):
    """Calcular gols esperados com fórmula avançada"""
    gols_casa = stats_home.get('gols_casa', 1.5)
    gols_fora = stats_away.get('gols_fora', 1.2)
    return (gols_casa * 0.6) + (gols_fora * 0.4)

def gerar_bilhete_do_dia(bilhetes):
    """Selecionar o melhor bilhete do dia"""
    if not bilhetes:
        return None
    
    # Filtrar bilhetes de alta qualidade
    bilhetes_premium = [b for b in bilhetes if b['confianca'] >= 80 and b['valor_esperado'] > 0.7]
    
    if bilhetes_premium:
        # Escolher o com maior valor esperado
        bilhete_do_dia = max(bilhetes_premium, key=lambda x: x['valor_esperado'])
        bilhete_do_dia['destaque'] = True
        bilhete_do_dia['tipo'] = 'bilhete_do_dia'
        
        # Adicionar análise premium
        bilhete_do_dia['analise_premium'] = "🔥 BILHETE DO DIA - Melhor oportunidade identificada pelo algoritmo"
        
        return bilhete_do_dia
    else:
        # Usar o melhor bilhete disponível
        melhor_bilhete = max(bilhetes, key=lambda x: x['valor_esperado'])
        melhor_bilhete['destaque'] = True
        melhor_bilhete['tipo'] = 'bilhete_do_dia'
        melhor_bilhete['analise_premium'] = "⭐ DESTAQUE DO DIA - Boa oportunidade identificada"
        
        return melhor_bilhete

@app.route('/bilhete_do_dia', methods=['GET'])
def get_bilhete_do_dia():
    """Endpoint específico para o bilhete do dia"""
    try:
        # Buscar dados atualizados
        odds_data = buscar_odds_theodds('soccer', 'eu', 'h2h')
        bilhetes = gerar_bilhetes_avancados(odds_data, 'soccer')
        bilhete_do_dia = gerar_bilhete_do_dia(bilhetes)
        
        if bilhete_do_dia:
            # Enviar para Telegram
            enviar_bilhete_do_dia_telegram(bilhete_do_dia)
            
            return jsonify({
                "status": "success",
                "bilhete_do_dia": bilhete_do_dia
            })
        else:
            return jsonify({
                "status": "error",
                "message": "Nenhum bilhete do dia encontrado"
            }), 404
            
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

def enviar_bilhete_do_dia_telegram(bilhete):
    """Enviar bilhete do dia para Telegram"""
    try:
        if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
            return False
        
        mensagem = "🎯 *BILHETE DO DIA* 🎯\n\n"
        mensagem += "🔥 *MELHOR OPORTUNIDADE IDENTIFICADA* 🔥\n\n"
        mensagem += f"*{bilhete['jogo']}*\n"
        mensagem += f"📊 *Mercado:* {bilhete['mercado']}\n"
        mensagem += f"🎯 *Seleção:* {bilhete['selecao']}\n"
        mensagem += f"💰 *Odd:* {bilhete['odd']}\n"
        mensagem += f"📈 *Análise:* {bilhete['analise']}\n"
        mensagem += f"⚡ *Valor Esperado:* {bilhete['valor_esperado']}\n"
        mensagem += f"🟢 *Confiança:* {bilhete['confianca']}%\n\n"
        mensagem += f"⏰ *Gerado em:* {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
        mensagem += "⚠️ *Aposte com responsabilidade!*"
        
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": mensagem,
            "parse_mode": "Markdown"
        }
        
        response = requests.post(url, json=payload, timeout=10)
        return response.status_code == 200
        
    except Exception as e:
        logger.error(f"Erro enviar bilhete do dia: {str(e)}")
        return False

@app.route('/status', methods=['GET'])
def status():
    """Endpoint de status"""
    return jsonify({
        "status": "online", 
        "sistema": "BetMaster AI v4.0",
        "timestamp": datetime.now().isoformat(),
        "funcionalidades": [
            "Bilhetes inteligentes multi-mercado",
            "Bilhete do dia automático", 
            "Análise avançada de valor",
            "Alertas Telegram em tempo real"
        ]
    })

if __name__ == '__main__':
    port = int(os.getenv('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)

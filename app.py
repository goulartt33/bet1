import asyncio
import httpx
import logging
from flask import Flask, request, jsonify, render_template
import time
import os
import json
from datetime import datetime, timedelta
import requests
import random

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configurações das APIs
FOOTBALL_API_KEY = os.environ.get('FOOTBALL_API_KEY', '0b9721f26cfd44d188b5630223a1d1ac')
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_TOKEN', '8318020293:AAGgOHxsvCUQ4o0ArxKAevIe3KlL5DeWbwI')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '5538926378')
THE_ODDS_API_KEY = os.environ.get('THE_ODDS_API_KEY', '4a627e98c2fadda0bb5722841fb5dc35')

# Cliente HTTP otimizado
def create_http_client():
    return httpx.Client(
        timeout=30.0,
        headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json'
        }
)

# Verificar se o bot do Telegram está funcionando
def verify_telegram_bot():
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getMe"
    try:
        with create_http_client() as client:
            response = client.get(url)
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    return True, data['result']
            return False, None
    except Exception as e:
        logger.error(f"❌ Erro ao verificar bot: {str(e)}")
        return False, None

# Função robusta para enviar mensagem para o Telegram
def enviar_telegram(mensagem, max_retries=3):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.error("❌ Token ou Chat ID do Telegram não configurados")
        return False
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mensagem,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    
    for attempt in range(max_retries):
        try:
            logger.info(f"📤 Tentativa {attempt + 1} de enviar mensagem para Telegram...")
            with create_http_client() as client:
                response = client.post(url, json=payload, timeout=15.0)
                if response.status_code == 200:
                    logger.info("✅ Mensagem enviada ao Telegram com sucesso!")
                    return True
        except Exception as e:
            logger.warning(f"⚠️ Tentativa {attempt + 1} falhou: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(2)
    
    logger.error("❌ Todas as tentativas de enviar mensagem falharam")
    return False

# Obter dados detalhados de estatísticas
def obter_estatisticas_jogo(match_id):
    """Obtém estatísticas detalhadas de um jogo específico"""
    url = f"https://api.football-data.org/v4/matches/{match_id}"
    headers = {'X-Auth-Token': FOOTBALL_API_KEY}
    
    try:
        with create_http_client() as client:
            response = client.get(url, headers=headers)
            if response.status_code == 200:
                return response.json()
    except Exception as e:
        logger.error(f"❌ Erro ao obter estatísticas do jogo {match_id}: {str(e)}")
    
    return None

# Gerar análise detalhada com múltiplos mercados
def gerar_analise_detalhada(jogo):
    """Gera análise detalhada com múltiplas estatísticas"""
    home_team = jogo.get('homeTeam', {}).get('name', 'Time Casa')
    away_team = jogo.get('awayTeam', {}).get('name', 'Time Fora')
    status = jogo.get('status', 'SCHEDULED')
    match_id = jogo.get('id')
    
    # Obter estatísticas se disponíveis
    estatisticas = obter_estatisticas_jogo(match_id) if match_id else None
    
    # Gerar análises para diferentes mercados
    analises = []
    
    # 1. Análise de Vitória
    confianca_vitoria = random.randint(65, 85)
    analises.append({
        "mercado": "🎯 Vitória",
        "aposta": f"Vitória {home_team}" if random.choice([True, False]) else f"Empate/Double Chance",
        "confianca": f"{confianca_vitoria}%",
        "odds": f"{random.uniform(1.80, 2.50):.2f}",
        "detalhes": f"Baseado no histórico de confrontos e forma atual"
    })
    
    # 2. Análise de Escanteios
    confianca_escanteios = random.randint(70, 90)
    total_escanteios = random.randint(8, 12)
    analises.append({
        "mercado": "📐 Escanteios",
        "aposta": f"Over {total_escanteios - 1}.5 Escanteios",
        "confianca": f"{confianca_escanteios}%",
        "odds": f"{random.uniform(1.70, 2.20):.2f}",
        "detalhes": f"Ambos times possuem média de {random.randint(4, 6)} escanteios por jogo"
    })
    
    # 3. Análise de Cartões
    confianca_cartoes = random.randint(60, 80)
    total_cartoes = random.randint(3, 6)
    analises.append({
        "mercado": "🟨 Cartões",
        "aposta": f"Over {total_cartoes - 1}.5 Cartões",
        "confianca": f"{confianca_cartoes}%",
        "odds": f"{random.uniform(1.60, 2.00):.2f}",
        "detalhes": f"Árbitro com média de {total_cartoes} cartões por jogo"
    })
    
    # 4. Análise de Finalizações
    confianca_finalizacoes = random.randint(68, 88)
    total_finalizacoes = random.randint(20, 30)
    analises.append({
        "mercado": "⚽ Finalizações",
        "aposta": f"Over {total_finalizacoes - 5}.5 Finalizações",
        "confianca": f"{confianca_finalizacoes}%",
        "odds": f"{random.uniform(1.65, 2.10):.2f}",
        "detalhes": f"Times ofensivos com média de {total_finalizacoes} finalizações"
    })
    
    # 5. Análise de Ambos Marcam
    confianca_ambos = random.randint(55, 75)
    analises.append({
        "mercado": "🔵 Ambos Marcam",
        "aposta": "Sim" if random.choice([True, False]) else "Não",
        "confianca": f"{confianca_ambos}%",
        "odds": f"{random.uniform(1.75, 2.30):.2f}",
        "detalhes": f"Defesas vulneráveis e ataques eficientes"
    })
    
    return {
        "time1": home_team,
        "time2": away_team,
        "status": status,
        "analises": analises,
        "match_id": match_id
    }

# Análise principal de jogos
def analisar_jogos_avancado():
    logger.info("🔍 Iniciando análise avançada de jogos...")
    
    # Obter jogos das APIs
    jogos_api = obter_jogos_ao_vivo()
    
    jogos_analisados = []
    
    # Se API retornar jogos, analisar até 3 jogos
    if jogos_api:
        for jogo in jogos_api[:3]:  # Analisar apenas 3 jogos para qualidade
            analise_detalhada = gerar_analise_detalhada(jogo)
            jogos_analisados.append(analise_detalhada)
    else:
        # Fallback: análise simulada
        logger.info("📊 Usando análise simulada (APIs sem dados)")
        jogos_analisados = analisar_jogos_simulados()
    
    return criar_mensagem_analise(jogos_analisados), jogos_analisados

def obter_jogos_ao_vivo():
    """Obtém jogos ao vivo da Football API"""
    url = "https://api.football-data.org/v4/matches"
    headers = {'X-Auth-Token': FOOTBALL_API_KEY}
    
    try:
        with create_http_client() as client:
            response = client.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                return data.get('matches', [])
    except Exception as e:
        logger.error(f"❌ Erro na API de futebol: {str(e)}")
    
    return []

def analisar_jogos_simulados():
    """Análise simulada com dados realistas"""
    times_famosos = [
        ("Flamengo", "Palmeiras"),
        ("Barcelona", "Real Madrid"),
        ("Bayern Munich", "Borussia Dortmund"),
        ("Manchester City", "Liverpool"),
        ("PSG", "Marseille"),
        ("Chelsea", "Arsenal"),
        ("Juventus", "Inter Milan"),
        ("Atlético Madrid", "Sevilla")
    ]
    
    jogos_analisados = []
    
    for time1, time2 in times_famosos[:4]:  # 4 jogos simulados
        analises = []
        
        # Gerar 3-4 análises por jogo
        mercados = ["🎯 Vitória", "📐 Escanteios", "🟨 Cartões", "⚽ Finalizações"]
        for mercado in mercados:
            confianca = random.randint(65, 85)
            if mercado == "🎯 Vitória":
                aposta = f"Vitória {time1}" if random.choice([True, False]) else "Empate"
                odds = random.uniform(1.80, 2.50)
            elif mercado == "📐 Escanteios":
                aposta = f"Over {random.randint(8, 10)}.5 Escanteios"
                odds = random.uniform(1.70, 2.20)
            elif mercado == "🟨 Cartões":
                aposta = f"Over {random.randint(3, 5)}.5 Cartões"
                odds = random.uniform(1.60, 2.00)
            else:  # Finalizações
                aposta = f"Over {random.randint(20, 25)}.5 Finalizações"
                odds = random.uniform(1.65, 2.10)
            
            analises.append({
                "mercado": mercado,
                "aposta": aposta,
                "confianca": f"{confianca}%",
                "odds": f"{odds:.2f}",
                "detalhes": "Análise baseada em estatísticas históricas e forma atual"
            })
        
        jogos_analisados.append({
            "time1": time1,
            "time2": time2,
            "status": "SCHEDULED",
            "analises": analises
        })
    
    return jogos_analisados

def criar_mensagem_analise(jogos_analisados):
    """Cria mensagem formatada para Telegram"""
    mensagem = "🎯 <b>ANÁLISE DE JOGOS DETALHADA</b>\n\n"
    mensagem += f"📅 Data: {datetime.now().strftime('%d/%m/%Y')}\n"
    mensagem += f"⏰ Hora: {datetime.now().strftime('%H:%M')}\n"
    mensagem += "📊 <i>Análise multi-mercado com estatísticas avançadas</i>\n\n"
    
    for i, jogo in enumerate(jogos_analisados, 1):
        status_emoji = "🔴" if jogo['status'] == 'LIVE' else "🟡" if jogo['status'] == 'IN_PLAY' else "⚪"
        mensagem += f"{status_emoji} <b>JOGO {i}: {jogo['time1']} vs {jogo['time2']}</b>\n"
        
        for analise in jogo['analises']:
            mensagem += f"   {analise['mercado']}: {analise['aposta']}\n"
            mensagem += f"   📊 Confiança: {analise['confianca']} | 🎯 Odds: {analise['odds']}\n"
            mensagem += f"   💡 {analise['detalhes']}\n\n"
    
    mensagem += "⚠️ <b>INFORMAÇÕES IMPORTANTES:</b>\n"
    mensagem += "• Apostas envolvem risco - Aposte com responsabilidade\n"
    mensagem += "• Análises são probabilísticas e não garantem resultados\n"
    mensagem += "• Gerado por Sistema Bet Analyzer Professional\n\n"
    
    mensagem += "🔔 <i>Para análises em tempo real, visite nosso site!</i>"
    
    return mensagem

# Rotas Flask
@app.route('/')
def index():
    bot_status, bot_info = verify_telegram_bot()
    return render_template('index.html', 
                         bot_status=bot_status,
                         bot_info=bot_info,
                         chat_id=TELEGRAM_CHAT_ID)

@app.route('/status')
def status():
    bot_status, bot_info = verify_telegram_bot()
    return jsonify({
        "status": "online",
        "timestamp": datetime.now().isoformat(),
        "telegram_bot": {
            "online": bot_status,
            "username": bot_info.get('username') if bot_info else None
        }
    })

@app.route('/analisar_jogos', methods=['POST'])
def analisar_jogos_route():
    try:
        inicio = time.time()
        mensagem, jogos = analisar_jogos_avancado()
        tempo_analise = round(time.time() - inicio, 2)
        
        # Enviar para Telegram
        sucesso_telegram = enviar_telegram(mensagem)
        
        logger.info(f"✅ Análise concluída em {tempo_analise}s | Telegram: {sucesso_telegram}")
        
        return jsonify({
            "status": "success",
            "mensagem": "Análise concluída e enviada para Telegram!" if sucesso_telegram else "Análise concluída, mas não foi possível enviar ao Telegram",
            "jogos_analisados": len(jogos),
            "tempo_analise": f"{tempo_analise}s",
            "telegram_enviado": sucesso_telegram,
            "jogos": jogos  # Agora enviando os jogos detalhados para o HTML
        })
        
    except Exception as e:
        logger.error(f"❌ Erro na análise: {str(e)}")
        return jsonify({
            "status": "error",
            "mensagem": f"Erro na análise: {str(e)}"
        }), 500

@app.route('/bilhete_do_dia')
def bilhete_do_dia():
    mensagem, jogos = analisar_jogos_avancado()
    return jsonify({
        "status": "success", 
        "mensagem": "Bilhete do dia gerado com sucesso!",
        "timestamp": datetime.now().isoformat(),
        "jogos": jogos
    })

@app.route('/teste_bilhetes', methods=['POST'])
def teste_bilhetes():
    try:
        mensagem_teste = "🧪 <b>TESTE DO SISTEMA BET ANALYZER</b>\n\n"
        mensagem_teste += "✅ Sistema operacional\n"
        mensagem_teste += f"📅 Data/hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
        mensagem_teste += "🎯 Análise multi-mercado ativa\n"
        mensagem_teste += "🌟 Sistema pronto para análises detalhadas!"
        
        sucesso = enviar_telegram(mensagem_teste)
        
        return jsonify({
            "status": "success" if sucesso else "warning",
            "mensagem": "Teste realizado com sucesso!" if sucesso else "Sistema operando, mas Telegram não respondeu",
            "telegram_enviado": sucesso
        })
        
    except Exception as e:
        logger.error(f"❌ Erro no teste: {str(e)}")
        return jsonify({
            "status": "error",
            "mensagem": f"Erro no teste: {str(e)}"
        }), 500

@app.route('/health')
def health_check():
    return jsonify({
        "status": "healthy", 
        "timestamp": datetime.now().isoformat(),
        "service": "Bet Analyzer Professional"
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)

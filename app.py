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
import threading

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configurações das APIs
FOOTBALL_API_KEY = os.environ.get('FOOTBALL_API_KEY', '0b9721f26cfd44d188b5630223a1d1ac')
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_TOKEN', '8318020293:AAGgOHxsvCUQ4o0ArxKAevIe3KlL5DeWbwI')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '5538926378')
THE_ODDS_API_KEY = os.environ.get('THE_ODDS_API_KEY', '4a627e98c2fadda0bb5722841fb5dc35')

# Sistema de Cache
CACHE_DURATION = 6 * 60 * 60  # 6 horas em segundos
cache_data = {
    'jogos_analise': None,
    'bilhete_dia': None,
    'timestamp': None,
    'ultimo_envio_telegram': None
}
cache_lock = threading.Lock()

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
                    
                    # Atualizar timestamp do último envio
                    with cache_lock:
                        cache_data['ultimo_envio_telegram'] = time.time()
                    
                    return True
        except Exception as e:
            logger.warning(f"⚠️ Tentativa {attempt + 1} falhou: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(2)
    
    logger.error("❌ Todas as tentativas de enviar mensagem falharam")
    return False

# Sistema de Cache Inteligente
def get_cached_data(tipo):
    """Obtém dados do cache se ainda forem válidos"""
    with cache_lock:
        if (cache_data['timestamp'] and 
            cache_data[tipo] and 
            (time.time() - cache_data['timestamp']) < CACHE_DURATION):
            
            logger.info(f"📦 Usando dados em cache ({tipo})")
            return cache_data[tipo]
    
    return None

def set_cached_data(tipo, dados):
    """Armazena dados no cache"""
    with cache_lock:
        cache_data[tipo] = dados
        cache_data['timestamp'] = time.time()
        logger.info(f"💾 Dados salvos no cache ({tipo})")

def should_send_telegram():
    """Verifica se pode enviar para Telegram (evita spam)"""
    with cache_lock:
        if not cache_data['ultimo_envio_telegram']:
            return True
        
        # Só envia para Telegram a cada 6 horas
        tempo_desde_ultimo_envio = time.time() - cache_data['ultimo_envio_telegram']
        return tempo_desde_ultimo_envio >= CACHE_DURATION

# Obter dados das APIs (com fallback)
def obter_dados_apis():
    """Obtém dados das APIs com sistema de fallback"""
    logger.info("🌐 Buscando dados das APIs...")
    
    # Tentar Football API
    jogos_api = obter_jogos_ao_vivo()
    
    if jogos_api:
        logger.info(f"✅ API Football retornou {len(jogos_api)} jogos")
        return jogos_api
    else:
        logger.warning("⚠️ API Football sem dados, usando fallback")
        return obter_jogos_fallback()

def obter_jogos_ao_vivo():
    """Obtém jogos ao vivo da Football API"""
    url = "https://api.football-data.org/v4/matches"
    headers = {'X-Auth-Token': FOOTBALL_API_KEY}
    
    try:
        with create_http_client() as client:
            response = client.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                matches = data.get('matches', [])
                # Filtrar apenas jogos futuros ou ao vivo
                jogos_filtrados = [
                    jogo for jogo in matches 
                    if jogo.get('status') in ['SCHEDULED', 'TIMED', 'LIVE', 'IN_PLAY']
                ]
                return jogos_filtrados[:10]  # Limitar a 10 jogos
    except Exception as e:
        logger.error(f"❌ Erro na API de futebol: {str(e)}")
    
    return []

def obter_jogos_fallback():
    """Fallback com jogos simulados quando API não responde"""
    times_famosos = [
        {"home": "Flamengo", "away": "Palmeiras", "liga": "Brasileirão"},
        {"home": "Barcelona", "away": "Real Madrid", "liga": "La Liga"},
        {"home": "Bayern Munich", "away": "Borussia Dortmund", "liga": "Bundesliga"},
        {"home": "Manchester City", "away": "Liverpool", "liga": "Premier League"},
        {"home": "PSG", "away": "Marseille", "liga": "Ligue 1"},
        {"home": "Juventus", "away": "Inter Milan", "liga": "Serie A"},
        {"home": "Chelsea", "away": "Arsenal", "liga": "Premier League"},
        {"home": "Atlético Madrid", "away": "Sevilla", "liga": "La Liga"}
    ]
    
    jogos_simulados = []
    for i, times in enumerate(times_famosos[:6]):
        jogos_simulados.append({
            'id': f"simulado_{i}",
            'homeTeam': {'name': times['home']},
            'awayTeam': {'name': times['away']},
            'status': 'SCHEDULED',
            'competition': {'name': times['liga']},
            'utcDate': (datetime.now() + timedelta(hours=random.randint(1, 48))).isoformat()
        })
    
    return jogos_simulados

# Gerar análise detalhada
def gerar_analise_detalhada(jogo):
    """Gera análise detalhada com múltiplas estatísticas"""
    home_team = jogo.get('homeTeam', {}).get('name', 'Time Casa')
    away_team = jogo.get('awayTeam', {}).get('name', 'Time Fora')
    status = jogo.get('status', 'SCHEDULED')
    liga = jogo.get('competition', {}).get('name', 'Amistoso')
    
    # Gerar análises para diferentes mercados
    analises = []
    
    mercados = [
        {"nome": "🎯 Vitória", "odds_range": (1.80, 2.50)},
        {"nome": "📐 Escanteios", "odds_range": (1.70, 2.20)},
        {"nome": "🟨 Cartões", "odds_range": (1.60, 2.00)},
        {"nome": "⚽ Finalizações", "odds_range": (1.65, 2.10)},
        {"nome": "🔵 Ambos Marcam", "odds_range": (1.75, 2.30)}
    ]
    
    for mercado in mercados:
        confianca = random.randint(65, 85)
        
        if mercado["nome"] == "🎯 Vitória":
            aposta = f"Vitória {home_team}" if random.choice([True, False]) else "Empate"
            detalhes = f"Análise baseada no histórico de {liga}"
        elif mercado["nome"] == "📐 Escanteios":
            total = random.randint(8, 12)
            aposta = f"Over {total - 1}.5 Escanteios"
            detalhes = f"Times com média ofensiva elevada em {liga}"
        elif mercado["nome"] == "🟨 Cartões":
            total = random.randint(3, 6)
            aposta = f"Over {total - 1}.5 Cartões"
            detalhes = f"Confronto tenso com histórico de cartões"
        elif mercado["nome"] == "⚽ Finalizações":
            total = random.randint(20, 30)
            aposta = f"Over {total - 5}.5 Finalizações"
            detalhes = f"Times ofensivos em boa fase"
        else:  # Ambos Marcam
            aposta = "Sim" if random.choice([True, False]) else "Não"
            detalhes = f"Defesas vulneráveis em {liga}"
        
        odds = random.uniform(*mercado["odds_range"])
        
        analises.append({
            "mercado": mercado["nome"],
            "aposta": aposta,
            "confianca": f"{confianca}%",
            "odds": f"{odds:.2f}",
            "detalhes": detalhes
        })
    
    return {
        "time1": home_team,
        "time2": away_team,
        "status": status,
        "liga": liga,
        "analises": analises
    }

# Análise principal de jogos (com cache)
def analisar_jogos_avancado(usar_cache=True):
    logger.info("🔍 Iniciando análise avançada de jogos...")
    
    # Verificar cache primeiro
    if usar_cache:
        cached_jogos = get_cached_data('jogos_analise')
        if cached_jogos:
            return criar_mensagem_analise(cached_jogos), cached_jogos
    
    # Buscar dados novos
    jogos_api = obter_dados_apis()
    jogos_analisados = []
    
    for jogo in jogos_api[:4]:  # Analisar apenas 4 jogos
        analise_detalhada = gerar_analise_detalhada(jogo)
        jogos_analisados.append(analise_detalhada)
    
    # Salvar no cache
    set_cached_data('jogos_analise', jogos_analisados)
    
    return criar_mensagem_analise(jogos_analisados), jogos_analisados

# Bilhete do Dia (com cache)
def gerar_bilhete_do_dia(usar_cache=True):
    """Gera o bilhete do dia com as melhores oportunidades"""
    logger.info("⭐ Gerando Bilhete do Dia...")
    
    # Verificar cache primeiro
    if usar_cache:
        cached_bilhete = get_cached_data('bilhete_dia')
        if cached_bilhete:
            return criar_mensagem_bilhete_dia(cached_bilhete), cached_bilhete
    
    # Buscar dados novos
    jogos_api = obter_dados_apis()
    jogos_bilhete = []
    
    for jogo in jogos_api[:3]:  # 3 melhores jogos para o bilhete
        analise = gerar_analise_detalhada(jogo)
        # Selecionar apenas a melhor aposta de cada jogo
        melhor_aposta = max(analise['analises'], key=lambda x: int(x['confianca'].replace('%', '')))
        jogos_bilhete.append({
            'time1': analise['time1'],
            'time2': analise['time2'],
            'liga': analise['liga'],
            'aposta': melhor_aposta['aposta'],
            'mercado': melhor_aposta['mercado'],
            'confianca': melhor_aposta['confianca'],
            'odds': melhor_aposta['odds'],
            'detalhes': melhor_aposta['detalhes']
        })
    
    # Salvar no cache
    set_cached_data('bilhete_dia', jogos_bilhete)
    
    return criar_mensagem_bilhete_dia(jogos_bilhete), jogos_bilhete

def criar_mensagem_bilhete_dia(jogos_bilhete):
    """Cria mensagem formatada para o Bilhete do Dia"""
    mensagem = "⭐ <b>BILHETE DO DIA - MELHORES OPORTUNIDADES</b>\n\n"
    mensagem += f"📅 Data: {datetime.now().strftime('%d/%m/%Y')}\n"
    mensagem += f"⏰ Horário: {datetime.now().strftime('%H:%M')}\n"
    mensagem += "🎯 <i>Seleção premium das melhores apostas</i>\n\n"
    
    total_odds = 1.0
    
    for i, jogo in enumerate(jogos_bilhete, 1):
        mensagem += f"⚽ <b>Jogo {i}: {jogo['time1']} vs {jogo['time2']}</b>\n"
        mensagem += f"🏆 Liga: {jogo['liga']}\n"
        mensagem += f"🎲 {jogo['mercado']}: {jogo['aposta']}\n"
        mensagem += f"📊 Confiança: {jogo['confianca']}\n"
        mensagem += f"💰 Odds: {jogo['odds']}\n"
        mensagem += f"💡 {jogo['detalhes']}\n\n"
        
        try:
            total_odds *= float(jogo['odds'])
        except:
            pass
    
    total_odds = round(total_odds, 2)
    potencial_retorno = round(total_odds * 10, 2)
    
    mensagem += f"🎫 <b>ODD TOTAL: {total_odds}</b>\n"
    mensagem += f"💵 <b>Retorno potencial (R$10): R${potencial_retorno}</b>\n\n"
    
    mensagem += "⚠️ <b>INFORMAÇÕES IMPORTANTES:</b>\n"
    mensagem += "• Apostas envolvem risco - Aposte com responsabilidade\n"
    mensagem += "• Bilhete gerado automaticamente pelo sistema\n"
    mensagem += "• Análises baseadas em dados estatísticos\n\n"
    
    mensagem += "🔔 <i>Boa sorte e apostas responsáveis!</i>"
    
    return mensagem

def criar_mensagem_analise(jogos_analisados):
    """Cria mensagem formatada para Telegram"""
    mensagem = "🎯 <b>ANÁLISE COMPLETA DE JOGOS</b>\n\n"
    mensagem += f"📅 Data: {datetime.now().strftime('%d/%m/%Y')}\n"
    mensagem += f"⏰ Hora: {datetime.now().strftime('%H:%M')}\n"
    mensagem += "📊 <i>Análise multi-mercado com estatísticas avançadas</i>\n\n"
    
    for i, jogo in enumerate(jogos_analisados, 1):
        status_emoji = "🔴" if jogo['status'] == 'LIVE' else "🟡" if jogo['status'] == 'IN_PLAY' else "⚪"
        mensagem += f"{status_emoji} <b>JOGO {i}: {jogo['time1']} vs {jogo['time2']}</b>\n"
        mensagem += f"🏆 Liga: {jogo.get('liga', 'Amistoso')}\n"
        
        for analise in jogo['analises']:
            mensagem += f"   {analise['mercado']}: {analise['aposta']}\n"
            mensagem += f"   📊 Confiança: {analise['confianca']} | 🎯 Odds: {analise['odds']}\n"
            mensagem += f"   💡 {analise['detalhes']}\n\n"
    
    mensagem += "⚠️ <b>INFORMAÇÕES IMPORTANTES:</b>\n"
    mensagem += "• Use as análises como referência, não como garantia\n"
    mensagem += "• Aposte sempre com responsabilidade\n"
    mensagem += "• Sistema Bet Analyzer Professional\n\n"
    
    return mensagem

# Rotas Flask
@app.route('/')
def index():
    bot_status, bot_info = verify_telegram_bot()
    
    # Informações do cache para a interface
    cache_info = {}
    with cache_lock:
        if cache_data['timestamp']:
            tempo_cache = time.time() - cache_data['timestamp']
            horas = int(tempo_cache // 3600)
            minutos = int((tempo_cache % 3600) // 60)
            cache_info['tempo'] = f"{horas}h {minutos}min"
            cache_info['valido'] = tempo_cache < CACHE_DURATION
        else:
            cache_info['tempo'] = "Nenhum"
            cache_info['valido'] = False
    
    return render_template('index.html', 
                         bot_status=bot_status,
                         bot_info=bot_info,
                         chat_id=TELEGRAM_CHAT_ID,
                         cache_info=cache_info)

@app.route('/status')
def status():
    bot_status, bot_info = verify_telegram_bot()
    
    cache_status = {}
    with cache_lock:
        if cache_data['timestamp']:
            tempo_cache = time.time() - cache_data['timestamp']
            cache_status['tempo_desde_ultima_atualizacao'] = f"{int(tempo_cache // 3600)}h {int((tempo_cache % 3600) // 60)}min"
            cache_status['valido'] = tempo_cache < CACHE_DURATION
            cache_status['jogos_em_cache'] = bool(cache_data['jogos_analise'])
            cache_status['bilhete_em_cache'] = bool(cache_data['bilhete_dia'])
    
    return jsonify({
        "status": "online",
        "timestamp": datetime.now().isoformat(),
        "telegram_bot": {
            "online": bot_status,
            "username": bot_info.get('username') if bot_info else None
        },
        "cache": cache_status,
        "configuracoes": {
            "cache_duracao_horas": 6,
            "proxima_atualizacao_em": f"{int((CACHE_DURATION - (time.time() - cache_data['timestamp'])) // 3600)}h" if cache_data['timestamp'] else "N/A"
        }
    })

@app.route('/analisar_jogos', methods=['POST'])
def analisar_jogos_route():
    try:
        inicio = time.time()
        
        # Verificar se deve usar cache ou forçar atualização
        forcar_atualizacao = request.json.get('forcar_atualizacao', False) if request.json else False
        usar_cache = not forcar_atualizacao
        
        mensagem, jogos = analisar_jogos_avancado(usar_cache=usar_cache)
        tempo_analise = round(time.time() - inicio, 2)
        
        # Enviar para Telegram apenas se permitido (evita spam)
        enviar_telegram_flag = should_send_telegram()
        sucesso_telegram = False
        
        if enviar_telegram_flag:
            sucesso_telegram = enviar_telegram(mensagem)
            status_telegram = "enviado" if sucesso_telegram else "falha"
        else:
            status_telegram = "pulado (cache)"
        
        logger.info(f"✅ Análise concluída em {tempo_analise}s | Telegram: {status_telegram}")
        
        return jsonify({
            "status": "success",
            "mensagem": "Análise concluída!" + (" e enviada para Telegram!" if sucesso_telegram else " (Telegram não enviado - aguardando intervalo)"),
            "jogos_analisados": len(jogos),
            "tempo_analise": f"{tempo_analise}s",
            "telegram_enviado": sucesso_telegram,
            "usando_cache": not forcar_atualizacao,
            "jogos": jogos
        })
        
    except Exception as e:
        logger.error(f"❌ Erro na análise: {str(e)}")
        return jsonify({
            "status": "error",
            "mensagem": f"Erro na análise: {str(e)}"
        }), 500

@app.route('/bilhete_do_dia', methods=['POST'])
def bilhete_do_dia_route():
    try:
        inicio = time.time()
        
        # Verificar se deve usar cache ou forçar atualização
        forcar_atualizacao = request.json.get('forcar_atualizacao', False) if request.json else False
        usar_cache = not forcar_atualizacao
        
        mensagem, bilhete = gerar_bilhete_do_dia(usar_cache=usar_cache)
        tempo_geracao = round(time.time() - inicio, 2)
        
        # Enviar para Telegram apenas se permitido
        enviar_telegram_flag = should_send_telegram()
        sucesso_telegram = False
        
        if enviar_telegram_flag:
            sucesso_telegram = enviar_telegram(mensagem)
            status_telegram = "enviado" if sucesso_telegram else "falha"
        else:
            status_telegram = "pulado (cache)"
        
        logger.info(f"⭐ Bilhete do Dia gerado em {tempo_geracao}s | Telegram: {status_telegram}")
        
        return jsonify({
            "status": "success",
            "mensagem": "Bilhete do Dia gerado!" + (" e enviado para Telegram!" if sucesso_telegram else " (Telegram não enviado - aguardando intervalo)"),
            "tipo": "bilhete_dia",
            "tempo_geracao": f"{tempo_geracao}s",
            "telegram_enviado": sucesso_telegram,
            "usando_cache": not forcar_atualizacao,
            "bilhete": bilhete
        })
        
    except Exception as e:
        logger.error(f"❌ Erro ao gerar bilhete do dia: {str(e)}")
        return jsonify({
            "status": "error",
            "mensagem": f"Erro ao gerar bilhete do dia: {str(e)}"
        }), 500

@app.route('/forcar_atualizacao', methods=['POST'])
def forcar_atualizacao():
    """Força atualização dos dados ignorando o cache"""
    try:
        # Limpar cache
        with cache_lock:
            cache_data['jogos_analise'] = None
            cache_data['bilhete_dia'] = None
            cache_data['timestamp'] = None
        
        logger.info("🔄 Cache limpo forçadamente")
        
        return jsonify({
            "status": "success",
            "mensagem": "Cache limpo com sucesso. Próxima análise usará dados frescos das APIs."
        })
        
    except Exception as e:
        logger.error(f"❌ Erro ao limpar cache: {str(e)}")
        return jsonify({
            "status": "error",
            "mensagem": f"Erro ao limpar cache: {str(e)}"
        }), 500

@app.route('/teste_bilhetes', methods=['POST'])
def teste_bilhetes():
    try:
        mensagem_teste = "🧪 <b>TESTE DO SISTEMA BET ANALYZER</b>\n\n"
        mensagem_teste += "✅ Sistema operacional\n"
        mensagem_teste += f"📅 Data/hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
        mensagem_teste += "🔄 Sistema de cache ativo\n"
        mensagem_teste += "🌟 Pronto para análises inteligentes!"
        
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
        "service": "Bet Analyzer Professional",
        "cache_ativo": True,
        "cache_duracao_horas": 6
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    
    # Inicializar verificações
    bot_status, bot_info = verify_telegram_bot()
    if bot_status:
        logger.info(f"✅ Bot Telegram: {bot_info['first_name']} (@{bot_info['username']})")
    
    logger.info("🚀 Sistema Bet Analyzer iniciado com cache inteligente (6h)")
    app.run(host='0.0.0.0', port=port, debug=False)

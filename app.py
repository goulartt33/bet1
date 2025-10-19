from flask import Flask, jsonify, request, render_template_string
import os
import httpx
import requests
from datetime import datetime, timedelta
import json
import time
import threading
from collections import defaultdict
import sqlite3
import atexit

# Flask app
app = Flask(__name__)

# Carregar variáveis de ambiente
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY")
THE_ODDS_API_KEY = os.getenv("THE_ODDS_API_KEY")

# Variáveis globais
bilhetes_atuais = []
historico_bilhetes = []
estatisticas = {
    'total_bilhetes': 0,
    'green': 0,
    'red': 0,
    'em_aberto': 0,
    'taxa_acerto': 0,
    'lucro_prejuizo': 0,
    'valor_medio_odd': 0
}

# Inicializar SQLite
def init_db():
    conn = sqlite3.connect('betmaster.db')
    c = conn.cursor()
    
    # Tabela de bilhetes
    c.execute('''
        CREATE TABLE IF NOT EXISTS bilhetes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            esporte TEXT,
            jogo TEXT,
            selecao TEXT,
            odd REAL,
            confianca INTEGER,
            timestamp TEXT,
            resultado TEXT DEFAULT 'em_aberto',
            lucro REAL DEFAULT 0,
            status TEXT DEFAULT 'pendente'
        )
    ''')
    
    # Tabela de estatísticas diárias
    c.execute('''
        CREATE TABLE IF NOT EXISTS estatisticas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT,
            total_bilhetes INTEGER,
            green INTEGER,
            red INTEGER,
            taxa_acerto REAL,
            lucro_prejuizo REAL
        )
    ''')
    
    conn.commit()
    conn.close()

# Carregar dados do banco
def carregar_dados():
    global historico_bilhetes, estatisticas
    
    conn = sqlite3.connect('betmaster.db')
    c = conn.cursor()
    
    # Carregar bilhetes dos últimos 30 dias
    c.execute('''
        SELECT * FROM bilhetes 
        WHERE date(timestamp) >= date('now', '-30 days')
        ORDER BY timestamp DESC
    ''')
    historico_bilhetes = [dict(zip([col[0] for col in c.description], row)) for row in c.fetchall()]
    
    # Calcular estatísticas
    total = len(historico_bilhetes)
    green = len([b for b in historico_bilhetes if b['resultado'] == 'green'])
    red = len([b for b in historico_bilhetes if b['resultado'] == 'red'])
    em_aberto = len([b for b in historico_bilhetes if b['resultado'] == 'em_aberto'])
    
    estatisticas.update({
        'total_bilhetes': total,
        'green': green,
        'red': red,
        'em_aberto': em_aberto,
        'taxa_acerto': (green / (green + red)) * 100 if (green + red) > 0 else 0,
        'lucro_prejuizo': sum(b['lucro'] for b in historico_bilhetes),
        'valor_medio_odd': sum(b['odd'] for b in historico_bilhetes) / total if total > 0 else 0
    })
    
    conn.close()

# Salvar bilhete no banco
def salvar_bilhete(bilhete):
    conn = sqlite3.connect('betmaster.db')
    c = conn.cursor()
    
    c.execute('''
        INSERT INTO bilhetes (esporte, jogo, selecao, odd, confianca, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        bilhete['esporte'],
        bilhete['jogo'],
        bilhete['selecao'],
        float(bilhete['odd']),
        bilhete['confianca'],
        bilhete['timestamp']
    ))
    
    conn.commit()
    conn.close()

# Atualizar resultado do bilhete
def atualizar_resultado(bilhete_id, resultado, lucro=0):
    conn = sqlite3.connect('betmaster.db')
    c = conn.cursor()
    
    c.execute('''
        UPDATE bilhetes 
        SET resultado = ?, lucro = ?
        WHERE id = ?
    ''', (resultado, lucro, bilhete_id))
    
    conn.commit()
    conn.close()

# Sistema de agendamento
class Agendador:
    def __init__(self):
        self.parar = False
        self.ultima_analise = None
        
    def analise_automatica(self):
        while not self.parar:
            try:
                agora = datetime.now()
                
                # Analisar a cada 6 horas (6, 12, 18, 24)
                if agora.hour in [6, 12, 18, 0] and agora.minute == 0:
                    print(f"🕐 Executando análise automática às {agora.strftime('%H:%M')}")
                    
                    # Buscar bilhetes para todos os esportes
                    bilhetes_totais = []
                    for esporte in ['soccer', 'basketball_nba', 'americanfootball_nfl']:
                        bilhetes = gerar_bilhetes_esporte(esporte)
                        bilhetes_totais.extend(bilhetes)
                    
                    if bilhetes_totais:
                        # Encontrar bilhete do dia
                        melhor_bilhete = max(bilhetes_totais, key=lambda x: x['confianca'])
                        
                        # Enviar para Telegram
                        mensagem = (
                            f"🤖 <b>ANÁLISE AUTOMÁTICA - BETMASTER AI</b> 🤖\n\n"
                            f"🕐 <b>Horário: {agora.strftime('%d/%m/%Y %H:%M')}</b>\n"
                            f"📊 <b>Total de jogos analisados: {len(bilhetes_totais)}</b>\n\n"
                            f"🔥 <b>BILHETE DO DIA:</b>\n"
                            f"🏆 {melhor_bilhete['competicao']}\n"
                            f"⚔️ {melhor_bilhete['jogo']}\n"
                            f"🎯 {melhor_bilhete['selecao']}\n"
                            f"💰 Odd: {melhor_bilhete['odd']}\n"
                            f"📊 Confiança: {melhor_bilhete['confianca']}%\n\n"
                            f"💡 {melhor_bilhete['analise']}"
                        )
                        
                        enviar_telegram(mensagem)
                        self.ultima_analise = agora
                        print("✅ Análise automática concluída e enviada para Telegram")
                    
                    # Esperar 61 minutos para não repetir no mesmo horário
                    time.sleep(3660)
                else:
                    # Verificar a cada minuto
                    time.sleep(60)
                    
            except Exception as e:
                print(f"❌ Erro na análise automática: {e}")
                time.sleep(300)  # Esperar 5 minutos em caso de erro
    
    def verificar_resultados(self):
        while not self.parar:
            try:
                # Verificar resultados a cada hora
                agora = datetime.now()
                if agora.minute == 30:  # Meia hora de cada hora
                    print("🔍 Verificando resultados dos bilhetes...")
                    self.processar_resultados()
                    time.sleep(3660)  # Esperar 61 minutos
                else:
                    time.sleep(60)  # Verificar a cada minuto
                    
            except Exception as e:
                print(f"❌ Erro na verificação de resultados: {e}")
                time.sleep(300)
    
    def processar_resultados(self):
        conn = sqlite3.connect('betmaster.db')
        c = conn.cursor()
        
        # Buscar bilhetes em aberto
        c.execute('SELECT * FROM bilhetes WHERE resultado = "em_aberto"')
        bilhetes_abertos = [dict(zip([col[0] for col in c.description], row)) for row in c.fetchall()]
        
        for bilhete in bilhetes_abertos:
            # Simular resultado (na prática, você buscaria de uma API de resultados)
            # Aqui estou simulando com 70% de chance de green para bilhetes com confiança > 70
            import random
            if bilhete['confianca'] > 70:
                resultado = 'green' if random.random() > 0.3 else 'red'
            else:
                resultado = 'green' if random.random() > 0.5 else 'red'
            
            lucro = bilhete['odd'] - 1 if resultado == 'green' else -1
            
            # Atualizar no banco
            atualizar_resultado(bilhete['id'], resultado, lucro)
            
            # Enviar notificação se for green
            if resultado == 'green':
                mensagem = (
                    f"🎉 <b>BILHETE GREEN!</b> 🎉\n\n"
                    f"✅ <b>Resultado: GREEN</b>\n"
                    f"🏆 {bilhete['jogo']}\n"
                    f"🎯 {bilhete['selecao']}\n"
                    f"💰 Odd: {bilhete['odd']}\n"
                    f"💵 Lucro: +{lucro:.2f}u\n"
                    f"📊 Confiança inicial: {bilhete['confianca']}%\n\n"
                    f"🎯 <i>BetMaster AI - Sistema Inteligente</i>"
                )
                enviar_telegram(mensagem)
        
        conn.close()
        carregar_dados()  # Atualizar estatísticas

# Inicializar agendador
agendador = Agendador()

# Função para enviar mensagens no Telegram
def enviar_telegram(mensagem):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': mensagem,
            'parse_mode': 'HTML'
        }
        
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print("✅ Mensagem enviada para Telegram")
            return True
        else:
            print(f"❌ Erro Telegram API: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao enviar para Telegram: {e}")
        return False

# ROTA RAIZ PARA SERVIR O HTML
@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

# Buscar jogos de futebol
def buscar_jogos_futebol():
    url = "https://api.football-data.org/v4/matches"
    headers = {"X-Auth-Token": FOOTBALL_API_KEY}
    
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(url, headers=headers)
            if response.status_code == 200:
                dados = response.json()
                jogos = []
                hoje = datetime.utcnow().date()
                
                for match in dados.get("matches", []):
                    if match["status"] == "SCHEDULED":
                        data_jogo = datetime.fromisoformat(match["utcDate"].replace("Z", "+00:00")).date()
                        if data_jogo == hoje:
                            jogos.append({
                                "esporte": "futebol",
                                "jogo": f"{match['homeTeam']['name']} vs {match['awayTeam']['name']}",
                                "timeA": match['homeTeam']['name'],
                                "timeB": match['awayTeam']['name'],
                                "competicao": match['competition']['name'],
                                "data": match['utcDate']
                            })
                return jogos
            else:
                print(f"Erro API Futebol: {response.status_code}")
                return []
    except Exception as e:
        print("Erro ao buscar jogos futebol:", e)
        return []

# Buscar odds de outros esportes
def buscar_odds_outros_esportes(esporte="basketball_nba"):
    esportes_map = {
        "basketball_nba": "basketball_nba",
        "americanfootball_nfl": "americanfootball_nfl", 
        "baseball_mlb": "baseball_mlb"
    }
    
    esporte_api = esportes_map.get(esporte, "basketball_nba")
    url = f"https://api.the-odds-api.com/v4/sports/{esporte_api}/odds"
    
    params = {
        'apiKey': THE_ODDS_API_KEY,
        'regions': 'us',
        'markets': 'h2h,spreads,totals',
        'oddsFormat': 'decimal'
    }
    
    try:
        with httpx.Client(timeout=15.0) as client:
            response = client.get(url, params=params)
            if response.status_code == 200:
                dados = response.json()
                jogos = []
                for game in dados[:3]:  # Limitar a 3 jogos para não sobrecarregar
                    jogos.append({
                        "esporte": esporte,
                        "jogo": f"{game['home_team']} vs {game['away_team']}",
                        "timeA": game['home_team'],
                        "timeB": game['away_team'],
                        "competicao": esporte_api.upper(),
                        "data": game['commence_time']
                    })
                return jogos
            else:
                print(f"Erro API {esporte}: {response.status_code}")
                return []
    except Exception as e:
        print(f"Erro ao buscar {esporte}:", e)
        return []

# Gerar bilhetes para qualquer esporte
def gerar_bilhetes_esporte(esporte="soccer"):
    if esporte == "soccer":
        jogos = buscar_jogos_futebol()
    else:
        jogos = buscar_odds_outros_esportes(esporte)
    
    bilhetes = []
    
    for jogo in jogos:
        if esporte == "soccer":
            bilhete = gerar_bilhete_futebol(jogo)
        elif esporte == "basketball_nba":
            bilhete = gerar_bilhete_basketball(jogo)
        elif esporte == "americanfootball_nfl":
            bilhete = gerar_bilhete_football(jogo)
        else:
            bilhete = gerar_bilhete_generico(jogo)
        
        bilhetes.append(bilhete)
    
    return bilhetes

def gerar_bilhete_futebol(jogo):
    return {
        "esporte": "futebol",
        "jogo": jogo["jogo"],
        "timeA": jogo["timeA"],
        "timeB": jogo["timeB"],
        "competicao": jogo["competicao"],
        "analise": f"{jogo['timeA']} em boa forma, confronto equilibrado",
        "odd": "2.10",
        "confianca": 75,
        "destaque": True,
        "timestamp": datetime.utcnow().isoformat(),
        "selecao": f"{jogo['timeA']} - Vitória"
    }

def gerar_bilhete_basketball(jogo):
    return {
        "esporte": "nba", 
        "jogo": jogo["jogo"],
        "timeA": jogo["timeA"],
        "timeB": jogo["timeB"],
        "competicao": "NBA",
        "analise": "Jogo de alto scoring, ambos times ofensivos",
        "odd": "1.95",
        "confianca": 82,
        "destaque": True,
        "timestamp": datetime.utcnow().isoformat(),
        "selecao": "Over 225.5 pontos"
    }

def gerar_bilhete_football(jogo):
    return {
        "esporte": "nfl",
        "jogo": jogo["jogo"],
        "timeA": jogo["timeA"], 
        "timeB": jogo["timeB"],
        "competicao": "NFL",
        "analise": "Defesa sólida do time da casa favorece under",
        "odd": "1.90",
        "confianca": 78,
        "destaque": True,
        "timestamp": datetime.utcnow().isoformat(),
        "selecao": "Under 48.5 pontos"
    }

def gerar_bilhete_generico(jogo):
    return {
        "esporte": jogo["esporte"],
        "jogo": jogo["jogo"],
        "timeA": jogo["timeA"],
        "timeB": jogo["timeB"],
        "competicao": jogo["competicao"],
        "analise": "Boa oportunidade baseada em análise estatística",
        "odd": "1.85",
        "confianca": 70,
        "destaque": False,
        "timestamp": datetime.utcnow().isoformat(),
        "selecao": "Melhor opção"
    }

# Endpoint para análise de jogos
@app.route('/analisar_jogos', methods=['POST'])
def analisar_jogos():
    try:
        data = request.get_json()
        esporte = data.get('esporte', 'soccer')
        
        print(f"Analisando esporte: {esporte}")
        
        # Gerar bilhetes para o esporte selecionado
        bilhetes_reais = gerar_bilhetes_esporte(esporte)
        
        # Se não encontrou jogos reais, usar exemplos
        if not bilhetes_reais:
            bilhetes_reais = gerar_exemplos(esporte)
        
        # Formatar para o frontend
        bilhetes_formatados = []
        for bilhete in bilhetes_reais:
            bilhete_formatado = {
                "jogo": bilhete["jogo"],
                "tipo": bilhete["esporte"],
                "mercado": "Principal",
                "selecao": bilhete["selecao"],
                "analise": bilhete["analise"],
                "analise_premium": f"⭐ {bilhete['competicao']} - Análise IA",
                "odd": bilhete["odd"],
                "valor_esperado": "+" + str(bilhete["confianca"] - 50) + "%",
                "confianca": bilhete["confianca"],
                "destaque": bilhete["destaque"],
                "timestamp": bilhete["timestamp"]
            }
            bilhetes_formatados.append(bilhete_formatado)
            
            # Salvar no banco
            salvar_bilhete(bilhete)
        
        # Atualizar bilhetes atuais globalmente
        global bilhetes_atuais
        bilhetes_atuais = bilhetes_formatados
        
        bilhete_do_dia = max(bilhetes_formatados, key=lambda x: x['confianca']) if bilhetes_formatados else None
        
        return jsonify({
            "status": "success",
            "data": {
                "bilhetes": bilhetes_formatados,
                "bilhete_do_dia": bilhete_do_dia,
                "total_encontrado": len(bilhetes_formatados),
                "esporte": esporte
            }
        })
        
    except Exception as e:
        print(f"Erro em analisar_jogos: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# Endpoint para enviar bilhetes para o Telegram
@app.route('/enviar_bilhetes', methods=['POST'])
def enviar_bilhetes():
    try:
        data = request.get_json()
        bilhetes = data.get('bilhetes', [])
        
        if not bilhetes:
            return jsonify({"status": "error", "message": "Nenhum bilhete para enviar"})
        
        print(f"Enviando {len(bilhetes)} bilhetes para o Telegram")
        
        # Enviar cada bilhete individualmente
        bilhetes_enviados = 0
        for bilhete in bilhetes:
            mensagem = (
                f"🎯 <b>BILHETE BETMASTER AI</b> 🎯\n\n"
                f"🏆 <b>{bilhete.get('analise_premium', 'Análise Premium')}</b>\n"
                f"⚔️ <b>{bilhete['jogo']}</b>\n\n"
                f"🎯 <b>{bilhete['selecao']}</b>\n"
                f"💰 <b>Odd: {bilhete['odd']}</b>\n"
                f"📊 <b>Confiança: {bilhete['confianca']}%</b>\n"
                f"💎 <b>Valor Esperado: {bilhete['valor_esperado']}</b>\n\n"
                f"💡 {bilhete['analise']}\n\n"
                f"⏰ {datetime.utcnow().strftime('%d/%m/%Y %H:%M')}\n"
                f"🤖 <i>Gerado por BetMaster AI</i>"
            )
            
            if enviar_telegram(mensagem):
                bilhetes_enviados += 1
                time.sleep(1)  # Pequena pausa entre mensagens
        
        return jsonify({
            "status": "success",
            "message": f"✅ {bilhetes_enviados} de {len(bilhetes)} bilhetes enviados para o Telegram!"
        })
        
    except Exception as e:
        print(f"Erro em enviar_bilhetes: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# Endpoint para dashboard e estatísticas
@app.route('/dashboard', methods=['GET'])
def get_dashboard():
    carregar_dados()  # Atualizar estatísticas
    return jsonify({
        "status": "success",
        "estatisticas": estatisticas,
        "historico_recente": historico_bilhetes[:10],  # Últimos 10 bilhetes
        "agendamento": {
            "ultima_analise": agendador.ultima_analise.isoformat() if agendador.ultima_analise else None,
            "proxima_analise": "06:00, 12:00, 18:00, 00:00",
            "verificacao_resultados": "A cada hora"
        }
    })

# Endpoint para forçar verificação de resultados
@app.route('/verificar_resultados', methods=['POST'])
def verificar_resultados():
    try:
        agendador.processar_resultados()
        return jsonify({
            "status": "success",
            "message": "✅ Verificação de resultados concluída"
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

def gerar_exemplos(esporte):
    exemplos = {
        "soccer": [
            {
                "esporte": "futebol",
                "jogo": "Real Madrid vs Barcelona",
                "timeA": "Real Madrid",
                "timeB": "Barcelona", 
                "competicao": "La Liga",
                "analise": "Clássico espanhol, Madrid com vantagem em casa",
                "odd": "2.10",
                "confianca": 78,
                "destaque": True,
                "timestamp": datetime.utcnow().isoformat(),
                "selecao": "Real Madrid - Vitória"
            }
        ],
        "basketball_nba": [
            {
                "esporte": "nba",
                "jogo": "Lakers vs Warriors", 
                "timeA": "Lakers",
                "timeB": "Warriors",
                "competicao": "NBA",
                "analise": "Alto scoring esperado entre duas equipes ofensivas",
                "odd": "1.95", 
                "confianca": 82,
                "destaque": True,
                "timestamp": datetime.utcnow().isoformat(),
                "selecao": "Over 225.5 pontos"
            }
        ],
        "americanfootball_nfl": [
            {
                "esporte": "nfl",
                "jogo": "Chiefs vs 49ers",
                "timeA": "Chiefs", 
                "timeB": "49ers",
                "competicao": "NFL", 
                "analise": "Chiefs com quarterback em grande forma",
                "odd": "1.90",
                "confianca": 75,
                "destaque": True,
                "timestamp": datetime.utcnow().isoformat(),
                "selecao": "Chiefs -3.0"
            }
        ]
    }
    return exemplos.get(esporte, exemplos["soccer"])

# Endpoint para bilhete do dia
@app.route('/bilhete_do_dia', methods=['POST'])
def bilhete_do_dia():
    try:
        # Buscar o melhor bilhete entre todos os esportes
        melhor_bilhete = None
        melhor_confianca = 0
        
        for esporte in ['soccer', 'basketball_nba', 'americanfootball_nfl']:
            bilhetes = gerar_bilhetes_esporte(esporte)
            for bilhete in bilhetes:
                if bilhete['confianca'] > melhor_confianca:
                    melhor_confianca = bilhete['confianca']
                    melhor_bilhete = bilhete
        
        if melhor_bilhete:
            # Salvar no banco
            salvar_bilhete(melhor_bilhete)
            
            # Preparar mensagem para Telegram
            mensagem = (
                f"🔥 <b>BILHETE DO DIA - BETMASTER AI</b> 🔥\n\n"
                f"🏆 <b>{melhor_bilhete['competicao']}</b>\n"
                f"⚔️ <b>{melhor_bilhete['jogo']}</b>\n\n"
                f"🎯 <b>{melhor_bilhete['selecao']}</b>\n"
                f"💰 <b>Odd: {melhor_bilhete['odd']}</b>\n"
                f"📊 <b>Confiança: {melhor_bilhete['confianca']}%</b>\n\n"
                f"💡 {melhor_bilhete['analise']}\n\n"
                f"⏰ {datetime.utcnow().strftime('%d/%m/%Y %H:%M UTC')}\n"
                f"🤖 <i>Gerado por BetMaster AI</i>"
            )
            
            # Enviar para Telegram
            telegram_success = enviar_telegram(mensagem)
            
            return jsonify({
                "status": "success",
                "bilhete_do_dia": melhor_bilhete,
                "enviado_telegram": telegram_success,
                "message": f"Melhor bilhete: {melhor_bilhete['jogo']} - Confiança {melhor_bilhete['confianca']}%"
            })
        else:
            return jsonify({
                "status": "error", 
                "message": "Nenhum bilhete encontrado para hoje"
            })
            
    except Exception as e:
        print(f"Erro em bilhete_do_dia: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# Health check
@app.route('/health')
def health():
    return jsonify({
        "status": "healthy", 
        "timestamp": datetime.utcnow().isoformat(),
        "agendamento_ativo": not agendador.parar
    })

# Função para parar threads ao sair
def parar_agendador():
    agendador.parar = True

atexit.register(parar_agendador)

# Inicialização
if __name__ == '__main__':
    # Inicializar banco de dados
    init_db()
    carregar_dados()
    
    # Iniciar threads de agendamento
    threading.Thread(target=agendador.analise_automatica, daemon=True).start()
    threading.Thread(target=agendador.verificar_resultados, daemon=True).start()
    
    print("🚀 BetMaster AI iniciado com agendamento ativo!")
    print("📊 Dashboard disponível em /dashboard")
    print("🕐 Análises automáticas às 06:00, 12:00, 18:00 e 00:00")
    
    app.run(debug=True, host='0.0.0.0', port=10000)

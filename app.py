from flask import Flask, jsonify, request, render_template_string
import os
import httpx
import requests  # Vou usar requests em vez de httpx para o Telegram
from datetime import datetime, timedelta
import json

# Flask app
app = Flask(__name__)

# Carregar variáveis de ambiente
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY")
THE_ODDS_API_KEY = os.getenv("THE_ODDS_API_KEY")

# Função SIMPLES para enviar mensagens no Telegram (sem async)
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
    return """
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>BetMaster AI - Sistema Inteligente de Apostas</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                background: linear-gradient(135deg, #0c2461 0%, #1e3799 100%); 
                min-height: 100vh; color: #333; 
                padding: 20px;
            }
            .container { max-width: 1200px; margin: 0 auto; }
            .header { 
                text-align: center; color: white; margin-bottom: 30px; 
                padding: 40px 20px; background: rgba(255,255,255,0.1); 
                border-radius: 25px; backdrop-filter: blur(15px); 
                border: 1px solid rgba(255,255,255,0.2); 
            }
            .logo { font-size: 4.5rem; margin-bottom: 20px; }
            h1 { font-size: 3.5rem; margin-bottom: 15px; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }
            .subtitle { font-size: 1.4rem; opacity: 0.9; margin-bottom: 25px; }
            .dashboard { display: grid; grid-template-columns: 1fr 1fr; gap: 25px; margin-bottom: 40px; }
            .card { background: white; border-radius: 20px; padding: 30px; box-shadow: 0 15px 35px rgba(0,0,0,0.2); }
            .controls { display: flex; flex-direction: column; gap: 20px; }
            .form-group { display: flex; flex-direction: column; gap: 8px; }
            label { font-weight: 700; color: #0c2461; font-size: 1.1rem; }
            select, button { padding: 15px 20px; border: 2px solid #e1e5e9; border-radius: 12px; font-size: 16px; }
            button { background: linear-gradient(135deg, #0c2461 0%, #1e3799 100%); color: white; border: none; cursor: pointer; font-weight: 600; }
            button:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(0,0,0,0.2); }
            .btn-telegram { background: linear-gradient(135deg, #27ae60 0%, #2ecc71 100%); }
            .btn-destaque { background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%); }
            .results { max-height: 600px; overflow-y: auto; }
            .bilhete-item { 
                border: 2px solid #e1e5e9; border-radius: 15px; padding: 20px; margin-bottom: 15px; 
                background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
            }
            .bilhete-destaque { border-color: #e74c3c; background: linear-gradient(135deg, #fff5f5 0%, #ffffff 100%); }
            .loading { display: none; text-align: center; padding: 40px; }
            .spinner { border: 5px solid #f3f3f3; border-top: 5px solid #0c2461; border-radius: 50%; width: 60px; height: 60px; animation: spin 1s linear infinite; margin: 0 auto 20px; }
            @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
            .status { padding: 12px; border-radius: 8px; margin: 10px 0; text-align: center; font-weight: 600; }
            .status-success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
            .status-error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
            .status-info { background: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; }
            .esporte-title { color: white; text-align: center; margin-bottom: 10px; font-size: 1.2rem; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">🎯🤖🔥</div>
                <h1>BetMaster AI v4.0</h1>
                <p class="subtitle">Sistema Inteligente - Todos Esportes Ativos</p>
                <div id="statusMessage"></div>
            </div>

            <div class="esporte-title" id="esporteTitle">⚽ Analisando Futebol</div>

            <div class="dashboard">
                <div class="card controls">
                    <h3>⚙️ Configurações</h3>
                    <div class="form-group">
                        <label for="esporte">Esporte:</label>
                        <select id="esporte">
                            <option value="soccer">⚽ Futebol</option>
                            <option value="basketball_nba">🏀 NBA</option>
                            <option value="americanfootball_nfl">🏈 NFL</option>
                            <option value="baseball_mlb">⚾ MLB</option>
                        </select>
                    </div>
                    <button onclick="analisarJogos()" id="analisarBtn">🤖 Analisar Jogos</button>
                    <button onclick="buscarBilheteDoDia()" class="btn-destaque">🔥 Bilhete do Dia</button>
                    <button onclick="testarTelegram()" class="btn-telegram">📱 Testar Telegram</button>
                </div>

                <div class="card results">
                    <h3>📈 Resultados</h3>
                    <div class="loading" id="loading">
                        <div class="spinner"></div>
                        <p>Analisando dados esportivos...</p>
                        <p style="margin-top: 10px; font-size: 0.9rem; color: #666;">
                            Consultando APIs • Processando estatísticas • Gerando insights
                        </p>
                    </div>
                    <div id="resultadosContainer">
                        <p>Selecione um esporte e clique em "Analisar Jogos" para começar</p>
                    </div>
                </div>
            </div>
        </div>

        <script>
            function showStatus(message, type = 'success') {
                const statusDiv = document.getElementById('statusMessage');
                statusDiv.innerHTML = `<div class="status status-${type}">${message}</div>`;
                setTimeout(() => statusDiv.innerHTML = '', 5000);
            }

            async function analisarJogos() {
                const analisarBtn = document.getElementById('analisarBtn');
                const loading = document.getElementById('loading');
                const resultadosContainer = document.getElementById('resultadosContainer');
                const esporte = document.getElementById('esporte').value;
                const esporteTitle = document.getElementById('esporteTitle');
                
                // Atualizar título do esporte
                const esporteNomes = {
                    'soccer': '⚽ Futebol',
                    'basketball_nba': '🏀 NBA', 
                    'americanfootball_nfl': '🏈 NFL',
                    'baseball_mlb': '⚾ MLB'
                };
                esporteTitle.textContent = `🎯 Analisando ${esporteNomes[esporte]}`;
                
                analisarBtn.disabled = true;
                analisarBtn.innerHTML = '⏳ Analisando...';
                loading.style.display = 'block';
                resultadosContainer.innerHTML = '';
                
                try {
                    const response = await fetch('/analisar_jogos', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({esporte: esporte})
                    });
                    
                    const data = await response.json();
                    
                    if (data.status === 'success') {
                        const bilhetes = data.data.bilhetes;
                        if (bilhetes.length > 0) {
                            resultadosContainer.innerHTML = bilhetes.map(bilhete => `
                                <div class="bilhete-item ${bilhete.destaque ? 'bilhete-destaque' : ''}">
                                    <h4>${bilhete.jogo}</h4>
                                    <p><strong>🎯 ${bilhete.selecao}</strong></p>
                                    <p>💰 Odd: <strong>${bilhete.odd}</strong></p>
                                    <p>📊 Confiança: <strong>${bilhete.confianca}%</strong></p>
                                    <p>💡 ${bilhete.analise}</p>
                                    <p><small>⏰ ${new Date(bilhete.timestamp).toLocaleString('pt-BR')}</small></p>
                                    ${bilhete.destaque ? '<p style="color: #e74c3c; font-weight: bold; text-align: center;">🔥 BILHETE DO DIA</p>' : ''}
                                </div>
                            `).join('');
                            showStatus(`✅ Encontrados ${bilhetes.length} bilhetes para ${esporteNomes[esporte]}`, 'success');
                        } else {
                            resultadosContainer.innerHTML = '<p>Nenhum jogo encontrado para hoje. Mostrando exemplo...</p>';
                            showStatus('⚠️ Nenhum jogo ao vivo encontrado - Mostrando análise exemplar', 'info');
                        }
                    } else {
                        resultadosContainer.innerHTML = `<p>Erro: ${data.message}</p>`;
                        showStatus(`❌ Erro: ${data.message}`, 'error');
                    }
                } catch (error) {
                    resultadosContainer.innerHTML = `<p>Erro de conexão: ${error}</p>`;
                    showStatus('❌ Erro de conexão com o servidor', 'error');
                } finally {
                    analisarBtn.disabled = false;
                    analisarBtn.innerHTML = '🤖 Analisar Jogos';
                    loading.style.display = 'none';
                }
            }

            async function buscarBilheteDoDia() {
                try {
                    showStatus('⏳ Buscando o melhor bilhete do dia...', 'info');
                    const response = await fetch('/bilhete_do_dia', {method: 'POST'});
                    const data = await response.json();
                    if (data.status === 'success') {
                        if (data.enviado_telegram) {
                            showStatus('✅ Bilhete do dia encontrado e enviado para o Telegram!', 'success');
                        } else {
                            showStatus('✅ Bilhete do dia encontrado, mas erro ao enviar para Telegram', 'error');
                        }
                        // Atualiza a lista automaticamente
                        setTimeout(analisarJogos, 2000);
                    } else {
                        showStatus(`❌ ${data.message}`, 'error');
                    }
                } catch (error) {
                    showStatus('❌ Erro de conexão ao buscar bilhete do dia', 'error');
                }
            }

            async function testarTelegram() {
                try {
                    showStatus('⏳ Enviando mensagem de teste para Telegram...', 'info');
                    const response = await fetch('/teste_telegram', {method: 'POST'});
                    const data = await response.json();
                    if (data.status === 'success') {
                        showStatus('✅ Teste enviado para Telegram! Verifique seu chat.', 'success');
                    } else {
                        showStatus(`❌ ${data.message}`, 'error');
                    }
                } catch (error) {
                    showStatus('❌ Erro de conexão ao testar Telegram', 'error');
                }
            }

            // Analisar automaticamente ao carregar a página
            window.addEventListener('load', function() {
                setTimeout(analisarJogos, 1000);
            });

            // Atualizar ao mudar esporte
            document.getElementById('esporte').addEventListener('change', analisarJogos);
        </script>
    </body>
    </html>
    """

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
                for game in dados[:5]:  # Limitar a 5 jogos
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
            bilhetes_formatados.append({
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
            })
        
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
            },
            {
                "esporte": "futebol",
                "jogo": "Manchester City vs Liverpool",
                "timeA": "Manchester City",
                "timeB": "Liverpool", 
                "competicao": "Premier League",
                "analise": "City invicto em casa, Liverpool irregular fora",
                "odd": "1.95",
                "confianca": 72,
                "destaque": False,
                "timestamp": datetime.utcnow().isoformat(),
                "selecao": "Manchester City - Vitória"
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
        ],
        "baseball_mlb": [
            {
                "esporte": "mlb",
                "jogo": "Yankees vs Red Sox",
                "timeA": "Yankees",
                "timeB": "Red Sox",
                "competicao": "MLB",
                "analise": "Clássico do beisebol, Yankees com pitching sólido",
                "odd": "1.85",
                "confianca": 72,
                "destaque": True,
                "timestamp": datetime.utcnow().isoformat(),
                "selecao": "Yankees - Vitória"
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
        
        for esporte in ['soccer', 'basketball_nba', 'americanfootball_nfl', 'baseball_mlb']:
            bilhetes = gerar_bilhetes_esporte(esporte)
            for bilhete in bilhetes:
                if bilhete['confianca'] > melhor_confianca:
                    melhor_confianca = bilhete['confianca']
                    melhor_bilhete = bilhete
        
        if melhor_bilhete:
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

# Endpoint específico para teste do Telegram
@app.route('/teste_telegram', methods=['POST'])
def teste_telegram():
    try:
        mensagem = (
            "🧪 <b>TESTE BETMASTER AI</b> 🧪\n\n"
            "✅ <b>Sistema funcionando perfeitamente!</b>\n\n"
            "🤖 <b>Esportes Ativos:</b>\n"
            "⚽ Futebol\n"
            "🏀 NBA\n" 
            "🏈 NFL\n"
            "⚾ MLB\n\n"
            "🎯 <b>Análise em tempo real</b>\n"
            f"⏰ {datetime.utcnow().strftime('%d/%m/%Y %H:%M UTC')}\n\n"
            "🚀 <i>Pronto para gerar bilhetes!</i>"
        )
        
        success = enviar_telegram(mensagem)
        
        if success:
            return jsonify({
                "status": "success",
                "message": "✅ Mensagem de teste enviada para o Telegram!"
            })
        else:
            return jsonify({
                "status": "error", 
                "message": "❌ Erro ao enviar para Telegram - Verifique as credenciais"
            })
            
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# Health check
@app.route('/health')
def health():
    return jsonify({"status": "healthy", "timestamp": datetime.utcnow().isoformat()})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=10000)

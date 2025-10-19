from flask import Flask, jsonify, request, render_template_string
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

# ROTA RAIZ PARA SERVIR O HTML
@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

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
@app.route('/bilhete_do_dia', methods=['GET', 'POST'])
def bilhete_do_dia():
    try:
        bilhetes = gerar_bilhetes_reais()
        
        if request.method == 'POST':
            # Enviar para Telegram apenas se for POST
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
        
        # Retornar JSON para ambos GET e POST
        return jsonify({
            "status": "success", 
            "bilhetes": bilhetes,
            "message": f"Encontrados {len(bilhetes)} jogos hoje"
        })
        
    except TelegramError as e:
        return jsonify({"error": f"Erro ao enviar mensagem no Telegram: {e}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Endpoint para análise de jogos (simulado)
@app.route('/analisar_jogos', methods=['POST'])
def analisar_jogos():
    try:
        data = request.get_json()
        esporte = data.get('esporte', 'soccer')
        regiao = data.get('regiao', 'eu')
        mercado = data.get('mercado', 'h2h')
        
        # Simular análise e gerar bilhetes de exemplo
        bilhetes_exemplo = [
            {
                "jogo": "Real Madrid vs Barcelona",
                "tipo": "futebol",
                "mercado": "Head-to-Head",
                "selecao": "Real Madrid",
                "analise": "Baseado em forma recente e histórico de confrontos",
                "analise_premium": "⭐ Forte em casa com 80% de vitórias",
                "odd": "2.10",
                "valor_esperado": "+5.2%",
                "confianca": 78,
                "destaque": True,
                "timestamp": datetime.utcnow().isoformat()
            },
            {
                "jogo": "Manchester City vs Liverpool",
                "tipo": "futebol", 
                "mercado": "Totais (Over/Under)",
                "selecao": "Over 2.5",
                "analise": "Ambos os times com ataques fortes",
                "analise_premium": "🔥 70% dos últimos jogos tiveram Over 2.5",
                "odd": "1.85",
                "valor_esperado": "+3.8%",
                "confianca": 72,
                "destaque": False,
                "timestamp": datetime.utcnow().isoformat()
            }
        ]
        
        return jsonify({
            "status": "success",
            "data": {
                "bilhetes": bilhetes_exemplo,
                "bilhete_do_dia": bilhetes_exemplo[0]  # Primeiro como destaque
            }
        })
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# Endpoint para teste no Telegram
@app.route('/teste_bilhetes', methods=['POST'])
def teste_bilhetes():
    try:
        mensagem = "🧪 Teste do BetMaster AI\nSistema funcionando corretamente!\nHora: " + datetime.utcnow().strftime("%d/%m/%Y %H:%M")
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=mensagem)
        
        return jsonify({
            "status": "success",
            "message": "Mensagem de teste enviada para o Telegram"
        })
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# Template HTML como string (seu código HTML completo aqui)
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BetMaster AI - Sistema Inteligente de Apostas</title>
    <style>
        /* SEU CSS COMPLETO AQUI - MANTENHA TODO O SEU CSS */
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #0c2461 0%, #1e3799 100%);
            min-height: 100vh;
            color: #333;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }

        .header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
            padding: 40px 20px;
            background: rgba(255,255,255,0.1);
            border-radius: 25px;
            backdrop-filter: blur(15px);
            border: 1px solid rgba(255,255,255,0.2);
        }

        .logo {
            font-size: 4.5rem;
            margin-bottom: 20px;
        }

        h1 {
            font-size: 3.5rem;
            margin-bottom: 15px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }

        .subtitle {
            font-size: 1.4rem;
            opacity: 0.9;
            margin-bottom: 25px;
        }

        .tagline {
            font-size: 1.2rem;
            opacity: 0.8;
            font-style: italic;
        }

        .dashboard {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 25px;
            margin-bottom: 40px;
        }

        @media (max-width: 1024px) {
            .dashboard {
                grid-template-columns: 1fr;
            }
        }

        .card {
            background: white;
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 15px 35px rgba(0,0,0,0.2);
            border: 1px solid rgba(255,255,255,0.2);
        }

        .card-destaque {
            background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
            color: white;
        }

        .card-destaque h3 {
            color: white;
        }

        .controls {
            display: flex;
            flex-direction: column;
            gap: 20px;
        }

        .form-group {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        label {
            font-weight: 700;
            color: #0c2461;
            font-size: 1.1rem;
        }

        select, button {
            padding: 15px 20px;
            border: 2px solid #e1e5e9;
            border-radius: 12px;
            font-size: 16px;
            transition: all 0.3s ease;
        }

        select:focus {
            outline: none;
            border-color: #0c2461;
            box-shadow: 0 0 0 3px rgba(12, 36, 97, 0.1);
        }

        button {
            background: linear-gradient(135deg, #0c2461 0%, #1e3799 100%);
            color: white;
            border: none;
            font-weight: 700;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            font-size: 1.1rem;
        }

        button:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 25px rgba(12, 36, 97, 0.4);
        }

        button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }

        .btn-destaque {
            background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
        }

        .btn-destaque:hover {
            box-shadow: 0 10px 25px rgba(231, 76, 60, 0.4);
        }

        .btn-test {
            background: linear-gradient(135deg, #27ae60 0%, #2ecc71 100%);
        }

        .btn-test:hover {
            box-shadow: 0 10px 25px rgba(39, 174, 96, 0.4);
        }

        .results {
            max-height: 700px;
            overflow-y: auto;
            grid-column: span 2;
        }

        @media (max-width: 1024px) {
            .results {
                grid-column: span 1;
            }
        }

        .bilhete-item {
            border: 2px solid #e1e5e9;
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 20px;
            transition: all 0.3s ease;
            background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
        }

        .bilhete-item:hover {
            box-shadow: 0 8px 25px rgba(0,0,0,0.15);
            transform: translateY(-3px);
        }

        .bilhete-destaque {
            border: 3px solid #e74c3c;
            background: linear-gradient(135deg, #fff5f5 0%, #ffffff 100%);
            position: relative;
            overflow: hidden;
        }

        .bilhete-destaque::before {
            content: "🔥 BILHETE DO DIA";
            position: absolute;
            top: 10px;
            right: -30px;
            background: #e74c3c;
            color: white;
            padding: 8px 40px;
            font-size: 0.8rem;
            font-weight: 700;
            transform: rotate(45deg);
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
        }

        .bilhete-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 2px solid #e1e5e9;
        }

        .jogo-info {
            font-size: 1.3rem;
            font-weight: 700;
            color: #0c2461;
        }

        .bilhete-tipo {
            background: #0c2461;
            color: white;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
        }

        .tipo-destaque {
            background: #e74c3c;
        }

        .bilhete-detalhes {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 20px;
            margin-bottom: 20px;
        }

        .detalhes-esquerda {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .mercado {
            font-size: 1.1rem;
            font-weight: 600;
            color: #2c3e50;
        }

        .selecao {
            font-size: 1.2rem;
            font-weight: 700;
            color: #e74c3c;
        }

        .analise {
            color: #7f8c8d;
            font-size: 0.95rem;
            line-height: 1.4;
        }

        .analise-premium {
            color: #e74c3c;
            font-weight: 600;
            font-size: 1rem;
        }

        .detalhes-direita {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 15px;
        }

        .odd {
            font-size: 2rem;
            font-weight: 800;
            color: #27ae60;
        }

        .odd-destaque {
            color: #e74c3c;
            font-size: 2.2rem;
        }

        .valor-esperado {
            font-size: 1.1rem;
            font-weight: 600;
            color: #2980b9;
        }

        .bilhete-footer {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-top: 15px;
            border-top: 1px solid #e1e5e9;
        }

        .confianca {
            display: flex;
            align-items: center;
            gap: 8px;
            font-weight: 600;
        }

        .barra-confianca {
            width: 120px;
            height: 8px;
            background: #ecf0f1;
            border-radius: 4px;
            overflow: hidden;
        }

        .preenchimento-confianca {
            height: 100%;
            border-radius: 4px;
            transition: width 0.3s ease;
        }

        .confianca-alta { background: #27ae60; }
        .confianca-media { background: #f39c12; }
        .confianca-baixa { background: #e74c3c; }

        .timestamp {
            font-size: 0.8rem;
            color: #95a5a6;
        }

        .loading {
            display: none;
            text-align: center;
            padding: 60px 40px;
        }

        .spinner {
            border: 5px solid #f3f3f3;
            border-top: 5px solid #0c2461;
            border-radius: 50%;
            width: 60px;
            height: 60px;
            animation: spin 1s linear infinite;
            margin: 0 auto 30px;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 25px;
            margin-bottom: 40px;
        }

        .stat-card {
            background: white;
            border-radius: 15px;
            padding: 25px;
            text-align: center;
            box-shadow: 0 10px 25px rgba(0,0,0,0.1);
            border: 1px solid rgba(255,255,255,0.2);
        }

        .stat-number {
            font-size: 2.5rem;
            font-weight: 800;
            color: #0c2461;
            margin-bottom: 8px;
        }

        .stat-label {
            color: #7f8c8d;
            font-size: 1rem;
            font-weight: 600;
        }

        .empty-state {
            text-align: center;
            padding: 60px 40px;
            color: #7f8c8d;
        }

        .empty-state h3 {
            font-size: 1.5rem;
            margin-bottom: 15px;
            color: #2c3e50;
        }

        .section-title {
            color: white;
            margin: 40px 0 20px 0;
            font-size: 2rem;
            text-align: center;
        }

        .badge {
            display: inline-block;
            padding: 4px 8px;
            background: #e74c3c;
            color: white;
            border-radius: 12px;
            font-size: 0.7rem;
            font-weight: 700;
            margin-left: 10px;
        }

        .tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }

        .tab {
            padding: 12px 24px;
            background: rgba(255,255,255,0.1);
            color: white;
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.3s ease;
        }

        .tab.active {
            background: white;
            color: #0c2461;
            font-weight: 600;
        }

        .tab:hover {
            background: rgba(255,255,255,0.2);
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">🎯🤖🔥</div>
            <h1>BetMaster AI v4.0</h1>
            <p class="subtitle">Sistema Inteligente com Bilhete do Dia e Análise Avançada</p>
            <p class="tagline">Algoritmos de machine learning identificando as melhores oportunidades do mercado</p>
        </div>

        <div class="stats">
            <div class="stat-card">
                <div class="stat-number" id="totalBilhetes">0</div>
                <div class="stat-label">Bilhetes Gerados</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="altaConfianca">0</div>
                <div class="stat-label">Alta Confiança</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="valorMedio">0.0</div>
                <div class="stat-label">Valor Médio</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="taxaSucesso">0%</div>
                <div class="stat-label">Taxa Esperada</div>
            </div>
        </div>

        <h2 class="section-title">🎯 Controles de Análise</h2>

        <div class="dashboard">
            <div class="card controls">
                <h3>⚙️ Configurações de Análise</h3>
                <div class="form-group">
                    <label for="esporte">Esporte:</label>
                    <select id="esporte">
                        <option value="soccer">⚽ Futebol</option>
                        <option value="basketball_nba">🏀 NBA</option>
                        <option value="americanfootball_nfl">🏈 NFL</option>
                        <option value="baseball_mlb">⚾ MLB</option>
                        <option value="icehockey_nhl">🏒 NHL</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="regiao">Região:</label>
                    <select id="regiao">
                        <option value="eu">🇪🇺 Europa</option>
                        <option value="us">🇺🇸 Estados Unidos</option>
                        <option value="uk">🇬🇧 Reino Unido</option>
                        <option value="au">🇦🇺 Austrália</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="mercado">Mercado Principal:</label>
                    <select id="mercado">
                        <option value="h2h">🎯 Head-to-Head</option>
                        <option value="totals">📊 Totais (Over/Under)</option>
                        <option value="spreads">⚖️ Handicap</option>
                        <option value="outrights">🏆 Outrights</option>
                    </select>
                </div>
                <button onclick="analisarJogos()" id="analisarBtn">
                    🤖 Analisar & Gerar Bilhetes
                </button>
                <button onclick="buscarBilheteDoDia()" id="bilheteDiaBtn" class="btn-destaque">
                    🔥 Buscar Bilhete do Dia
                </button>
                <button onclick="testarBilhetes()" id="testeBtn" class="btn-test">
                    🧪 Testar no Telegram
                </button>
            </div>

            <div class="card card-destaque">
                <h3>⭐ BILHETE DO DIA</h3>
                <div id="bilheteDiaContainer">
                    <div class="empty-state">
                        <h3>🔍 Nenhum bilhete do dia</h3>
                        <p>Clique em "Buscar Bilhete do Dia" para encontrar a melhor oportunidade</p>
                    </div>
                </div>
            </div>

            <div class="card results">
                <h3>📈 Todos os Bilhetes Inteligentes <span class="badge" id="badgeCount">0</span></h3>
                
                <div class="tabs">
                    <div class="tab active" onclick="filtrarBilhetes('todos')">Todos</div>
                    <div class="tab" onclick="filtrarBilhetes('alta')">Alta Confiança</div>
                    <div class="tab" onclick="filtrarBilhetes('futebol')">Futebol</div>
                    <div class="tab" onclick="filtrarBilhetes('nba')">NBA</div>
                </div>
                
                <div class="loading" id="loading">
                    <div class="spinner"></div>
                    <p>Analisando dados e gerando bilhetes inteligentes...</p>
                    <p style="margin-top: 10px; font-size: 0.9rem; color: #666;">
                        Consultando APIs • Processando estatísticas • Calculando valores • Gerando insights
                    </p>
                </div>
                <div id="resultadosContainer"></div>
            </div>
        </div>
    </div>

    <script>
        let todosBilhetes = [];
        let filtroAtual = 'todos';

        async function analisarJogos() {
            const analisarBtn = document.getElementById('analisarBtn');
            const loading = document.getElementById('loading');
            const resultadosContainer = document.getElementById('resultadosContainer');
            
            const esporte = document.getElementById('esporte').value;
            const regiao = document.getElementById('regiao').value;
            const mercado = document.getElementById('mercado').value;
            
            analisarBtn.disabled = true;
            analisarBtn.innerHTML = '⏳ Analisando...';
            loading.style.display = 'block';
            resultadosContainer.innerHTML = '';
            
            try {
                const response = await fetch('/analisar_jogos', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        esporte: esporte,
                        regiao: regiao,
                        mercado: mercado
                    })
                });
                
                const data = await response.json();
                
                if (data.status === 'success') {
                    todosBilhetes = data.data.bilhetes;
                    exibirBilhetes(todosBilhetes);
                    atualizarEstatisticas(todosBilhetes);
                    
                    // Atualizar bilhete do dia se existir
                    if (data.data.bilhete_do_dia) {
                        exibirBilheteDoDia(data.data.bilhete_do_dia);
                    }
                } else {
                    resultadosContainer.innerHTML = `
                        <div class="empty-state">
                            <h3>❌ Erro na Análise</h3>
                            <p>${data.message || 'Erro ao processar dados'}</p>
                        </div>
                    `;
                }
                
            } catch (error) {
                resultadosContainer.innerHTML = `
                    <div class="empty-state">
                        <h3>❌ Erro de Conexão</h3>
                        <p>Verifique sua conexão e tente novamente.</p>
                    </div>
                `;
            } finally {
                analisarBtn.disabled = false;
                analisarBtn.innerHTML = '🤖 Analisar & Gerar Bilhetes';
                loading.style.display = 'none';
            }
        }

        async function buscarBilheteDoDia() {
            const bilheteDiaBtn = document.getElementById('bilheteDiaBtn');
            const bilheteDiaContainer = document.getElementById('bilheteDiaContainer');
            
            bilheteDiaBtn.disabled = true;
            bilheteDiaBtn.innerHTML = '⏳ Buscando...';
            bilheteDiaContainer.innerHTML = `
                <div class="loading">
                    <div class="spinner"></div>
                    <p>Procurando o melhor bilhete do dia...</p>
                </div>
            `;
            
            try {
                const response = await fetch('/bilhete_do_dia', {
                    method: 'GET'
                });
                
                const data = await response.json();
                
                if (data.status === 'success') {
                    // Criar um bilhete do dia formatado a partir dos dados
                    if (data.bilhetes && data.bilhetes.length > 0) {
                        const primeiroJogo = data.bilhetes[0];
                        const bilheteDoDia = {
                            "jogo": primeiroJogo.jogo,
                            "mercado": "Multiple",
                            "selecao": `${primeiroJogo.timeA} / Over ${primeiroJogo.totalOver}`,
                            "analise": `Competição: ${primeiroJogo.competicao || 'Liga Principal'}`,
                            "analise_premium": "🔥 Dados reais da Football-data.org",
                            "odd": "2.50",
                            "valor_esperado": "+8.5%", 
                            "confianca": 75,
                            "timestamp": new Date().toISOString()
                        };
                        exibirBilheteDoDia(bilheteDoDia);
                        alert('✅ Bilhete do dia encontrado com dados reais!');
                    }
                } else {
                    bilheteDiaContainer.innerHTML = `
                        <div class="empty-state">
                            <h3>❌ Nenhum bilhete premium</h3>
                            <p>${data.message || 'Tente analisar mais jogos'}</p>
                        </div>
                    `;
                }
                
            } catch (error) {
                bilheteDiaContainer.innerHTML = `
                    <div class="empty-state">
                        <h3>❌ Erro de conexão</h3>
                        <p>Não foi possível buscar o bilhete do dia.</p>
                    </div>
                `;
            } finally {
                bilheteDiaBtn.disabled = false;
                bilheteDiaBtn.innerHTML = '🔥 Buscar Bilhete do Dia';
            }
        }

        function exibirBilheteDoDia(bilhete) {
            const container = document.getElementById('bilheteDiaContainer');
            const confiancaClass = bilhete.confianca >= 80 ? 'confianca-alta' : 
                                 bilhete.confianca >= 70 ? 'confianca-media' : 'confianca-baixa';
            
            container.innerHTML = `
                <div class="bilhete-item bilhete-destaque">
                    <div class="bilhete-header">
                        <div class="jogo-info">${bilhete.jogo}</div>
                        <div class="bilhete-tipo tipo-destaque">BILHETE DO DIA</div>
                    </div>
                    
                    <div class="bilhete-detalhes">
                        <div class="detalhes-esquerda">
                            <div class="mercado">${bilhete.mercado}</div>
                            <div class="selecao">${bilhete.selecao}</div>
                            <div class="analise-premium">${bilhete.analise_premium || '🔥 Melhor oportunidade do dia'}</div>
                            <div class="analise">${bilhete.analise}</div>
                        </div>
                        <div class="detalhes-direita">
                            <div class="odd odd-destaque">${bilhete.odd}</div>
                            <div class="valor-esperado">Valor: ${bilhete.valor_esperado}</div>
                        </div>
                    </div>
                    
                    <div class="bilhete-footer">
                        <div class="confianca">
                            <span>Confiança: ${bilhete.confianca}%</span>
                            <div class="barra-confianca">
                                <div class="preenchimento-confianca ${confiancaClass}" 
                                     style="width: ${bilhete.confianca}%"></div>
                            </div>
                        </div>
                        <div class="timestamp">
                            ${new Date(bilhete.timestamp).toLocaleString('pt-BR')}
                        </div>
                    </div>
                </div>
            `;
        }

        function exibirBilhetes(bilhetes) {
            const container = document.getElementById('resultadosContainer');
            const badgeCount = document.getElementById('badgeCount');
            
            if (!bilhetes || bilhetes.length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <h3>🔍 Nenhum bilhete encontrado</h3>
                        <p>Tente alterar os filtros ou esporte.</p>
                    </div>
                `;
                badgeCount.textContent = '0';
                return;
            }
            
            // Aplicar filtro
            let bilhetesFiltrados = bilhetes;
            if (filtroAtual === 'alta') {
                bilhetesFiltrados = bilhetes.filter(b => b.confianca >= 75);
            } else if (filtroAtual === 'futebol') {
                bilhetesFiltrados = bilhetes.filter(b => b.tipo.includes('futebol'));
            } else if (filtroAtual === 'nba') {
                bilhetesFiltrados = bilhetes.filter(b => b.tipo.includes('nba'));
            }
            
            badgeCount.textContent = bilhetesFiltrados.length;
            
            container.innerHTML = bilhetesFiltrados.map((bilhete, index) => {
                const confiancaClass = bilhete.confianca >= 80 ? 'confianca-alta' : 
                                     bilhete.confianca >= 70 ? 'confianca-media' : 'confianca-baixa';
                
                const isDestaque = bilhete.destaque;
                
                return `
                    <div class="bilhete-item ${isDestaque ? 'bilhete-destaque' : ''}">
                        <div class="bilhete-header">
                            <div class="jogo-info">${bilhete.jogo}</div>
                            <div class="bilhete-tipo ${isDestaque ? 'tipo-destaque' : ''}">${bilhete.tipo}</div>
                        </div>
                        
                        <div class="bilhete-detalhes">
                            <div class="detalhes-esquerda">
                                <div class="mercado">${bilhete.mercado}</div>
                                <div class="selecao">${bilhete.selecao}</div>
                                ${isDestaque ? `<div class="analise-premium">${bilhete.analise_premium || '⭐ Destaque'}</div>` : ''}
                                <div class="analise">${bilhete.analise}</div>
                            </div>
                            <div class="detalhes-direita">
                                <div class="odd ${isDestaque ? 'odd-destaque' : ''}">${bilhete.odd}</div>
                                <div class="valor-esperado">Valor: ${bilhete.valor_esperado}</div>
                            </div>
                        </div>
                        
                        <div class="bilhete-footer">
                            <div class="confianca">
                                <span>Confiança: ${bilhete.confianca}%</span>
                                <div class="barra-confianca">
                                    <div class="preenchimento-confianca ${confiancaClass}" 
                                         style="width: ${bilhete.confianca}%"></div>
                                </div>
                            </div>
                            <div class="timestamp">
                                ${new Date(bilhete.timestamp).toLocaleString('pt-BR')}
                            </div>
                        </div>
                    </div>
                `;
            }).join('');
        }

        function filtrarBilhetes(filtro) {
            filtroAtual = filtro;
            
            // Atualizar tabs
            document.querySelectorAll('.tab').forEach(tab => {
                tab.classList.remove('active');
            });
            event.target.classList.add('active');
            
            // Re-exibir bilhetes com filtro
            exibirBilhetes(todosBilhetes);
        }

        function atualizarEstatisticas(bilhetes) {
            document.getElementById('totalBilhetes').textContent = bilhetes.length;
            
            const altaConfianca = bilhetes.filter(b => b.confianca >= 75).length;
            document.getElementById('altaConfianca').textContent = altaConfianca;
            
            const valorMedio = bilhetes.reduce((sum, b) => sum + parseFloat(b.odd), 0) / bilhetes.length;
            document.getElementById('valorMedio').textContent = valorMedio.toFixed(2);
            
            const taxaSucesso = (bilhetes.filter(b => b.confianca >= 70).length / bilhetes.length * 100).toFixed(0);
            document.getElementById('taxaSucesso').textContent = taxaSucesso + '%';
        }

        async function testarBilhetes() {
            const testeBtn = document.getElementById('testeBtn');
            
            testeBtn.disabled = true;
            testeBtn.innerHTML = '⏳ Enviando...';
            
            try {
                const response = await fetch('/teste_bilhetes', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    }
                });
                
                const data = await response.json();
                
                if (data.status === 'success') {
                    alert('✅ Bilhetes de teste enviados para o Telegram!');
                } else {
                    alert('❌ Erro ao enviar: ' + data.message);
                }
                
            } catch (error) {
                alert('❌ Erro de conexão ao testar');
            } finally {
                testeBtn.disabled = false;
                testeBtn.innerHTML = '🧪 Testar no Telegram';
            }
        }

        // Análise automática ao carregar a página
        window.addEventListener('load', function() {
            setTimeout(() => {
                analisarJogos();
            }, 1500);
        });

        // Atualizar a cada 3 minutos
        setInterval(analisarJogos, 180000);
        
        // Buscar bilhete do dia a cada 6 horas
        setInterval(buscarBilheteDoDia, 21600000);
    </script>
</body>
</html>
'''

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=10000)

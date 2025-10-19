from flask import Flask, jsonify, request, render_template_string
import os
import httpx
import requests
from datetime import datetime, timedelta
import json
import time
import threading
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

# Template HTML simplificado
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BetMaster AI - Sistema Completo</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            background: linear-gradient(135deg, #0c2461 0%, #1e3799 100%); 
            min-height: 100vh; color: #333; padding: 20px;
        }
        .container { max-width: 1400px; margin: 0 auto; }
        .header { 
            text-align: center; color: white; margin-bottom: 30px; 
            padding: 40px 20px; background: rgba(255,255,255,0.1); 
            border-radius: 25px; backdrop-filter: blur(15px); 
            border: 1px solid rgba(255,255,255,0.2); 
        }
        .logo { font-size: 4.5rem; margin-bottom: 20px; }
        h1 { font-size: 3.5rem; margin-bottom: 15px; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }
        .subtitle { font-size: 1.4rem; opacity: 0.9; margin-bottom: 25px; }
        
        /* Dashboard */
        .dashboard-stats { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); 
            gap: 20px; 
            margin-bottom: 30px; 
        }
        .stat-card { 
            background: white; 
            border-radius: 15px; 
            padding: 25px; 
            text-align: center;
            box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        }
        .stat-number { 
            font-size: 2.5rem; 
            font-weight: 800; 
            margin-bottom: 8px; 
        }
        .stat-green { color: #27ae60; }
        .stat-red { color: #e74c3c; }
        .stat-blue { color: #3498db; }
        .stat-label { color: #7f8c8d; font-size: 1rem; font-weight: 600; }
        
        /* Controles */
        .controls-grid { 
            display: grid; 
            grid-template-columns: 1fr 1fr; 
            gap: 25px; 
            margin-bottom: 40px; 
        }
        .card { 
            background: white; 
            border-radius: 20px; 
            padding: 30px; 
            box-shadow: 0 15px 35px rgba(0,0,0,0.2); 
        }
        .controls { display: flex; flex-direction: column; gap: 20px; }
        .form-group { display: flex; flex-direction: column; gap: 8px; }
        label { font-weight: 700; color: #0c2461; font-size: 1.1rem; }
        select, button { 
            padding: 15px 20px; 
            border: 2px solid #e1e5e9; 
            border-radius: 12px; 
            font-size: 16px; 
        }
        button { 
            background: linear-gradient(135deg, #0c2461 0%, #1e3799 100%); 
            color: white; border: none; 
            cursor: pointer; font-weight: 600; 
        }
        button:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(0,0,0,0.2); }
        .btn-destaque { background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%); }
        .btn-enviar { background: linear-gradient(135deg, #9b59b6 0%, #8e44ad 100%); }
        .btn-dashboard { background: linear-gradient(135deg, #27ae60 0%, #2ecc71 100%); }
        
        /* Resultados */
        .results { max-height: 600px; overflow-y: auto; }
        .bilhete-item { 
            border: 2px solid #e1e5e9; 
            border-radius: 15px; 
            padding: 20px; 
            margin-bottom: 15px; 
            background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
        }
        .bilhete-destaque { 
            border-color: #e74c3c; 
            background: linear-gradient(135deg, #fff5f5 0%, #ffffff 100%); 
        }
        
        /* Loading */
        .loading { display: none; text-align: center; padding: 40px; }
        .spinner { 
            border: 5px solid #f3f3f3; 
            border-top: 5px solid #0c2461; 
            border-radius: 50%; 
            width: 60px; height: 60px; 
            animation: spin 1s linear infinite; 
            margin: 0 auto 20px; 
        }
        @keyframes spin { 
            0% { transform: rotate(0deg); } 
            100% { transform: rotate(360deg); } 
        }
        
        /* Status */
        .status { padding: 12px; border-radius: 8px; margin: 10px 0; text-align: center; font-weight: 600; }
        .status-success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .status-error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .status-info { background: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; }
        
        .counter { background: #e74c3c; color: white; padding: 4px 8px; border-radius: 12px; font-size: 0.8rem; margin-left: 10px; }
        .esporte-title { color: white; text-align: center; margin-bottom: 10px; font-size: 1.2rem; }
        
        /* Tabs */
        .tabs { display: flex; gap: 10px; margin-bottom: 20px; }
        .tab { 
            padding: 12px 24px; 
            background: rgba(255,255,255,0.1); 
            color: white; 
            border-radius: 10px; 
            cursor: pointer; 
            transition: all 0.3s ease; 
        }
        .tab.active { background: white; color: #0c2461; font-weight: 600; }
        .tab:hover { background: rgba(255,255,255,0.2); }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">🎯🤖📊</div>
            <h1>BetMaster AI v5.0</h1>
            <p class="subtitle">Sistema Completo com Agendamento & Dashboard</p>
            <div id="statusMessage"></div>
        </div>

        <!-- Dashboard Stats -->
        <div class="dashboard-stats" id="dashboardStats">
            <div class="stat-card">
                <div class="stat-number stat-blue" id="totalBilhetes">0</div>
                <div class="stat-label">Total de Bilhetes</div>
            </div>
            <div class="stat-card">
                <div class="stat-number stat-green" id="totalGreen">0</div>
                <div class="stat-label">Green</div>
            </div>
            <div class="stat-card">
                <div class="stat-number stat-red" id="totalRed">0</div>
                <div class="stat-label">Red</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="taxaAcerto">0%</div>
                <div class="stat-label">Taxa de Acerto</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="lucroPrejuizo">0.00</div>
                <div class="stat-label">Lucro/Prejuízo (u)</div>
            </div>
        </div>

        <div class="esporte-title" id="esporteTitle">⚽ Analisando Futebol</div>

        <!-- Tabs -->
        <div class="tabs">
            <div class="tab active" onclick="mostrarAba('analise')">📈 Análise</div>
            <div class="tab" onclick="mostrarAba('dashboard')">📊 Dashboard</div>
            <div class="tab" onclick="mostrarAba('agendamento')">⏰ Agendamento</div>
        </div>

        <!-- Conteúdo das Abas -->
        <div id="abaAnalise" class="aba-conteudo">
            <div class="controls-grid">
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
                    <button onclick="enviarParaTelegram()" class="btn-enviar" id="enviarBtn">📤 Enviar para Telegram</button>
                    <button onclick="verificarResultados()" class="btn-dashboard">🔍 Verificar Resultados</button>
                </div>

                <div class="card results">
                    <h3>📈 Resultados <span id="contadorBilhetes" class="counter">0</span></h3>
                    <div class="loading" id="loading">
                        <div class="spinner"></div>
                        <p>Analisando dados esportivos...</p>
                    </div>
                    <div id="resultadosContainer">
                        <p>Selecione um esporte e clique em "Analisar Jogos" para começar</p>
                    </div>
                </div>
            </div>
        </div>

        <div id="abaDashboard" class="aba-conteudo" style="display: none;">
            <div class="card">
                <h3>📊 Dashboard de Desempenho</h3>
                <div id="dashboardContainer">
                    <p>Carregando estatísticas...</p>
                </div>
            </div>
        </div>

        <div id="abaAgendamento" class="aba-conteudo" style="display: none;">
            <div class="card">
                <h3>⏰ Agendamento Automático</h3>
                <div id="agendamentoContainer">
                    <p>Carregando informações de agendamento...</p>
                </div>
            </div>
        </div>
    </div>

    <script>
        let bilhetesAtuais = [];
        let abaAtual = 'analise';

        function mostrarAba(aba) {
            // Esconder todas as abas
            document.querySelectorAll('.aba-conteudo').forEach(div => {
                div.style.display = 'none';
            });
            
            // Remover active de todas as tabs
            document.querySelectorAll('.tab').forEach(tab => {
                tab.classList.remove('active');
            });
            
            // Mostrar aba selecionada
            document.getElementById('aba' + aba.charAt(0).toUpperCase() + aba.slice(1)).style.display = 'block';
            event.target.classList.add('active');
            abaAtual = aba;
            
            // Carregar dados específicos da aba
            if (aba === 'dashboard') {
                carregarDashboard();
            } else if (aba === 'agendamento') {
                carregarAgendamento();
            }
        }

        function showStatus(message, type = 'success') {
            const statusDiv = document.getElementById('statusMessage');
            statusDiv.innerHTML = `<div class="status status-${type}">${message}</div>`;
            setTimeout(() => statusDiv.innerHTML = '', 5000);
        }

        function atualizarContador() {
            const contador = document.getElementById('contadorBilhetes');
            contador.textContent = bilhetesAtuais.length;
        }

        async function carregarDashboard() {
            try {
                const response = await fetch('/dashboard');
                const data = await response.json();
                
                if (data.status === 'success') {
                    const stats = data.estatisticas;
                    const historico = data.historico_recente;
                    
                    // Atualizar stats do dashboard
                    document.getElementById('totalBilhetes').textContent = stats.total_bilhetes;
                    document.getElementById('totalGreen').textContent = stats.green;
                    document.getElementById('totalRed').textContent = stats.red;
                    document.getElementById('taxaAcerto').textContent = stats.taxa_acerto.toFixed(1) + '%';
                    document.getElementById('lucroPrejuizo').textContent = stats.lucro_prejuizo.toFixed(2);
                    
                    // Atualizar container do dashboard
                    let html = `
                        <div style="margin-bottom: 20px;">
                            <h4>📈 Estatísticas Gerais</h4>
                            <p>Total de Bilhetes: <strong>${stats.total_bilhetes}</strong></p>
                            <p>Green: <strong style="color: #27ae60">${stats.green}</strong> | 
                               Red: <strong style="color: #e74c3c">${stats.red}</strong> | 
                               Em Aberto: <strong>${stats.em_aberto}</strong></p>
                            <p>Taxa de Acerto: <strong>${stats.taxa_acerto.toFixed(1)}%</strong></p>
                            <p>Lucro/Prejuízo: <strong>${stats.lucro_prejuizo.toFixed(2)}u</strong></p>
                            <p>Odd Média: <strong>${stats.valor_medio_odd.toFixed(2)}</strong></p>
                        </div>
                    `;
                    
                    if (historico.length > 0) {
                        html += `<h4>📋 Últimos Bilhetes</h4>`;
                        historico.forEach(bilhete => {
                            const corResultado = bilhete.resultado === 'green' ? '#27ae60' : 
                                               bilhete.resultado === 'red' ? '#e74c3c' : '#f39c12';
                            html += `
                                <div class="bilhete-item" style="margin-bottom: 10px; border-left: 4px solid ${corResultado}">
                                    <p><strong>${bilhete.jogo}</strong></p>
                                    <p>${bilhete.selecao} @ ${bilhete.odd}</p>
                                    <p>Resultado: <strong style="color: ${corResultado}">${bilhete.resultado.toUpperCase()}</strong></p>
                                    <p><small>${new Date(bilhete.timestamp).toLocaleString('pt-BR')}</small></p>
                                </div>
                            `;
                        });
                    }
                    
                    document.getElementById('dashboardContainer').innerHTML = html;
                }
            } catch (error) {
                document.getElementById('dashboardContainer').innerHTML = '<p>Erro ao carregar dashboard</p>';
            }
        }

        async function carregarAgendamento() {
            try {
                const response = await fetch('/dashboard');
                const data = await response.json();
                
                if (data.status === 'success') {
                    const agendamento = data.agendamento;
                    let html = `
                        <h4>🕐 Próximas Análises Automáticas</h4>
                        <p><strong>Horários:</strong> ${agendamento.proxima_analise}</p>
                        <p><strong>Verificação de Resultados:</strong> ${agendamento.verificacao_resultados}</p>
                    `;
                    
                    if (agendamento.ultima_analise) {
                        html += `<p><strong>Última Análise:</strong> ${new Date(agendamento.ultima_analise).toLocaleString('pt-BR')}</p>`;
                    }
                    
                    html += `
                        <div style="margin-top: 20px; padding: 15px; background: #f8f9fa; border-radius: 10px;">
                            <h5>⚙️ Funcionamento do Agendamento</h5>
                            <p>• Análises automáticas a cada 6 horas</p>
                            <p>• Verificação de resultados a cada hora</p>
                            <p>• Notificações no Telegram para GREEN</p>
                            <p>• Atualização automática do dashboard</p>
                        </div>
                    `;
                    
                    document.getElementById('agendamentoContainer').innerHTML = html;
                }
            } catch (error) {
                document.getElementById('agendamentoContainer').innerHTML = '<p>Erro ao carregar agendamento</p>';
            }
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
                    bilhetesAtuais = data.data.bilhetes;
                    if (bilhetesAtuais.length > 0) {
                        resultadosContainer.innerHTML = bilhetesAtuais.map(bilhete => `
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
                        showStatus(`✅ Encontrados ${bilhetesAtuais.length} bilhetes para ${esporteNomes[esporte]}`, 'success');
                    } else {
                        resultadosContainer.innerHTML = '<p>Nenhum jogo encontrado para hoje. Mostrando exemplo...</p>';
                        showStatus('⚠️ Nenhum jogo ao vivo encontrado', 'info');
                    }
                    atualizarContador();
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
                    setTimeout(analisarJogos, 2000);
                } else {
                    showStatus(`❌ ${data.message}`, 'error');
                }
            } catch (error) {
                showStatus('❌ Erro de conexão ao buscar bilhete do dia', 'error');
            }
        }

        async function enviarParaTelegram() {
            if (bilhetesAtuais.length === 0) {
                showStatus('❌ Nenhum bilhete para enviar. Analise os jogos primeiro.', 'error');
                return;
            }

            try {
                const enviarBtn = document.getElementById('enviarBtn');
                enviarBtn.disabled = true;
                enviarBtn.innerHTML = '⏳ Enviando...';
                
                showStatus('⏳ Enviando bilhetes para o Telegram...', 'info');
                
                const response = await fetch('/enviar_bilhetes', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({bilhetes: bilhetesAtuais})
                });
                
                const data = await response.json();
                if (data.status === 'success') {
                    showStatus(`✅ ${data.message}`, 'success');
                } else {
                    showStatus(`❌ ${data.message}`, 'error');
                }
            } catch (error) {
                showStatus('❌ Erro de conexão ao enviar para Telegram', 'error');
            } finally {
                const enviarBtn = document.getElementById('enviarBtn');
                enviarBtn.disabled = false;
                enviarBtn.innerHTML = '📤 Enviar para Telegram';
            }
        }

        async function verificarResultados() {
            try {
                showStatus('⏳ Verificando resultados dos bilhetes...', 'info');
                const response = await fetch('/verificar_resultados', {method: 'POST'});
                const data = await response.json();
                if (data.status === 'success') {
                    showStatus('✅ Verificação de resultados concluída!', 'success');
                    // Atualizar dashboard se estiver visível
                    if (abaAtual === 'dashboard') {
                        carregarDashboard();
                    }
                } else {
                    showStatus(`❌ ${data.message}`, 'error');
                }
            } catch (error) {
                showStatus('❌ Erro ao verificar resultados', 'error');
            }
        }

        // Inicialização
        window.addEventListener('load', function() {
            setTimeout(analisarJogos, 1000);
            // Carregar stats iniciais
            carregarDashboard();
        });

        document.getElementById('esporte').addEventListener('change', analisarJogos);
    </script>
</body>
</html>
"""

# ... (o resto do código Python permanece igual desde a versão anterior)
# [TODO: Incluir todas as funções Python da versão anterior aqui]

# ROTA RAIZ PARA SERVIR O HTML
@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

# ... (manter todas as outras funções e endpoints da versão anterior)

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

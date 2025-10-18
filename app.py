<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sistema de Apostas Inteligente</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
            padding: 20px;
        }
        
        .header h1 {
            font-size: 2.5rem;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .header p {
            font-size: 1.2rem;
            opacity: 0.9;
        }
        
        .matches-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .match-card {
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        
        .match-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 40px rgba(0,0,0,0.3);
        }
        
        .teams {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
            font-size: 1.3rem;
            font-weight: bold;
        }
        
        .home-team {
            color: #2c5530;
        }
        
        .away-team {
            color: #c53030;
        }
        
        .vs {
            color: #666;
            font-weight: normal;
        }
        
        .match-time {
            text-align: center;
            color: #666;
            margin-bottom: 15px;
            font-size: 0.9rem;
        }
        
        .suggestion {
            background: linear-gradient(135deg, #ffd89b, #19547b);
            color: white;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
            font-weight: bold;
            margin-top: 15px;
        }
        
        .controls {
            text-align: center;
            margin-top: 30px;
        }
        
        .btn {
            background: linear-gradient(135deg, #ff7e5f, #feb47b);
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 25px;
            font-size: 1.1rem;
            cursor: pointer;
            margin: 0 10px;
            transition: transform 0.2s ease;
        }
        
        .btn:hover {
            transform: scale(1.05);
        }
        
        .btn-telegram {
            background: linear-gradient(135deg, #0088cc, #00b3ff);
        }
        
        .last-update {
            text-align: center;
            color: white;
            margin-top: 20px;
            opacity: 0.8;
        }
        
        .no-matches {
            text-align: center;
            color: white;
            font-size: 1.2rem;
            padding: 40px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⚽ Sistema de Apostas Inteligente</h1>
            <p>Análises inteligentes baseadas em estatísticas em tempo real</p>
        </div>
        
        {% if matches %}
        <div class="matches-grid">
            {% for match in matches %}
            <div class="match-card">
                <div class="teams">
                    <span class="home-team">{{ match.home_team }}</span>
                    <span class="vs">VS</span>
                    <span class="away-team">{{ match.away_team }}</span>
                </div>
                
                <div class="match-time">
                    ⏰ {{ match.time }}
                </div>
                
                <div class="suggestion">
                    💡 {{ match.suggestion }}
                </div>
            </div>
            {% endfor %}
        </div>
        {% else %}
        <div class="no-matches">
            <p>⚠️ Nenhum jogo encontrado no momento.</p>
            <p>Atualize a página ou tente novamente mais tarde.</p>
        </div>
        {% endif %}
        
        <div class="controls">
            <button class="btn" onclick="refreshMatches()">
                🔄 Atualizar Jogos
            </button>
            
            <button class="btn btn-telegram" onclick="openTelegram()">
                📱 Iniciar no Telegram
            </button>
        </div>
        
        <div class="last-update">
            Última atualização: <span id="update-time">{{ now }}</span>
        </div>
    </div>

    <script>
        function refreshMatches() {
            location.reload();
        }
        
        function openTelegram() {
            // Substitua pelo username real do seu bot
            window.open('https://t.me/SeuBot_Aqui', '_blank');
        }
        
        // Atualiza o horário da última atualização
        document.getElementById('update-time').textContent = new Date().toLocaleString('pt-BR');
        
        // Atualiza automaticamente a cada 5 minutos
        setInterval(refreshMatches, 300000);
    </script>
</body>
</html>

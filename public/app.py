// API Base URL
const API_BASE_URL = window.location.origin;

// Elementos DOM
const playerListElement = document.querySelector('.player-list');
const playerDetailsElement = document.querySelector('.player-details');
const betItemsElement = document.querySelector('.bet-items');

// Estado da aplicação
let currentPlayer = null;
let players = [];

// Inicialização
document.addEventListener('DOMContentLoaded', function() {
    loadPlayers();
    setupTabs();
    setupFilters();
    
    // Verificar saúde da API
    checkAPIHealth();
});

// Verificar saúde da API
async function checkAPIHealth() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        const data = await response.json();
        console.log('✅ API conectada:', data);
    } catch (error) {
        console.error('❌ Erro ao conectar com API:', error);
        showNotification('Usando dados locais - API offline', 'warning');
    }
}

// Carregar lista de jogadores
async function loadPlayers() {
    try {
        showLoading('Carregando jogadores...');
        
        const response = await fetch(`${API_BASE_URL}/api/players`);
        const result = await response.json();
        
        if (result.success) {
            players = result.data;
            renderPlayerList();
            
            if (players.length > 0) {
                await selectPlayer(players[0]);
            }
        } else {
            throw new Error(result.message);
        }
    } catch (error) {
        console.error('Erro ao carregar jogadores:', error);
        showNotification('Erro ao carregar dados. Usando dados de exemplo.', 'error');
        
        // Usar dados locais em caso de erro
        players = getFallbackPlayers();
        renderPlayerList();
        
        if (players.length > 0) {
            selectPlayer(players[0]);
        }
    } finally {
        hideLoading();
    }
}

// Renderizar lista de jogadores
function renderPlayerList() {
    playerListElement.innerHTML = '';
    
    players.forEach(player => {
        const playerItem = document.createElement('div');
        playerItem.className = 'player-item';
        playerItem.dataset.id = player.id;
        
        playerItem.innerHTML = `
            <div class="player-avatar">${getInitials(player.name)}</div>
            <div class="player-info">
                <h3>${player.name}</h3>
                <p>${player.team} • ${player.position}</p>
            </div>
        `;
        
        playerItem.addEventListener('click', () => selectPlayer(player));
        playerListElement.appendChild(playerItem);
    });
}

// Selecionar jogador
async function selectPlayer(player) {
    try {
        showLoading(`Carregando dados de ${player.name}...`);
        
        // Remover classe active de todos os jogadores
        document.querySelectorAll('.player-item').forEach(item => {
            item.classList.remove('active');
        });
        
        // Adicionar classe active ao jogador selecionado
        document.querySelector(`.player-item[data-id="${player.id}"]`).classList.add('active');
        
        // Buscar dados atualizados do jogador
        const response = await fetch(`${API_BASE_URL}/api/players/${player.id}/stats`);
        const result = await response.json();
        
        if (result.success) {
            currentPlayer = result.data.player;
            updatePlayerDetails(result.data);
        } else {
            throw new Error(result.message);
        }
    } catch (error) {
        console.error('Erro ao carregar dados do jogador:', error);
        showNotification('Usando dados locais do jogador', 'warning');
        
        // Usar dados locais em caso de erro
        currentPlayer = player;
        updatePlayerDetails({
            player: player,
            stats: player.stats,
            suggestions: calculateLocalSuggestions(player.stats)
        });
    } finally {
        hideLoading();
    }
}

// Atualizar detalhes do jogador
function updatePlayerDetails(data) {
    const { player, stats, suggestions } = data;
    
    const playerInfoLarge = document.querySelector('.player-info-large');
    playerInfoLarge.innerHTML = `
        <div class="player-avatar-large">${getInitials(player.name)}</div>
        <h2>${player.name}</h2>
        <p>${player.team} • ${player.position}</p>
    `;
    
    // Atualizar estatísticas
    updateStatsCards(stats);
    
    // Atualizar sugestões
    renderSuggestions(suggestions);
    
    // Atualizar gráfico de desempenho
    updatePerformanceChart(stats.last5);
}

// Atualizar cards de estatísticas
function updateStatsCards(stats) {
    document.querySelector('.stat-card:nth-child(1) .stat-value').textContent = stats.points.toFixed(1);
    document.querySelector('.stat-card:nth-child(2) .stat-value').textContent = stats.assists.toFixed(1);
    document.querySelector('.stat-card:nth-child(3) .stat-value').textContent = stats.rebounds.toFixed(1);
    document.querySelector('.stat-card:nth-child(4) .stat-value').textContent = stats.threes.toFixed(1);
    
    // Atualizar barras de progresso (simulação)
    updateProgressBars(stats);
}

// Atualizar barras de progresso
function updateProgressBars(stats) {
    const maxPoints = 35;
    const maxAssists = 12;
    const maxRebounds = 15;
    const maxThrees = 6;
    
    document.querySelector('.stat-card:nth-child(1) .progress-fill').style.width = `${(stats.points / maxPoints) * 100}%`;
    document.querySelector('.stat-card:nth-child(2) .progress-fill').style.width = `${(stats.assists / maxAssists) * 100}%`;
    document.querySelector('.stat-card:nth-child(3) .progress-fill').style.width = `${(stats.rebounds / maxRebounds) * 100}%`;
    document.querySelector('.stat-card:nth-child(4) .progress-fill').style.width = `${(stats.threes / maxThrees) * 100}%`;
}

// Renderizar sugestões
function renderSuggestions(suggestions) {
    const suggestionsContainer = document.querySelector('#suggestions .suggestions');
    suggestionsContainer.innerHTML = '';
    
    suggestions.forEach(suggestion => {
        const suggestionElement = document.createElement('div');
        suggestionElement.className = 'suggestion-item';
        suggestionElement.dataset.type = suggestion.type;
        
        suggestionElement.innerHTML = `
            <div class="suggestion-header">
                <div class="suggestion-title">${suggestion.market}</div>
                <div class="confidence">${suggestion.confidence}%</div>
            </div>
            <p>${suggestion.description}</p>
            <div class="suggestion-details">
                <span>Sugestão: ${suggestion.suggestion}</span>
                <span class="suggestion-value">${suggestion.odds}</span>
            </div>
        `;
        
        suggestionElement.addEventListener('click', () => {
            addToBetSlip(currentPlayer.name, suggestion.market, suggestion.suggestion, suggestion.odds);
            showNotification('Sugestão adicionada ao bilhete!', 'success');
        });
        
        suggestionsContainer.appendChild(suggestionElement);
    });
}

// Resto do código JavaScript mantido similar ao anterior...
// (funções calculateLocalSuggestions, addToBetSlip, setupTabs, etc.)

// Funções auxiliares
function getInitials(name) {
    return name.split(' ').map(n => n[0]).join('');
}

function showLoading(message = 'Carregando...') {
    // Implementar loading spinner
    console.log('Loading:', message);
}

function hideLoading() {
    // Esconder loading spinner
}

function showNotification(message, type = 'info') {
    // Implementar notificações
    console.log(`Notification [${type}]:`, message);
}

// Dados de fallback
function getFallbackPlayers() {
    return [
        {
            id: 1,
            name: "LeBron James",
            team: "Los Angeles Lakers",
            position: "SF",
            stats: {
                points: 25.3,
                assists: 7.9,
                rebounds: 7.1,
                threes: 2.2,
                last5: [28, 32, 22, 26, 29]
            }
        },
        {
            id: 2,
            name: "Stephen Curry",
            team: "Golden State Warriors",
            position: "PG",
            stats: {
                points: 29.4,
                assists: 6.3,
                rebounds: 6.1,
                threes: 4.9,
                last5: [35, 28, 31, 27, 33]
            }
        }
    ];
}

function calculateLocalSuggestions(stats) {
    // Implementação local das sugestões (similar à do servidor)
    // ... código similar ao calculateSuggestions do servidor
}
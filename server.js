const express = require('express');
const axios = require('axios');
const cors = require('cors');
const path = require('path');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// Configuração da API
const API_KEY = process.env.SPORTS_DATA_API_KEY;
const BASE_URL = process.env.SPORTS_DATA_BASE_URL;

// Dados mockados para desenvolvimento (caso a API não esteja disponível)
const mockPlayers = [
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
    },
    {
        id: 3,
        name: "Kevin Durant",
        team: "Phoenix Suns",
        position: "SF",
        stats: {
            points: 27.1,
            assists: 5.6,
            rebounds: 6.7,
            threes: 2.1,
            last5: [25, 30, 28, 24, 29]
        }
    }
];

// Função para buscar dados reais da API
async function fetchPlayerStats(playerId) {
    try {
        const response = await axios.get(`${BASE_URL}/stats/json/PlayerGameStatsByPlayer/${playerId}`, {
            params: {
                key: API_KEY
            }
        });
        return response.data;
    } catch (error) {
        console.error('Erro ao buscar dados da API:', error.message);
        return null;
    }
}

// Função para calcular sugestões inteligentes
function calculateSuggestions(playerStats) {
    const pointsAvg = playerStats.points;
    const assistsAvg = playerStats.assists;
    const reboundsAvg = playerStats.rebounds;
    const threesAvg = playerStats.threes;
    
    const suggestions = [];
    
    // Sugestão para Pontos
    const pointsSuggestion = Math.floor(pointsAvg * 0.85);
    const pointsConfidence = calculateConfidence(playerStats.last5, pointsSuggestion);
    suggestions.push({
        type: 'points',
        market: 'Pontos',
        suggestion: `Mais de ${pointsSuggestion}`,
        confidence: pointsConfidence,
        odds: getOdds(pointsConfidence),
        average: pointsAvg,
        description: `Média de ${pointsAvg.toFixed(1)} pontos nos últimos 5 jogos`
    });
    
    // Sugestão para Pontos + Assistências
    const pointsAssistsAvg = pointsAvg + assistsAvg;
    const pointsAssistsSuggestion = Math.floor(pointsAssistsAvg * 0.85);
    const pointsAssistsConfidence = calculateConfidence(playerStats.last5, pointsAssistsSuggestion, true);
    suggestions.push({
        type: 'points_assists',
        market: 'Pontos + Assistências',
        suggestion: `Mais de ${pointsAssistsSuggestion}`,
        confidence: pointsAssistsConfidence,
        odds: getOdds(pointsAssistsConfidence),
        average: pointsAssistsAvg,
        description: `Média de ${pointsAssistsAvg.toFixed(1)} pontos + assistências`
    });
    
    // Sugestão para Rebotes
    const reboundsSuggestion = Math.floor(reboundsAvg * 0.9);
    const reboundsConfidence = calculateConfidence([], reboundsSuggestion, false, 70);
    suggestions.push({
        type: 'rebounds',
        market: 'Rebotes',
        suggestion: `Mais de ${reboundsSuggestion}`,
        confidence: reboundsConfidence,
        odds: getOdds(reboundsConfidence),
        average: reboundsAvg,
        description: `Média de ${reboundsAvg.toFixed(1)} rebotes`
    });
    
    // Sugestão para Cestas de 3 pontos
    const threesSuggestion = Math.floor(threesAvg * 0.8);
    const threesConfidence = calculateConfidence([], threesSuggestion, false, 65);
    suggestions.push({
        type: 'threes',
        market: 'Cestas de 3 pontos',
        suggestion: `Mais de ${threesSuggestion}`,
        confidence: threesConfidence,
        odds: getOdds(threesConfidence),
        average: threesAvg,
        description: `Média de ${threesAvg.toFixed(1)} cestas de 3 pontos`
    });
    
    return suggestions;
}

// Função para calcular confiança
function calculateConfidence(last5Games, suggestion, isPointsAssists = false, baseConfidence = 60) {
    if (last5Games.length === 0) {
        return baseConfidence;
    }
    
    let aboveCount = 0;
    
    if (isPointsAssists) {
        // Para pontos + assistências, estimar assistências baseadas nos pontos
        last5Games.forEach(points => {
            const estimatedAssists = points * 0.3; // Estimativa simplificada
            if (points + estimatedAssists > suggestion) {
                aboveCount++;
            }
        });
    } else {
        // Para pontos apenas
        last5Games.forEach(points => {
            if (points > suggestion) {
                aboveCount++;
            }
        });
    }
    
    const percentage = (aboveCount / last5Games.length) * 100;
    return Math.min(95, Math.max(baseConfidence, Math.round(percentage)));
}

// Função para gerar odds baseadas na confiança
function getOdds(confidence) {
    if (confidence >= 85) return '-140';
    if (confidence >= 80) return '-130';
    if (confidence >= 75) return '+110';
    if (confidence >= 70) return '+120';
    if (confidence >= 65) return '+150';
    return '+180';
}

// Rotas da API

// Rota principal - servir o frontend
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// Rota para listar jogadores
app.get('/api/players', (req, res) => {
    // Em produção, isso buscaria da API real
    res.json({
        success: true,
        data: mockPlayers,
        lastUpdated: new Date().toISOString()
    });
});

// Rota para obter estatísticas de um jogador
app.get('/api/players/:id/stats', (req, res) => {
    const playerId = parseInt(req.params.id);
    const player = mockPlayers.find(p => p.id === playerId);
    
    if (!player) {
        return res.status(404).json({
            success: false,
            message: 'Jogador não encontrado'
        });
    }
    
    const suggestions = calculateSuggestions(player.stats);
    
    res.json({
        success: true,
        data: {
            player: player,
            stats: player.stats,
            suggestions: suggestions
        }
    });
});

// Rota para obter sugestões específicas
app.get('/api/players/:id/suggestions', (req, res) => {
    const playerId = parseInt(req.params.id);
    const player = mockPlayers.find(p => p.id === playerId);
    
    if (!player) {
        return res.status(404).json({
            success: false,
            message: 'Jogador não encontrado'
        });
    }
    
    const suggestions = calculateSuggestions(player.stats);
    
    res.json({
        success: true,
        data: suggestions
    });
});

// Health check para Render
app.get('/health', (req, res) => {
    res.json({ 
        status: 'OK', 
        timestamp: new Date().toISOString(),
        environment: process.env.NODE_ENV 
    });
});

// Iniciar servidor
app.listen(PORT, () => {
    console.log(`🚀 Sistema NBA rodando na porta ${PORT}`);
    console.log(`📊 Ambiente: ${process.env.NODE_ENV}`);
    console.log(`🔗 Acesse: http://localhost:${PORT}`);
});
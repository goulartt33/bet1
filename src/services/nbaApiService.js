const axios = require('axios');
const { mockPlayers } = require('../data/mockData');

const API_KEY = process.env.SPORTS_DATA_API_KEY;
const BASE_URL = process.env.SPORTS_DATA_BASE_URL || 'https://api.sportsdata.io/v3/nba';

class NbaApiService {
    constructor() {
        this.useMockData = !API_KEY || API_KEY === 'your_free_api_key_here';
        
        if (this.useMockData) {
            console.log('⚠️  Using mock data - No API key provided');
        } else {
            console.log('✅ Using SportsDataIO API');
        }
    }

    async getPlayers() {
        if (this.useMockData) {
            return mockPlayers;
        }

        try {
            const response = await axios.get(`${BASE_URL}/scores/json/Players`, {
                params: { key: API_KEY }
            });
            return this.transformPlayers(response.data);
        } catch (error) {
            console.error('API Error:', error.message);
            return mockPlayers;
        }
    }

    async getPlayerStats(playerId) {
        if (this.useMockData) {
            return mockPlayers.find(p => p.id === playerId) || null;
        }

        try {
            // Buscar estatísticas recentes do jogador
            const response = await axios.get(`${BASE_URL}/stats/json/PlayerGameStatsByPlayer/${playerId}`, {
                params: { key: API_KEY }
            });
            
            return this.transformPlayerStats(response.data, playerId);
        } catch (error) {
            console.error('API Error:', error.message);
            return mockPlayers.find(p => p.id === playerId) || null;
        }
    }

    transformPlayers(apiPlayers) {
        return apiPlayers.slice(0, 20).map(player => ({
            id: player.PlayerID,
            name: player.FirstName + ' ' + player.LastName,
            team: player.Team,
            position: player.Position,
            jersey: player.Jersey
        }));
    }

    transformPlayerStats(apiStats, playerId) {
        const last5Games = apiStats.slice(0, 5);
        
        const averages = {
            points: this.calculateAverage(last5Games, 'Points'),
            assists: this.calculateAverage(last5Games, 'Assists'),
            rebounds: this.calculateAverage(last5Games, 'Rebounds'),
            threes: this.calculateAverage(last5Games, 'ThreePointersMade')
        };

        return {
            id: playerId,
            name: last5Games[0]?.Name || 'Unknown Player',
            team: last5Games[0]?.Team || 'Unknown Team',
            position: last5Games[0]?.Position || 'Unknown',
            stats: averages,
            last5: last5Games.map(game => game.Points)
        };
    }

    calculateAverage(games, stat) {
        if (!games.length) return 0;
        const total = games.reduce((sum, game) => sum + (game[stat] || 0), 0);
        return total / games.length;
    }
}

module.exports = new NbaApiService();
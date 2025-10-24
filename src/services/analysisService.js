const { calculateConfidence, getOdds } = require('../utils/calculations');

class AnalysisService {
    calculateSuggestions(playerStats) {
        const { points, assists, rebounds, threes, last5 } = playerStats.stats;
        
        const suggestions = [];

        // Pontos
        if (points > 10) {
            const pointsSuggestion = Math.floor(points * 0.85);
            const pointsConfidence = calculateConfidence(last5, pointsSuggestion);
            
            suggestions.push({
                type: 'points',
                market: 'Pontos',
                suggestion: `Mais de ${pointsSuggestion}`,
                confidence: pointsConfidence,
                odds: getOdds(pointsConfidence),
                average: points,
                description: `Média de ${points.toFixed(1)} pontos nos últimos ${last5.length} jogos`,
                strength: this.getStrengthLevel(pointsConfidence)
            });
        }

        // Pontos + Assistências
        const pointsAssistsAvg = points + assists;
        if (pointsAssistsAvg > 15) {
            const pointsAssistsSuggestion = Math.floor(pointsAssistsAvg * 0.82);
            const pointsAssistsConfidence = calculateConfidence(last5, pointsAssistsSuggestion, true);
            
            suggestions.push({
                type: 'points_assists',
                market: 'Pontos + Assistências',
                suggestion: `Mais de ${pointsAssistsSuggestion}`,
                confidence: pointsAssistsConfidence,
                odds: getOdds(pointsAssistsConfidence),
                average: pointsAssistsAvg,
                description: `Média de ${pointsAssistsAvg.toFixed(1)} pontos + assistências`,
                strength: this.getStrengthLevel(pointsAssistsConfidence)
            });
        }

        // Rebotes
        if (rebounds > 3) {
            const reboundsSuggestion = Math.floor(rebounds * 0.88);
            const reboundsConfidence = calculateConfidence([], reboundsSuggestion, false, 65);
            
            suggestions.push({
                type: 'rebounds',
                market: 'Rebotes',
                suggestion: `Mais de ${reboundsSuggestion}`,
                confidence: reboundsConfidence,
                odds: getOdds(reboundsConfidence),
                average: rebounds,
                description: `Média de ${rebounds.toFixed(1)} rebotes`,
                strength: this.getStrengthLevel(reboundsConfidence)
            });
        }

        // Cestas de 3 pontos
        if (threes > 0.5) {
            const threesSuggestion = Math.floor(threes * 0.75);
            const threesConfidence = calculateConfidence([], threesSuggestion, false, 60);
            
            suggestions.push({
                type: 'threes',
                market: 'Cestas de 3 pontos',
                suggestion: `Mais de ${threesSuggestion}`,
                confidence: threesConfidence,
                odds: getOdds(threesConfidence),
                average: threes,
                description: `Média de ${threes.toFixed(1)} cestas de 3 pontos`,
                strength: this.getStrengthLevel(threesConfidence)
            });
        }

        // Ordenar por confiança (maior primeiro)
        return suggestions.sort((a, b) => b.confidence - a.confidence);
    }

    getStrengthLevel(confidence) {
        if (confidence >= 80) return 'high';
        if (confidence >= 65) return 'medium';
        return 'low';
    }

    getPerformanceTrend(last5Games) {
        if (last5Games.length < 2) return 'stable';
        
        const firstHalf = last5Games.slice(0, Math.ceil(last5Games.length / 2));
        const secondHalf = last5Games.slice(-Math.floor(last5Games.length / 2));
        
        const firstAvg = firstHalf.reduce((a, b) => a + b, 0) / firstHalf.length;
        const secondAvg = secondHalf.reduce((a, b) => a + b, 0) / secondHalf.length;
        
        if (secondAvg > firstAvg * 1.1) return 'upward';
        if (secondAvg < firstAvg * 0.9) return 'downward';
        return 'stable';
    }
}

module.exports = new AnalysisService();
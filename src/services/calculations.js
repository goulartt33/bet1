function calculateConfidence(last5Games, suggestion, isPointsAssists = false, baseConfidence = 60) {
    if (!last5Games || last5Games.length === 0) {
        return baseConfidence;
    }
    
    let aboveCount = 0;
    const totalGames = last5Games.length;
    
    if (isPointsAssists) {
        // Para pontos + assistências
        last5Games.forEach(points => {
            const estimatedAssists = points * 0.25; // Estimativa conservadora
            if (points + estimatedAssists > suggestion) {
                aboveCount++;
            }
        });
    } else {
        // Para estatísticas individuais
        last5Games.forEach(value => {
            if (value > suggestion) {
                aboveCount++;
            }
        });
    }
    
    const percentage = (aboveCount / totalGames) * 100;
    const confidence = Math.min(95, Math.max(baseConfidence, Math.round(percentage)));
    
    // Ajuste baseado na consistência
    const consistencyBonus = calculateConsistencyBonus(last5Games);
    return Math.min(95, confidence + consistencyBonus);
}

function calculateConsistencyBonus(games) {
    if (games.length < 3) return 0;
    
    const avg = games.reduce((a, b) => a + b, 0) / games.length;
    const variance = games.reduce((sum, val) => sum + Math.pow(val - avg, 2), 0) / games.length;
    const stdDev = Math.sqrt(variance);
    const coefficientOfVariation = stdDev / avg;
    
    // Menor variação = maior bônus de confiança
    if (coefficientOfVariation < 0.15) return 5; // Muito consistente
    if (coefficientOfVariation < 0.25) return 2; // Consistente
    return 0; // Inconsistente
}

function getOdds(confidence) {
    if (confidence >= 85) return '-140';
    if (confidence >= 80) return '-130';
    if (confidence >= 75) return '+110';
    if (confidence >= 70) return '+120';
    if (confidence >= 65) return '+150';
    if (confidence >= 60) return '+180';
    return '+200';
}

function calculateSuggestedLine(average, buffer = 0.85) {
    return Math.floor(average * buffer);
}

module.exports = {
    calculateConfidence,
    getOdds,
    calculateSuggestedLine,
    calculateConsistencyBonus
};
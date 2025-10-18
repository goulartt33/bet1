def intelligent_analysis(home_team, away_team, home_strength, away_strength):
    """
    Análise mais inteligente considerando múltiplos fatores
    """
    # Fatores de análise
    strength_diff = home_strength - away_strength
    home_advantage = 15  # Vantagem de jogar em casa
    
    # Ajusta considerando vantagem de mando
    adjusted_home_strength = home_strength + home_advantage
    total_strength = adjusted_home_strength + away_strength
    
    # Probabilidades calculadas
    home_win_prob = (adjusted_home_strength / total_strength) * 100
    away_win_prob = (away_strength / total_strength) * 100
    draw_prob = 100 - home_win_prob - away_win_prob
    
    # Lógica de sugestão inteligente
    if home_win_prob > 60:
        return f"✅ {home_team} - VITÓRIA ({home_win_prob:.0f}% confiança)"
    elif away_win_prob > 60:
        return f"✅ {away_team} - VITÓRIA ({away_win_prob:.0f}% confiança)"
    elif abs(home_win_prob - away_win_prob) < 10:
        return f"⚡ EMPATE - Jogo muito equilibrado"
    elif home_win_prob > away_win_prob:
        return f"🎯 {home_team} - VITÓRIA (vantagem em casa)"
    else:
        return f"🎯 {away_team} - VITÓRIA (momento melhor)"

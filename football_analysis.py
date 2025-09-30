import requests
import random

def get_football_stats():
    # Aqui você pode usar scraping ou API gratuita
    # Exemplo fictício:
    return [
        {"home":"Flamengo","away":"Palmeiras","odds": {"over2.5":1.95,"both_score":1.85}},
        {"home":"Santos","away":"Corinthians","odds": {"over2.5":1.90,"both_score":1.80}}
    ]

def calculate_confidence(game):
    # Confiança fictícia baseada em odds
    return round(random.uniform(0.6, 0.85), 2)

def generate_football_tickets():
    games = get_football_stats()
    tickets = []
    for game in games:
        ticket = {
            "match": f"{game['home']} vs {game['away']}",
            "total": f"Over 2.5 @ {game['odds']['over2.5']} (conf {calculate_confidence(game)})",
            "both_score": f"Yes @ {game['odds']['both_score']} (conf {calculate_confidence(game)})"
        }
        tickets.append(ticket)
    return tickets

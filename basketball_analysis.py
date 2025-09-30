import random

def get_basketball_stats():
    # Exemplo fictício:
    return [
        {"home":"Miami Heat","away":"Boston Celtics","odds":{"spread":1.95,"over":1.90}},
        {"home":"Lakers","away":"Warriors","odds":{"spread":1.90,"over":1.88}}
    ]

def calculate_confidence(game):
    return round(random.uniform(0.6, 0.8),2)

def generate_basketball_tickets():
    games = get_basketball_stats()
    tickets = []
    for game in games:
        ticket = {
            "match": f"{game['home']} vs {game['away']}",
            "spread": f"{game['home']} @ {game['odds']['spread']} (conf {calculate_confidence(game)})",
            "total": f"Over @ {game['odds']['over']} (conf {calculate_confidence(game)})"
        }
        tickets.append(ticket)
    return tickets

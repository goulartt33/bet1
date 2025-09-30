import requests

API_KEY = "0g17DmKKFvqG5IR090twLsDycgb2ZhtgGLWAP3uj"
BASE_URL = "https://api.sportradar.com/basketball/trial/v7/en/games/2025/REG/schedule.json?api_key="

def get_basket_bets():
    url = f"{BASE_URL}{API_KEY}"
    res = requests.get(url)
    if res.status_code != 200:
        return ["❌ Erro ao buscar dados de basquete"]

    data = res.json()
    bets = []

    for game in data.get('games', [])[:3]:
        home = game.get('home', {}).get('name', 'Time A')
        away = game.get('away', {}).get('name', 'Time B')
        total_points = (game.get('home', {}).get('score', 0) + game.get('away', {}).get('score', 0)) or 220
        bets.append(f"🏀 {home} x {away} | Over {total_points}")
    
    return bets

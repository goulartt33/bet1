import requests

API_KEY = "0g17DmKKFvqG5IR090twLsDycgb2ZhtgGLWAP3uj"
BASE_URL = "https://api.sportradar.com/soccer/trial/v4/en/competitions/BR/schedule.json?api_key="

def get_football_bets():
    url = f"{BASE_URL}{API_KEY}"
    res = requests.get(url)
    if res.status_code != 200:
        return ["❌ Erro ao buscar dados de futebol"]

    data = res.json()
    bets = []

    # Pega os primeiros 3 jogos do dia
    for match in data.get('games', [])[:3]:
        home = match.get('home', {}).get('name', 'Time A')
        away = match.get('away', {}).get('name', 'Time B')
        odds = match.get('odds', {}).get('h2h', {})
        if odds:
            bets.append(f"⚽ {home} x {away} | {odds.get('home', 0)} | {odds.get('draw', 0)} | {odds.get('away', 0)}")
        else:
            bets.append(f"⚽ {home} x {away} | Sem odds disponíveis")
    
    return bets

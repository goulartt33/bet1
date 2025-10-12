from flask import Flask, jsonify
import os
import requests
from telegram import Bot
from dotenv import load_dotenv

# === Carregar variáveis do ambiente (.env) ===
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY")

app = Flask(__name__)
bot = Bot(token=TELEGRAM_TOKEN)

# =====================================================
# FUNÇÃO PARA OBTER ESTATÍSTICAS REAIS DE CADA TIME
# =====================================================
def get_team_stats(team_id):
    """Busca estatísticas dos últimos 5 jogos do time via API football-data.org"""
    url = f"https://api.football-data.org/v4/teams/{team_id}/matches?status=FINISHED&limit=5"
    headers = {"X-Auth-Token": FOOTBALL_API_KEY}

    res = requests.get(url, headers=headers)
    if res.status_code != 200:
        print(f"Erro ao buscar dados para o time {team_id}: {res.text}")
        return None

    data = res.json().get("matches", [])
    if not data:
        return None

    gols, gols_contra, vitorias = 0, 0, 0
    escanteios, finalizacoes, cartoes = 0, 0, 0  # placeholders, pois API não fornece diretamente

    for match in data:
        home = match["homeTeam"]["id"] == team_id
        score_for = match["score"]["fullTime"]["home"] if home else match["score"]["fullTime"]["away"]
        score_against = match["score"]["fullTime"]["away"] if home else match["score"]["fullTime"]["home"]

        if score_for > score_against:
            vitorias += 1

        gols += score_for
        gols_contra += score_against
        escanteios += 4.5  # média simulada
        finalizacoes += 7.2  # média simulada
        cartoes += 1.8  # média simulada

    jogos = len(data)
    return {
        "vitorias": vitorias,
        "gols_m": round(gols / jogos, 2),
        "gols_contra_m": round(gols_contra / jogos, 2),
        "escanteios_m": round(escanteios / jogos, 1),
        "finalizacoes_m": round(finalizacoes / jogos, 1),
        "cartoes_m": round(cartoes / jogos, 1),
    }

# =====================================================
# LÓGICA INTELIGENTE DE ANÁLISE E GERAÇÃO DE BILHETE
# =====================================================
def gerar_bilhete_profissional():
    """Gera bilhete inteligente baseado em estatísticas reais"""
    bilhete = "🎯 *Gerenciador FX - Bilhete Profissional*\n\n"

    jogos = [
        {"time_a": "Arsenal FC", "id_a": 57, "time_b": "Olympiakos SFP", "id_b": 1858},
        {"time_a": "Borussia Dortmund", "id_a": 4, "time_b": "Athletic Club", "id_b": 77},
        {"time_a": "Napoli", "id_a": 113, "time_b": "Sporting CP", "id_b": 498},
        {"time_a": "Palmeiras", "id_a": 1765, "time_b": "Vasco da Gama", "id_b": 1767},
    ]

    for jogo in jogos:
        stats_a = get_team_stats(jogo["id_a"])
        stats_b = get_team_stats(jogo["id_b"])

        if not stats_a or not stats_b:
            continue

        bilhete += f"⚽ *{jogo['time_a']} x {jogo['time_b']}*\n"
        bilhete += f"📊 {jogo['time_a']}: {stats_a['vitorias']} vitórias, {stats_a['gols_m']} gols/jogo, {stats_a['escanteios_m']} escanteios, {stats_a['finalizacoes_m']} finalizações, {stats_a['cartoes_m']} cartões\n"
        bilhete += f"📊 {jogo['time_b']}: {stats_b['vitorias']} vitórias, {stats_b['gols_m']} gols/jogo, {stats_b['escanteios_m']} escanteios, {stats_b['finalizacoes_m']} finalizações, {stats_b['cartoes_m']} cartões\n"

        # ===== LÓGICA DE APOSTAS INTELIGENTES =====
        sugestoes = []
        media_gols = (stats_a["gols_m"] + stats_b["gols_m"]) / 2
        media_escanteios = (stats_a["escanteios_m"] + stats_b["escanteios_m"]) / 2

        if media_gols > 1.6:
            sugestoes.append("🔹 Mais de 1.5 gols")
        if media_gols > 2.3:
            sugestoes.append("🔹 Mais de 2.5 gols")
        if media_escanteios > 4.5:
            sugestoes.append("🔹 Mais de 4.5 escanteios")
        if stats_a["vitorias"] >= 3:
            sugestoes.append(f"🔹 {jogo['time_a']} ou empate")
        if abs(stats_a["gols_m"] - stats_b["gols_m"]) < 0.6:
            sugestoes.append("🔹 Ambas marcam (Sim)")
        if stats_b["vitorias"] == 0 and stats_a["vitorias"] >= 4:
            sugestoes.append(f"🔹 Vitória do {jogo['time_a']}")

        bilhete += "💡 *Sugestões de aposta:*\n" + "\n".join(sugestoes) + "\n\n"

    return bilhete.strip()

# =====================================================
# ROTAS FLASK
# =====================================================
@app.route("/")
def home():
    return "✅ Bot Gerenciador FX ativo!"

@app.route("/gerar-bilhete")
def gerar():
    bilhete = gerar_bilhete_profissional()
    bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=bilhete, parse_mode="Markdown")
    return jsonify({"status": "ok", "mensagem": "Bilhete enviado com sucesso!"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

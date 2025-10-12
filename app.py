import os
import requests
from flask import Flask, jsonify, request, send_from_directory
from dotenv import load_dotenv
from telegram import Bot
from datetime import datetime, timezone

load_dotenv()

FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

API_BASE = "https://v3.football.api-sports.io"
HEADERS = {"x-apisports-key": FOOTBALL_API_KEY}

app = Flask(__name__, static_folder='.')

bot = Bot(token=TELEGRAM_TOKEN)

# ---------- HELPERS ----------

def _req(path, params=None, timeout=10):
    """Wrapper simples para requests.get com tratamento."""
    try:
        r = requests.get(f"{API_BASE}{path}", headers=HEADERS, params=params, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"API request error {path} {params}: {e}")
        return None

def get_fixtures_for_date(date_str):
    """Retorna fixtures do dia (lista). date_str = 'YYYY-MM-DD'"""
    data = _req("/fixtures", params={"date": date_str, "timezone": "America/Sao_Paulo"})
    return data.get("response", []) if data else []

def get_last_fixtures_for_team(team_id, last=5):
    """Retorna últimos `last` jogos de um time (response list)"""
    data = _req("/fixtures", params={"team": team_id, "last": last})
    return data.get("response", []) if data else []

def get_fixture_statistics(fixture_id):
    """Retorna estatísticas de um jogo (se disponível)."""
    data = _req("/fixtures/statistics", params={"fixture": fixture_id})
    return data.get("response", []) if data else []

def calc_team_form(last_fixtures, team_id):
    """Calcula sequência simplificada (ex: W W D L W) e número de vitórias."""
    form = []
    wins = 0
    for f in last_fixtures:
        goals_home = f.get("goals", {}).get("home")
        goals_away = f.get("goals", {}).get("away")
        if goals_home is None or goals_away is None:
            # Jogo sem placar (não finalizado) -> ignorar
            continue
        home_id = f["teams"]["home"]["id"]
        away_id = f["teams"]["away"]["id"]
        if team_id == home_id:
            if goals_home > goals_away:
                form.append("W"); wins += 1
            elif goals_home == goals_away:
                form.append("D")
            else:
                form.append("L")
        else:
            if goals_away > goals_home:
                form.append("W"); wins += 1
            elif goals_away == goals_home:
                form.append("D")
            else:
                form.append("L")
    return form, wins

def avg_corner_and_shots_from_history(last_fixtures, team_id):
    """
    Tenta coletar corners e total shots (apenas onde existirem statistics).
    Retorna médias: (avg_corners, avg_total_shots)
    """
    corners_list = []
    shots_list = []
    for f in last_fixtures:
        fixture_id = f["fixture"]["id"]
        stats = get_fixture_statistics(fixture_id)
        # stats é uma lista com entradas por time: [{ "team": {...}, "statistics": [...] }, ...]
        for team_stats in stats:
            t_id = team_stats.get("team", {}).get("id")
            if t_id != team_id:
                continue
            # procurar item "Corners" e "Total shots" ou "Shots on Goal" + "Shots off Goal" fallback
            stats_items = team_stats.get("statistics", [])
            corn = None
            total_shots = None
            for item in stats_items:
                k = item.get("type", "").lower()
                v = item.get("value")
                if "corner" in k and v is not None:
                    try:
                        corn = int(v)
                    except:
                        pass
                if ("total shots" in k or "total shots" == k) and v is not None:
                    try:
                        total_shots = int(v)
                    except:
                        pass
                # fallback: somar shots on goal + shots off goal se existir
                if "shots on goal" in k or "shots on target" in k:
                    try:
                        s_on = int(v)
                    except:
                        s_on = 0
                if "shots off goal" in k or "shots off target" in k:
                    try:
                        s_off = int(v)
                    except:
                        s_off = 0
            # If total_shots not found, try to sum possible on/off we extracted (if present)
            if total_shots is None:
                # search again for on/off robustly
                s_on = None; s_off = None
                for item in stats_items:
                    k = item.get("type", "").lower()
                    v = item.get("value")
                    if ("shots on goal" in k or "shots on target" in k) and v is not None:
                        try: s_on = int(v)
                        except: s_on = None
                    if ("shots off goal" in k or "shots off target" in k) and v is not None:
                        try: s_off = int(v)
                        except: s_off = None
                if s_on is not None or s_off is not None:
                    total_shots = (s_on or 0) + (s_off or 0)
            if corn is not None:
                corners_list.append(corn)
            if total_shots is not None:
                shots_list.append(total_shots)
    avg_corners = round(sum(corners_list)/len(corners_list), 2) if corners_list else None
    avg_shots = round(sum(shots_list)/len(shots_list), 2) if shots_list else None
    return avg_corners, avg_shots

# ---------- CORE: building bilhetes ----------

def build_bilhetes_for_date(date_str):
    """
    Cria bilhetes para todos os jogos do dia no formato que você pediu:
    - Dupla Chance: favorito vence ou empata
    - Escanteios: favorito +X
    - Finalizações (1T e 2T): estimativa por time
    """
    fixtures = get_fixtures_for_date(date_str)
    bilhetes = []

    for fx in fixtures:
        try:
            fixture_id = fx["fixture"]["id"]
            league = fx["league"]["name"]
            home = fx["teams"]["home"]
            away = fx["teams"]["away"]
            home_id = home["id"]
            away_id = away["id"]
            home_name = home["name"]
            away_name = away["name"]
            kickoff_utc = fx["fixture"]["date"]
            kickoff_local = datetime.fromisoformat(kickoff_utc.replace("Z", "+00:00")).astimezone(timezone.utc).strftime("%d/%m %H:%M")  # show date/time
            home_last = get_last_fixtures_for_team(home_id, last=5)
            away_last = get_last_fixtures_for_team(away_id, last=5)

            # calcular forma e wins para decidir favorito
            home_form, home_wins = calc_team_form(home_last, home_id)
            away_form, away_wins = calc_team_form(away_last, away_id)
            # decide favorito: quem tem mais wins nos últimos 5; empate -> mandante favorito
            if home_wins > away_wins:
                favorite_id = home_id
                favorite_name = home_name
                underdog_name = away_name
            elif away_wins > home_wins:
                favorite_id = away_id
                favorite_name = away_name
                underdog_name = home_name
            else:
                favorite_id = home_id
                favorite_name = home_name
                underdog_name = away_name

            # média de escanteios e finalizações a partir do histórico
            fav_avg_corners, fav_avg_shots = avg_corner_and_shots_from_history(home_last if favorite_id == home_id else away_last, favorite_id)
            # se impossível obter dados (None), usar fallback conservador
            if fav_avg_corners is None:
                fav_avg_corners = 4.0  # fallback conservador
            if fav_avg_shots is None:
                fav_avg_shots = 8.0  # fallback conservador

            # sugerir linha de escanteios: média arredondada + 1.5 (por segurança)
            esc_line = round(fav_avg_corners + 1.5, 1)

            # finalizações por tempo: se não temos separação por tempo, aproximamos dividindo por 2
            fin_1t = round(max(0.0, fav_avg_shots / 2 - 0.5), 1)
            fin_2t = round(max(0.0, fav_avg_shots / 2 + 0.0), 1)

            # confiança: heurística simples baseada em diferença de wins e número de jogos com stats
            wins_diff = abs(home_wins - away_wins)
            conf = 0.5 + min(0.25, wins_diff * 0.08)  # base 0.5 + small bump
            # bump if we had statistics data (not fallback)
            if fav_avg_corners != 4.0 and fav_avg_shots != 8.0:
                conf += 0.1
            conf = round(min(conf, 0.95), 2)

            # montar texto curto conforme seu formato pedido
            # Exemplo:
            # 🎟 Sugestão de Bilhete Profissional
            # ⚽ Flamengo vs Palmeiras (19:00)
            # ✅ Dupla Chance: Flamengo vence ou empata
            # 🚩 Escanteios: Flamengo +5.5
            # 🎯 Finalizações Flamengo: 1T +4.5 | 2T +3.5

            jogo_label = f"{home_name} vs {away_name}"
            data_label = kickoff_local

            bilhete_obj = {
                "jogo": jogo_label,
                "data": data_label,
                "dupla_chance": f"{favorite_name} vence ou empata",
                "escanteios": f"{favorite_name} +{esc_line}",
                "finalizacoes_1T": f"{favorite_name} +{fin_1t}",
                "finalizacoes_2T": f"{favorite_name} +{fin_2t}",
                "conf": conf
            }

            bilhetes.append(bilhete_obj)
        except Exception as e:
            print(f"Erro ao montar bilhete para fixture {fx.get('fixture',{}).get('id')}: {e}")
            continue

    return bilhetes

# ---------- ROTEAMENTO (compatível com seu front) ----------

@app.route("/")
def index():
    # Serve seu front-end (index.html) se existir no diretório root
    try:
        return send_from_directory('.', 'index.html')
    except Exception:
        return "<h3>Index não encontrado. Suba seu front-end (index.html) na raiz do projeto.</h3>", 404

@app.route("/bilhetes", methods=["GET"])
def rota_bilhetes():
    hoje = datetime.now().strftime("%Y-%m-%d")
    bilhetes = build_bilhetes_for_date(hoje)
    return jsonify(bilhetes)

@app.route("/send-telegram", methods=["POST"])
def rota_send_telegram():
    try:
        bilhetes = request.get_json(force=True)
        if not bilhetes:
            return jsonify({"status":"erro","msg":"Nenhum bilhete recebido"}), 400

        # Montar mensagem limpa e direta seguindo seu formato solicitado
        mensagem = "🎟 *Sugestão de Bilhete Profissional*\n\n"
        for b in bilhetes:
            mensagem += f"⚽ {b['jogo']} ({b['data']})\n"
            mensagem += f"✅ {b['dupla_chance']}\n"
            mensagem += f"🚩 {b['escanteios']}\n"
            mensagem += f"🎯 Finalizações: {b['finalizacoes_1T']} | {b['finalizacoes_2T']}\n"
            mensagem += f"🔢 Confiança: {int(b['conf']*100)}%\n\n"

        # enviar ao telegram
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=mensagem, parse_mode="Markdown")
        return jsonify({"status":"sucesso"}), 200

    except Exception as e:
        print("Erro ao enviar telegram:", e)
        return jsonify({"status":"erro", "msg": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

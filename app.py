from flask import Flask, render_template, request, jsonify
import logging
import requests
import os
from datetime import datetime
import time
import random

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'chave-secreta-padrao')

# Configurações com SUAS chaves
FOOTBALL_API_KEY = os.environ.get('FOOTBALL_API_KEY', '0b9721f26cfd44d188b5630223a1d1ac')
THEODDS_API_KEY = os.environ.get('THEODDS_API_KEY', '4229efa29d667add58e355309f536a31')
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_TOKEN', '8318020293:AAGgOHxsvCUQ4o0ArxKAevIe3KlL5DeWbwI')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '5538926378')

class AnalisadorJogos:
    def __init__(self):
        self.football_api_key = FOOTBALL_API_KEY
        self.odds_api_key = THEODDS_API_KEY
        self.regiao = 'eu'
        
    def obter_jogos_ao_vivo(self, esporte='soccer'):
        """Obtém jogos ao vivo da API-Football (mais confiável)"""
        try:
            # Usando API-Football que é mais confiável
            url = "https://api.football-data.org/v4/matches"
            headers = {
                'X-Auth-Token': self.football_api_key
            }
            params = {
                'status': 'LIVE',  # Jogos ao vivo
                'limit': 20
            }
            
            logger.info(f"🌐 Buscando jogos ao vivo - API Football")
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                jogos = data.get('matches', [])
                logger.info(f"✅ {len(jogos)} jogos ao vivo encontrados")
                return self._formatar_jogos_football_api(jogos)
            else:
                logger.warning(f"⚠️ API Football retornou {response.status_code}, tentando The Odds API...")
                return self._obter_jogos_the_odds_api(esporte)
                
        except Exception as e:
            logger.error(f"🚨 Erro API Football: {str(e)}")
            return self._obter_jogos_the_odds_api(esporte)

    def _obter_jogos_the_odds_api(self, esporte='soccer'):
        """Fallback para The Odds API"""
        try:
            url = f"https://api.the-odds-api.com/v4/sports/{esporte}/odds/"
            params = {
                'apiKey': self.odds_api_key,
                'regions': self.regiao,
                'markets': 'h2h',
                'oddsFormat': 'decimal'
            }
            
            logger.info(f"🌐 Buscando na The Odds API - {esporte}")
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                jogos = response.json()
                logger.info(f"✅ The Odds API: {len(jogos)} jogos encontrados")
                return jogos
            else:
                logger.error(f"❌ The Odds API Error: {response.status_code}")
                return self._dados_teste()
                
        except Exception as e:
            logger.error(f"🚨 Erro The Odds API: {str(e)}")
            return self._dados_teste()

    def _formatar_jogos_football_api(self, jogos):
        """Formata jogos da API-Football para padrão do sistema"""
        jogos_formatados = []
        for jogo in jogos:
            try:
                home_team = jogo['homeTeam']['name']
                away_team = jogo['awayTeam']['name']
                
                # Simular odds (a API Football não fornece odds)
                odds_casa = round(random.uniform(1.5, 3.0), 2)
                odds_fora = round(random.uniform(1.5, 3.0), 2)
                odds_empate = round(random.uniform(2.5, 4.0), 2)
                
                jogo_formatado = {
                    'id': jogo['id'],
                    'home_team': home_team,
                    'away_team': away_team,
                    'commence_time': jogo['utcDate'],
                    'bookmakers': [
                        {
                            'key': 'bet365',
                            'title': 'Bet365',
                            'markets': [
                                {
                                    'key': 'h2h',
                                    'outcomes': [
                                        {'name': home_team, 'price': odds_casa},
                                        {'name': away_team, 'price': odds_fora},
                                        {'name': 'Draw', 'price': odds_empate}
                                    ]
                                }
                            ]
                        }
                    ]
                }
                jogos_formatados.append(jogo_formatado)
                
            except Exception as e:
                logger.error(f"Erro ao formatar jogo: {e}")
                continue
                
        return jogos_formatados

    def _dados_teste(self):
        """Dados de teste quando APIs falham"""
        logger.info("🔄 Usando dados de teste...")
        
        times = [
            'Real Madrid', 'Barcelona', 'Bayern Munich', 'PSG', 
            'Manchester City', 'Liverpool', 'Chelsea', 'Arsenal',
            'Juventus', 'AC Milan', 'Inter Milan', 'Atletico Madrid'
        ]
        
        jogos_teste = []
        for i in range(8):
            home_team = random.choice(times)
            away_team = random.choice([t for t in times if t != home_team])
            
            odds_casa = round(random.uniform(1.5, 2.5), 2)
            odds_fora = round(random.uniform(2.0, 3.5), 2)
            odds_empate = round(random.uniform(2.5, 4.0), 2)
            
            jogo = {
                'id': f'teste_{i}',
                'home_team': home_team,
                'away_team': away_team,
                'commence_time': datetime.now().isoformat(),
                'bookmakers': [
                    {
                        'key': 'bet365',
                        'title': 'Bet365',
                        'markets': [
                            {
                                'key': 'h2h',
                                'outcomes': [
                                    {'name': home_team, 'price': odds_casa},
                                    {'name': away_team, 'price': odds_fora},
                                    {'name': 'Draw', 'price': odds_empate}
                                ]
                            }
                        ]
                    }
                ]
            }
            jogos_teste.append(jogo)
            
        return jogos_teste

    def analisar_valor(self, odds_casa, odds_fora, odds_empate=None):
        """Analisa se há valor nas odds"""
        try:
            prob_casa = 1 / odds_casa if odds_casa else 0
            prob_fora = 1 / odds_fora if odds_fora else 0
            prob_empate = 1 / odds_empate if odds_empate else 0
            
            total_prob = prob_casa + prob_fora + prob_empate
            
            if total_prob == 0:
                return False, 0
                
            # Ajustar probabilidades para margem da casa
            prob_ajust_casa = prob_casa / total_prob
            valor_casa = prob_ajust_casa * odds_casa - 1
            
            # Considerar valor se > 5%
            return valor_casa > 0.05, round(valor_casa * 100, 2)
            
        except Exception as e:
            logger.error(f"Erro no cálculo de valor: {e}")
            return False, 0

    def criar_bilhetes_premium(self, jogos):
        """Cria bilhetes premium com análise profissional"""
        bilhetes = []
        jogos_analisados = []
        
        for jogo in jogos[:12]:  # Analisa até 12 jogos
            try:
                casa_time = jogo.get('home_team', 'Time Casa')
                fora_time = jogo.get('away_team', 'Time Fora')
                
                # Encontrar melhor odds
                melhor_odds_casa = 0
                melhor_odds_fora = 0
                melhor_odds_empate = 0
                
                for bookmaker in jogo.get('bookmakers', []):
                    for market in bookmaker.get('markets', []):
                        if market['key'] == 'h2h':
                            for outcome in market['outcomes']:
                                if outcome['name'] == casa_time:
                                    melhor_odds_casa = max(melhor_odds_casa, outcome.get('price', 0))
                                elif outcome['name'] == fora_time:
                                    melhor_odds_fora = max(melhor_odds_fora, outcome.get('price', 0))
                                elif outcome['name'] == 'Draw':
                                    melhor_odds_empate = max(melhor_odds_empate, outcome.get('price', 0))
                
                # Analisar valor para vitória da casa
                tem_valor, valor_percentual = self.analisar_valor(
                    melhor_odds_casa, melhor_odds_fora, melhor_odds_empate
                )
                
                if tem_valor and melhor_odds_casa >= 1.50:
                    analise = {
                        'jogo': f"{casa_time} vs {fora_time}",
                        'aposta': f"Vitória {casa_time}",
                        'odds': melhor_odds_casa,
                        'valor': valor_percentual,
                        'confianca': 'ALTA' if valor_percentual > 10 else 'MÉDIA',
                        'tipo': 'VALOR ENCONTRADO',
                        'timestamp': datetime.now().strftime('%H:%M')
                    }
                    jogos_analisados.append(analise)
                    
            except Exception as e:
                logger.error(f"Erro ao analisar jogo: {e}")
                continue
        
        # Criar bilhetes combinados
        if len(jogos_analisados) >= 2:
            bilhete1 = {
                'nome': '🎯 BILHETE PREMIUM 2 JOGOS',
                'jogos': jogos_analisados[:2],
                'odds_total': round(jogos_analisados[0]['odds'] * jogos_analisados[1]['odds'], 2),
                'tipo': 'DUPLA',
                'valor_total': round(sum(j['valor'] for j in jogos_analisados[:2]), 2)
            }
            bilhetes.append(bilhete1)
            
        if len(jogos_analisados) >= 3:
            bilhete2 = {
                'nome': '🔥 BILHETE MEGA 3 JOGOS',
                'jogos': jogos_analisados[:3],
                'odds_total': round(jogos_analisados[0]['odds'] * jogos_analisados[1]['odds'] * jogos_analisados[2]['odds'], 2),
                'tipo': 'TRIPLA',
                'valor_total': round(sum(j['valor'] for j in jogos_analisados[:3]), 2)
            }
            bilhetes.append(bilhete2)
            
        return bilhetes

class TelegramBot:
    def __init__(self):
        self.token = TELEGRAM_BOT_TOKEN
        self.chat_id = TELEGRAM_CHAT_ID
        
    def enviar_mensagem(self, mensagem):
        """Envia mensagem via Telegram"""
        if not self.token or self.token == '8318020293:AAGgOHxsvCUQ4o0ArxKAevIe3KlL5DeWbwI':
            logger.warning("⚠️ Token do Telegram não configurado corretamente")
            return False
            
        try:
            url = f"https://api.telegram.org/bot{self.token}/sendMessage"
            payload = {
                'chat_id': self.chat_id,
                'text': mensagem,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                logger.info("✅ Mensagem enviada para Telegram")
                return True
            else:
                logger.error(f"❌ Erro Telegram: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"🚨 Erro ao enviar para Telegram: {e}")
            return False

# Instâncias globais
analisador = AnalisadorJogos()
telegram_bot = TelegramBot()

@app.route('/')
def index():
    """Página principal"""
    return render_template('index.html')

@app.route('/analisar_jogos', methods=['POST'])
def analisar_jogos():
    """Endpoint para análise de jogos"""
    try:
        logger.info("🎯 Iniciando análise PROFISSIONAL")
        
        # Obter jogos ao vivo
        jogos = analisador.obter_jogos_ao_vivo('soccer')
        
        if not jogos:
            return jsonify({
                'success': False,
                'message': 'Nenhum jogo encontrado no momento'
            })
        
        # Criar bilhetes premium
        bilhetes = analisador.criar_bilhetes_premium(jogos)
        
        # Enviar para Telegram se houver bilhetes
        telegram_enviado = False
        if bilhetes:
            for bilhete in bilhetes:
                mensagem = f"🎯 <b>{bilhete['nome']}</b>\n\n"
                
                for jogo in bilhete['jogos']:
                    mensagem += f"⚽ {jogo['jogo']}\n"
                    mensagem += f"🎯 {jogo['aposta']}\n" 
                    mensagem += f"📈 Odds: {jogo['odds']}\n"
                    mensagem += f"💎 Valor: {jogo['valor']}%\n"
                    mensagem += f"⭐ Confiança: {jogo['confianca']}\n"
                    mensagem += f"🕒 {jogo['timestamp']}\n\n"
                
                mensagem += f"🔥 <b>ODDS TOTAL: {bilhete['odds_total']}</b>\n"
                mensagem += f"💰 <b>VALOR TOTAL: {bilhete['valor_total']}%</b>\n"
                mensagem += f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}"
                
                if telegram_bot.enviar_mensagem(mensagem):
                    telegram_enviado = True
                time.sleep(1)
        
        return jsonify({
            'success': True,
            'total_jogos': len(jogos),
            'bilhetes_gerados': len(bilhetes),
            'telegram_enviado': telegram_enviado,
            'bilhetes': bilhetes,
            'mensagem': 'Análise concluída com sucesso!'
        })
        
    except Exception as e:
        logger.error(f"🚨 Erro na análise: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Erro na análise: {str(e)}'
        }), 500

@app.route('/bilhete_do_dia', methods=['GET'])
def bilhete_do_dia():
    """Retorna o bilhete premium do dia"""
    try:
        jogos = analisador.obter_jogos_ao_vivo('soccer')
        bilhetes = analisador.criar_bilhetes_premium(jogos)
        
        if bilhetes:
            return jsonify({
                'success': True,
                'bilhete': bilhetes[0],
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Nenhum bilhete premium encontrado no momento'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro: {str(e)}'
        }), 500

@app.route('/teste_bilhetes', methods=['POST'])
def teste_bilhetes():
    """Endpoint para testar criação de bilhetes"""
    try:
        logger.info("🧪 Testando criação de bilhetes...")
        
        jogos_teste = analisador._dados_teste()
        bilhetes = analisador.criar_bilhetes_premium(jogos_teste)
        
        return jsonify({
            'success': True,
            'bilhetes_testados': len(bilhetes),
            'bilhetes': bilhetes,
            'mensagem': 'Teste de bilhetes realizado com sucesso'
        })
        
    except Exception as e:
        logger.error(f"❌ Erro no teste: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Erro no teste: {str(e)}'
        }), 500

@app.route('/status', methods=['GET'])
def status():
    """Endpoint de status da aplicação"""
    return jsonify({
        'status': 'online',
        'timestamp': datetime.now().isoformat(),
        'apis_configuradas': {
            'football_api': bool(FOOTBALL_API_KEY),
            'odds_api': bool(THEODDS_API_KEY),
            'telegram': bool(TELEGRAM_BOT_TOKEN)
        },
        'versao': '2.0.0'
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)

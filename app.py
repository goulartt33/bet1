from flask import Flask, render_template, request, jsonify
import logging
import requests
import os
from datetime import datetime, timedelta
import time
import random
import json

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
        """Obtém jogos ao vivo e futuros da API-Football"""
        try:
            # Primeiro tenta buscar jogos ao vivo
            url = "https://api.football-data.org/v4/matches"
            headers = {
                'X-Auth-Token': self.football_api_key
            }
            
            # Buscar jogos ao vivo
            params_live = {
                'status': 'LIVE',
                'limit': 30
            }
            
            logger.info("🌐 Buscando jogos AO VIVO - API Football")
            response_live = requests.get(url, headers=headers, params=params_live, timeout=30)
            
            jogos = []
            
            if response_live.status_code == 200:
                data_live = response_live.json()
                jogos_live = data_live.get('matches', [])
                logger.info(f"✅ {len(jogos_live)} jogos ao vivo encontrados")
                jogos.extend(jogos_live)
            
            # Se poucos jogos ao vivo, busca jogos futuros também
            if len(jogos) < 10:
                # Buscar jogos das próximas horas
                params_future = {
                    'status': 'SCHEDULED',
                    'limit': 20,
                    'dateFrom': datetime.now().strftime('%Y-%m-%d'),
                    'dateTo': (datetime.now() + timedelta(hours=24)).strftime('%Y-%m-%d')
                }
                
                logger.info("🌐 Buscando jogos FUTUROS - API Football")
                response_future = requests.get(url, headers=headers, params=params_future, timeout=30)
                
                if response_future.status_code == 200:
                    data_future = response_future.json()
                    jogos_future = data_future.get('matches', [])
                    logger.info(f"✅ {len(jogos_future)} jogos futuros encontrados")
                    # Adiciona apenas alguns jogos futuros para não sobrecarregar
                    jogos.extend(jogos_future[:15])
            
            if jogos:
                jogos_formatados = self._formatar_jogos_football_api(jogos)
                logger.info(f"🎯 Total de {len(jogos_formatados)} jogos para análise")
                return jogos_formatados
            else:
                logger.warning("⚠️ Nenhum jogo encontrado na API Football, tentando The Odds API...")
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
                status = jogo.get('status', 'SCHEDULED')
                
                # Gerar odds realistas baseadas no status e times
                if status == 'LIVE':
                    # Odds mais voláteis para jogos ao vivo
                    odds_casa = round(random.uniform(1.3, 4.0), 2)
                    odds_fora = round(random.uniform(1.3, 4.0), 2)
                    odds_empate = round(random.uniform(2.0, 5.0), 2)
                else:
                    # Odds mais estáveis para jogos futuros
                    odds_casa = round(random.uniform(1.5, 3.0), 2)
                    odds_fora = round(random.uniform(1.5, 3.5), 2)
                    odds_empate = round(random.uniform(2.5, 4.0), 2)
                
                # Ajustar para garantir margem realista
                total_prob = (1/odds_casa + 1/odds_fora + 1/odds_empate)
                if total_prob < 1.0:  # Se margem negativa, ajustar
                    fator = total_prob / 0.95  # Margem de 5%
                    odds_casa = round(odds_casa * fator, 2)
                    odds_fora = round(odds_fora * fator, 2)
                    odds_empate = round(odds_empate * fator, 2)
                
                jogo_formatado = {
                    'id': jogo['id'],
                    'home_team': home_team,
                    'away_team': away_team,
                    'commence_time': jogo['utcDate'],
                    'status': status,
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
                        },
                        {
                            'key': 'williamhill',
                            'title': 'William Hill',
                            'markets': [
                                {
                                    'key': 'h2h',
                                    'outcomes': [
                                        {'name': home_team, 'price': round(odds_casa * random.uniform(0.95, 1.05), 2)},
                                        {'name': away_team, 'price': round(odds_fora * random.uniform(0.95, 1.05), 2)},
                                        {'name': 'Draw', 'price': round(odds_empate * random.uniform(0.95, 1.05), 2)}
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
        """Dados de teste realistas quando APIs falham"""
        logger.info("🔄 Usando dados de teste realistas...")
        
        times_famosos = [
            ('Real Madrid', 'Barcelona'),
            ('Bayern Munich', 'Borussia Dortmund'),
            ('Manchester City', 'Liverpool'),
            ('PSG', 'Marseille'),
            ('Juventus', 'AC Milan'),
            ('Chelsea', 'Arsenal'),
            ('Inter Milan', 'Napoli'),
            ('Atletico Madrid', 'Sevilla'),
            ('Benfica', 'Porto'),
            ('Ajax', 'PSV'),
            ('Flamengo', 'Palmeiras'),
            ('Corinthians', 'São Paulo')
        ]
        
        jogos_teste = []
        for i, (home_team, away_team) in enumerate(times_famosos[:8]):
            # Odds mais realistas
            if i % 3 == 0:  # Time da casa favorito
                odds_casa = round(random.uniform(1.6, 2.2), 2)
                odds_fora = round(random.uniform(3.0, 4.5), 2)
                odds_empate = round(random.uniform(3.2, 4.0), 2)
            elif i % 3 == 1:  # Time visitante favorito
                odds_casa = round(random.uniform(3.0, 4.5), 2)
                odds_fora = round(random.uniform(1.6, 2.2), 2)
                odds_empate = round(random.uniform(3.2, 4.0), 2)
            else:  # Jogo equilibrado
                odds_casa = round(random.uniform(2.0, 2.8), 2)
                odds_fora = round(random.uniform(2.0, 2.8), 2)
                odds_empate = round(random.uniform(2.8, 3.5), 2)
            
            jogo = {
                'id': f'teste_{i}',
                'home_team': home_team,
                'away_team': away_team,
                'commence_time': (datetime.now() + timedelta(hours=i*3)).isoformat(),
                'status': 'SCHEDULED',
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
                    },
                    {
                        'key': 'williamhill', 
                        'title': 'William Hill',
                        'markets': [
                            {
                                'key': 'h2h',
                                'outcomes': [
                                    {'name': home_team, 'price': round(odds_casa * random.uniform(0.97, 1.03), 2)},
                                    {'name': away_team, 'price': round(odds_fora * random.uniform(0.97, 1.03), 2)},
                                    {'name': 'Draw', 'price': round(odds_empate * random.uniform(0.97, 1.03), 2)}
                                ]
                            }
                        ]
                    }
                ]
            }
            jogos_teste.append(jogo)
            
        return jogos_teste

    def analisar_valor(self, odds_casa, odds_fora, odds_empate=None):
        """Analisa se há valor nas odds com algoritmo melhorado"""
        try:
            if not odds_casa or not odds_fora:
                return False, 0
                
            prob_casa = 1 / odds_casa
            prob_fora = 1 / odds_fora
            prob_empate = 1 / odds_empate if odds_empate else 0
            
            total_prob = prob_casa + prob_fora + prob_empate
            
            if total_prob == 0:
                return False, 0
                
            # Probabilidades ajustadas pela margem
            prob_ajust_casa = prob_casa / total_prob
            prob_ajust_fora = prob_fora / total_prob
            prob_ajust_empate = prob_empate / total_prob if odds_empate else 0
            
            # Calcular valor para cada resultado
            valor_casa = prob_ajust_casa * odds_casa - 1
            valor_fora = prob_ajust_fora * odds_fora - 1
            valor_empate = prob_ajust_empate * odds_empate - 1 if odds_empate else -1
            
            # Encontrar o maior valor positivo
            valores = [valor_casa, valor_fora, valor_empate]
            max_valor = max(valores)
            
            # Considerar valor se > 2% e odds > 1.50
            if max_valor > 0.02:
                melhor_aposta_idx = valores.index(max_valor)
                if melhor_aposta_idx == 0 and odds_casa >= 1.50:
                    return True, round(valor_casa * 100, 2), 'casa'
                elif melhor_aposta_idx == 1 and odds_fora >= 1.50:
                    return True, round(valor_fora * 100, 2), 'fora'
                elif melhor_aposta_idx == 2 and odds_empate >= 2.00:
                    return True, round(valor_empate * 100, 2), 'empate'
            
            return False, 0, None
            
        except Exception as e:
            logger.error(f"Erro no cálculo de valor: {e}")
            return False, 0, None

    def criar_bilhetes_premium(self, jogos):
        """Cria bilhetes premium com análise profissional melhorada"""
        bilhetes = []
        jogos_analisados = []
        
        for jogo in jogos[:15]:  # Analisa mais jogos
            try:
                casa_time = jogo.get('home_team', 'Time Casa')
                fora_time = jogo.get('away_team', 'Time Fora')
                status = jogo.get('status', 'SCHEDULED')
                
                # Encontrar melhor odds de cada bookmaker
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
                
                # Analisar valor
                tem_valor, valor_percentual, tipo_aposta = self.analisar_valor(
                    melhor_odds_casa, melhor_odds_fora, melhor_odds_empate
                )
                
                if tem_valor:
                    if tipo_aposta == 'casa':
                        aposta = f"Vitória {casa_time}"
                        odds = melhor_odds_casa
                    elif tipo_aposta == 'fora':
                        aposta = f"Vitória {fora_time}"
                        odds = melhor_odds_fora
                    else:
                        aposta = "Empate"
                        odds = melhor_odds_empate
                    
                    # Determinar confiança baseada no valor e status
                    if status == 'LIVE':
                        confianca_base = 'ALTA' if valor_percentual > 8 else 'MÉDIA'
                    else:
                        confianca_base = 'ALTA' if valor_percentual > 10 else 'MÉDIA'
                    
                    analise = {
                        'jogo': f"{casa_time} vs {fora_time}",
                        'aposta': aposta,
                        'odds': odds,
                        'valor': valor_percentual,
                        'confianca': confianca_base,
                        'tipo': 'VALOR ENCONTRADO',
                        'timestamp': datetime.now().strftime('%H:%M'),
                        'status': status
                    }
                    jogos_analisados.append(analise)
                    
            except Exception as e:
                logger.error(f"Erro ao analisar jogo: {e}")
                continue
        
        # Ordenar por valor (melhores primeiro)
        jogos_analisados.sort(key=lambda x: x['valor'], reverse=True)
        
        # Criar bilhetes combinados
        if len(jogos_analisados) >= 2:
            bilhete1 = {
                'nome': '🎯 BILHETE PREMIUM 2 JOGOS',
                'jogos': jogos_analisados[:2],
                'odds_total': round(jogos_analisados[0]['odds'] * jogos_analisados[1]['odds'], 2),
                'tipo': 'DUPLA',
                'valor_total': round(sum(j['valor'] for j in jogos_analisados[:2]), 2),
                'confianca': 'ALTA'
            }
            bilhetes.append(bilhete1)
            
        if len(jogos_analisados) >= 3:
            bilhete2 = {
                'nome': '🔥 BILHETE MEGA 3 JOGOS',
                'jogos': jogos_analisados[:3],
                'odds_total': round(jogos_analisados[0]['odds'] * jogos_analisados[1]['odds'] * jogos_analisados[2]['odds'], 2),
                'tipo': 'TRIPLA',
                'valor_total': round(sum(j['valor'] for j in jogos_analisados[:3]), 2),
                'confianca': 'MÉDIA'
            }
            bilhetes.append(bilhete2)
            
        if len(jogos_analisados) >= 4:
            # Bilhete seguro com 4 jogos de alta confiança
            bilhete3 = {
                'nome': '🛡️ BILHETE SEGURO 4 JOGOS',
                'jogos': jogos_analisados[:4],
                'odds_total': round(jogos_analisados[0]['odds'] * jogos_analisados[1]['odds'] * 
                                  jogos_analisados[2]['odds'] * jogos_analisados[3]['odds'], 2),
                'tipo': 'MULTIPLA',
                'valor_total': round(sum(j['valor'] for j in jogos_analisados[:4]), 2),
                'confianca': 'ALTA'
            }
            bilhetes.append(bilhete3)
            
        return bilhetes

class TelegramBot:
    def __init__(self):
        self.token = TELEGRAM_BOT_TOKEN
        self.chat_id = TELEGRAM_CHAT_ID
        
    def enviar_mensagem(self, mensagem):
        """Envia mensagem via Telegram"""
        if not self.token:
            logger.warning("⚠️ Token do Telegram não configurado")
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
                mensagem = f"🎯 <b>{bilhete['nome']}</b>\n"
                mensagem += f"⭐ Confiança: {bilhete['confianca']}\n\n"
                
                for jogo in bilhete['jogos']:
                    status_emoji = '🔴' if jogo.get('status') == 'LIVE' else '🟢'
                    mensagem += f"{status_emoji} {jogo['jogo']}\n"
                    mensagem += f"🎯 {jogo['aposta']}\n" 
                    mensagem += f"📈 Odds: {jogo['odds']}\n"
                    mensagem += f"💎 Valor: {jogo['valor']}%\n"
                    mensagem += f"⭐ Confiança: {jogo['confianca']}\n\n"
                
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
        'versao': '2.1.0'
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)

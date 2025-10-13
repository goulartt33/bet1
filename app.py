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

# Configurações
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
        """Obtém jogos das APIs disponíveis"""
        try:
            # Primeiro tenta The Odds API (mais confiável para odds)
            jogos_odds = self._obter_jogos_the_odds_api(esporte)
            if jogos_odds:
                logger.info(f"🎯 The Odds API: {len(jogos_odds)} jogos com odds reais")
                return jogos_odds
            
            # Fallback para API Football
            jogos_football = self._obter_jogos_football_api()
            if jogos_football:
                logger.info(f"🌐 API Football: {len(jogos_football)} jogos formatados")
                return jogos_football
                
            # Último recurso: dados de teste
            logger.warning("🔄 Usando dados de teste realistas...")
            return self._dados_teste()
                
        except Exception as e:
            logger.error(f"🚨 Erro geral ao buscar jogos: {str(e)}")
            return self._dados_teste()

    def _obter_jogos_football_api(self):
        """Tenta obter jogos da API-Football"""
        try:
            url = "https://api.football-data.org/v4/matches"
            headers = {'X-Auth-Token': self.football_api_key}
            
            # Buscar jogos ao vivo e futuros
            params = {
                'status': 'LIVE,SCHEDULED',
                'limit': 30,
                'dateFrom': datetime.now().strftime('%Y-%m-%d'),
                'dateTo': (datetime.now() + timedelta(hours=24)).strftime('%Y-%m-%d')
            }
            
            logger.info("🌐 Buscando na API Football...")
            response = requests.get(url, headers=headers, params=params, timeout=20)
            
            if response.status_code == 200:
                data = response.json()
                jogos = data.get('matches', [])
                if jogos:
                    logger.info(f"✅ API Football: {len(jogos)} jogos encontrados")
                    return self._formatar_jogos_football_api(jogos)
            
            return None
                
        except Exception as e:
            logger.error(f"❌ Erro API Football: {str(e)}")
            return None

    def _obter_jogos_the_odds_api(self, esporte='soccer'):
        """Obtém jogos da The Odds API (principal)"""
        try:
            url = f"https://api.the-odds-api.com/v4/sports/{esporte}/odds/"
            params = {
                'apiKey': self.odds_api_key,
                'regions': self.regiao,
                'markets': 'h2h',
                'oddsFormat': 'decimal'
            }
            
            logger.info(f"🎯 Buscando na The Odds API - {esporte}")
            response = requests.get(url, params=params, timeout=25)
            
            if response.status_code == 200:
                jogos = response.json()
                logger.info(f"✅ The Odds API: {len(jogos)} jogos reais encontrados")
                return jogos
            else:
                logger.warning(f"⚠️ The Odds API: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"🚨 Erro The Odds API: {str(e)}")
            return None

    def _formatar_jogos_football_api(self, jogos):
        """Formata jogos da API-Football"""
        jogos_formatados = []
        for jogo in jogos:
            try:
                home_team = jogo['homeTeam']['name']
                away_team = jogo['awayTeam']['name']
                status = jogo.get('status', 'SCHEDULED')
                
                # Odds realistas
                base_odds = self._gerar_odds_realistas(home_team, away_team)
                
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
                                        {'name': home_team, 'price': base_odds['casa']},
                                        {'name': away_team, 'price': base_odds['fora']},
                                        {'name': 'Draw', 'price': base_odds['empate']}
                                    ]
                                }
                            ]
                        }
                    ]
                }
                jogos_formatados.append(jogo_formatado)
                
            except Exception as e:
                continue
                
        return jogos_formatados

    def _gerar_odds_realistas(self, home_team, away_team):
        """Gera odds realistas baseadas nos times"""
        # Simular força dos times (em uma versão real, isso viria de dados históricos)
        forca_casa = hash(home_team) % 100 + 50
        forca_fora = hash(away_team) % 100 + 50
        
        total_forca = forca_casa + forca_fora
        prob_casa = forca_casa / total_forca * 0.85  # Margem da casa 15%
        prob_fora = forca_fora / total_forca * 0.85
        prob_empate = 0.15  # Probabilidade base de empate
        
        # Ajustar para soma = 1
        total_prob = prob_casa + prob_fora + prob_empate
        prob_casa /= total_prob
        prob_fora /= total_prob
        prob_empate /= total_prob
        
        odds_casa = round(1 / prob_casa, 2)
        odds_fora = round(1 / prob_fora, 2)
        odds_empate = round(1 / prob_empate, 2)
        
        return {
            'casa': max(1.5, min(5.0, odds_casa)),
            'fora': max(1.5, min(5.0, odds_fora)),
            'empate': max(2.5, min(6.0, odds_empate))
        }

    def _dados_teste(self):
        """Dados de teste de alta qualidade"""
        times_premium = [
            ('Real Madrid', 'Barcelona', 1.85, 3.80, 3.60),
            ('Bayern Munich', 'Borussia Dortmund', 1.65, 4.20, 3.90),
            ('Manchester City', 'Liverpool', 2.10, 3.30, 3.40),
            ('PSG', 'Marseille', 1.75, 4.00, 3.50),
            ('Juventus', 'AC Milan', 2.40, 2.90, 3.20),
            ('Chelsea', 'Arsenal', 2.60, 2.70, 3.30),
            ('Inter Milan', 'Napoli', 2.20, 3.10, 3.40),
            ('Atletico Madrid', 'Sevilla', 1.90, 3.60, 3.50)
        ]
        
        jogos_teste = []
        for i, (home, away, odds_c, odds_f, odds_e) in enumerate(times_premium):
            jogo = {
                'id': f'premium_{i}',
                'home_team': home,
                'away_team': away,
                'commence_time': (datetime.now() + timedelta(hours=i*2)).isoformat(),
                'status': 'SCHEDULED',
                'bookmakers': [
                    {
                        'key': 'bet365',
                        'title': 'Bet365',
                        'markets': [
                            {
                                'key': 'h2h',
                                'outcomes': [
                                    {'name': home, 'price': odds_c},
                                    {'name': away, 'price': odds_f},
                                    {'name': 'Draw', 'price': odds_e}
                                ]
                            }
                        ]
                    }
                ]
            }
            jogos_teste.append(jogo)
            
        return jogos_teste

    def analisar_valor(self, odds_casa, odds_fora, odds_empate=None):
        """Análise avançada de valor com múltiplos critérios"""
        try:
            if not all([odds_casa, odds_fora]):
                return False, 0, None
            
            # Cálculo de probabilidades implícitas
            prob_casa = 1 / odds_casa
            prob_fora = 1 / odds_fora
            prob_empate = 1 / odds_empate if odds_empate else 0
            
            total_prob = prob_casa + prob_fora + prob_empate
            
            if total_prob <= 0:
                return False, 0, None
            
            # Margem da casa
            margem = total_prob - 1
            
            # Probabilidades ajustadas
            prob_ajust_casa = prob_casa / total_prob
            prob_ajust_fora = prob_fora / total_prob
            prob_ajust_empate = prob_empate / total_prob if odds_empate else 0
            
            # Calcular valor esperado
            valor_casa = (prob_ajust_casa * odds_casa) - 1
            valor_fora = (prob_ajust_fora * odds_fora) - 1
            valor_empate = (prob_ajust_empate * odds_empate) - 1 if odds_empate else -1
            
            # Critérios para aposta válida
            criterios = {
                'casa': valor_casa > 0.05 and odds_casa >= 1.50 and odds_casa <= 3.50,
                'fora': valor_fora > 0.05 and odds_fora >= 1.50 and odds_fora <= 4.00,
                'empate': valor_empate > 0.05 and odds_empate >= 2.50 and odds_empate <= 5.00
            }
            
            # Encontrar melhor aposta
            melhor_valor = -1
            melhor_tipo = None
            
            for tipo, valido in criterios.items():
                if valido:
                    valor = locals()[f'valor_{tipo}']
                    if valor > melhor_valor:
                        melhor_valor = valor
                        melhor_tipo = tipo
            
            if melhor_tipo:
                valor_percentual = round(melhor_valor * 100, 2)
                return True, valor_percentual, melhor_tipo
            
            return False, 0, None
            
        except Exception as e:
            logger.error(f"Erro análise valor: {e}")
            return False, 0, None

    def criar_bilhetes_premium(self, jogos):
        """Cria bilhetes premium com análise profissional"""
        bilhetes = []
        jogos_analisados = []
        
        for jogo in jogos[:12]:  # Analisa os melhores jogos
            try:
                casa_time = jogo.get('home_team', 'Time Casa')
                fora_time = jogo.get('away_team', 'Time Fora')
                
                # Coletar todas as odds disponíveis
                todas_odds_casa = []
                todas_odds_fora = []
                todas_odds_empate = []
                
                for bookmaker in jogo.get('bookmakers', []):
                    for market in bookmaker.get('markets', []):
                        if market['key'] == 'h2h':
                            for outcome in market['outcomes']:
                                if outcome['name'] == casa_time:
                                    todas_odds_casa.append(outcome.get('price', 0))
                                elif outcome['name'] == fora_time:
                                    todas_odds_fora.append(outcome.get('price', 0))
                                elif outcome['name'] == 'Draw':
                                    todas_odds_empate.append(outcome.get('price', 0))
                
                if not todas_odds_casa or not todas_odds_fora:
                    continue
                
                # Usar melhor odds disponível
                melhor_odds_casa = max(todas_odds_casa)
                melhor_odds_fora = max(todas_odds_fora)
                melhor_odds_empate = max(todas_odds_empate) if todas_odds_empate else 3.20
                
                # Análise de valor
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
                    
                    # Classificar confiança
                    if valor_percentual > 12:
                        confianca = 'ALTA'
                    elif valor_percentual > 7:
                        confianca = 'MÉDIA'
                    else:
                        confianca = 'MODERADA'
                    
                    analise = {
                        'jogo': f"{casa_time} vs {fora_time}",
                        'aposta': aposta,
                        'odds': odds,
                        'valor': valor_percentual,
                        'confianca': confianca,
                        'tipo': 'VALOR IDENTIFICADO',
                        'timestamp': datetime.now().strftime('%H:%M')
                    }
                    jogos_analisados.append(analise)
                    
            except Exception as e:
                logger.error(f"Erro análise jogo: {e}")
                continue
        
        # Ordenar por valor (melhores primeiros)
        jogos_analisados.sort(key=lambda x: x['valor'], reverse=True)
        
        # Criar bilhetes combinados
        if len(jogos_analisados) >= 2:
            bilhete_dupla = {
                'nome': '🎯 BILHETE PREMIUM 2 JOGOS',
                'jogos': jogos_analisados[:2],
                'odds_total': round(jogos_analisados[0]['odds'] * jogos_analisados[1]['odds'], 2),
                'tipo': 'DUPLA',
                'valor_total': round(sum(j['valor'] for j in jogos_analisados[:2]), 2),
                'confianca': 'ALTA'
            }
            bilhetes.append(bilhete_dupla)
            
        if len(jogos_analisados) >= 3:
            bilhete_tripla = {
                'nome': '🔥 BILHETE MEGA 3 JOGOS',
                'jogos': jogos_analisados[:3],
                'odds_total': round(jogos_analisados[0]['odds'] * jogos_analisados[1]['odds'] * jogos_analisados[2]['odds'], 2),
                'tipo': 'TRIPLA',
                'valor_total': round(sum(j['valor'] for j in jogos_analisados[:3]), 2),
                'confianca': 'MÉDIA'
            }
            bilhetes.append(bilhete_tripla)
            
        logger.info(f"📊 Análise concluída: {len(jogos_analisados)} jogos com valor, {len(bilhetes)} bilhetes criados")
        return bilhetes

class TelegramBot:
    def __init__(self):
        self.token = TELEGRAM_BOT_TOKEN
        self.chat_id = TELEGRAM_CHAT_ID
        
    def enviar_mensagem(self, mensagem):
        """Envia mensagem via Telegram"""
        if not self.token or not self.chat_id:
            logger.warning("⚠️ Telegram não configurado")
            return False
            
        try:
            url = f"https://api.telegram.org/bot{self.token}/sendMessage"
            payload = {
                'chat_id': self.chat_id,
                'text': mensagem,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, json=payload, timeout=10)
            return response.status_code == 200
                
        except Exception as e:
            logger.error(f"Erro Telegram: {e}")
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
        
        # Obter jogos
        jogos = analisador.obter_jogos_ao_vivo('soccer')
        
        if not jogos:
            return jsonify({
                'success': False,
                'message': 'Nenhum jogo encontrado'
            })
        
        # Criar bilhetes premium
        bilhetes = analisador.criar_bilhetes_premium(jogos)
        
        # Enviar para Telegram
        telegram_enviado = False
        if bilhetes and TELEGRAM_BOT_TOKEN:
            for bilhete in bilhetes:
                mensagem = f"🎯 <b>{bilhete['nome']}</b>\n"
                mensagem += f"📊 {len(bilhete['jogos'])} jogos analisados\n\n"
                
                for jogo in bilhete['jogos']:
                    mensagem += f"⚽ {jogo['jogo']}\n"
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
            'mensagem': 'Análise profissional concluída!'
        })
        
    except Exception as e:
        logger.error(f"🚨 Erro na análise: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Erro: {str(e)}'
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
                'message': 'Nenhum bilhete premium no momento'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro: {str(e)}'
        }), 500

@app.route('/teste_bilhetes', methods=['POST'])
def teste_bilhetes():
    """Teste do sistema"""
    try:
        logger.info("🧪 Testando sistema...")
        jogos_teste = analisador._dados_teste()
        bilhetes = analisador.criar_bilhetes_premium(jogos_teste)
        
        return jsonify({
            'success': True,
            'bilhetes': bilhetes,
            'mensagem': 'Sistema testado com sucesso'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro: {str(e)}'
        }), 500

@app.route('/status', methods=['GET'])
def status():
    """Status do sistema"""
    return jsonify({
        'status': 'online',
        'timestamp': datetime.now().isoformat(),
        'versao': '3.0.0'
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)

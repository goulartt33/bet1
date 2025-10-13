from flask import Flask, render_template, request, jsonify
import logging
import requests
import os
from datetime import datetime, timedelta
import time
import json

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'chave-secreta-padrao')

# Configurações
THEODDS_API_KEY = os.environ.get('THEODDS_API_KEY', '4229efa29d667add58e355309f536a31')
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_TOKEN', '8318020293:AAGgOHxsvCUQ4o0ArxKAevIe3KlL5DeWbwI')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '5538926378')

class AnalisadorJogosReais:
    def __init__(self):
        self.odds_api_key = THEODDS_API_KEY
        self.regiao = 'eu'
        
    def obter_jogos_reais(self, esporte='soccer'):
        """Obtém jogos REAIS da The Odds API"""
        try:
            url = f"https://api.the-odds-api.com/v4/sports/{esporte}/odds/"
            params = {
                'apiKey': self.odds_api_key,
                'regions': self.regiao,
                'markets': 'h2h',
                'oddsFormat': 'decimal'
            }
            
            logger.info("🎯 Buscando jogos REAIS na The Odds API...")
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                jogos = response.json()
                if jogos and len(jogos) > 0:
                    logger.info(f"✅ {len(jogos)} jogos REAIS encontrados")
                    
                    # Log dos primeiros jogos para debug
                    for i, jogo in enumerate(jogo[:3]):
                        logger.info(f"📊 Jogo {i+1}: {jogo.get('home_team')} vs {jogo.get('away_team')}")
                        if jogo.get('bookmakers'):
                            for bookmaker in jogo['bookmakers'][:2]:
                                if bookmaker.get('markets'):
                                    for market in bookmaker['markets']:
                                        if market.get('outcomes'):
                                            logger.info(f"   📈 {bookmaker.get('key')}: {market['outcomes']}")
                    
                    return jogos
                else:
                    logger.warning("⚠️ API retornou lista vazia")
                    return []
            else:
                logger.error(f"❌ Erro API: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"🚨 Erro ao buscar jogos reais: {str(e)}")
            return []

    def analisar_valor_real(self, odds_casa, odds_fora, odds_empate):
        """Análise de valor com dados REAIS"""
        try:
            # Garantir que temos odds válidas
            if not all([odds_casa, odds_fora, odds_empate]):
                return False, 0, None
                
            # Converter para float
            odds_casa = float(odds_casa)
            odds_fora = float(odds_fora) 
            odds_empate = float(odds_empate)
            
            # Calcular probabilidades implícitas
            prob_casa = 1 / odds_casa
            prob_fora = 1 / odds_fora
            prob_empate = 1 / odds_empate
            
            total_prob = prob_casa + prob_fora + prob_empate
            
            # Ajustar pela margem da casa
            prob_ajust_casa = prob_casa / total_prob
            prob_ajust_fora = prob_fora / total_prob
            prob_ajust_empate = prob_empate / total_prob
            
            # Calcular valor esperado
            valor_casa = (prob_ajust_casa * odds_casa) - 1
            valor_fora = (prob_ajust_fora * odds_fora) - 1
            valor_empate = (prob_ajust_empate * odds_empate) - 1
            
            # Encontrar melhor valor
            melhor_valor = max(valor_casa, valor_fora, valor_empate)
            
            # Critério mais permissivo para dados reais
            if melhor_valor > 0.01:  # Apenas 1% de valor
                if melhor_valor == valor_casa:
                    return True, round(valor_casa * 100, 2), 'casa'
                elif melhor_valor == valor_fora:
                    return True, round(valor_fora * 100, 2), 'fora'
                else:
                    return True, round(valor_empate * 100, 2), 'empate'
            
            return False, 0, None
            
        except Exception as e:
            logger.error(f"Erro análise valor real: {e}")
            return False, 0, None

    def extrair_odds_reais(self, jogo):
        """Extrai odds REAIS dos bookmakers"""
        try:
            todas_odds_casa = []
            todas_odds_fora = []
            todas_odds_empate = []
            
            for bookmaker in jogo.get('bookmakers', []):
                for market in bookmaker.get('markets', []):
                    if market.get('key') == 'h2h':
                        for outcome in market.get('outcomes', []):
                            name = outcome.get('name', '')
                            price = outcome.get('price', 0)
                            
                            if name == jogo.get('home_team'):
                                todas_odds_casa.append(price)
                            elif name == jogo.get('away_team'):
                                todas_odds_fora.append(price)
                            elif name == 'Draw':
                                todas_odds_empate.append(price)
            
            # Usar médias para ser mais realista
            if todas_odds_casa and todas_odds_fora and todas_odds_empate:
                odds_casa = sum(todas_odds_casa) / len(todas_odds_casa)
                odds_fora = sum(todas_odds_fora) / len(todas_odds_fora)
                odds_empate = sum(todas_odds_empate) / len(todas_odds_empate)
                
                return odds_casa, odds_fora, odds_empate
            else:
                return None, None, None
                
        except Exception as e:
            logger.error(f"Erro extrair odds reais: {e}")
            return None, None, None

    def criar_bilhetes_reais(self, jogos):
        """Cria bilhetes com dados REAIS"""
        jogos_analisados = []
        
        for jogo in jogos:
            try:
                casa_time = jogo.get('home_team')
                fora_time = jogo.get('away_team')
                
                if not casa_time or not fora_time:
                    continue
                
                # Extrair odds REAIS
                odds_casa, odds_fora, odds_empate = self.extrair_odds_reais(jogo)
                
                if not all([odds_casa, odds_fora, odds_empate]):
                    continue
                
                # Analisar valor
                tem_valor, valor_percentual, tipo_aposta = self.analisar_valor_real(
                    odds_casa, odds_fora, odds_empate
                )
                
                if tem_valor:
                    if tipo_aposta == 'casa':
                        aposta = f"Vitória {casa_time}"
                        odds = odds_casa
                    elif tipo_aposta == 'fora':
                        aposta = f"Vitória {fora_time}"
                        odds = odds_fora
                    else:
                        aposta = "Empate"
                        odds = odds_empate
                    
                    # Classificar confiança
                    if valor_percentual > 5:
                        confianca = 'ALTA'
                    elif valor_percentual > 2:
                        confianca = 'MÉDIA'
                    else:
                        confianca = 'MODERADA'
                    
                    analise = {
                        'jogo': f"{casa_time} vs {fora_time}",
                        'aposta': aposta,
                        'odds': round(odds, 2),
                        'valor': valor_percentual,
                        'confianca': confianca,
                        'tipo': 'VALOR REAL',
                        'timestamp': datetime.now().strftime('%H:%M'),
                        'bookmakers': len(jogo.get('bookmakers', [])),
                        'commence_time': jogo.get('commence_time', '')
                    }
                    jogos_analisados.append(analise)
                    logger.info(f"✅ Jogo REAL com valor: {casa_time} vs {fora_time} - {valor_percentual}%")
                    
            except Exception as e:
                logger.error(f"❌ Erro analisar jogo real: {e}")
                continue
        
        # Ordenar por valor
        jogos_analisados.sort(key=lambda x: x['valor'], reverse=True)
        
        # Criar bilhetes
        bilhetes = []
        
        if len(jogos_analisados) >= 2:
            bilhete_dupla = {
                'nome': '🎯 BILHETE REAL 2 JOGOS',
                'jogos': jogos_analisados[:2],
                'odds_total': round(jogos_analisados[0]['odds'] * jogos_analisados[1]['odds'], 2),
                'tipo': 'DUPLA',
                'valor_total': round(sum(j['valor'] for j in jogos_analisados[:2]), 2),
                'confianca': 'ALTA'
            }
            bilhetes.append(bilhete_dupla)
            
        if len(jogos_analisados) >= 3:
            bilhete_tripla = {
                'nome': '🔥 BILHETE REAL 3 JOGOS',
                'jogos': jogos_analisados[:3],
                'odds_total': round(jogos_analisados[0]['odds'] * jogos_analisados[1]['odds'] * jogos_analisados[2]['odds'], 2),
                'tipo': 'TRIPLA',
                'valor_total': round(sum(j['valor'] for j in jogos_analisados[:3]), 2),
                'confianca': 'MÉDIA'
            }
            bilhetes.append(bilhete_tripla)
        
        logger.info(f"📊 Análise REAL: {len(jogos_analisados)} jogos com valor, {len(bilhetes)} bilhetes")
        return bilhetes

class TelegramBot:
    def __init__(self):
        self.token = TELEGRAM_BOT_TOKEN
        self.chat_id = TELEGRAM_CHAT_ID
        
    def enviar_mensagem(self, mensagem):
        if not self.token or not self.chat_id:
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

# Instância global
analisador = AnalisadorJogosReais()
telegram_bot = TelegramBot()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analisar_jogos', methods=['POST'])
def analisar_jogos():
    try:
        logger.info("🎯 Iniciando análise com dados REAIS")
        
        # Obter jogos REAIS
        jogos = analisador.obter_jogos_reais('soccer')
        
        if not jogos:
            return jsonify({
                'success': False,
                'message': 'Nenhum jogo REAL encontrado na API'
            })
        
        # Criar bilhetes REAIS
        bilhetes = analisador.criar_bilhetes_reais(jogos)
        
        telegram_enviado = False
        if bilhetes:
            for bilhete in bilhetes:
                mensagem = f"🎯 <b>{bilhete['nome']}</b>\n"
                mensagem += f"📊 Dados REAIS da API • {len(bilhete['jogos'])} jogos\n\n"
                
                for jogo in bilhete['jogos']:
                    mensagem += f"⚽ {jogo['jogo']}\n"
                    mensagem += f"🎯 {jogo['aposta']}\n" 
                    mensagem += f"📈 Odds: {jogo['odds']}\n"
                    mensagem += f"💎 Valor: {jogo['valor']}%\n"
                    mensagem += f"⭐ Confiança: {jogo['confianca']}\n"
                    mensagem += f"🏷️ {jogo['tipo']}\n\n"
                
                mensagem += f"🔥 <b>ODDS TOTAL: {bilhete['odds_total']}</b>\n"
                mensagem += f"💰 <b>VALOR TOTAL: {bilhete['valor_total']}%</b>\n"
                mensagem += f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}"
                
                if telegram_bot.enviar_mensagem(mensagem):
                    telegram_enviado = True
                time.sleep(1)
        
        if bilhetes:
            return jsonify({
                'success': True,
                'total_jogos': len(jogos),
                'bilhetes_gerados': len(bilhetes),
                'telegram_enviado': telegram_enviado,
                'bilhetes': bilhetes,
                'mensagem': 'Análise com dados REAIS concluída!'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Nenhum valor identificado nos jogos reais no momento'
            })
        
    except Exception as e:
        logger.error(f"🚨 Erro análise real: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Erro na análise: {str(e)}'
        }), 500

@app.route('/bilhete_do_dia', methods=['GET'])
def bilhete_do_dia():
    try:
        jogos = analisador.obter_jogos_reais('soccer')
        bilhetes = analisador.criar_bilhetes_reais(jogos)
        
        if bilhetes:
            return jsonify({
                'success': True,
                'bilhete': bilhetes[0],
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Nenhum bilhete real encontrado no momento'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro: {str(e)}'
        }), 500

@app.route('/teste_bilhetes', methods=['POST'])
def teste_bilhetes():
    try:
        logger.info("🧪 Testando sistema com dados REAIS...")
        jogos = analisador.obter_jogos_reais('soccer')
        bilhetes = analisador.criar_bilhetes_reais(jogos)
        
        return jsonify({
            'success': True,
            'total_jogos': len(jogos),
            'bilhetes': bilhetes,
            'mensagem': 'Sistema testado com dados REAIS!'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro: {str(e)}'
        }), 500

@app.route('/status', methods=['GET'])
def status():
    return jsonify({
        'status': 'online',
        'timestamp': datetime.now().isoformat(),
        'api_odds': 'ativa',
        'dados': 'REAIS',
        'versao': '6.0.0-dados-reais'
    })

@app.route('/debug_jogos', methods=['GET'])
def debug_jogos():
    """Endpoint para debug - mostra os dados brutos da API"""
    try:
        jogos = analisador.obter_jogos_reais('soccer')
        
        jogos_debug = []
        for jogo in jogos[:5]:  # Mostrar apenas 5 para debug
            debug_info = {
                'home_team': jogo.get('home_team'),
                'away_team': jogo.get('away_team'),
                'bookmakers_count': len(jogo.get('bookmakers', [])),
                'odds_samples': []
            }
            
            for bookmaker in jogo.get('bookmakers', [])[:2]:
                for market in bookmaker.get('markets', []):
                    if market.get('key') == 'h2h':
                        debug_info['odds_samples'].append({
                            'bookmaker': bookmaker.get('key'),
                            'outcomes': market.get('outcomes', [])
                        })
            
            jogos_debug.append(debug_info)
        
        return jsonify({
            'success': True,
            'total_jogos': len(jogos),
            'debug_info': jogos_debug
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)

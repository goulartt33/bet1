from flask import Flask, render_template, request, jsonify, session
import logging
import requests
import json
import os
from datetime import datetime
import time

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'chave-secreta-padrao')

# Configurações
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

class AnalisadorJogos:
    def __init__(self):
        self.odds_api_key = os.environ.get('ODDS_API_KEY', '')
        self.regiao = 'eu'
        
    def obter_jogos_ao_vivo(self, esporte='soccer'):
        """Obtém jogos ao vivo da API de odds"""
        try:
            url = f"https://api.the-odds-api.com/v4/sports/{esporte}/odds/"
            params = {
                'apiKey': self.odds_api_key,
                'regions': self.regiao,
                'markets': 'h2h',
                'oddsFormat': 'decimal'
            }
            
            logger.info(f"🌐 Buscando jogos de {esporte} - Região: {self.regiao}")
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                jogos = response.json()
                logger.info(f"✅ {esporte}: {len(jogos)} jogos encontrados")
                return jogos
            else:
                logger.error(f"❌ Erro API: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"🚨 Erro ao buscar jogos: {str(e)}")
            return []

    def analisar_valor(self, odds_casa, odds_fora, odds_empate=None):
        """Analisa se há valor nas odds"""
        try:
            # Cálculo de probabilidade implícita
            prob_casa = 1 / odds_casa if odds_casa else 0
            prob_fora = 1 / odds_fora if odds_fora else 0
            prob_empate = 1 / odds_empate if odds_empate else 0
            
            total_prob = prob_casa + prob_fora + prob_empate
            
            if total_prob == 0:
                return False, 0
                
            # Margem da casa
            margem = total_prob - 1
            
            # Encontrar valor (probabilidade implícita < probabilidade real estimada)
            prob_real_casa = prob_casa / total_prob
            valor_casa = prob_real_casa * odds_casa - 1 if odds_casa else 0
            
            return valor_casa > 0.05, valor_casa  # 5% de valor mínimo
            
        except Exception as e:
            logger.error(f"Erro no cálculo de valor: {e}")
            return False, 0

    def criar_bilhetes_premium(self, jogos):
        """Cria bilhetes premium com análise profissional"""
        bilhetes = []
        jogos_analisados = []
        
        for jogo in jogos[:10]:  # Analisa os primeiros 10 jogos
            try:
                casa_time = jogo.get('home_team', 'Time Casa')
                fora_time = jogo.get('away_team', 'Time Fora')
                
                # Encontrar melhor odds
                melhor_odds_casa = 0
                melhor_odds_fora = 0
                
                for bookmaker in jogo.get('bookmakers', []):
                    for market in bookmaker.get('markets', []):
                        if market['key'] == 'h2h':
                            for outcome in market['outcomes']:
                                if outcome['name'] == casa_time:
                                    melhor_odds_casa = max(melhor_odds_casa, outcome.get('price', 0))
                                elif outcome['name'] == fora_time:
                                    melhor_odds_fora = max(melhor_odds_fora, outcome.get('price', 0))
                
                # Analisar valor
                tem_valor, valor_percentual = self.analisar_valor(melhor_odds_casa, melhor_odds_fora)
                
                if tem_valor and melhor_odds_casa >= 1.50:
                    analise = {
                        'jogo': f"{casa_time} vs {fora_time}",
                        'aposta': f"Vitória {casa_time}",
                        'odds': melhor_odds_casa,
                        'valor': round(valor_percentual * 100, 2),
                        'confianca': 'ALTA' if valor_percentual > 0.1 else 'MÉDIA',
                        'tipo': 'VALOR ENCONTRADO'
                    }
                    jogos_analisados.append(analise)
                    
            except Exception as e:
                logger.error(f"Erro ao analisar jogo: {e}")
                continue
        
        # Criar bilhetes combinados
        if len(jogos_analisados) >= 2:
            # Bilhete 1: 2 jogos de alta confiança
            bilhete1 = {
                'nome': 'BILHETE PREMIUM 2 JOGOS',
                'jogos': jogos_analisados[:2],
                'odds_total': round(jogos_analisados[0]['odds'] * jogos_analisados[1]['odds'], 2),
                'tipo': 'DUPLA'
            }
            bilhetes.append(bilhete1)
            
        if len(jogos_analisados) >= 3:
            # Bilhete 2: 3 jogos
            bilhete2 = {
                'nome': 'BILHETE MEGA 3 JOGOS', 
                'jogos': jogos_analisados[:3],
                'odds_total': round(jogos_analisados[0]['odds'] * jogos_analisados[1]['odds'] * jogos_analisados[2]['odds'], 2),
                'tipo': 'TRIPLA'
            }
            bilhetes.append(bilhete2)
            
        return bilhetes

class TelegramBot:
    def __init__(self):
        self.token = TELEGRAM_BOT_TOKEN
        self.chat_id = TELEGRAM_CHAT_ID
        
    def enviar_mensagem(self, mensagem):
        """Envia mensagem via Telegram"""
        if not self.token or not self.chat_id:
            logger.warning("Token ou Chat ID do Telegram não configurado")
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
            logger.error(f"Erro ao enviar para Telegram: {e}")
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
        logger.info("🎯 Análise PROFISSIONAL - soccer")
        
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
        if bilhetes and TELEGRAM_BOT_TOKEN:
            for bilhete in bilhetes:
                mensagem = f"🎯 <b>BILHETE {bilhete['tipo']}</b>\n"
                mensagem += f"📊 {bilhete['nome']}\n\n"
                
                for jogo in bilhete['jogos']:
                    mensagem += f"⚽ {jogo['jogo']}\n"
                    mensagem += f"🎯 {jogo['aposta']}\n" 
                    mensagem += f"📈 Odds: {jogo['odds']}\n"
                    mensagem += f"💎 Valor: {jogo['valor']}%\n"
                    mensagem += f"⭐ Confiança: {jogo['confianca']}\n\n"
                
                mensagem += f"🔥 <b>ODDS TOTAL: {bilhete['odds_total']}</b>\n"
                mensagem += f"⏰ {datetime.now().strftime('%d/%m/%Y %H:%M')}"
                
                telegram_bot.enviar_mensagem(mensagem)
                time.sleep(1)
            
            logger.info(f"✅ ENVIO PREMIUM: {len(bilhetes)} bilhetes enviados")
        
        return jsonify({
            'success': True,
            'total_jogos': len(jogos),
            'bilhetes_gerados': len(bilhetes),
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
                'bilhete': bilhetes[0]  # Retorna o primeiro bilhete
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Nenhum bilhete premium encontrado hoje'
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
        
        # Dados de teste
        jogos_teste = [
            {
                'home_team': 'Time A',
                'away_team': 'Time B', 
                'bookmakers': [
                    {
                        'markets': [
                            {
                                'key': 'h2h',
                                'outcomes': [
                                    {'name': 'Time A', 'price': 1.85},
                                    {'name': 'Time B', 'price': 3.50}
                                ]
                            }
                        ]
                    }
                ]
            }
        ]
        
        bilhetes = analisador.criar_bilhetes_premium(jogos_teste)
        
        return jsonify({
            'success': True,
            'bilhetes_testados': len(bilhetes),
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
        'versao': '1.0.0'
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)

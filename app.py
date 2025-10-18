import asyncio
import httpx
import logging
from flask import Flask, request, jsonify, render_template
from functools import wraps
import time
import threading
from concurrent.futures import ThreadPoolExecutor
import os

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configurações do Telegram
TELEGRAM_BOT_TOKEN = "8318020293:AAGgOHxsvCUQ4o0ArxKAevIe3KlL5DeWbwI"
TELEGRAM_CHAT_ID = "7144216765"

# Cliente HTTP global com configurações otimizadas
def create_http_client():
    return httpx.AsyncClient(
        timeout=30.0,
        limits=httpx.Limits(
            max_connections=10,
            max_keepalive_connections=5
        ),
        headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    )

# Gerenciador de clientes HTTP por thread
class HTTPClientManager:
    def __init__(self):
        self.clients = {}
        self.lock = threading.Lock()
    
    def get_client(self):
        thread_id = threading.get_ident()
        with self.lock:
            if thread_id not in self.clients:
                self.clients[thread_id] = create_http_client()
            return self.clients[thread_id]
    
    def close_all(self):
        with self.lock:
            for client in self.clients.values():
                try:
                    client.close()
                except:
                    pass
            self.clients.clear()

http_manager = HTTPClientManager()

# Decorator para executar funções assíncronas de forma síncrona
def async_to_sync(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            # Tentar usar o loop de eventos existente
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Se o loop estiver rodando, usar ThreadPoolExecutor
                with ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        lambda: asyncio.run(func(*args, **kwargs))
                    )
                    return future.result()
            else:
                # Se não estiver rodando, executar normalmente
                return asyncio.run(func(*args, **kwargs))
        except RuntimeError:
            # Criar novo loop se necessário
            return asyncio.new_event_loop().run_until_complete(func(*args, **kwargs))
    return wrapper

# Função para enviar mensagem para o Telegram
async def enviar_telegram_async(mensagem):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mensagem,
        "parse_mode": "HTML"
    }
    
    client = http_manager.get_client()
    
    try:
        logger.info("📤 Enviando mensagem para Telegram...")
        response = await client.post(url, json=payload)
        response.raise_for_status()
        logger.info("✅ Mensagem enviada ao Telegram com sucesso!")
        return True
    except httpx.TimeoutException:
        logger.error("❌ Timeout ao enviar mensagem para Telegram")
        return False
    except httpx.HTTPStatusError as e:
        logger.error(f"❌ Erro HTTP {e.response.status_code}: {e.response.text}")
        return False
    except Exception as e:
        logger.error(f"❌ Erro inesperado ao enviar mensagem: {str(e)}")
        return False

# Versão síncrona para uso em rotas Flask
@async_to_sync
async def enviar_telegram(mensagem):
    return await enviar_telegram_async(mensagem)

# Função para análise de jogos (exemplo)
def analisar_jogos():
    logger.info("🔍 Iniciando análise de jogos...")
    
    # Simulação de análise
    time.sleep(1)
    
    jogos_analisados = [
        {"time1": "Time A", "time2": "Time B", "aposta": "Over 2.5", "confianca": "85%"},
        {"time1": "Time C", "time2": "Time D", "aposta": "Ambas marcam", "confianca": "78%"}
    ]
    
    mensagem = "🎯 <b>ANÁLISE DE JOGOS - BILHETE DO DIA</b>\n\n"
    
    for i, jogo in enumerate(jogos_analisados, 1):
        mensagem += f"⚽ <b>Jogo {i}:</b>\n"
        mensagem += f"🏆 {jogo['time1']} vs {jogo['time2']}\n"
        mensagem += f"🎲 Aposta: {jogo['aposta']}\n"
        mensagem += f"📊 Confiança: {jogo['confianca']}\n\n"
    
    mensagem += "⚠️ <i>Lembre-se: Apostas envolvem risco. Aposte com responsabilidade.</i>"
    
    return mensagem, jogos_analisados

# Rotas Flask
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analisar_jogos', methods=['POST'])
def analisar_jogos_route():
    try:
        mensagem, jogos = analisar_jogos()
        
        # Tentar enviar para Telegram
        sucesso = enviar_telegram(mensagem)
        
        return jsonify({
            "status": "success" if sucesso else "warning",
            "mensagem": "Análise concluída!" if sucesso else "Análise concluída, mas não foi possível enviar ao Telegram",
            "jogos": jogos,
            "telegram_enviado": sucesso
        })
        
    except Exception as e:
        logger.error(f"❌ Erro na análise: {str(e)}")
        return jsonify({
            "status": "error",
            "mensagem": f"Erro na análise: {str(e)}"
        }), 500

@app.route('/bilhete_do_dia')
def bilhete_do_dia():
    return jsonify({
        "status": "success",
        "mensagem": "Bilhete do dia gerado com sucesso!",
        "bilhete": "Exemplo de bilhete"
    })

@app.route('/teste_bilhetes', methods=['POST'])
def teste_bilhetes():
    try:
        mensagem = "🧪 <b>TESTE DE ENVIO</b>\n\n"
        mensagem += "Esta é uma mensagem de teste do sistema!\n"
        mensagem += f"📅 Hora do envio: {time.strftime('%d/%m/%Y %H:%M:%S')}\n\n"
        mensagem += "✅ Sistema funcionando corretamente!"
        
        sucesso = enviar_telegram(mensagem)
        
        return jsonify({
            "status": "success" if sucesso else "warning",
            "mensagem": "Teste enviado com sucesso!" if sucesso else "Teste concluído, mas não foi possível enviar ao Telegram"
        })
        
    except Exception as e:
        logger.error(f"❌ Erro no teste: {str(e)}")
        return jsonify({
            "status": "error",
            "mensagem": f"Erro no teste: {str(e)}"
        }), 500

# Health check para Render
@app.route('/health')
def health_check():
    return jsonify({"status": "healthy", "timestamp": time.time()})

# Limpeza ao fechar a aplicação
@app.teardown_appcontext
def close_http_clients(exception=None):
    http_manager.close_all()

# Inicialização
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)

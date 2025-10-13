from flask import Flask, request, jsonify, render_template
import requests
import os
from datetime import datetime
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configurações
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

@app.route('/')
def index():
    """Página inicial"""
    return render_template('index.html')

@app.route('/buscar', methods=['POST'])
def buscar():
    """Endpoint para buscar dados e enviar para o Telegram"""
    try:
        # Obter dados do formulário
        data = request.get_json()
        
        if not data:
            return jsonify({"status": "error", "message": "Nenhum dado recebido"}), 400
        
        # Exemplo de dados (substitua pela sua lógica real)
        search_term = data.get('termo', 'padrão')
        resultado = f"Busca realizada para: {search_term}"
        
        # Enviar para o Telegram (se configurado)
        if BOT_TOKEN and CHAT_ID:
            mensagem_telegram = f"🚀 Nova busca no site!\n📅 Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n🔍 Termo: {search_term}\n✅ Resultado: {resultado}"
            enviar_telegram(mensagem_telegram)
        
        # Retornar resposta
        return jsonify({
            "status": "success",
            "message": "Busca realizada com sucesso",
            "data": {
                "termo": search_term,
                "resultado": resultado,
                "timestamp": datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Erro na busca: {str(e)}")
        return jsonify({"status": "error", "message": "Erro interno do servidor"}), 500

def enviar_telegram(mensagem):
    """Enviar mensagem para o Telegram"""
    try:
        if not BOT_TOKEN or not CHAT_ID:
            logger.warning("Token do bot ou Chat ID não configurados")
            return False
            
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": CHAT_ID,
            "text": mensagem,
            "parse_mode": "HTML"
        }
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            logger.info("Mensagem enviada para o Telegram com sucesso")
            return True
        else:
            logger.error(f"Erro ao enviar para Telegram: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Erro na função enviar_telegram: {str(e)}")
        return False

@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint para verificar se a aplicação está rodando"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "environment": "production"
    })

@app.route('/info', methods=['GET'])
def info():
    """Endpoint para informações da aplicação"""
    return jsonify({
        "app": "Flask Bot Application",
        "version": "1.0.0",
        "telegram_configured": bool(BOT_TOKEN and CHAT_ID),
        "server_time": datetime.now().isoformat()
    })

if __name__ == '__main__':
    # Verificar variáveis de ambiente importantes
    required_vars = ['BOT_TOKEN', 'CHAT_ID']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.warning(f"Variáveis de ambiente importantes não definidas: {', '.join(missing_vars)}")
    else:
        logger.info("Todas as variáveis de ambiente estão configuradas")
    
    port = int(os.getenv('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)

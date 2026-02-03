"""
Aplicação Flask - Bot Worker API
Servidor de API para chatbot inteligente com busca em múltiplas fontes
"""

from flask import Flask, jsonify
from flask_cors import CORS
import logging

from controllers.bot_controller import bot_bp
from controllers.user_controller import user_bp

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Inicializa aplicação Flask
app = Flask(__name__)

# Configuração CORS (permite requisições do frontend)
CORS(app, resources={
    r"/api/*": {
        "origins": "*",  # Em produção, especifique os domínios permitidos
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Registra blueprints
app.register_blueprint(bot_bp)
app.register_blueprint(user_bp)

logger.info("Blueprints registrados: bot, user")


@app.route('/')
def index():
    """
    Rota raiz - Informações da API
    """
    return jsonify({
        "service": "Bot Worker API",
        "version": "2.0.0",
        "status": "online",
        "endpoints": {
            "bot": "/api/bot/*",
            "users": "/api/*",
            "health": "/health",
            "docs": "/docs"
        }
    })


@app.route('/health')
def health():
    """
    Health check da aplicação
    """
    return jsonify({
        "status": "healthy",
        "service": "Bot Worker API",
        "database": "connected"  # Pode adicionar verificação real do DB aqui
    }), 200


@app.route('/docs')
def docs():
    """
    Documentação simplificada da API
    """
    return jsonify({
        "api_version": "2.0.0",
        "documentation": {
            "bot_endpoints": {
                "POST /api/bot/question": "Faz uma pergunta ao bot",
                "GET /api/bot/history": "Lista histórico de conversas (paginado)",
                "GET /api/bot/conversation/:id": "Busca conversa específica",
                "GET /api/bot/search": "Busca conversas por palavra-chave",
                "DELETE /api/bot/conversation/:id": "Deleta conversa específica",
                "GET /api/bot/stats": "Estatísticas do usuário",
                "DELETE /api/bot/history/clear": "Limpa histórico completo",
                "GET /api/bot/health": "Health check do bot"
            },
            "user_endpoints": {
                "POST /api/register": "Registra novo usuário",
                "POST /api/login": "Faz login (retorna JWT)",
                "GET /api/all": "Lista todos os usuários"
            }
        },
        "example_request": {
            "endpoint": "/api/bot/question",
            "method": "POST",
            "body": {
                "pergunta": "Qual a capital da França?",
                "user_id": 1
            }
        }
    })


@app.errorhandler(404)
def not_found(error):
    """Handler para rotas não encontradas"""
    return jsonify({
        "error": "Endpoint não encontrado",
        "message": "Verifique a documentação em /docs"
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handler para erros internos"""
    logger.error(f"Erro interno: {error}")
    return jsonify({
        "error": "Erro interno do servidor",
        "message": "Por favor, tente novamente mais tarde"
    }), 500


if __name__ == "__main__":
    logger.info("Iniciando Bot Worker API...")
    logger.info("Acesse http://localhost:5000 para informações da API")
    logger.info("Documentação disponível em http://localhost:5000/docs")
    
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False  # Em produção, sempre False
    )

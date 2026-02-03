"""
Bot Controller - Rotas da API para o bot
"""

from flask import Blueprint, jsonify, request
from bot.workers.bot_worker import BotWorker
import logging

logger = logging.getLogger(__name__)

bot_bp = Blueprint('bot', __name__, url_prefix="/api/bot")

# Instância única do worker
bot_worker = BotWorker()


@bot_bp.route('/question', methods=['POST'])
def question():
    """
    Processa uma pergunta do usuário.
    
    Request Body:
        {
            "pergunta": "Qual a capital da França?",
            "user_id": 1  // opcional, mas necessário para salvar no DB
        }
    
    Response:
        {
            "status": "success",
            "query": "Qual a capital da França?",
            "response": "Paris é a capital...",
            "source": "google",
            "processing_time": 1.234,
            "user_id": 1
        }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "JSON inválido"}), 400
        
        pergunta = data.get("pergunta")
        user_id = data.get("user_id")  # Opcional
        
        if not pergunta:
            return jsonify({"error": "Campo 'pergunta' é obrigatório"}), 400
        
        # Processa a pergunta
        resultado = bot_worker.process_query(pergunta, user_id)
        
        # Retorna resposta completa
        return jsonify(resultado), 200 if resultado['status'] == 'success' else 400
        
    except Exception as e:
        logger.error(f"Erro no endpoint /question: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Erro interno do servidor",
            "message": str(e)
        }), 500


@bot_bp.route('/history', methods=['GET'])
def get_history():
    """
    Retorna histórico de conversas do usuário com paginação.
    
    Query Params:
        - user_id (int, obrigatório): ID do usuário
        - limit (int, opcional): Conversas por página (default: 20)
        - offset (int, opcional): Deslocamento para paginação (default: 0)
    
    Response:
        {
            "status": "success",
            "conversations": [
                {
                    "id": 1,
                    "pergunta": "...",
                    "resposta_preview": "...",
                    "fonte": "google",
                    "tempo_processamento": 1.2,
                    "created_at": "2024-01-29T10:30:00"
                }
            ],
            "pagination": {
                "total": 50,
                "limit": 20,
                "offset": 0,
                "has_more": true
            }
        }
    """
    try:
        user_id = request.args.get('user_id', type=int)
        limit = request.args.get('limit', default=20, type=int)
        offset = request.args.get('offset', default=0, type=int)
        
        if not user_id:
            return jsonify({"error": "Parâmetro 'user_id' é obrigatório"}), 400
        
        # Valida limites
        if limit > 100:
            limit = 100
        if limit < 1:
            limit = 20
        if offset < 0:
            offset = 0
        
        resultado = bot_worker.get_user_history(user_id, limit, offset)
        
        return jsonify(resultado), 200
        
    except Exception as e:
        logger.error(f"Erro no endpoint /history: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Erro interno do servidor",
            "message": str(e)
        }), 500


@bot_bp.route('/conversation/<int:conversation_id>', methods=['GET'])
def get_conversation(conversation_id):
    """
    Retorna uma conversa específica por ID.
    
    Response:
        {
            "status": "success",
            "conversation": {
                "id": 1,
                "user_id": 1,
                "pergunta": "...",
                "resposta": "...",
                "fonte": "google",
                "tempo_processamento": 1.2,
                "status": "success",
                "metadata": {...},
                "created_at": "2024-01-29T10:30:00"
            }
        }
    """
    try:
        resultado = bot_worker.get_conversation(conversation_id)
        
        status_code = 200 if resultado['status'] == 'success' else 404
        return jsonify(resultado), status_code
        
    except Exception as e:
        logger.error(f"Erro no endpoint /conversation/{conversation_id}: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Erro interno do servidor",
            "message": str(e)
        }), 500


@bot_bp.route('/search', methods=['GET'])
def search_conversations():
    """
    Busca conversas por palavra-chave.
    
    Query Params:
        - user_id (int, obrigatório): ID do usuário
        - q (str, obrigatório): Termo de busca
        - limit (int, opcional): Máximo de resultados (default: 20)
    
    Response:
        {
            "status": "success",
            "query": "França",
            "results": [...],
            "total": 5
        }
    """
    try:
        user_id = request.args.get('user_id', type=int)
        query = request.args.get('q', type=str)
        limit = request.args.get('limit', default=20, type=int)
        
        if not user_id:
            return jsonify({"error": "Parâmetro 'user_id' é obrigatório"}), 400
        
        if not query:
            return jsonify({"error": "Parâmetro 'q' é obrigatório"}), 400
        
        # Valida limite
        if limit > 100:
            limit = 100
        if limit < 1:
            limit = 20
        
        resultado = bot_worker.search_conversations(user_id, query, limit)
        
        return jsonify(resultado), 200
        
    except Exception as e:
        logger.error(f"Erro no endpoint /search: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Erro interno do servidor",
            "message": str(e)
        }), 500


@bot_bp.route('/conversation/<int:conversation_id>', methods=['DELETE'])
def delete_conversation(conversation_id):
    """
    Deleta uma conversa específica.
    
    Request Body:
        {
            "user_id": 1  // Para validar ownership
        }
    
    Response:
        {
            "status": "success",
            "message": "Conversa deletada com sucesso"
        }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "JSON inválido"}), 400
        
        user_id = data.get("user_id")
        
        if not user_id:
            return jsonify({"error": "Campo 'user_id' é obrigatório"}), 400
        
        resultado = bot_worker.delete_conversation(conversation_id, user_id)
        
        status_code = 200 if resultado['status'] == 'success' else 403
        return jsonify(resultado), status_code
        
    except Exception as e:
        logger.error(f"Erro no endpoint DELETE /conversation/{conversation_id}: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Erro interno do servidor",
            "message": str(e)
        }), 500


@bot_bp.route('/stats', methods=['GET'])
def get_statistics():
    """
    Retorna estatísticas do usuário.
    
    Query Params:
        - user_id (int, obrigatório): ID do usuário
    
    Response:
        {
            "status": "success",
            "statistics": {
                "total_perguntas": 50,
                "tempo_medio": 1.23,
                "cache_hits": 15,
                "taxa_cache": 30.0,
                "sucessos": 48,
                "erros": 2,
                "taxa_sucesso": 96.0,
                "fontes_mais_usadas": [
                    {"fonte": "google", "count": 25},
                    {"fonte": "wolfram", "count": 15}
                ]
            }
        }
    """
    try:
        user_id = request.args.get('user_id', type=int)
        
        if not user_id:
            return jsonify({"error": "Parâmetro 'user_id' é obrigatório"}), 400
        
        resultado = bot_worker.get_user_statistics(user_id)
        
        return jsonify(resultado), 200
        
    except Exception as e:
        logger.error(f"Erro no endpoint /stats: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Erro interno do servidor",
            "message": str(e)
        }), 500


@bot_bp.route('/history/clear', methods=['DELETE'])
def clear_history():
    """
    Limpa todo o histórico de conversas do usuário.
    
    Request Body:
        {
            "user_id": 1
        }
    
    Response:
        {
            "status": "success",
            "message": "15 conversas deletadas",
            "deleted_count": 15
        }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "JSON inválido"}), 400
        
        user_id = data.get("user_id")
        
        if not user_id:
            return jsonify({"error": "Campo 'user_id' é obrigatório"}), 400
        
        resultado = bot_worker.clear_user_history(user_id)
        
        return jsonify(resultado), 200
        
    except Exception as e:
        logger.error(f"Erro no endpoint /history/clear: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Erro interno do servidor",
            "message": str(e)
        }), 500


@bot_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check do bot.
    
    Response:
        {
            "status": "online",
            "service": "bot",
            "cache_size": 10
        }
    """
    try:
        from bot.bot_worker import cache
        
        return jsonify({
            "status": "online",
            "service": "bot",
            "cache_size": len(cache)
        }), 200
        
    except Exception as e:
        logger.error(f"Erro no endpoint /health: {str(e)}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

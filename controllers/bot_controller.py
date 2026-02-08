"""
Bot Controller - Rotas da API para o bot
"""

from flask import Blueprint, jsonify, request
from bot.bot_worker import BotWorker
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

@bot_bp.route('/feedback', methods=['POST'])
def register_feedback():
    """
    Registra feedback do usuário sobre uma resposta.

    Request Body:
        {
            "conversation_id": 123,
            "tipo": "positivo",  // "positivo", "negativo" ou "neutro"
            "detalhes": "Resposta muito útil!"  // opcional
        }

    Response:
        {
            "status": "success",
            "message": "Feedback registrado com sucesso"
        }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "JSON inválido"}), 400

        conversation_id = data.get("conversation_id")
        tipo_feedback = data.get("tipo")
        detalhes = data.get("detalhes")

        if not conversation_id or not tipo_feedback:
            return jsonify({
                "error": "Campos 'conversation_id' e 'tipo' são obrigatórios"
            }), 400

        if tipo_feedback not in ["positivo", "negativo", "neutro"]:
            return jsonify({
                "error": "Tipo de feedback deve ser 'positivo', 'negativo' ou 'neutro'"
            }), 400

        # Registra feedback
        sucesso = bot_worker.registrar_feedback(
            conversation_id, 
            tipo_feedback, 
            detalhes
        )

        if sucesso:
            return jsonify({
                "status": "success",
                "message": "Feedback registrado com sucesso"
            }), 200
        else:
            return jsonify({
                "status": "error",
                "message": "Falha ao registrar feedback"
            }), 400

    except Exception as e:
        logger.error(f"Erro no endpoint /feedback: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Erro interno do servidor",
            "message": str(e)
        }), 500


@bot_bp.route('/feedback/correcao', methods=['POST'])
def register_correction():
    """
    Registra correção quando a resposta do bot está errada.

    Request Body:
        {
            "conversation_id": 123,
            "resposta_correta": "A resposta correta é..."
        }

    Response:
        {
            "status": "success",
            "message": "Correção registrada com sucesso"
        }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "JSON inválido"}), 400

        conversation_id = data.get("conversation_id")
        resposta_correta = data.get("resposta_correta")

        if not conversation_id or not resposta_correta:
            return jsonify({
                "error": "Campos 'conversation_id' e 'resposta_correta' são obrigatórios"
            }), 400

        # Registra correção
        sucesso = bot_worker.registrar_correcao(
            conversation_id, 
            resposta_correta
        )

        if sucesso:
            return jsonify({
                "status": "success",
                "message": "Correção registrada com sucesso"
            }), 200
        else:
            return jsonify({
                "status": "error",
                "message": "Falha ao registrar correção"
            }), 400

    except Exception as e:
        logger.error(f"Erro no endpoint /feedback/correcao: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Erro interno do servidor",
            "message": str(e)
        }), 500


@bot_bp.route('/feedback/taxa-satisfacao', methods=['GET'])
def get_satisfaction_rate():
    """
    Retorna taxa de satisfação baseada nos feedbacks.

    Query Params:
        - user_id (int, opcional): Se fornecido, retorna taxa do usuário específico

    Response:
        {
            "status": "success",
            "taxa_satisfacao": 85.5,
            "total": 100,
            "positivos": 85,
            "negativos": 10,
            "neutros": 5
        }
    """
    try:
        user_id = request.args.get('user_id', type=int)

        resultado = bot_worker.obter_taxa_satisfacao(user_id)

        return jsonify({
            "status": "success",
            **resultado
        }), 200

    except Exception as e:
        logger.error(f"Erro no endpoint /feedback/taxa-satisfacao: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Erro interno do servidor",
            "message": str(e)
        }), 500


# ================================
# ENDPOINTS DE ADMINISTRAÇÃO/ML
# ================================

@bot_bp.route('/admin/retrain', methods=['POST'])
def retrain_models():
    """
    Retreina os modelos de ML com dados mais recentes.
    ATENÇÃO: Endpoint administrativo - requer autenticação em produção!

    Response:
        {
            "status": "success",
            "message": "Modelos retreinados com sucesso"
        }
    """
    try:
        # TODO: Adicionar autenticação de admin aqui

        # Retreina modelos
        bot_worker.sistema_aprendizado.retreinar_periodicamente()

        return jsonify({
            "status": "success",
            "message": "Modelos retreinados com sucesso"
        }), 200

    except Exception as e:
        logger.error(f"Erro no endpoint /admin/retrain: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Erro interno do servidor",
            "message": str(e)
        }), 500


@bot_bp.route('/admin/stats/fontes', methods=['GET'])
def get_sources_statistics():
    """
    Retorna estatísticas de desempenho das fontes de dados.
    ATENÇÃO: Endpoint administrativo - requer autenticação em produção!

    Response:
        {
            "status": "success",
            "stats_fontes": {
                "wolfram": {
                    "total_usos": 150,
                    "sucessos": 145,
                    "falhas": 5,
                    "tempo_medio": 1.23,
                    "score_qualidade": 0.87
                },
                ...
            }
        }
    """
    try:
        # TODO: Adicionar autenticação de admin aqui

        stats = dict(bot_worker.sistema_aprendizado.stats_fontes)

        return jsonify({
            "status": "success",
            "stats_fontes": stats
        }), 200

    except Exception as e:
        logger.error(f"Erro no endpoint /admin/stats/fontes: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Erro interno do servidor",
            "message": str(e)
        }), 500


@bot_bp.route('/admin/padroes-aprendidos', methods=['GET'])
def get_learned_patterns():
    """
    Retorna padrões de perguntas-respostas aprendidos.
    ATENÇÃO: Endpoint administrativo - requer autenticação em produção!

    Query Params:
        - limit (int, opcional): Número máximo de padrões (default: 50)

    Response:
        {
            "status": "success",
            "total_padroes": 150,
            "padroes": [
                {
                    "pergunta": "qual capital frança",
                    "resposta": "Paris é...",
                    "qualidade": 0.95,
                    "usos": 10
                },
                ...
            ]
        }
    """
    try:
        # TODO: Adicionar autenticação de admin aqui

        limit = request.args.get('limit', default=50, type=int)

        padroes = bot_worker.sistema_aprendizado.padroes_pergunta_resposta

        # Converte para lista ordenada por qualidade
        padroes_lista = []
        for pergunta, dados in padroes.items():
            padroes_lista.append({
                "pergunta": pergunta,
                "resposta": dados["resposta"][:100] + "..." if len(dados["resposta"]) > 100 else dados["resposta"],
                "qualidade": dados["qualidade"],
                "usos": dados["usos"],
                "ultima_atualizacao": dados["ultima_atualizacao"].isoformat()
            })

        # Ordena por qualidade
        padroes_lista.sort(key=lambda x: x["qualidade"], reverse=True)

        return jsonify({
            "status": "success",
            "total_padroes": len(padroes_lista),
            "padroes": padroes_lista[:limit]
        }), 200

    except Exception as e:
        logger.error(f"Erro no endpoint /admin/padroes-aprendidos: {str(e)}", exc_info=True)
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

"""
Bot Controller - Rotas da API para o bot
"""

from flask import Blueprint, jsonify, request
from bot.bot_worker_v2 import get_bot_worker
from bot.utils.production_config import MODO_PRODUCAO, DEEP_LEARNING_AVAILABLE
import logging

logger = logging.getLogger(__name__)

bot_bp = Blueprint('bot', __name__, url_prefix="/api/bot")

# Instância única do worker
bot_worker = get_bot_worker()

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
# ENDPOINTS ADMINISTRATIVOS V2
# ================================

@bot_bp.route('/admin/retrain-all', methods=['POST'])
def retrain_all_models():
    """
    Retreina TODOS os modelos ML (ensemble + ranqueador + LDA).

    ⚠️ ADMIN ONLY - Adicionar autenticação!

    Response:
        {
            "status": "success",
            "message": "Modelos retreinados",
            "detalhes": {
                "intencao_ensemble": true,
                "ranqueador_fontes": true,
                "topic_model": true
            }
        }
    """
    try:
        # TODO: Adicionar autenticação

        logger.info("=" * 60)
        logger.info("RETREINAMENTO COMPLETO SOLICITADO")
        logger.info("=" * 60)

        bot_worker.sistema_ml.retreinar_tudo()

        return jsonify({
            "status": "success",
            "message": "Todos os modelos retreinados com sucesso",
            "detalhes": {
                "intencao_ensemble": True,
                "ranqueador_fontes": True,
                "topic_model": True
            }
        }), 200

    except Exception as e:
        logger.error(f"Erro no retreinamento: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Erro ao retreinar modelos",
            "message": str(e)
        }), 500

@bot_bp.route('/admin/reload-models', methods=['POST'])
def reload_models():
    """
    Recarrega modelos sem reiniciar servidor.
    Útil após retreinamento.
    """
    try:
        bot_worker = get_bot_worker()
        bot_worker.sistema_ml.carregar_modelos()
        
        return jsonify({
            "status": "success",
            "message": "Modelos recarregados com sucesso"
        }), 200
    except Exception as e:
        logger.error(f"Erro ao recarregar modelos: {str(e)}")
        return jsonify({
            "error": str(e)
        }), 500

@bot_bp.route('/admin/topics', methods=['GET'])
def get_topics():
    """
    Lista tópicos descobertos pelo LDA.

    ⚠️ ADMIN ONLY - Adicionar autenticação!

    Response:
        {
            "status": "success",
            "n_topics": 20,
            "topics": [
                {
                    "id": 0,
                    "top_words": ["brasil", "capital", "país"],
                    "weight": 0.15
                },
                ...
            ]
        }
    """
    try:
        # TODO: Adicionar autenticação

        if not bot_worker.sistema_ml.lda_model:
            return jsonify({
                "status": "error",
                "message": "Modelo LDA não treinado ainda"
            }), 400

        lda = bot_worker.sistema_ml.lda_model
        vectorizer = bot_worker.sistema_ml.lda_vectorizer

        if not vectorizer:
            return jsonify({
                "status": "error",
                "message": "Vectorizer não disponível"
            }), 400

        feature_names = vectorizer.get_feature_names_out()

        topics = []
        for topic_idx, topic in enumerate(lda.components_):
            # Top 10 palavras
            top_indices = topic.argsort()[-10:][::-1]
            top_words = [feature_names[i] for i in top_indices]
            weight = topic.sum() / lda.components_.sum()

            topics.append({
                "id": topic_idx,
                "top_words": top_words,
                "weight": round(weight, 4)
            })

        return jsonify({
            "status": "success",
            "n_topics": len(topics),
            "topics": topics
        }), 200

    except Exception as e:
        logger.error(f"Erro ao buscar tópicos: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Erro ao buscar tópicos",
            "message": str(e)
        }), 500


@bot_bp.route('/admin/stats/fontes-avancadas', methods=['GET'])
def get_advanced_source_stats():
    """
    Estatísticas avançadas de cada fonte.

    ⚠️ ADMIN ONLY - Adicionar autenticação!

    Response:
        {
            "status": "success",
            "fontes": {
                "wolfram": {
                    "total_usos": 150,
                    "taxa_sucesso": 0.967,
                    "tempo_medio": 1.23,
                    "score_qualidade": 0.87,
                    "tipos_pergunta_boas": {
                        "quanto": 45,
                        "qual": 30
                    },
                    "topicos_bons": {
                        "1": 50,
                        "5": 30
                    }
                },
                ...
            }
        }
    """
    try:
        # TODO: Adicionar autenticação

        stats_fontes = {}

        for fonte, stats in bot_worker.sistema_ml.stats_fontes.items():
            stats_fontes[fonte] = {
                "total_usos": stats["total_usos"],
                "sucessos": stats["sucessos"],
                "falhas": stats["falhas"],
                "taxa_sucesso": round(stats["taxa_sucesso"], 3),
                "tempo_medio": round(stats["tempo_medio"], 2),
                "score_qualidade": round(stats["score_qualidade"], 3),
                "taxa_feedback_positivo": round(stats.get("taxa_feedback_positivo", 0.5), 3),
                "tipos_pergunta_boas": dict(stats["tipos_pergunta_boas"].most_common(5)),
                "topicos_bons": {str(k): v for k, v in stats["topicos_bons"].most_common(5)},
                "ultimo_scores": stats["historico_scores"][-10:] if stats["historico_scores"] else []
            }

        return jsonify({
            "status": "success",
            "fontes": stats_fontes
        }), 200

    except Exception as e:
        logger.error(f"Erro ao buscar stats avançadas: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Erro ao buscar estatísticas",
            "message": str(e)
        }), 500


@bot_bp.route('/admin/model-performance', methods=['GET'])
def get_model_performance():
    """
    Performance de cada modelo do ensemble.

    ⚠️ ADMIN ONLY - Adicionar autenticação!

    Response:
        {
            "status": "success",
            "models": {
                "naive_bayes": {"trained": true},
                "random_forest": {"trained": true},
                "gradient_boosting": {"trained": true},
                "lstm": {"trained": false}
            }
        }
    """
    try:
        # TODO: Adicionar autenticação

        ml_system = bot_worker.sistema_ml

        models = {
            "naive_bayes": {
                "trained": ml_system.modelo_intencao_nb is not None,
                "type": "MultinomialNB"
            },
            "random_forest": {
                "trained": ml_system.modelo_intencao_rf is not None,
                "type": "RandomForestClassifier"
            },
            "gradient_boosting": {
                "trained": ml_system.modelo_intencao_gb is not None,
                "type": "GradientBoostingClassifier"
            },
            "lstm": {
                "trained": ml_system.modelo_intencao_lstm is not None,
                "type": "LSTM Deep Learning"
            },
            "ranqueador_fontes": {
                "trained": ml_system.modelo_ranqueamento_fontes is not None,
                "type": "RandomForestClassifier"
            },
            "lda_topics": {
                "trained": ml_system.lda_model is not None,
                "type": "LatentDirichletAllocation",
                "n_topics": ml_system.lda_model.n_components if ml_system.lda_model else 0
            }
        }

        return jsonify({
            "status": "success",
            "models": models,
            "ensemble_ready": all([
                models["naive_bayes"]["trained"],
                models["random_forest"]["trained"],
                models["gradient_boosting"]["trained"]
            ])
        }), 200

    except Exception as e:
        logger.error(f"Erro ao buscar performance: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Erro ao buscar performance dos modelos",
            "message": str(e)
        }), 500


@bot_bp.route('/admin/fontes/ranking', methods=['POST'])
def get_fonte_ranking():
    """
    Ranqueia fontes para uma pergunta específica.

    ⚠️ ADMIN ONLY - Adicionar autenticação!

    Request:
        {
            "pergunta": "Qual a capital da França?"
        }

    Response:
        {
            "status": "success",
            "pergunta": "Qual a capital da França?",
            "ranking": [
                {"fonte": "wikipedia", "score": 0.89},
                {"fonte": "google", "score": 0.72},
                {"fonte": "wolfram", "score": 0.45}
            ]
        }
    """
    try:
        # TODO: Adicionar autenticação

        data = request.get_json()

        if not data or "pergunta" not in data:
            return jsonify({
                "error": "Campo 'pergunta' é obrigatório"
            }), 400

        pergunta = data["pergunta"]

        # Pega todas as fontes disponíveis
        fontes = list(bot_worker.buscador.fontes_disponiveis.keys())

        # Ranqueia
        ranking = bot_worker.sistema_ml.ranquear_fontes_inteligente(pergunta, fontes)

        return jsonify({
            "status": "success",
            "pergunta": pergunta,
            "ranking": [
                {"fonte": fonte, "score": round(score, 3)}
                for fonte, score in ranking
            ]
        }), 200

    except Exception as e:
        logger.error(f"Erro ao ranquear fontes: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Erro ao ranquear fontes",
            "message": str(e)
        }), 500


@bot_bp.route('/admin/predict-intent', methods=['POST'])
def predict_intent_ensemble():
    """
    Prevê intenção usando ensemble para uma pergunta.

    ⚠️ ADMIN ONLY - Útil para debug!

    Request:
        {
            "pergunta": "Oi, tudo bem?"
        }

    Response:
        {
            "status": "success",
            "pergunta": "Oi, tudo bem?",
            "intencao": "saudacao",
            "confianca": 0.95
        }
    """
    try:
        # TODO: Adicionar autenticação

        data = request.get_json()

        if not data or "pergunta" not in data:
            return jsonify({
                "error": "Campo 'pergunta' é obrigatório"
            }), 400

        pergunta = data["pergunta"]

        # Prevê intenção
        intencao, confianca = bot_worker.sistema_ml.prever_intencao_ensemble(pergunta)

        return jsonify({
            "status": "success",
            "pergunta": pergunta,
            "intencao": intencao,
            "confianca": round(confianca, 3)
        }), 200

    except Exception as e:
        logger.error(f"Erro ao prever intenção: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Erro ao prever intenção",
            "message": str(e)
        }), 500


@bot_bp.route('/admin/detect-topic', methods=['POST'])
def detect_topic():
    """
    Detecta tópico de uma pergunta.

    ⚠️ ADMIN ONLY

    Request:
        {
            "pergunta": "Qual a capital do Brasil?"
        }

    Response:
        {
            "status": "success",
            "pergunta": "Qual a capital do Brasil?",
            "topico": 5,
            "top_words": ["brasil", "capital", "país"]
        }
    """
    try:
        # TODO: Adicionar autenticação

        data = request.get_json()

        if not data or "pergunta" not in data:
            return jsonify({
                "error": "Campo 'pergunta' é obrigatório"
            }), 400

        pergunta = data["pergunta"]

        # Detecta tópico
        topico = bot_worker.sistema_ml.detectar_topico(pergunta)

        if topico < 0:
            return jsonify({
                "status": "error",
                "message": "Modelo LDA não treinado"
            }), 400

        # Pega palavras do tópico
        lda = bot_worker.sistema_ml.lda_model
        vectorizer = bot_worker.sistema_ml.lda_vectorizer

        feature_names = vectorizer.get_feature_names_out()
        topic_words = lda.components_[topico]
        top_indices = topic_words.argsort()[-10:][::-1]
        top_words = [feature_names[i] for i in top_indices]

        return jsonify({
            "status": "success",
            "pergunta": pergunta,
            "topico": topico,
            "top_words": top_words
        }), 200

    except Exception as e:
        logger.error(f"Erro ao detectar tópico: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Erro ao detectar tópico",
            "message": str(e)
        }), 500

@bot_bp.route('/health', methods=['GET'])
def health_check():
    try:
        bot_worker = get_bot_worker()
        ml = bot_worker.sistema_ml

        return jsonify({
            "status": "online",
            "modo_producao": MODO_PRODUCAO,
            "modelos_carregados": {
                "ensemble_nb": ml.modelo_intencao_nb is not None,
                "ensemble_rf": ml.modelo_intencao_rf is not None,
                "ensemble_gb": ml.modelo_intencao_gb is not None,
                "lstm": ml.modelo_intencao_lstm is not None,
                "ranqueador": ml.modelo_ranqueamento_fonte is not None,
                "lda": ml.lda_model is not None
            },
            "cache_size": len(cache),
            "deep_learning": DEEP_LEARNING_AVAILABLE
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

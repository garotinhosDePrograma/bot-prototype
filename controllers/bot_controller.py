from bot.bot_worker import BotWorker
from flask import Blueprint, jsonify, request

bot_bp = Blueprint('bot', __name__, url_prefix="/api")

b = BotWorker()

@bot_bp.route('/question', methods=['POST'])
def question():
    data = request.get_json()
    if not data:
        return jsonify({"error": "data inválida"}), 400
    
    pergunta = data.get("pergunta")
    user_id = data.get("id")

    if not pergunta:
        return jsonify({"error": "Pergunta é obrigatória"}), 400

    response = b.process_query(pergunta, user_id)

    if not response:
        return jsonify({"error": "Erro ao processar pergunta"}), 400

    return jsonify({"resposta": response})
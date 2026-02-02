from flask import Blueprint, jsonify, request
from workers.user_worker import UserWorker

user_bp = Blueprint('users', __name__, url_prefix='/api')

worker = UserWorker()

@user_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data:
        return jsonify({"error": "data inválida"}), 400

    nome = data.get("nome")
    email = data.get("email")
    senha = data.get("senha")
    if not all([nome, email, senha]):
        return jsonify({"error": "Campos obrigatórios faltando"}), 400

    
    user = worker.create(nome, email, senha)
    if not user:
        return jsonify({"error": "Erro interno ao criar usuário"}), 500

    return jsonify({"message": "Usuário criado com sucesso"})

@user_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data:
        return jsonify({"error": "data inválida"}), 400

    email = data.get("email")
    senha = data.get("senha")
    if not all([email, senha]):
        return jsonify({"error": "Campos obrigatórios faltando"}), 400

    return worker.login(email, senha)

@user_bp.route('/all', methods=['GET'])
def get_all_users():
    return worker.getAll()
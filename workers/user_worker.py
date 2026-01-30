from flask import jsonify
from repositories.user_repository import UserRepository
from datetime import datetime, timedelta
import bcrypt
import jwt

repo = UserRepository()

SECRET_KEY = "TXGKPOYWXGENEISJSIWHRBF"

class UserWorker:
    def create(self, nome, email, senha):
        user = repo.getByEmail(email)
        if user:
            return jsonify({"error": "Email já existe"}), 400

        hash = bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt())

        created = repo.create(nome, email, hash)
        if not created:
            return jsonify({"error": "Erro ao criar usuário"}), 400

        return jsonify({"message": "Usuário criado com sucesso"})

    def login(self, email, senha):
        user = repo.getByEmail(email)
        if not user.email:
            return jsonify({"error": "Email inválido"}), 401

        if user.senha != bcrypt.checkpw(senha.encode("utf-8"), user.senha):
            return jsonify({"error": "Senha inválida"}), 401

        token = jwt.encode(
            {
                "id": user.id,
                "exp": datetime.utcnow() + timedelta(hours=1)
            },
            SECRET_KEY,
            algorithm="HS256"
        )

        return jsonify({
            "token": token,
            "user": user
        })
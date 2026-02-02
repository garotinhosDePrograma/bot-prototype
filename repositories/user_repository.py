from models.user import User
from utils.db import get_db_cursor
from mysql.connector import Error

class UserRepository:
    def create(self, nome, email, senha):
        try:
            with get_db_cursor() as cur:
                cur.execute(
                    "INSERT INTO usuarios (nome, email, senha) VALUES (%s,%s,%s)",
                    (nome, email, senha)
                )
                user_id = cur.lastrowid

                return User(
                    id=user_id,
                    nome=nome,
                    email=email,
                    senha=senha
                )
        except Error as e:
            print(f"Erro ao criar usuário: {e}")
            return False

    def getAll(self):
        try:
            with get_db_cursor() as cur:
                cur.execute("SELECT id, nome, email FROM usuarios")
                users = cur.fetchall()

                return users
        
        except Error as e:
            print(f"Erro ao buscar usuários: {e}")
            return None

    def getByEmail(self, email):
        try:
            with get_db_cursor() as cur:
                cur.execute(
                    "SELECT * FROM usuarios WHERE email = %s",
                    (email,)
                )
                user = cur.fetchone()

                if user:
                    return User(**user)
                return None
        
        except Error as e:
            print(f"Erro ao buscar usuário pelo email: {e}")
            return None
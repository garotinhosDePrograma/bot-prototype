from utils.db import get_db_cursor
from mysql.connector import Error

def db():
    try:
        with get_db_cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    nome VARCHAR(200) NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    senha VARCHAR(255) NOT NULL
                )
            """)
            print("criado")
    
    except Error as e:
        print(f"Erro ao criar table: {e}")

db()
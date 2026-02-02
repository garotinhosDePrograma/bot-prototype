import mysql.connector
from mysql.connector import pooling, Error
import os
from urllib.parse import urlparse
from dotenv import load_dotenv
from contextlib import contextmanager

load_dotenv()

connection_url = os.getenv('CONN_URL')
parsed_url = urlparse(connection_url)

config = {
    'host': parsed_url.hostname,
    'port': parsed_url.port,
    'user': parsed_url.username,
    'password': parsed_url.password,
    'database': parsed_url.path.decode('utf-8').lstrip('/') if isinstance(parsed_url.path, bytes) else parsed_url.path.lstrip('/'),
    'ssl_disabled': False,
}

try:
    connection_pool = pooling.MySQLConnectionPool(
        pool_name="mylinks_pool",
        pool_size=5,
        pool_reset_session=True,
        **config
    )
    print("Connection pool criada com sucesso.")
except Error as e:
    print(f"Erro ao criar pool: {e}")
    connection_pool = None

def get_db():
    if connection_pool:
        return connection_pool.get_connection()

    return mysql.connector.connect(**config)

@contextmanager
def get_db_cursor(dictionary=True):
    conn = get_db()
    cursor = conn.cursor(dictionary=dictionary)
    try:
        yield cursor
        conn.commit()
    except Error as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()
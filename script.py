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

"""
Script de migração - Criação da tabela bot_conversations
Execute: python migrations/create_bot_conversations_table.py
"""

def create_bot_conversations_table():
    """
    Cria a tabela bot_conversations para armazenar histórico de conversas com o bot.

    Campos:
    - id: Identificador único da conversa
    - user_id: Referência ao usuário que fez a pergunta
    - pergunta: Texto da pergunta feita
    - resposta: Texto da resposta gerada
    - fonte: API(s) que forneceram a resposta (wolfram, google, duckduckgo, wikipedia)
    - tempo_processamento: Tempo em segundos para processar a query
    - status: Status da operação (success, error)
    - metadata: JSON com dados adicionais (logs_processo, tipo_pergunta, etc)
    - created_at: Timestamp de criação
    """
    try:
        with get_db_cursor() as cur:
            # Cria a tabela
            cur.execute("""
                CREATE TABLE IF NOT EXISTS bot_conversations (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    user_id INT NOT NULL,
                    pergunta TEXT NOT NULL,
                    resposta TEXT NOT NULL,
                    fonte VARCHAR(100),
                    tempo_processamento FLOAT,
                    status VARCHAR(20) DEFAULT 'success',
                    metadata JSON,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                    FOREIGN KEY (user_id) REFERENCES usuarios(id) ON DELETE CASCADE,
                    INDEX idx_user_created (user_id, created_at DESC),
                    INDEX idx_status (status),
                    INDEX idx_fonte (fonte)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            print("✅ Tabela 'bot_conversations' criada com sucesso!")

            # Verifica se a tabela foi criada
            cur.execute("SHOW TABLES LIKE 'bot_conversations'")
            result = cur.fetchone()

            if result:
                print("✅ Verificação: tabela existe no banco de dados")

                # Mostra estrutura da tabela
                cur.execute("DESCRIBE bot_conversations")
                columns = cur.fetchall()

                print("\n📋 Estrutura da tabela:")
                print("-" * 80)
                for col in columns:
                    print(f"  {col['Field']:20} {col['Type']:20} {col['Null']:5} {col['Key']:5}")
                print("-" * 80)
            else:
                print("⚠️  Aviso: tabela não foi encontrada após criação")

    except Error as e:
        print(f"❌ Erro ao criar tabela bot_conversations: {e}")
        return False

    return True


def rollback_bot_conversations_table():
    """
    Remove a tabela bot_conversations (rollback da migração).
    Use com cuidado - isso apaga todos os dados!
    """
    try:
        with get_db_cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS bot_conversations")
            print("✅ Tabela 'bot_conversations' removida com sucesso!")
    except Error as e:
        print(f"❌ Erro ao remover tabela: {e}")
        return False

    return True


if __name__ == "__main__":
    print("\n" + "="*80)
    print("🗄️  MIGRAÇÃO: Criação da tabela bot_conversations")
    print("="*80 + "\n")

    import sys

    # Verifica se é rollback
    if len(sys.argv) > 1 and sys.argv[1] == "--rollback":
        print("⚠️  ATENÇÃO: Você está prestes a DELETAR a tabela bot_conversations!")
        confirm = input("Digite 'confirmar' para prosseguir: ")

        if confirm.lower() == "confirmar":
            rollback_bot_conversations_table()
        else:
            print("❌ Rollback cancelado.")
    else:
        # Executa migração
        create_bot_conversations_table()

    print("\n" + "="*80)
    print("✨ Migração concluída!")
    print("="*80 + "\n")
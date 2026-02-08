from models.bot_conversation import BotConversation
from utils.db import get_db_cursor
from mysql.connector import Error
import json
import logging

logger = logging.getLogger(__name__)

class BotRepository:
    def create_conversation(
        self, 
        user_id, 
        pergunta, 
        resposta, 
        fonte=None, 
        tempo_processamento=None,
        status='success',
        metadata=None
    ):
        """
        Cria uma nova conversa no banco de dados.

        Args:
            user_id (int): ID do usuário
            pergunta (str): Pergunta feita
            resposta (str): Resposta gerada
            fonte (str, optional): Fonte(s) usada(s)
            tempo_processamento (float, optional): Tempo em segundos
            status (str): Status da operação ('success' ou 'error')
            metadata (dict, optional): Dados adicionais

        Returns:
            BotConversation: Instância criada ou None se falhar
        """
        try:
            # Converte metadata para JSON string
            metadata_json = json.dumps(metadata) if metadata else None

            with get_db_cursor() as cur:
                cur.execute("""
                    INSERT INTO bot_conversations 
                    (user_id, pergunta, resposta, fonte, tempo_processamento, status, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    user_id,
                    pergunta,
                    resposta,
                    fonte,
                    tempo_processamento,
                    status,
                    metadata_json
                ))

                conversation_id = cur.lastrowid

                logger.info(f"Conversa criada: ID={conversation_id}, user_id={user_id}")

                # Retorna a conversa criada
                return BotConversation(
                    id=conversation_id,
                    user_id=user_id,
                    pergunta=pergunta,
                    resposta=resposta,
                    fonte=fonte,
                    tempo_processamento=tempo_processamento,
                    status=status,
                    metadata=metadata
                )

        except Error as e:
            logger.error(f"Erro ao criar conversa: {e}")
            return None

    def get_conversation_by_id(self, conversation_id):
        """
        Busca uma conversa específica por ID.

        Args:
            conversation_id (int): ID da conversa

        Returns:
            BotConversation: Instância encontrada ou None
        """
        try:
            with get_db_cursor() as cur:
                cur.execute("""
                    SELECT * FROM bot_conversations 
                    WHERE id = %s
                """, (conversation_id,))

                data = cur.fetchone()

                if data:
                    return BotConversation.from_dict(data)
                return None

        except Error as e:
            logger.error(f"Erro ao buscar conversa {conversation_id}: {e}")
            return None

    def get_user_conversations(self, user_id, limit=20, offset=0):
        """
        Busca conversas de um usuário com paginação.

        Args:
            user_id (int): ID do usuário
            limit (int): Número máximo de resultados
            offset (int): Deslocamento para paginação

        Returns:
            list[BotConversation]: Lista de conversas
        """
        try:
            with get_db_cursor() as cur:
                cur.execute("""
                    SELECT * FROM bot_conversations 
                    WHERE user_id = %s 
                    ORDER BY created_at DESC
                    LIMIT %s OFFSET %s
                """, (user_id, limit, offset))

                rows = cur.fetchall()

                conversations = [BotConversation.from_dict(row) for row in rows]

                logger.info(f"Buscadas {len(conversations)} conversas do usuário {user_id}")
                return conversations

        except Error as e:
            logger.error(f"Erro ao buscar conversas do usuário {user_id}: {e}")
            return []

    def get_total_conversations_count(self, user_id):
        """
        Retorna o total de conversas de um usuário.
        Útil para paginação no frontend.

        Args:
            user_id (int): ID do usuário

        Returns:
            int: Total de conversas
        """
        try:
            with get_db_cursor() as cur:
                cur.execute("""
                    SELECT COUNT(*) as total 
                    FROM bot_conversations 
                    WHERE user_id = %s
                """, (user_id,))

                result = cur.fetchone()
                return result['total'] if result else 0

        except Error as e:
            logger.error(f"Erro ao contar conversas do usuário {user_id}: {e}")
            return 0

    def search_conversations(self, user_id, query, limit=20):
        """
        Busca conversas por palavra-chave na pergunta ou resposta.

        Args:
            user_id (int): ID do usuário
            query (str): Termo de busca
            limit (int): Número máximo de resultados

        Returns:
            list[BotConversation]: Lista de conversas encontradas
        """
        try:
            with get_db_cursor() as cur:
                search_term = f"%{query}%"

                cur.execute("""
                    SELECT * FROM bot_conversations 
                    WHERE user_id = %s 
                    AND (pergunta LIKE %s OR resposta LIKE %s)
                    ORDER BY created_at DESC
                    LIMIT %s
                """, (user_id, search_term, search_term, limit))

                rows = cur.fetchall()

                conversations = [BotConversation.from_dict(row) for row in rows]

                logger.info(f"Busca '{query}': {len(conversations)} resultados para usuário {user_id}")
                return conversations

        except Error as e:
            logger.error(f"Erro ao buscar conversas: {e}")
            return []

    def delete_conversation(self, conversation_id, user_id):
        """
        Deleta uma conversa específica.
        Valida se a conversa pertence ao usuário antes de deletar.

        Args:
            conversation_id (int): ID da conversa
            user_id (int): ID do usuário (para validação)

        Returns:
            bool: True se deletado com sucesso, False caso contrário
        """
        try:
            with get_db_cursor() as cur:
                # Deleta apenas se pertencer ao usuário
                cur.execute("""
                    DELETE FROM bot_conversations 
                    WHERE id = %s AND user_id = %s
                """, (conversation_id, user_id))

                deleted = cur.rowcount > 0

                if deleted:
                    logger.info(f"Conversa {conversation_id} deletada pelo usuário {user_id}")
                else:
                    logger.warning(f"Tentativa de deletar conversa {conversation_id} falhou (usuário {user_id})")

                return deleted

        except Error as e:
            logger.error(f"Erro ao deletar conversa {conversation_id}: {e}")
            return False

    def delete_user_conversations(self, user_id):
        """
        Deleta todas as conversas de um usuário.

        Args:
            user_id (int): ID do usuário

        Returns:
            int: Número de conversas deletadas
        """
        try:
            with get_db_cursor() as cur:
                cur.execute("""
                    DELETE FROM bot_conversations 
                    WHERE user_id = %s
                """, (user_id,))

                deleted_count = cur.rowcount

                logger.info(f"{deleted_count} conversas deletadas do usuário {user_id}")
                return deleted_count

        except Error as e:
            logger.error(f"Erro ao deletar conversas do usuário {user_id}: {e}")
            return 0

    def get_user_statistics(self, user_id):
        """
        Calcula estatísticas das conversas do usuário.

        Args:
            user_id (int): ID do usuário

        Returns:
            dict: Estatísticas (total, tempo_medio, cache_hits, etc)
        """
        try:
            with get_db_cursor() as cur:
                # Busca estatísticas gerais
                cur.execute("""
                    SELECT 
                        COUNT(*) as total_perguntas,
                        AVG(tempo_processamento) as tempo_medio,
                        SUM(CASE WHEN tempo_processamento < 0.1 THEN 1 ELSE 0 END) as cache_hits,
                        COUNT(CASE WHEN status = 'success' THEN 1 END) as sucessos,
                        COUNT(CASE WHEN status = 'error' THEN 1 END) as erros
                    FROM bot_conversations 
                    WHERE user_id = %s
                """, (user_id,))

                stats = cur.fetchone()

                # Busca fontes mais usadas
                cur.execute("""
                    SELECT fonte, COUNT(*) as count 
                    FROM bot_conversations 
                    WHERE user_id = %s AND fonte IS NOT NULL
                    GROUP BY fonte 
                    ORDER BY count DESC 
                    LIMIT 5
                """, (user_id,))

                fontes = cur.fetchall()

                return {
                    "total_perguntas": stats['total_perguntas'] or 0,
                    "tempo_medio": round(stats['tempo_medio'] or 0, 2),
                    "cache_hits": stats['cache_hits'] or 0,
                    "taxa_cache": round((stats['cache_hits'] / stats['total_perguntas'] * 100) if stats['total_perguntas'] > 0 else 0, 1),
                    "sucessos": stats['sucessos'] or 0,
                    "erros": stats['erros'] or 0,
                    "taxa_sucesso": round((stats['sucessos'] / stats['total_perguntas'] * 100) if stats['total_perguntas'] > 0 else 0, 1),
                    "fontes_mais_usadas": [
                        {"fonte": f['fonte'], "count": f['count']} 
                        for f in fontes
                    ]
                }

        except Error as e:
            logger.error(f"Erro ao calcular estatísticas do usuário {user_id}: {e}")
            return {
                "total_perguntas": 0,
                "tempo_medio": 0,
                "cache_hits": 0,
                "taxa_cache": 0,
                "sucessos": 0,
                "erros": 0,
                "taxa_sucesso": 0,
                "fontes_mais_usadas": []
            }

    def get_recent_conversations(self, user_id, days=7, limit=10):
        """
        Busca conversas recentes dos últimos N dias.

        Args:
            user_id (int): ID do usuário
            days (int): Número de dias para buscar
            limit (int): Número máximo de resultados

        Returns:
            list[BotConversation]: Lista de conversas recentes
        """
        try:
            with get_db_cursor() as cur:
                cur.execute("""
                    SELECT * FROM bot_conversations 
                    WHERE user_id = %s 
                    AND created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
                    ORDER BY created_at DESC
                    LIMIT %s
                """, (user_id, days, limit))

                rows = cur.fetchall()

                conversations = [BotConversation.from_dict(row) for row in rows]

                logger.info(f"{len(conversations)} conversas recentes (últimos {days} dias) do usuário {user_id}")
                return conversations

        except Error as e:
            logger.error(f"Erro ao buscar conversas recentes do usuário {user_id}: {e}")
            return []

    # ============================================
    # MÉTODOS NOVOS PARA FEEDBACK E APRENDIZADO
    # ============================================

    def update_conversation_metadata(self, conversation_id, metadata):
        """
        Atualiza o campo metadata de uma conversa.
        Usado principalmente para registrar feedback do usuário.

        Args:
            conversation_id (int): ID da conversa
            metadata (dict): Novo metadata

        Returns:
            bool: True se atualizado com sucesso, False caso contrário
        """
        try:
            metadata_json = json.dumps(metadata) if metadata else None

            with get_db_cursor() as cur:
                cur.execute("""
                    UPDATE bot_conversations 
                    SET metadata = %s 
                    WHERE id = %s
                """, (metadata_json, conversation_id))

                updated = cur.rowcount > 0

                if updated:
                    logger.info(f"Metadata atualizado para conversa {conversation_id}")
                else:
                    logger.warning(f"Tentativa de atualizar metadata da conversa {conversation_id} falhou")

                return updated

        except Error as e:
            logger.error(f"Erro ao atualizar metadata da conversa {conversation_id}: {e}")
            return False

    def get_conversations_with_feedback(self, tipo=None, limit=100):
        """
        Busca conversas que receberam feedback do usuário.
        Útil para análise e retreinamento do modelo.

        Args:
            tipo (str, optional): Tipo de feedback ('positivo', 'negativo', 'neutro')
            limit (int): Número máximo de resultados

        Returns:
            list[BotConversation]: Lista de conversas com feedback
        """
        try:
            with get_db_cursor() as cur:
                if tipo:
                    # Busca por tipo específico de feedback
                    cur.execute("""
                        SELECT * FROM bot_conversations 
                        WHERE metadata LIKE %s
                        ORDER BY created_at DESC
                        LIMIT %s
                    """, (f'%"tipo": "{tipo}"%', limit))
                else:
                    # Busca todas com feedback
                    cur.execute("""
                        SELECT * FROM bot_conversations 
                        WHERE metadata LIKE %s
                        ORDER BY created_at DESC
                        LIMIT %s
                    """, ('%"feedback"%', limit))

                rows = cur.fetchall()

                conversations = [BotConversation.from_dict(row) for row in rows]

                logger.info(f"Buscadas {len(conversations)} conversas com feedback (tipo: {tipo or 'todos'})")
                return conversations

        except Error as e:
            logger.error(f"Erro ao buscar conversas com feedback: {e}")
            return []

    def get_user_conversations_with_feedback(self, user_id):
        """
        Busca conversas de um usuário que receberam feedback.

        Args:
            user_id (int): ID do usuário

        Returns:
            list[BotConversation]: Lista de conversas com feedback
        """
        try:
            with get_db_cursor() as cur:
                cur.execute("""
                    SELECT * FROM bot_conversations 
                    WHERE user_id = %s 
                    AND metadata LIKE %s
                    ORDER BY created_at DESC
                """, (user_id, '%"feedback"%'))

                rows = cur.fetchall()

                conversations = [BotConversation.from_dict(row) for row in rows]

                logger.info(f"Buscadas {len(conversations)} conversas com feedback do usuário {user_id}")
                return conversations

        except Error as e:
            logger.error(f"Erro ao buscar conversas com feedback do usuário {user_id}: {e}")
            return []

    def get_all_conversations_with_feedback(self):
        """
        Busca todas as conversas (de todos os usuários) que receberam feedback.

        Returns:
            list[BotConversation]: Lista de conversas com feedback
        """
        try:
            with get_db_cursor() as cur:
                cur.execute("""
                    SELECT * FROM bot_conversations 
                    WHERE metadata LIKE %s
                    ORDER BY created_at DESC
                """, ('%"feedback"%',))

                rows = cur.fetchall()

                conversations = [BotConversation.from_dict(row) for row in rows]

                logger.info(f"Buscadas {len(conversations)} conversas com feedback (todos os usuários)")
                return conversations

        except Error as e:
            logger.error(f"Erro ao buscar todas conversas com feedback: {e}")
            return []

    def get_all_conversations_for_training(self, limit=1000):
        """
        Busca conversas para treinamento de modelos de ML.
        Retorna conversas bem-sucedidas, ordenadas por mais recente.

        Args:
            limit (int): Número máximo de conversas

        Returns:
            list[BotConversation]: Lista de conversas para treino
        """
        try:
            with get_db_cursor() as cur:
                cur.execute("""
                    SELECT * FROM bot_conversations 
                    WHERE status = 'success'
                    ORDER BY created_at DESC
                    LIMIT %s
                """, (limit,))

                rows = cur.fetchall()

                conversations = [BotConversation.from_dict(row) for row in rows]

                logger.info(f"Buscadas {len(conversations)} conversas para treinamento")
                return conversations

        except Error as e:
            logger.error(f"Erro ao buscar conversas para treinamento: {e}")
            return []

    def get_conversations_with_metadata(self, limit=1000):
        """
        Busca conversas que têm metadata (usado para treinar avaliador de qualidade).

        Args:
            limit (int): Número máximo de conversas

        Returns:
            list[BotConversation]: Lista de conversas com metadata
        """
        try:
            with get_db_cursor() as cur:
                cur.execute("""
                    SELECT * FROM bot_conversations 
                    WHERE metadata IS NOT NULL 
                    AND metadata != '{}'
                    ORDER BY created_at DESC
                    LIMIT %s
                """, (limit,))

                rows = cur.fetchall()

                conversations = [BotConversation.from_dict(row) for row in rows]

                logger.info(f"Buscadas {len(conversations)} conversas com metadata")
                return conversations

        except Error as e:
            logger.error(f"Erro ao buscar conversas com metadata: {e}")
            return []
"""
Model para representar uma conversa do bot.
"""

from datetime import datetime
import json


class BotConversation:
    """
    Representa uma conversa entre usuário e bot.
    
    Attributes:
        id (int): ID único da conversa
        user_id (int): ID do usuário que fez a pergunta
        pergunta (str): Pergunta feita pelo usuário
        resposta (str): Resposta gerada pelo bot
        fonte (str): Fonte(s) de dados usada(s) (ex: 'wolfram', 'google+duckduckgo')
        tempo_processamento (float): Tempo em segundos para processar
        status (str): Status da operação ('success' ou 'error')
        metadata (dict): Dados adicionais (logs_processo, tipo_pergunta, etc)
        created_at (datetime): Data/hora da conversa
    """
    
    def __init__(
        self, 
        id=None,
        user_id=None,
        pergunta=None,
        resposta=None,
        fonte=None,
        tempo_processamento=None,
        status='success',
        metadata=None,
        created_at=None
    ):
        self.id = id
        self.user_id = user_id
        self.pergunta = pergunta
        self.resposta = resposta
        self.fonte = fonte
        self.tempo_processamento = tempo_processamento
        self.status = status
        self.metadata = metadata or {}
        self.created_at = created_at
    
    def to_dict(self, include_metadata=True):
        """
        Converte o model para dicionário.
        
        Args:
            include_metadata (bool): Se True, inclui o campo metadata completo
            
        Returns:
            dict: Representação em dicionário do model
        """
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "pergunta": self.pergunta,
            "resposta": self.resposta,
            "fonte": self.fonte,
            "tempo_processamento": self.tempo_processamento,
            "status": self.status,
            "created_at": self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at
        }
        
        if include_metadata:
            data["metadata"] = self.metadata
        
        return data
    
    def to_dict_summary(self):
        """
        Retorna versão resumida (sem resposta completa e metadata).
        Útil para listagens de histórico.
        
        Returns:
            dict: Versão resumida do model
        """
        return {
            "id": self.id,
            "user_id": self.user_id,
            "pergunta": self.pergunta,
            "resposta_preview": self.resposta[:100] + "..." if len(self.resposta) > 100 else self.resposta,
            "fonte": self.fonte,
            "tempo_processamento": self.tempo_processamento,
            "status": self.status,
            "created_at": self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at
        }
    
    @staticmethod
    def from_dict(data):
        """
        Cria uma instância de BotConversation a partir de um dicionário.
        Útil para desserializar dados do banco.
        
        Args:
            data (dict): Dicionário com os dados
            
        Returns:
            BotConversation: Instância do model
        """
        # Converte metadata de JSON string para dict se necessário
        metadata = data.get('metadata')
        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
            except (json.JSONDecodeError, TypeError):
                metadata = {}
        
        return BotConversation(
            id=data.get('id'),
            user_id=data.get('user_id'),
            pergunta=data.get('pergunta'),
            resposta=data.get('resposta'),
            fonte=data.get('fonte'),
            tempo_processamento=data.get('tempo_processamento'),
            status=data.get('status', 'success'),
            metadata=metadata,
            created_at=data.get('created_at')
        )
    
    def __repr__(self):
        """Representação string do objeto."""
        return f"<BotConversation(id={self.id}, user_id={self.user_id}, pergunta='{self.pergunta[:30]}...')>"

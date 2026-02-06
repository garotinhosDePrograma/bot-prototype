"""
Sistema de feedback explícito do usuário para aprendizado supervisionado.
"""

import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

class SistemaFeedback:
    """
    Coleta e processa feedback do usuário sobre respostas.
    """
    
    def __init__(self, repository):
        self.repository = repository
    
    def registrar_feedback(
        self, 
        conversation_id: int, 
        tipo_feedback: str,  # "positivo", "negativo", "neutro"
        detalhes: Optional[str] = None
    ) -> bool:
        """
        Registra feedback do usuário sobre uma resposta.
        
        Args:
            conversation_id: ID da conversa
            tipo_feedback: "positivo", "negativo" ou "neutro"
            detalhes: Comentários adicionais do usuário
        """
        try:
            conversa = self.repository.get_conversation_by_id(conversation_id)
            
            if not conversa:
                logger.error(f"Conversa {conversation_id} não encontrada")
                return False
            
            # Atualiza metadata da conversa
            metadata = conversa.metadata or {}
            metadata["feedback"] = {
                "tipo": tipo_feedback,
                "detalhes": detalhes,
                "timestamp": datetime.now().isoformat()
            }
            
            # Salva no banco
            self.repository.update_conversation_metadata(conversation_id, metadata)
            
            logger.info(f"Feedback registrado: {tipo_feedback} para conversa {conversation_id}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao registrar feedback: {str(e)}")
            return False
    
    def registrar_correcao(
        self, 
        conversation_id: int, 
        resposta_correta: str
    ) -> bool:
        """
        Registra correção do usuário quando resposta está errada.
        Muito valioso para aprendizado supervisionado!
        """
        try:
            conversa = self.repository.get_conversation_by_id(conversation_id)
            
            if not conversa:
                return False
            
            # Salva correção
            metadata = conversa.metadata or {}
            metadata["correcao"] = {
                "resposta_original": conversa.resposta,
                "resposta_correta": resposta_correta,
                "timestamp": datetime.now().isoformat()
            }
            
            self.repository.update_conversation_metadata(conversation_id, metadata)
            
            logger.info(f"Correção registrada para conversa {conversation_id}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao registrar correção: {str(e)}")
            return False
    
    def obter_conversas_com_feedback(self, tipo: Optional[str] = None, limit: int = 100):
        """
        Busca conversas que receberam feedback.
        Útil para análise e retreinamento.
        """
        try:
            conversas = self.repository.get_conversations_with_feedback(tipo, limit)
            return conversas
        except Exception as e:
            logger.error(f"Erro ao buscar conversas com feedback: {str(e)}")
            return []
    
    def calcular_taxa_satisfacao(self, user_id: Optional[int] = None) -> dict:
        """
        Calcula taxa de satisfação geral ou por usuário.
        """
        try:
            if user_id:
                conversas = self.repository.get_user_conversations_with_feedback(user_id)
            else:
                conversas = self.repository.get_all_conversations_with_feedback()
            
            if not conversas:
                return {"taxa_satisfacao": 0, "total": 0}
            
            positivos = 0
            negativos = 0
            neutros = 0
            
            for conversa in conversas:
                feedback = conversa.metadata.get("feedback", {})
                tipo = feedback.get("tipo", "")
                
                if tipo == "positivo":
                    positivos += 1
                elif tipo == "negativo":
                    negativos += 1
                else:
                    neutros += 1
            
            total = len(conversas)
            taxa = (positivos / total) * 100 if total > 0 else 0
            
            return {
                "taxa_satisfacao": round(taxa, 2),
                "total": total,
                "positivos": positivos,
                "negativos": negativos,
                "neutros": neutros
            }
            
        except Exception as e:
            logger.error(f"Erro ao calcular satisfação: {str(e)}")
            return {"taxa_satisfacao": 0, "total": 0}

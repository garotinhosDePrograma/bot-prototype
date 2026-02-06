"""
Bot Worker - Versão refatorada com integração ao banco de dados
Busca em todas as APIs e combina respostas de forma inteligente
"""

import logging
import time
from random import choice
from cachetools import TTLCache

from bot.utils.config import Config
from bot.api.search import BuscadorAPI
from bot.utils.text_utils import normalizar_texto, detectar_idioma, traduzir
from bot.utils.question_analyzer import AnalisadorPergunta
from bot.utils.response_combiner import CombinadorRespostas
from bot.utils.response_formatter import FormatadorResposta, RESPOSTAS_INTENCAO
from bot.utils.advanced_analyzer import AnalisadorAvancado
from bot.utils.search_strategy import EstrategiaBusca
from bot.ml.learning_system import SistemaAprendizado
from bot.ml.feedback_system import SistemaFeedback
from repositories.bot_repository import BotRepository

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cache de respostas (em memória)
cache = TTLCache(maxsize=100, ttl=3600)

# Contexto da conversa
contexto = []


class BotWorker:
    """
    Chatbot que busca informações em múltiplas fontes,
    combina as respostas de forma inteligente e salva no banco de dados.
    """

    def __init__(self):
        # Inicializa componentes
        self.buscador = BuscadorAPI(
            wolfram_app_id=Config.WOLFRAM_APP_ID,
            google_cx=Config.GOOGLE_CX,
            google_api_key=Config.GOOGLE_API_KEY
        )
        self.analisador = AnalisadorPergunta()
        self.combinador = CombinadorRespostas()
        self.formatador = FormatadorResposta()
        self.repository = BotRepository()

        self.analisador_avancado = AnalisadorAvancado()
        self.estrategia_busca = EstrategiaBusca()
        self.sistema_aprendizado = SistemaAprendizado(self.repository)
        self.sistema_feedback = SistemaFeedback(self.repository)

        self.contador_conversas = 0
        
        logger.info("BotWorker inicializado com sucesso (versão com DB).")

    def process_query(self, query: str, user_id: int = None) -> dict:
        """
        Processa uma query do usuário e retorna resposta estruturada.
        Se user_id for fornecido, salva a conversa no banco de dados.

        Args:
            query: Pergunta do usuário
            user_id: ID do usuário (opcional, mas necessário para salvar no DB)

        Returns:
            Dicionário com status, resposta e metadados incluindo logs do processo
        """
        start_time = time.time()
        logs_processo = []

        try:
            logs_processo.append({"etapa": "inicio", "timestamp": time.time() - start_time, "detalhes": f"Query recebida: {query}"})
            logger.info(f"Processando query: {query} (user_id: {user_id})")

            # Valida entrada
            valid, message = self._validate_input(query)
            if not valid:
                logs_processo.append({"etapa": "validacao", "timestamp": time.time() - start_time, "status": "erro", "detalhes": message})
                
                # Salva erro no banco se user_id fornecido
                if user_id:
                    self._save_conversation(
                        user_id=user_id,
                        pergunta=query,
                        resposta=message,
                        fonte="validacao",
                        tempo_processamento=time.time() - start_time,
                        status="error",
                        logs_processo=logs_processo
                    )
                
                return {
                    "status": "error",
                    "query": query,
                    "message": message,
                    "user_id": user_id,
                    "response": "",
                    "source": "validacao",
                    "processing_time": round(time.time() - start_time, 3),
                    "logs_processo": logs_processo
                }

            logs_processo.append({"etapa": "validacao", "timestamp": time.time() - start_time, "status": "ok"})

            # Obtém resposta
            response, source, logs_busca = self._get_bot_response_with_logs(query, start_time)
            logs_processo.extend(logs_busca)

            processing_time = time.time() - start_time
            logs_processo.append({"etapa": "fim", "timestamp": processing_time, "detalhes": "Processamento concluído"})

            # Salva conversa no banco se user_id fornecido
            if user_id:
                self._save_conversation(
                    user_id=user_id,
                    pergunta=query,
                    resposta=response,
                    fonte=source,
                    tempo_processamento=processing_time,
                    status="success",
                    logs_processo=logs_processo
                )

            return {
                "status": "success",
                "query": query,
                "response": response,
                "source": source,
                "user_id": user_id,
                "processing_time": round(processing_time, 3),
                "logs_processo": logs_processo
            }

        except Exception as e:
            logger.error(f"Erro ao processar query: {str(e)}", exc_info=True)
            processing_time = time.time() - start_time
            logs_processo.append({"etapa": "erro", "timestamp": processing_time, "detalhes": str(e)})
            
            error_message = "Ocorreu um erro ao processar sua pergunta."
            
            # Salva erro no banco se user_id fornecido
            if user_id:
                self._save_conversation(
                    user_id=user_id,
                    pergunta=query,
                    resposta=error_message,
                    fonte="erro",
                    tempo_processamento=processing_time,
                    status="error",
                    logs_processo=logs_processo
                )
            
            return {
                "status": "error",
                "query": query,
                "message": f"Erro interno: {str(e)}",
                "response": error_message,
                "source": "erro",
                "user_id": user_id,
                "processing_time": round(processing_time, 3),
                "logs_processo": logs_processo
            }

    def _save_conversation(self, user_id, pergunta, resposta, fonte, tempo_processamento, status, logs_processo):
        """
        Salva a conversa no banco de dados via repository.
        
        Args:
            user_id (int): ID do usuário
            pergunta (str): Pergunta feita
            resposta (str): Resposta gerada
            fonte (str): Fonte(s) usada(s)
            tempo_processamento (float): Tempo em segundos
            status (str): Status da operação
            logs_processo (list): Logs detalhados do processo
        """
        try:
            # Prepara metadata
            metadata = {
                "logs_processo": logs_processo,
                "cache_usado": tempo_processamento < 0.1
            }
            
            # Salva no banco
            conversation = self.repository.create_conversation(
                user_id=user_id,
                pergunta=pergunta,
                resposta=resposta,
                fonte=fonte,
                tempo_processamento=tempo_processamento,
                status=status,
                metadata=metadata
            )
            
            if conversation:
                logger.info(f"Conversa salva no banco: ID={conversation.id}")
            else:
                logger.error("Falha ao salvar conversa no banco")
                
        except Exception as e:
            logger.error(f"Erro ao salvar conversa: {str(e)}", exc_info=True)

    def get_user_history(self, user_id, limit=20, offset=0):
        """
        Busca histórico de conversas do usuário.
        
        Args:
            user_id (int): ID do usuário
            limit (int): Número de conversas por página
            offset (int): Deslocamento para paginação
            
        Returns:
            dict: Histórico com conversas e metadados de paginação
        """
        try:
            conversations = self.repository.get_user_conversations(user_id, limit, offset)
            total = self.repository.get_total_conversations_count(user_id)
            
            return {
                "status": "success",
                "conversations": [c.to_dict_summary() for c in conversations],
                "pagination": {
                    "total": total,
                    "limit": limit,
                    "offset": offset,
                    "has_more": (offset + limit) < total
                }
            }
        except Exception as e:
            logger.error(f"Erro ao buscar histórico: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "message": str(e),
                "conversations": [],
                "pagination": {"total": 0, "limit": limit, "offset": offset, "has_more": False}
            }

    def get_conversation(self, conversation_id):
        """
        Busca uma conversa específica por ID.
        
        Args:
            conversation_id (int): ID da conversa
            
        Returns:
            dict: Conversa completa ou erro
        """
        try:
            conversation = self.repository.get_conversation_by_id(conversation_id)
            
            if conversation:
                return {
                    "status": "success",
                    "conversation": conversation.to_dict(include_metadata=True)
                }
            else:
                return {
                    "status": "error",
                    "message": "Conversa não encontrada"
                }
        except Exception as e:
            logger.error(f"Erro ao buscar conversa: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "message": str(e)
            }

    def search_conversations(self, user_id, query, limit=20):
        """
        Busca conversas por palavra-chave.
        
        Args:
            user_id (int): ID do usuário
            query (str): Termo de busca
            limit (int): Número máximo de resultados
            
        Returns:
            dict: Resultados da busca
        """
        try:
            conversations = self.repository.search_conversations(user_id, query, limit)
            
            return {
                "status": "success",
                "query": query,
                "results": [c.to_dict_summary() for c in conversations],
                "total": len(conversations)
            }
        except Exception as e:
            logger.error(f"Erro ao buscar conversas: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "message": str(e),
                "results": [],
                "total": 0
            }

    def delete_conversation(self, conversation_id, user_id):
        """
        Deleta uma conversa específica.
        
        Args:
            conversation_id (int): ID da conversa
            user_id (int): ID do usuário (para validação)
            
        Returns:
            dict: Resultado da operação
        """
        try:
            deleted = self.repository.delete_conversation(conversation_id, user_id)
            
            if deleted:
                return {
                    "status": "success",
                    "message": "Conversa deletada com sucesso"
                }
            else:
                return {
                    "status": "error",
                    "message": "Conversa não encontrada ou sem permissão"
                }
        except Exception as e:
            logger.error(f"Erro ao deletar conversa: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "message": str(e)
            }

    def get_user_statistics(self, user_id):
        """
        Retorna estatísticas do usuário.
        
        Args:
            user_id (int): ID do usuário
            
        Returns:
            dict: Estatísticas detalhadas
        """
        try:
            stats = self.repository.get_user_statistics(user_id)
            
            return {
                "status": "success",
                "statistics": stats
            }
        except Exception as e:
            logger.error(f"Erro ao buscar estatísticas: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "message": str(e),
                "statistics": {}
            }

    def clear_user_history(self, user_id):
        """
        Limpa todo o histórico do usuário.
        
        Args:
            user_id (int): ID do usuário
            
        Returns:
            dict: Resultado da operação
        """
        try:
            deleted_count = self.repository.delete_user_conversations(user_id)
            
            return {
                "status": "success",
                "message": f"{deleted_count} conversas deletadas",
                "deleted_count": deleted_count
            }
        except Exception as e:
            logger.error(f"Erro ao limpar histórico: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "message": str(e),
                "deleted_count": 0
            }

    def _validate_input(self, mensagem: str) -> tuple:
        """Valida entrada do usuário."""
        if len(mensagem) > 500:
            return False, "Mensagem muito longa! Tente algo mais curto."
        if not any(c.isalnum() for c in mensagem):
            return False, "Por favor, envie uma mensagem válida."
        return True, ""

    def _get_bot_response_with_logs(self, pergunta: str, start_time: float) -> tuple:
        """
        VERSÃO MELHORADA com análise avançada e aprendizado.
        """
        logs = []

        try:
            # 1. BUSCAR RESPOSTA APRENDIDA PRIMEIRO
            logs.append({"etapa": "buscar_aprendida", "timestamp": time.time() - start_time, "inicio": True})
            resposta_aprendida, qualidade_aprendida = self.sistema_aprendizado.buscar_resposta_aprendida(pergunta)
            
            if resposta_aprendida and qualidade_aprendida > 0.9:
                logs.append({"etapa": "buscar_aprendida", "timestamp": time.time() - start_time, 
                           "resultado": "encontrada", "qualidade": qualidade_aprendida})
                logger.info(f"Usando resposta aprendida (qualidade: {qualidade_aprendida:.2f})")
                return resposta_aprendida, "aprendizado", logs
            
            logs.append({"etapa": "buscar_aprendida", "timestamp": time.time() - start_time, "resultado": "nao_encontrada"})

            # 2. ANÁLISE AVANÇADA DA PERGUNTA
            logs.append({"etapa": "analise_avancada", "timestamp": time.time() - start_time, "inicio": True})
            analise_completa = self.analisador_avancado.analisar_completo(pergunta)
            logs.append({"etapa": "analise_avancada", "timestamp": time.time() - start_time, "resultado": analise_completa})
            
            # 3. DETECTAR INTENÇÃO (com ML se disponível)
            logs.append({"etapa": "detectar_intencao_ml", "timestamp": time.time() - start_time, "inicio": True})
            intencao = self.sistema_aprendizado.prever_intencao(pergunta)
            logs.append({"etapa": "detectar_intencao_ml", "timestamp": time.time() - start_time, "resultado": intencao})

            # Se não é pergunta de conhecimento, responde direto
            if intencao != "conhecimento":
                resposta = choice(RESPOSTAS_INTENCAO[intencao])
                logs.append({"etapa": "resposta_direta", "timestamp": time.time() - start_time, "intencao": intencao})
                return resposta, intencao, logs

            # 4. ATUALIZAR CONTEXTO
            self._atualizar_contexto(pergunta, intencao)

            # 5. VERIFICAR CACHE
            pergunta_normalizada = normalizar_texto(pergunta)
            if pergunta_normalizada in cache:
                logger.info("Resposta obtida do cache")
                logs.append({"etapa": "cache", "timestamp": time.time() - start_time, "resultado": "hit"})
                resposta, fonte = cache[pergunta_normalizada]
                return resposta, fonte, logs

            logs.append({"etapa": "cache", "timestamp": time.time() - start_time, "resultado": "miss"})

            # 6. DETECTAR TIPO DE PERGUNTA
            logs.append({"etapa": "tipo_pergunta", "timestamp": time.time() - start_time, "inicio": True})
            tipo_pergunta = self.analisador.detectar_tipo_pergunta(pergunta)
            logs.append({"etapa": "tipo_pergunta", "timestamp": time.time() - start_time, "resultado": tipo_pergunta})

            # 7. ESTRATÉGIA DE BUSCA INTELIGENTE
            logs.append({"etapa": "estrategia_busca", "timestamp": time.time() - start_time, "inicio": True})
            fontes_selecionadas = self.estrategia_busca.selecionar_fontes(analise_completa)
            queries_multiplas = self.estrategia_busca.criar_queries_multiplas(pergunta, analise_completa)
            logs.append({"etapa": "estrategia_busca", "timestamp": time.time() - start_time, 
                       "fontes": fontes_selecionadas, "queries": queries_multiplas})

            # 8. TRADUÇÃO E BUSCA
            idioma = detectar_idioma(pergunta)
            logs.append({"etapa": "detectar_idioma", "timestamp": time.time() - start_time, "idioma": idioma})

            # Busca com múltiplas queries se necessário
            resultados_agregados = {}
            
            for query in queries_multiplas[:2]:  # Máximo 2 queries para não sobrecarregar
                query_en = query if idioma == "en" else traduzir(query, origem=idioma, destino="en")
                logs.append({"etapa": "traduzir_query", "timestamp": time.time() - start_time, "query_en": query_en})

                # BUSCA NAS FONTES SELECIONADAS
                logs.append({"etapa": "buscar_apis", "timestamp": time.time() - start_time, "inicio": True})
                resultados = self.buscador.buscar_todas(query_en)
                
                # Filtra apenas fontes selecionadas
                resultados_filtrados = {k: v for k, v in resultados.items() if k in fontes_selecionadas}
                
                # Mescla resultados
                for fonte, resultado in resultados_filtrados.items():
                    if resultado and fonte not in resultados_agregados:
                        resultados_agregados[fonte] = resultado

            logs.append({"etapa": "buscar_apis", "timestamp": time.time() - start_time, "resultados": resultados_agregados})

            # 9. TRADUZ RESULTADOS
            logs.append({"etapa": "traduzir_resultados", "timestamp": time.time() - start_time, "inicio": True})
            resultados_pt = {}
            for fonte, resultado in resultados_agregados.items():
                if resultado:
                    try:
                        resultado_traduzido = traduzir(resultado, origem="en", destino="pt")
                        resultados_pt[fonte] = resultado_traduzido
                    except Exception as e:
                        logger.error(f"Erro ao traduzir resultado de {fonte}: {str(e)}")
                        resultados_pt[fonte] = resultado

            # 10. COMBINA RESPOSTAS
            logs.append({"etapa": "combinar_respostas", "timestamp": time.time() - start_time, "inicio": True})
            resposta_combinada, fonte_principal = self.combinador.combinar_com_fonte_principal(
                resultados_pt, 
                pergunta, 
                tipo_pergunta
            )

            if not resposta_combinada:
                logger.info("Nenhuma resposta válida encontrada")
                resposta = choice(RESPOSTAS_INTENCAO["desconhecida"])
                fonte = "nenhuma"
                logs.append({"etapa": "resposta_fallback", "timestamp": time.time() - start_time})
            else:
                # 11. FORMATA RESPOSTA
                logs.append({"etapa": "formatar_resposta", "timestamp": time.time() - start_time, "inicio": True})
                resposta = self.formatador.formatar_final(resposta_combinada, tipo_pergunta)
                fonte = fonte_principal

                # 12. AVALIA QUALIDADE DA RESPOSTA (ML)
                qualidade = self.sistema_aprendizado.avaliar_qualidade_resposta(pergunta, resposta)
                logs.append({"etapa": "avaliar_qualidade", "timestamp": time.time() - start_time, "qualidade": qualidade})

                # 13. APRENDE PADRÃO SE BOA RESPOSTA
                if qualidade > 0.7:
                    self.sistema_aprendizado.aprender_padrao(pergunta, resposta, qualidade)
                    logs.append({"etapa": "aprender_padrao", "timestamp": time.time() - start_time})

            # 14. ATUALIZA STATS DAS FONTES
            tempo_busca = time.time() - start_time
            sucesso = resposta_combinada is not None
            if fonte_principal and fonte_principal != "nenhuma":
                fontes_usadas = fonte_principal.split("+")
                for f in fontes_usadas:
                    self.sistema_aprendizado.atualizar_stats_fonte(f, tempo_busca, sucesso)

            # Salva no cache
            cache[pergunta_normalizada] = (resposta, fonte)
            logs.append({"etapa": "salvar_cache", "timestamp": time.time() - start_time})

            # 15. RETREINAMENTO PERIÓDICO
            self.contador_conversas += 1
            if self.contador_conversas % 100 == 0:  # A cada 100 conversas
                logger.info("Iniciando retreinamento periódico...")
                self.sistema_aprendizado.retreinar_periodicamente()

            return resposta, fonte, logs

        except Exception as e:
            logger.error(f"Erro ao obter resposta: {str(e)}", exc_info=True)
            logs.append({"etapa": "erro_geral", "timestamp": time.time() - start_time, "erro": str(e)})
            return "Ocorreu um erro ao processar sua pergunta.", "erro", logs

    def _atualizar_contexto(self, pergunta: str, intencao: str):
        """Atualiza o contexto da conversa."""
        global contexto

        contexto.append({
            "pergunta": normalizar_texto(pergunta),
            "intencao": intencao
        })

        # Mantém apenas últimas 5 interações
        if len(contexto) > 5:
            contexto.pop(0)
    
    def registrar_feedback(self, conversation_id: int, tipo: str, detalhes: str = None):
        """Registra feedback do usuário."""
        return self.sistema_feedback.registrar_feedback(conversation_id, tipo, detalhes)
    
    def registrar_correcao(self, conversation_id: int, resposta_correta: str):
        """Registra correção do usuário."""
        return self.sistema_feedback.registrar_correcao(conversation_id, resposta_correta)
    
    def obter_taxa_satisfacao(self, user_id: int = None):
        """Retorna taxa de satisfação."""
        return self.sistema_feedback.calcular_taxa_satisfacao(user_id)

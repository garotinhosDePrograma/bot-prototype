"""
Bot Worker V2.0 - Com ML Avançado e Múltiplas Fontes
Integração completa do sistema de aprendizado e busca unificada
"""

import logging
import time
from random import choice
from cachetools import TTLCache

from bot.utils.config import Config
from bot.utils.text_utils import normalizar_texto, detectar_idioma, traduzir
from bot.utils.question_analyzer import AnalisadorPergunta
from bot.utils.response_combiner import CombinadorRespostas
from bot.utils.response_formatter import FormatadorResposta, RESPOSTAS_INTENCAO
from bot.utils.advanced_analyzer import AnalisadorAvancado

# NOVOS IMPORTS
from bot.ml.advanced_learning_system import SistemaAprendizadoAvancado
from bot.api.unified_searcher import BuscadorUnificado

from bot.ml.feedback_system import SistemaFeedback
from repositories.bot_repository import BotRepository

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cache de respostas
cache = TTLCache(maxsize=200, ttl=3600)  # Aumentado para 200

# Contexto da conversa
contexto = []


class BotWorkerV2:
    """
    Bot Worker versão 2.0 com:
    - Ensemble de modelos ML
    - Ranqueamento inteligente de fontes
    - Topic modeling
    - Busca otimizada e paralela
    """

    def __init__(self):
        # Componentes básicos
        self.analisador = AnalisadorPergunta()
        self.analisador_avancado = AnalisadorAvancado()
        self.combinador = CombinadorRespostas()
        self.formatador = FormatadorResposta()
        self.repository = BotRepository()

        # NOVOS: Sistemas avançados
        self.buscador = BuscadorUnificado(
            wolfram_app_id=Config.WOLFRAM_APP_ID,
            google_cx=Config.GOOGLE_CX,
            google_api_key=Config.GOOGLE_API_KEY
        )

        self.sistema_ml = SistemaAprendizadoAvancado(self.repository)
        self.sistema_feedback = SistemaFeedback(self.repository)

        self.contador_conversas = 0

        logger.info("=" * 60)
        logger.info("BOT WORKER V2.0 INICIALIZADO")
        logger.info("Fontes disponíveis: " + ", ".join(self.buscador.fontes_disponiveis.keys()))
        logger.info("ML: Ensemble + Topic Modeling + Ranqueamento")
        logger.info("=" * 60)

    def process_query(self, query: str, user_id: int = None) -> dict:
        """
        Processa query com ML avançado e múltiplas fontes.
        """
        start_time = time.time()
        logs_processo = []

        try:
            logs_processo.append({
                "etapa": "inicio",
                "timestamp": time.time() - start_time,
                "detalhes": f"Query: {query}, Fontes: {len(self.buscador.fontes_disponiveis)}"
            })

            logger.info(f"[V2] Processando: {query} (user_id: {user_id})")

            # Valida entrada
            valid, message = self._validate_input(query)
            if not valid:
                logs_processo.append({
                    "etapa": "validacao",
                    "timestamp": time.time() - start_time,
                    "status": "erro",
                    "detalhes": message
                })

                if user_id:
                    self._save_conversation(
                        user_id, query, message, "validacao",
                        time.time() - start_time, "error", logs_processo
                    )

                return {
                    "status": "error",
                    "query": query,
                    "message": message,
                    "response": "",
                    "source": "validacao",
                    "processing_time": round(time.time() - start_time, 3),
                    "logs_processo": logs_processo
                }

            logs_processo.append({"etapa": "validacao", "timestamp": time.time() - start_time, "status": "ok"})

            # Obtém resposta com ML avançado
            response, source, logs_busca = self._get_bot_response_v2(query, start_time)
            logs_processo.extend(logs_busca)

            processing_time = time.time() - start_time

            # Salva conversa
            if user_id:
                self._save_conversation(
                    user_id, query, response, source,
                    processing_time, "success", logs_processo
                )

            return {
                "status": "success",
                "query": query,
                "response": response,
                "source": source,
                "user_id": user_id,
                "processing_time": round(processing_time, 3),
                "logs_processo": logs_processo,
                "version": "2.0"
            }

        except Exception as e:
            logger.error(f"Erro: {str(e)}", exc_info=True)
            processing_time = time.time() - start_time

            error_message = "Erro ao processar pergunta."

            if user_id:
                self._save_conversation(
                    user_id, query, error_message, "erro",
                    processing_time, "error", logs_processo
                )

            return {
                "status": "error",
                "query": query,
                "message": str(e),
                "response": error_message,
                "source": "erro",
                "processing_time": round(processing_time, 3),
                "logs_processo": logs_processo
            }

    def _get_bot_response_v2(self, pergunta: str, start_time: float) -> tuple:
        """
        VERSÃO 2.0 com ML avançado e busca inteligente.
        """
        logs = []

        try:
            # 1. BUSCAR RESPOSTA APRENDIDA
            logs.append({"etapa": "cache_ml", "timestamp": time.time() - start_time, "inicio": True})

            resposta_aprendida, qualidade = self.sistema_ml.buscar_resposta_aprendida(pergunta)

            if resposta_aprendida and qualidade > 0.9:
                logs.append({
                    "etapa": "cache_ml",
                    "timestamp": time.time() - start_time,
                    "hit": True,
                    "qualidade": qualidade
                })
                logger.info(f"✓ Resposta aprendida (Q={qualidade:.2f})")
                return resposta_aprendida, "aprendizado_ml", logs

            logs.append({"etapa": "cache_ml", "timestamp": time.time() - start_time, "hit": False})

            # 2. ANÁLISE COMPLETA
            logs.append({"etapa": "analise_avancada", "timestamp": time.time() - start_time})
            analise_completa = self.analisador_avancado.analisar_completo(pergunta)

            # 3. DETECTAR INTENÇÃO COM ENSEMBLE
            logs.append({"etapa": "intencao_ensemble", "timestamp": time.time() - start_time})
            intencao, confianca = self.sistema_ml.prever_intencao_ensemble(pergunta)
            logs.append({
                "etapa": "intencao_ensemble",
                "timestamp": time.time() - start_time,
                "intencao": intencao,
                "confianca": confianca
            })

            # Se não é conhecimento, responde direto
            if intencao != "conhecimento":
                resposta = choice(RESPOSTAS_INTENCAO.get(intencao, RESPOSTAS_INTENCAO["desconhecida"]))
                return resposta, intencao, logs

            # 4. DETECTAR TÓPICO
            logs.append({"etapa": "topic_modeling", "timestamp": time.time() - start_time})
            topico = self.sistema_ml.detectar_topico(pergunta)
            logs.append({"etapa": "topic_modeling", "timestamp": time.time() - start_time, "topico": topico})

            # 5. CACHE TRADICIONAL
            pergunta_norm = normalizar_texto(pergunta)
            if pergunta_norm in cache:
                logger.info("✓ Cache hit")
                logs.append({"etapa": "cache_tradicional", "timestamp": time.time() - start_time, "hit": True})
                resposta, fonte = cache[pergunta_norm]
                return resposta, fonte, logs

            logs.append({"etapa": "cache_tradicional", "timestamp": time.time() - start_time, "hit": False})

            # 6. TIPO DE PERGUNTA
            tipo_pergunta = self.analisador.detectar_tipo_pergunta(pergunta)
            logs.append({"etapa": "tipo_pergunta", "timestamp": time.time() - start_time, "tipo": tipo_pergunta})

            # 7. RANQUEAMENTO INTELIGENTE DE FONTES
            logs.append({"etapa": "ranquear_fontes", "timestamp": time.time() - start_time})

            fontes_ranqueadas = self.sistema_ml.ranquear_fontes_inteligente(
                pergunta,
                list(self.buscador.fontes_disponiveis.keys())
            )

            fontes_selecionadas = [f for f, _ in fontes_ranqueadas[:5]]  # Top 5

            logs.append({
                "etapa": "ranquear_fontes",
                "timestamp": time.time() - start_time,
                "ranking": fontes_ranqueadas[:5]
            })

            logger.info(f"Fontes selecionadas: {fontes_selecionadas}")

            # 8. TRADUÇÃO
            idioma = detectar_idioma(pergunta)
            pergunta_en = pergunta if idioma == "en" else traduzir(pergunta, origem=idioma, destino="en")

            logs.append({"etapa": "traducao", "timestamp": time.time() - start_time, "idioma": idioma})

            # 9. BUSCA INTELIGENTE E PARALELA
            logs.append({"etapa": "busca_inteligente", "timestamp": time.time() - start_time, "inicio": True})

            resultados = self.buscador.buscar_inteligente(
                pergunta_en,
                fontes_priorizadas=fontes_selecionadas,
                max_fontes=5,
                timeout_total=20
            )

            logs.append({
                "etapa": "busca_inteligente",
                "timestamp": time.time() - start_time,
                "fontes_consultadas": len(resultados),
                "fontes_com_resposta": sum(1 for r in resultados.values() if r)
            })

            # 10. TRADUZ RESULTADOS
            resultados_pt = {}
            for fonte, resultado in resultados.items():
                if resultado:
                    try:
                        resultado_pt = traduzir(resultado, origem="en", destino="pt")
                        resultados_pt[fonte] = resultado_pt
                    except:
                        resultados_pt[fonte] = resultado

            # 11. COMBINA RESPOSTAS
            logs.append({"etapa": "combinar", "timestamp": time.time() - start_time})

            resposta_combinada, fonte_principal = self.combinador.combinar_com_fonte_principal(
                resultados_pt,
                pergunta,
                tipo_pergunta
            )

            if not resposta_combinada:
                resposta = choice(RESPOSTAS_INTENCAO["desconhecida"])
                fonte = "nenhuma"
                qualidade_final = 0.0
            else:
                # 12. FORMATA
                resposta = self.formatador.formatar_final(resposta_combinada, tipo_pergunta)
                fonte = fonte_principal

                # 13. AVALIA QUALIDADE
                qualidade_final = self._avaliar_qualidade_resposta_v2(pergunta, resposta)

                logs.append({"etapa": "qualidade", "timestamp": time.time() - start_time, "score": qualidade_final})

                # 14. APRENDE SE BOA
                if qualidade_final > 0.7:
                    self.sistema_ml.aprender_padrao(pergunta, resposta, qualidade_final)

            # 15. ATUALIZA STATS AVANÇADAS
            tempo_busca = time.time() - start_time

            if fonte_principal and fonte_principal != "nenhuma":
                fontes_usadas = fonte_principal.split("+")

                for f in fontes_usadas:
                    self.sistema_ml.atualizar_stats_fonte_avancadas(
                        fonte=f,
                        tempo=tempo_busca,
                        sucesso=resposta_combinada is not None,
                        qualidade=qualidade_final,
                        tipo_pergunta=tipo_pergunta,
                        topico=topico
                    )

            # Cache
            cache[pergunta_norm] = (resposta, fonte)

            # 16. RETREINAMENTO PERIÓDICO
            self.contador_conversas += 1
            if self.contador_conversas % 50 == 0:  # A cada 50 conversas
                logger.info("⚙️ Retreinamento periódico...")
                self.sistema_ml.retreinar_tudo()

            return resposta, fonte, logs

        except Exception as e:
            logger.error(f"Erro V2: {str(e)}", exc_info=True)
            return "Erro ao processar pergunta.", "erro", logs

    def _avaliar_qualidade_resposta_v2(self, pergunta: str, resposta: str) -> float:
        """Avalia qualidade usando múltiplos critérios."""
        score = 0.0

        # Comprimento adequado
        if 50 < len(resposta) < 1000:
            score += 0.3
        elif len(resposta) >= 30:
            score += 0.1

        # Estrutura (múltiplas sentenças)
        num_sentencas = len([s for s in resposta.split('.') if len(s.strip()) > 10])
        if num_sentencas >= 2:
            score += 0.3
        elif num_sentencas >= 1:
            score += 0.1

        # Relevância (palavras da pergunta na resposta)
        palavras_pergunta = set(normalizar_texto(pergunta).split())
        palavras_resposta = set(normalizar_texto(resposta).split())

        overlap = len(palavras_pergunta & palavras_resposta) / max(len(palavras_pergunta), 1)
        score += overlap * 0.2

        # Não é mensagem de erro
        if "desculpe" not in resposta.lower() and "não sei" not in resposta.lower():
            score += 0.2

        return min(score, 1.0)

    def _validate_input(self, mensagem: str) -> tuple:
        """Valida entrada."""
        if len(mensagem) > 500:
            return False, "Mensagem muito longa"
        if not any(c.isalnum() for c in mensagem):
            return False, "Mensagem inválida"
        return True, ""

    def _save_conversation(self, user_id, pergunta, resposta, fonte, tempo, status, logs):
        """Salva conversa no banco."""
        try:
            metadata = {"logs_processo": logs}

            self.repository.create_conversation(
                user_id=user_id,
                pergunta=pergunta,
                resposta=resposta,
                fonte=fonte,
                tempo_processamento=tempo,
                status=status,
                metadata=metadata
            )
        except Exception as e:
            logger.error(f"Erro ao salvar: {str(e)}")

    # Métodos do sistema anterior (compatibilidade)
    def get_user_history(self, user_id, limit=20, offset=0):
        return self.repository.get_user_conversations(user_id, limit, offset)

    def get_conversation(self, conversation_id):
        conv = self.repository.get_conversation_by_id(conversation_id)
        return {"status": "success", "conversation": conv.to_dict()} if conv else {"status": "error"}

    def search_conversations(self, user_id, query, limit=20):
        convs = self.repository.search_conversations(user_id, query, limit)
        return {"status": "success", "results": [c.to_dict_summary() for c in convs]}

    def delete_conversation(self, conversation_id, user_id):
        deleted = self.repository.delete_conversation(conversation_id, user_id)
        return {"status": "success"} if deleted else {"status": "error"}

    def get_user_statistics(self, user_id):
        stats = self.repository.get_user_statistics(user_id)
        return {"status": "success", "statistics": stats}

    def clear_user_history(self, user_id):
        count = self.repository.delete_user_conversations(user_id)
        return {"status": "success", "deleted_count": count}

    def registrar_feedback(self, conversation_id, tipo, detalhes=None):
        return self.sistema_feedback.registrar_feedback(conversation_id, tipo, detalhes)

    def registrar_correcao(self, conversation_id, resposta_correta):
        return self.sistema_feedback.registrar_correcao(conversation_id, resposta_correta)

    def obter_taxa_satisfacao(self, user_id=None):
        return self.sistema_feedback.calcular_taxa_satisfacao(user_id)
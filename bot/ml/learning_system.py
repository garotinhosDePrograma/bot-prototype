"""
Sistema de aprendizado contínuo baseado em feedback e histórico.
"""

import logging
import json
import pickle
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.model_selection import train_test_split

logger = logging.getLogger(__name__)

class SistemaAprendizado:
    """
    Sistema que aprende com interações para melhorar respostas.
    """
    
    def __init__(self, db_repository):
        self.repository = db_repository
        self.modelo_intencao = None
        self.vectorizer_intencao = None
        self.modelo_qualidade = None
        self.vectorizer_qualidade = None
        
        # Estatísticas de fontes
        self.stats_fontes = defaultdict(lambda: {
            "total_usos": 0,
            "sucessos": 0,
            "falhas": 0,
            "tempo_medio": 0,
            "score_qualidade": 0.5
        })
        
        # Cache de padrões aprendidos
        self.padroes_pergunta_resposta = {}
        
        self.carregar_modelos()
    
    def treinar_detector_intencao(self):
        """
        Treina modelo para detectar intenção baseado em histórico.
        """
        logger.info("Treinando detector de intenção...")
        
        # Busca histórico do banco
        conversas = self.repository.get_all_conversations_for_training(limit=1000)
        
        if len(conversas) < 50:
            logger.warning("Dados insuficientes para treinar (mínimo 50)")
            return
        
        # Prepara dados de treino
        X = []  # Perguntas
        y = []  # Intenções (inferidas da fonte ou tipo)
        
        for conversa in conversas:
            pergunta = conversa.pergunta
            fonte = conversa.fonte
            
            # Infere intenção pela fonte
            if fonte in ["saudacao", "status", "despedida", "nome", "funcao"]:
                intencao = fonte
            else:
                intencao = "conhecimento"
            
            X.append(pergunta)
            y.append(intencao)
        
        # Treina modelo
        self.vectorizer_intencao = TfidfVectorizer(max_features=500)
        X_vec = self.vectorizer_intencao.fit_transform(X)
        
        self.modelo_intencao = MultinomialNB()
        self.modelo_intencao.fit(X_vec, y)
        
        logger.info(f"Modelo de intenção treinado com {len(X)} exemplos")
        
        # Salva modelo
        self.salvar_modelos()
    
    def treinar_avaliador_qualidade(self):
        """
        Treina modelo para prever qualidade da resposta.
        """
        logger.info("Treinando avaliador de qualidade...")
        
        # Busca conversas com feedback (se implementado)
        conversas = self.repository.get_conversations_with_metadata(limit=1000)
        
        X = []
        y = []
        
        for conversa in conversas:
            # Features: pergunta + resposta + fonte + tempo
            features_texto = f"{conversa.pergunta} {conversa.resposta}"
            
            # Label: qualidade inferida
            # (pode ser melhorado com feedback explícito do usuário)
            qualidade = self._inferir_qualidade(conversa)
            
            if qualidade is not None:
                X.append(features_texto)
                y.append(qualidade)
        
        if len(X) < 50:
            logger.warning("Dados insuficientes para treinar qualidade")
            return
        
        # Treina modelo
        self.vectorizer_qualidade = TfidfVectorizer(max_features=500)
        X_vec = self.vectorizer_qualidade.fit_transform(X)
        
        # Usa regressão logística para classificação binária (boa/ruim)
        from sklearn.linear_model import LogisticRegression
        self.modelo_qualidade = LogisticRegression()
        self.modelo_qualidade.fit(X_vec, y)
        
        logger.info(f"Modelo de qualidade treinado com {len(X)} exemplos")
        self.salvar_modelos()
    
    def _inferir_qualidade(self, conversa) -> int:
        """
        Infere qualidade baseado em heurísticas.
        1 = boa, 0 = ruim
        """
        # Heurísticas simples
        resposta = conversa.resposta
        tempo = conversa.tempo_processamento
        fonte = conversa.fonte
        
        # Resposta muito curta = ruim
        if len(resposta) < 30:
            return 0
        
        # Resposta de fallback = ruim
        if fonte in ["desconhecida", "erro"]:
            return 0
        
        # Tempo muito longo = ruim
        if tempo > 5.0:
            return 0
        
        # Resposta com múltiplas sentenças = provavelmente boa
        if len(resposta.split('.')) >= 2:
            return 1
        
        return None  # Incerto
    
    def prever_intencao(self, pergunta: str) -> str:
        """
        Prevê intenção usando modelo treinado.
        """
        if self.modelo_intencao is None:
            return "conhecimento"
        
        try:
            X = self.vectorizer_intencao.transform([pergunta])
            intencao = self.modelo_intencao.predict(X)[0]
            proba = self.modelo_intencao.predict_proba(X)[0]
            
            logger.info(f"Intenção prevista: {intencao} (confiança: {max(proba):.2f})")
            return intencao
        except:
            return "conhecimento"
    
    def avaliar_qualidade_resposta(self, pergunta: str, resposta: str) -> float:
        """
        Avalia qualidade da resposta (0.0 a 1.0).
        """
        if self.modelo_qualidade is None:
            return 0.5  # Neutro
        
        try:
            features = f"{pergunta} {resposta}"
            X = self.vectorizer_qualidade.transform([features])
            qualidade = self.modelo_qualidade.predict_proba(X)[0][1]  # Probabilidade de ser boa
            
            logger.info(f"Qualidade avaliada: {qualidade:.2f}")
            return qualidade
        except:
            return 0.5
    
    def atualizar_stats_fonte(self, fonte: str, tempo: float, sucesso: bool, qualidade: float = None):
        """
        Atualiza estatísticas de desempenho de cada fonte.
        """
        stats = self.stats_fontes[fonte]
        
        stats["total_usos"] += 1
        
        if sucesso:
            stats["sucessos"] += 1
        else:
            stats["falhas"] += 1
        
        # Atualiza tempo médio
        n = stats["total_usos"]
        stats["tempo_medio"] = (stats["tempo_medio"] * (n-1) + tempo) / n
        
        # Atualiza score de qualidade
        if qualidade is not None:
            stats["score_qualidade"] = (stats["score_qualidade"] * (n-1) + qualidade) / n
    
    def recomendar_fonte_principal(self, tipo_pergunta: str) -> str:
        """
        Recomenda melhor fonte baseado em aprendizado.
        """
        # Calcula score para cada fonte
        scores = {}
        
        for fonte, stats in self.stats_fontes.items():
            if stats["total_usos"] == 0:
                scores[fonte] = 0.5
                continue
            
            # Score baseado em taxa de sucesso e qualidade
            taxa_sucesso = stats["sucessos"] / stats["total_usos"]
            qualidade = stats["score_qualidade"]
            velocidade = 1.0 / (1.0 + stats["tempo_medio"])  # Normalizado
            
            # Score ponderado
            score = (taxa_sucesso * 0.4) + (qualidade * 0.4) + (velocidade * 0.2)
            scores[fonte] = score
        
        # Retorna melhor fonte
        if scores:
            melhor_fonte = max(scores.items(), key=lambda x: x[1])[0]
            logger.info(f"Fonte recomendada: {melhor_fonte} (scores: {scores})")
            return melhor_fonte
        
        return "google"  # Default
    
    def aprender_padrao(self, pergunta: str, resposta: str, qualidade: float):
        """
        Aprende padrões de pergunta-resposta bem sucedidas.
        """
        if qualidade < 0.7:  # Só aprende de boas respostas
            return
        
        # Normaliza pergunta para detectar padrões
        from bot.utils.text_utils import normalizar_texto
        pergunta_norm = normalizar_texto(pergunta)
        
        # Armazena padrão
        if pergunta_norm not in self.padroes_pergunta_resposta:
            self.padroes_pergunta_resposta[pergunta_norm] = {
                "resposta": resposta,
                "qualidade": qualidade,
                "usos": 1,
                "ultima_atualizacao": datetime.now()
            }
        else:
            # Atualiza padrão existente se nova resposta for melhor
            padrao = self.padroes_pergunta_resposta[pergunta_norm]
            if qualidade > padrao["qualidade"]:
                padrao["resposta"] = resposta
                padrao["qualidade"] = qualidade
            padrao["usos"] += 1
            padrao["ultima_atualizacao"] = datetime.now()
    
    def buscar_resposta_aprendida(self, pergunta: str) -> Tuple[str, float]:
        """
        Busca se já tem resposta aprendida para pergunta similar.
        """
        from bot.utils.text_utils import normalizar_texto
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        
        pergunta_norm = normalizar_texto(pergunta)
        
        # Busca exata
        if pergunta_norm in self.padroes_pergunta_resposta:
            padrao = self.padroes_pergunta_resposta[pergunta_norm]
            logger.info(f"Resposta aprendida encontrada (exata): qualidade={padrao['qualidade']:.2f}")
            return padrao["resposta"], padrao["qualidade"]
        
        # Busca por similaridade
        if not self.padroes_pergunta_resposta:
            return None, 0.0
        
        try:
            perguntas_conhecidas = list(self.padroes_pergunta_resposta.keys())
            todas_perguntas = perguntas_conhecidas + [pergunta_norm]
            
            vectorizer = TfidfVectorizer()
            tfidf_matrix = vectorizer.fit_transform(todas_perguntas)
            
            # Similaridade com última pergunta (nova)
            similaridades = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1])[0]
            
            # Pega mais similar
            idx_max = similaridades.argmax()
            max_sim = similaridades[idx_max]
            
            if max_sim > 0.85:  # Muito similar
                pergunta_similar = perguntas_conhecidas[idx_max]
                padrao = self.padroes_pergunta_resposta[pergunta_similar]
                logger.info(f"Resposta aprendida encontrada (similar {max_sim:.2f}): qualidade={padrao['qualidade']:.2f}")
                return padrao["resposta"], padrao["qualidade"]
        
        except Exception as e:
            logger.error(f"Erro ao buscar resposta aprendida: {str(e)}")
        
        return None, 0.0
    
    def salvar_modelos(self):
        """Salva modelos treinados em disco."""
        try:
            modelos = {
                "modelo_intencao": self.modelo_intencao,
                "vectorizer_intencao": self.vectorizer_intencao,
                "modelo_qualidade": self.modelo_qualidade,
                "vectorizer_qualidade": self.vectorizer_qualidade,
                "stats_fontes": dict(self.stats_fontes),
                "padroes": self.padroes_pergunta_resposta
            }
            
            with open("bot/ml/modelos_treinados.pkl", "wb") as f:
                pickle.dump(modelos, f)
            
            logger.info("Modelos salvos com sucesso")
        except Exception as e:
            logger.error(f"Erro ao salvar modelos: {str(e)}")
    
    def carregar_modelos(self):
        """Carrega modelos treinados."""
        try:
            with open("bot/ml/modelos_treinados.pkl", "rb") as f:
                modelos = pickle.load(f)
            
            self.modelo_intencao = modelos.get("modelo_intencao")
            self.vectorizer_intencao = modelos.get("vectorizer_intencao")
            self.modelo_qualidade = modelos.get("modelo_qualidade")
            self.vectorizer_qualidade = modelos.get("vectorizer_qualidade")
            self.stats_fontes = defaultdict(lambda: {
                "total_usos": 0, "sucessos": 0, "falhas": 0,
                "tempo_medio": 0, "score_qualidade": 0.5
            }, modelos.get("stats_fontes", {}))
            self.padroes_pergunta_resposta = modelos.get("padroes", {})
            
            logger.info("Modelos carregados com sucesso")
        except FileNotFoundError:
            logger.info("Nenhum modelo treinado encontrado - iniciando do zero")
        except Exception as e:
            logger.error(f"Erro ao carregar modelos: {str(e)}")
    
    def retreinar_periodicamente(self):
        """
        Retreina modelos com novos dados.
        Deve ser chamado periodicamente (ex: a cada 100 conversas).
        """
        logger.info("Iniciando retreinamento periódico...")
        self.treinar_detector_intencao()
        self.treinar_avaliador_qualidade()
        logger.info("Retreinamento concluído")

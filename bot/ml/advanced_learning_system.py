"""
Sistema de Aprendizado Avançado com Deep Learning e Ensemble Methods
Versão 2.0 - Com múltiplas fontes e aprendizado profundo
"""

import logging
import json
import pickle
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from pathlib import Path

# Machine Learning - Clássico
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, f1_score, classification_report
from sklearn.preprocessing import LabelEncoder

# Deep Learning (opcional - instalar: pip install tensorflow keras)
try:
    from tensorflow import keras
    from keras.models import Sequential, load_model
    from keras.layers import Dense, Embedding, LSTM, Dropout, Bidirectional
    from keras.preprocessing.text import Tokenizer
    from keras.preprocessing.sequence import pad_sequences
    DEEP_LEARNING_AVAILABLE = True
except ImportError:
    DEEP_LEARNING_AVAILABLE = False
    logging.warning("TensorFlow/Keras não disponível - usando apenas modelos clássicos")

# NLP Avançado
import spacy
from sklearn.decomposition import LatentDirichletAllocation

logger = logging.getLogger(__name__)


class SistemaAprendizadoAvancado:
    """
    Sistema de aprendizado de máquina avançado com múltiplos modelos.
    """

    def __init__(self, db_repository):
        self.repository = db_repository

        # Modelos de classificação (ensemble)
        self.modelo_intencao_nb = None  # Naive Bayes
        self.modelo_intencao_rf = None  # Random Forest
        self.modelo_intencao_gb = None  # Gradient Boosting
        self.modelo_intencao_lstm = None  # LSTM (Deep Learning)
        self.vectorizer_intencao = None
        self.tokenizer_intencao = None
        self.label_encoder_intencao = None

        # Modelos de qualidade
        self.modelo_qualidade_lr = None  # Logistic Regression
        self.modelo_qualidade_rf = None  # Random Forest
        self.vectorizer_qualidade = None

        # Modelo de ranqueamento de fontes
        self.modelo_ranqueamento_fontes = None
        self.vectorizer_fontes = None

        # Modelo de recomendação de fontes (novo)
        self.modelo_recomendacao = None

        # Topic modeling para clustering de perguntas
        self.lda_model = None
        self.lda_vectorizer = None

        # NLP
        try:
            self.nlp = spacy.load("pt_core_news_sm")
        except:
            self.nlp = None
            logger.warning("spaCy não disponível")

        # Estatísticas detalhadas de fontes
        self.stats_fontes = defaultdict(lambda: {
            "total_usos": 0,
            "sucessos": 0,
            "falhas": 0,
            "tempo_medio": 0,
            "score_qualidade": 0.5,
            "taxa_sucesso": 0.5,
            "taxa_feedback_positivo": 0.5,
            "tipos_pergunta_boas": Counter(),  # Em quais tipos de pergunta funciona bem
            "topicos_bons": Counter(),  # Em quais tópicos funciona bem
            "historico_scores": []  # Últimos 100 scores
        })

        # Cache de padrões aprendidos com embeddings
        self.padroes_pergunta_resposta = {}
        self.embeddings_perguntas = {}  # Vetores densos para matching semântico

        # Configurações
        self.caminho_modelos = Path("bot/ml/modelos_avancados")
        self.caminho_modelos.mkdir(parents=True, exist_ok=True)

        # Carrega modelos existentes
        self.carregar_modelos()

    # ============================================
    # TREINAMENTO - ENSEMBLE DE CLASSIFICADORES
    # ============================================

    def treinar_detector_intencao_ensemble(self, min_exemplos=50):
        """
        Treina ensemble de modelos para detectar intenção.
        Combina Naive Bayes, Random Forest, Gradient Boosting e LSTM.
        """
        logger.info("Treinando ensemble de detectores de intenção...")

        # Busca dados de treinamento
        conversas = self.repository.get_all_conversations_for_training(limit=5000)

        if len(conversas) < min_exemplos:
            logger.warning(f"Dados insuficientes: {len(conversas)}/{min_exemplos}")
            return False

        # Prepara dados
        X = []
        y = []

        for conversa in conversas:
            pergunta = conversa.pergunta

            # Infere intenção
            if conversa.fonte in ["saudacao", "status", "despedida", "nome", "funcao"]:
                intencao = conversa.fonte
            elif conversa.metadata and "tipo_pergunta" in conversa.metadata:
                intencao = conversa.metadata["tipo_pergunta"]
            else:
                intencao = "conhecimento"

            X.append(pergunta)
            y.append(intencao)

        # Split treino/teste
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        # Encoder de labels
        self.label_encoder_intencao = LabelEncoder()
        y_train_encoded = self.label_encoder_intencao.fit_transform(y_train)
        y_test_encoded = self.label_encoder_intencao.transform(y_test)

        # Vetorização TF-IDF
        self.vectorizer_intencao = TfidfVectorizer(
            max_features=1000,
            ngram_range=(1, 2),
            min_df=2
        )
        X_train_tfidf = self.vectorizer_intencao.fit_transform(X_train)
        X_test_tfidf = self.vectorizer_intencao.transform(X_test)

        # 1. Naive Bayes
        logger.info("Treinando Naive Bayes...")
        self.modelo_intencao_nb = MultinomialNB(alpha=0.1)
        self.modelo_intencao_nb.fit(X_train_tfidf, y_train_encoded)
        acc_nb = accuracy_score(y_test_encoded, self.modelo_intencao_nb.predict(X_test_tfidf))
        logger.info(f"Naive Bayes - Acurácia: {acc_nb:.3f}")

        # 2. Random Forest
        logger.info("Treinando Random Forest...")
        self.modelo_intencao_rf = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        self.modelo_intencao_rf.fit(X_train_tfidf, y_train_encoded)
        acc_rf = accuracy_score(y_test_encoded, self.modelo_intencao_rf.predict(X_test_tfidf))
        logger.info(f"Random Forest - Acurácia: {acc_rf:.3f}")

        # 3. Gradient Boosting
        logger.info("Treinando Gradient Boosting...")
        self.modelo_intencao_gb = GradientBoostingClassifier(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=5,
            random_state=42
        )
        self.modelo_intencao_gb.fit(X_train_tfidf, y_train_encoded)
        acc_gb = accuracy_score(y_test_encoded, self.modelo_intencao_gb.predict(X_test_tfidf))
        logger.info(f"Gradient Boosting - Acurácia: {acc_gb:.3f}")

        # 4. LSTM (Deep Learning)
        if DEEP_LEARNING_AVAILABLE and len(conversas) >= 200:
            logger.info("Treinando LSTM...")
            acc_lstm = self._treinar_lstm_intencao(X_train, y_train_encoded, X_test, y_test_encoded)
            logger.info(f"LSTM - Acurácia: {acc_lstm:.3f}")

        logger.info(f"Ensemble treinado com {len(X_train)} exemplos")
        self.salvar_modelos()
        return True

    def _treinar_lstm_intencao(self, X_train, y_train, X_test, y_test):
        """Treina modelo LSTM para classificação de intenção."""
        # Tokenização
        self.tokenizer_intencao = Tokenizer(num_words=5000, oov_token="<OOV>")
        self.tokenizer_intencao.fit_on_texts(X_train)

        # Sequências
        X_train_seq = self.tokenizer_intencao.texts_to_sequences(X_train)
        X_test_seq = self.tokenizer_intencao.texts_to_sequences(X_test)

        # Padding
        max_length = 50
        X_train_pad = pad_sequences(X_train_seq, maxlen=max_length, padding='post')
        X_test_pad = pad_sequences(X_test_seq, maxlen=max_length, padding='post')

        # Número de classes
        num_classes = len(np.unique(y_train))

        # Converte labels para one-hot
        y_train_cat = keras.utils.to_categorical(y_train, num_classes)
        y_test_cat = keras.utils.to_categorical(y_test, num_classes)

        # Modelo
        self.modelo_intencao_lstm = Sequential([
            Embedding(5000, 128, input_length=max_length),
            Bidirectional(LSTM(64, return_sequences=True)),
            Dropout(0.5),
            Bidirectional(LSTM(32)),
            Dropout(0.5),
            Dense(64, activation='relu'),
            Dropout(0.5),
            Dense(num_classes, activation='softmax')
        ])

        self.modelo_intencao_lstm.compile(
            optimizer='adam',
            loss='categorical_crossentropy',
            metrics=['accuracy']
        )

        # Treinamento
        history = self.modelo_intencao_lstm.fit(
            X_train_pad, y_train_cat,
            epochs=10,
            batch_size=32,
            validation_split=0.2,
            verbose=0
        )

        # Avaliação
        _, acc = self.modelo_intencao_lstm.evaluate(X_test_pad, y_test_cat, verbose=0)

        return acc

    def prever_intencao_ensemble(self, pergunta: str) -> Tuple[str, float]:
        """
        Prevê intenção usando ensemble voting.
        Retorna (intenção, confiança).
        """
        if not self.modelo_intencao_nb:
            return "conhecimento", 0.5

        try:
            # TF-IDF
            X = self.vectorizer_intencao.transform([pergunta])

            # Previsões de cada modelo
            predicoes = []
            pesos = []

            # Naive Bayes
            pred_nb = self.modelo_intencao_nb.predict(X)[0]
            proba_nb = self.modelo_intencao_nb.predict_proba(X)[0]
            predicoes.append(pred_nb)
            pesos.append(max(proba_nb))

            # Random Forest
            if self.modelo_intencao_rf:
                pred_rf = self.modelo_intencao_rf.predict(X)[0]
                proba_rf = self.modelo_intencao_rf.predict_proba(X)[0]
                predicoes.append(pred_rf)
                pesos.append(max(proba_rf))

            # Gradient Boosting
            if self.modelo_intencao_gb:
                pred_gb = self.modelo_intencao_gb.predict(X)[0]
                proba_gb = self.modelo_intencao_gb.predict_proba(X)[0]
                predicoes.append(pred_gb)
                pesos.append(max(proba_gb))

            # LSTM
            if self.modelo_intencao_lstm and self.tokenizer_intencao:
                seq = self.tokenizer_intencao.texts_to_sequences([pergunta])
                pad = pad_sequences(seq, maxlen=50, padding='post')
                proba_lstm = self.modelo_intencao_lstm.predict(pad, verbose=0)[0]
                pred_lstm = np.argmax(proba_lstm)
                predicoes.append(pred_lstm)
                pesos.append(max(proba_lstm))

            # Voting ponderado
            if len(predicoes) > 0:
                # Converte para votos
                votos = Counter()
                for pred, peso in zip(predicoes, pesos):
                    votos[pred] += peso

                # Classe vencedora
                classe_pred = votos.most_common(1)[0][0]
                confianca = votos[classe_pred] / sum(pesos)

                # Decodifica label
                intencao = self.label_encoder_intencao.inverse_transform([classe_pred])[0]

                logger.info(f"Ensemble - Intenção: {intencao} (confiança: {confianca:.2f})")
                return intencao, confianca

        except Exception as e:
            logger.error(f"Erro ao prever intenção: {str(e)}")

        return "conhecimento", 0.5

    # ============================================
    # RANQUEAMENTO INTELIGENTE DE FONTES
    # ============================================

    def treinar_ranqueador_fontes(self):
        """
        Treina modelo para ranquear fontes baseado em:
        - Tipo de pergunta
        - Entidades presentes
        - Histórico de sucesso
        - Tópico da pergunta
        """
        logger.info("Treinando ranqueador de fontes...")

        conversas = self.repository.get_all_conversations_for_training(limit=3000)

        if len(conversas) < 100:
            logger.warning("Dados insuficientes para treinar ranqueador")
            return False

        # Prepara dados
        X = []
        y = []

        for conversa in conversas:
            if not conversa.fonte or conversa.fonte == "erro":
                continue

            # Features da pergunta
            features_texto = self._extrair_features_pergunta(conversa.pergunta)

            # Label: fonte que deu melhor resultado
            fonte_principal = conversa.fonte.split("+")[0]  # Pega primeira fonte

            X.append(features_texto)
            y.append(fonte_principal)

        if len(X) < 50:
            return False

        # Vetorização
        self.vectorizer_fontes = TfidfVectorizer(max_features=500)
        X_vec = self.vectorizer_fontes.fit_transform(X)

        # Treina Random Forest
        self.modelo_ranqueamento_fontes = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        self.modelo_ranqueamento_fontes.fit(X_vec, y)

        logger.info(f"Ranqueador treinado com {len(X)} exemplos")
        self.salvar_modelos()
        return True

    def _extrair_features_pergunta(self, pergunta: str) -> str:
        """Extrai features textuais da pergunta."""
        features = [pergunta.lower()]

        if self.nlp:
            doc = self.nlp(pergunta)

            # Adiciona entidades
            for ent in doc.ents:
                features.append(f"ENT_{ent.label_}")

            # Adiciona POS tags
            for token in doc:
                if token.pos_ in ["NOUN", "VERB", "ADJ"]:
                    features.append(f"POS_{token.pos_}")

        return " ".join(features)

    def ranquear_fontes_inteligente(self, pergunta: str, fontes_disponiveis: List[str]) -> List[Tuple[str, float]]:
        """
        Ranqueia fontes por probabilidade de sucesso.
        Retorna lista de (fonte, score) ordenada.
        """
        if not self.modelo_ranqueamento_fontes:
            # Fallback: ranqueamento baseado em estatísticas
            return self._ranquear_fontes_estatisticas(fontes_disponiveis)

        try:
            features = self._extrair_features_pergunta(pergunta)
            X = self.vectorizer_fontes.transform([features])

            # Probabilidades para cada fonte
            classes = self.modelo_ranqueamento_fontes.classes_
            probas = self.modelo_ranqueamento_fontes.predict_proba(X)[0]

            # Combina com estatísticas históricas
            ranking = []
            for fonte in fontes_disponiveis:
                if fonte in classes:
                    idx = np.where(classes == fonte)[0][0]
                    score_ml = probas[idx]
                else:
                    score_ml = 0.1

                # Score histórico
                stats = self.stats_fontes[fonte]
                score_hist = stats.get("taxa_sucesso", 0.5)

                # Score combinado (70% ML, 30% histórico)
                score_final = (score_ml * 0.7) + (score_hist * 0.3)

                ranking.append((fonte, score_final))

            # Ordena por score
            ranking.sort(key=lambda x: x[1], reverse=True)

            logger.info(f"Ranking de fontes: {ranking[:3]}")
            return ranking

        except Exception as e:
            logger.error(f"Erro ao ranquear fontes: {str(e)}")
            return self._ranquear_fontes_estatisticas(fontes_disponiveis)

    def _ranquear_fontes_estatisticas(self, fontes: List[str]) -> List[Tuple[str, float]]:
        """Ranqueamento baseado apenas em estatísticas."""
        ranking = []
        for fonte in fontes:
            stats = self.stats_fontes[fonte]
            score = stats.get("taxa_sucesso", 0.5) * stats.get("score_qualidade", 0.5)
            ranking.append((fonte, score))

        ranking.sort(key=lambda x: x[1], reverse=True)
        return ranking

    # ============================================
    # TOPIC MODELING - LDA
    # ============================================

    def treinar_topic_model(self, n_topics=20):
        """
        Treina modelo LDA para descobrir tópicos nas perguntas.
        Útil para agrupar perguntas similares e recomendar fontes.
        """
        logger.info(f"Treinando LDA com {n_topics} tópicos...")

        conversas = self.repository.get_all_conversations_for_training(limit=5000)

        if len(conversas) < 100:
            return False

        perguntas = [c.pergunta for c in conversas]

        # Vetorização com Count Vectorizer (LDA usa frequências)
        self.lda_vectorizer = CountVectorizer(
            max_features=1000,
            min_df=2,
            max_df=0.8,
            stop_words=['o', 'a', 'de', 'que', 'e', 'do', 'da', 'em', 'um', 'para', 'é', 'com', 'não', 'uma', 'os', 'no', 'se', 'na', 'por', 'mais', 'as', 'dos', 'como', 'mas', 'ao', 'ele', 'das', 'à', 'seu', 'sua']
        )
        X = self.lda_vectorizer.fit_transform(perguntas)

        # Treina LDA
        self.lda_model = LatentDirichletAllocation(
            n_components=n_topics,
            max_iter=20,
            learning_method='online',
            random_state=42,
            n_jobs=-1
        )
        self.lda_model.fit(X)

        # Mostra tópicos
        self._mostrar_topicos()

        logger.info(f"LDA treinado com {len(perguntas)} documentos")
        self.salvar_modelos()
        return True

    def _mostrar_topicos(self, n_palavras=10):
        """Mostra palavras principais de cada tópico."""
        if not self.lda_model or not self.lda_vectorizer:
            return

        feature_names = self.lda_vectorizer.get_feature_names_out()

        logger.info("Tópicos descobertos:")
        for topic_idx, topic in enumerate(self.lda_model.components_):
            top_palavras = [feature_names[i] for i in topic.argsort()[-n_palavras:]]
            logger.info(f"Tópico {topic_idx}: {', '.join(top_palavras)}")

    def detectar_topico(self, pergunta: str) -> int:
        """Detecta tópico principal da pergunta."""
        if not self.lda_model:
            return -1

        try:
            X = self.lda_vectorizer.transform([pergunta])
            distribuicao = self.lda_model.transform(X)[0]
            topico = distribuicao.argmax()
            return topico
        except:
            return -1

    # ============================================
    # ATUALIZAÇÃO DE ESTATÍSTICAS AVANÇADAS
    # ============================================

    def atualizar_stats_fonte_avancadas(
        self, 
        fonte: str, 
        tempo: float, 
        sucesso: bool, 
        qualidade: float = None,
        tipo_pergunta: str = None,
        topico: int = None,
        teve_feedback: bool = False,
        feedback_positivo: bool = False
    ):
        """
        Atualiza estatísticas detalhadas da fonte.
        """
        stats = self.stats_fontes[fonte]

        stats["total_usos"] += 1
        n = stats["total_usos"]

        # Sucessos/Falhas
        if sucesso:
            stats["sucessos"] += 1
        else:
            stats["falhas"] += 1

        stats["taxa_sucesso"] = stats["sucessos"] / n

        # Tempo médio
        stats["tempo_medio"] = (stats["tempo_medio"] * (n-1) + tempo) / n

        # Qualidade
        if qualidade is not None:
            stats["historico_scores"].append(qualidade)
            if len(stats["historico_scores"]) > 100:
                stats["historico_scores"].pop(0)

            stats["score_qualidade"] = (stats["score_qualidade"] * (n-1) + qualidade) / n

        # Tipo de pergunta
        if tipo_pergunta and qualidade and qualidade > 0.7:
            stats["tipos_pergunta_boas"][tipo_pergunta] += 1

        # Tópico
        if topico is not None and topico >= 0 and qualidade and qualidade > 0.7:
            stats["topicos_bons"][topico] += 1

        # Feedback
        if teve_feedback:
            if feedback_positivo:
                stats["taxa_feedback_positivo"] = (
                    stats.get("taxa_feedback_positivo", 0.5) * 0.9 + 0.1
                )
            else:
                stats["taxa_feedback_positivo"] = (
                    stats.get("taxa_feedback_positivo", 0.5) * 0.9
                )

    # ============================================
    # PERSISTÊNCIA
    # ============================================

    def salvar_modelos(self):
        """Salva todos os modelos treinados."""
        try:
            logger.info("Salvando modelos...")

            modelos = {
                "modelo_intencao_nb": self.modelo_intencao_nb,
                "modelo_intencao_rf": self.modelo_intencao_rf,
                "modelo_intencao_gb": self.modelo_intencao_gb,
                "vectorizer_intencao": self.vectorizer_intencao,
                "label_encoder_intencao": self.label_encoder_intencao,
                "tokenizer_intencao": self.tokenizer_intencao,
                "modelo_qualidade_lr": self.modelo_qualidade_lr,
                "modelo_qualidade_rf": self.modelo_qualidade_rf,
                "vectorizer_qualidade": self.vectorizer_qualidade,
                "modelo_ranqueamento_fontes": self.modelo_ranqueamento_fontes,
                "vectorizer_fontes": self.vectorizer_fontes,
                "lda_model": self.lda_model,
                "lda_vectorizer": self.lda_vectorizer,
                "stats_fontes": dict(self.stats_fontes),
                "padroes": self.padroes_pergunta_resposta,
                "embeddings": self.embeddings_perguntas
            }

            # Salva modelos clássicos
            with open(self.caminho_modelos / "modelos_ensemble.pkl", "wb") as f:
                pickle.dump(modelos, f)

            # Salva modelo LSTM separadamente
            if self.modelo_intencao_lstm:
                self.modelo_intencao_lstm.save(self.caminho_modelos / "lstm_intencao.h5")

            logger.info("✓ Modelos salvos")

        except Exception as e:
            logger.error(f"Erro ao salvar modelos: {str(e)}")

    def carregar_modelos(self):
        """Carrega modelos salvos."""
        try:
            caminho_pkl = self.caminho_modelos / "modelos_ensemble.pkl"

            if not caminho_pkl.exists():
                logger.info("Nenhum modelo treinado encontrado")
                return

            with open(caminho_pkl, "rb") as f:
                modelos = pickle.load(f)

            self.modelo_intencao_nb = modelos.get("modelo_intencao_nb")
            self.modelo_intencao_rf = modelos.get("modelo_intencao_rf")
            self.modelo_intencao_gb = modelos.get("modelo_intencao_gb")
            self.vectorizer_intencao = modelos.get("vectorizer_intencao")
            self.label_encoder_intencao = modelos.get("label_encoder_intencao")
            self.tokenizer_intencao = modelos.get("tokenizer_intencao")
            self.modelo_qualidade_lr = modelos.get("modelo_qualidade_lr")
            self.modelo_qualidade_rf = modelos.get("modelo_qualidade_rf")
            self.vectorizer_qualidade = modelos.get("vectorizer_qualidade")
            self.modelo_ranqueamento_fontes = modelos.get("modelo_ranqueamento_fontes")
            self.vectorizer_fontes = modelos.get("vectorizer_fontes")
            self.lda_model = modelos.get("lda_model")
            self.lda_vectorizer = modelos.get("lda_vectorizer")
            self.stats_fontes = defaultdict(
                lambda: {
                    "total_usos": 0, "sucessos": 0, "falhas": 0,
                    "tempo_medio": 0, "score_qualidade": 0.5,
                    "taxa_sucesso": 0.5, "taxa_feedback_positivo": 0.5,
                    "tipos_pergunta_boas": Counter(),
                    "topicos_bons": Counter(),
                    "historico_scores": []
                },
                modelos.get("stats_fontes", {})
            )
            self.padroes_pergunta_resposta = modelos.get("padroes", {})
            self.embeddings_perguntas = modelos.get("embeddings", {})

            # Carrega LSTM
            caminho_lstm = self.caminho_modelos / "lstm_intencao.h5"
            if DEEP_LEARNING_AVAILABLE and caminho_lstm.exists():
                self.modelo_intencao_lstm = load_model(caminho_lstm)

            logger.info("✓ Modelos carregados")

        except Exception as e:
            logger.error(f"Erro ao carregar modelos: {str(e)}")

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

    def retreinar_tudo(self):
        """Retreina todos os modelos."""
        logger.info("=" * 60)
        logger.info("RETREINAMENTO COMPLETO")
        logger.info("=" * 60)
        self.treinar_detector_intencao_ensemble()
        self.treinar_ranqueador_fontes()
        self.treinar_topic_model()

        logger.info("=" * 60)
        logger.info("RETREINAMENTO CONCLUÍDO")
        logger.info("=" * 60)
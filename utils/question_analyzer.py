"""
Análise e processamento de perguntas usando NLP.
"""

import logging
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

# Carrega modelo spaCy
nlp = spacy.load("pt_core_news_sm")

# Intenções predefinidas
INTENCOES = {
    "saudacao": ["oi", "olá", "e ai", "bom dia", "boa noite", "boa tarde", "eae", "hello"],
    "status": ["tudo bem", "como você está", "como está"],
    "nome": ["qual seu nome", "como se chama", "quem é você"],
    "funcao": ["o que você faz", "para que serve", "qual sua função"],
    "despedida": ["tchau", "adeus", "até logo", "sair"]
}


class AnalisadorPergunta:
    """Classe para analisar e processar perguntas."""

    def __init__(self):
        self.nlp = nlp

    def detectar_intencao(self, mensagem: str) -> str:
        """Detecta a intenção da mensagem."""
        mensagem_limpa = mensagem.lower()
        vectorizer = TfidfVectorizer()
        max_sim = 0
        intencao = "conhecimento"

        for key, exemplos in INTENCOES.items():
            try:
                textos = exemplos + [mensagem_limpa]
                tfidf_matrix = vectorizer.fit_transform(textos)
                sim = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1]).max()
                if sim > max_sim and sim > 0.5:
                    max_sim = sim
                    intencao = key
            except:
                continue

        logger.info(f"Intenção detectada: {intencao} (similaridade: {max_sim:.2f})")
        return intencao

    def detectar_tipo_pergunta(self, pergunta: str) -> str:
        """
        Detecta o tipo de pergunta (qual, quem, como, por que, etc).
        Retorna o tipo detectado.
        """
        doc = self.nlp(pergunta.lower())

        for token in doc:
            if token.lemma_ in ["qual", "quais"]:
                return "qual"
            elif token.lemma_ in ["quem"]:
                return "quem"
            elif token.lemma_ in ["onde"]:
                return "onde"
            elif token.lemma_ in ["quando"]:
                return "quando"
            elif token.lemma_ in ["como", "de que forma", "de que maneira"]:
                return "como"
            elif token.lemma_ in ["por", "por que", "porque"]:
                return "porque"
            elif token.lemma_ in ["quanto", "quantos", "quantas"]:
                return "quanto"

        return "geral"

    def extrair_palavras_chave(self, texto: str, max_palavras: int = 10) -> list:
        """
        Extrai palavras-chave relevantes do texto.
        """
        doc = self.nlp(texto.lower())
        palavras_chave = []

        # Palavras interrogativas são sempre importantes
        interrogativas = ["por", "como", "o que", "qual", "quem", "onde", "quando", "quanto"]

        for token in doc:
            if token.lemma_ in interrogativas:
                palavras_chave.append(token.text)
            elif token.pos_ in ["NOUN", "PROPN", "VERB", "ADJ"] and not token.is_stop:
                palavras_chave.append(token.text)

        # Se não encontrou palavras-chave, retorna o texto original limitado
        if not palavras_chave:
            return texto.split()[:max_palavras]

        return palavras_chave[:max_palavras]

    def criar_query_busca(self, pergunta: str) -> str:
        """
        Cria uma query otimizada para busca em APIs externas.
        Mantém o contexto importante sem perder o sentido.
        """
        # Detecta tipo de pergunta
        tipo = self.detectar_tipo_pergunta(pergunta)

        # Para perguntas curtas (menos de 6 palavras), usa a pergunta inteira
        palavras_pergunta = pergunta.split()
        if len(palavras_pergunta) <= 6:
            logger.info(f"Query (pergunta curta): {pergunta}")
            return pergunta

        # Para perguntas explicativas, mantém muito mais contexto
        if tipo in ["como", "porque"]:
            # Remove apenas stopwords muito comuns, mantém estrutura
            doc = self.nlp(pergunta.lower())
            palavras_importantes = []

            for token in doc:
                # Mantém interrogativas, substantivos, verbos, adjetivos e nomes próprios
                if (token.pos_ in ["NOUN", "PROPN", "VERB", "ADJ", "ADV"] or 
                    token.lemma_ in ["como", "por", "que", "qual", "quem", "onde", "quando", "quanto"]):
                    palavras_importantes.append(token.text)

            # Se perdeu muito, usa palavras originais
            if len(palavras_importantes) < len(palavras_pergunta) * 0.6:
                query = pergunta
            else:
                query = " ".join(palavras_importantes)

            logger.info(f"Query (explicativa): {pergunta} -> {query}")
            return query

        # Para perguntas factuais, extrai termos principais
        else:
            palavras_chave = self.extrair_palavras_chave(pergunta, max_palavras=8)
            query = " ".join(palavras_chave)

            logger.info(f"Query (factual): {pergunta} -> {query}")
            return query

    def e_pergunta_factual(self, pergunta: str) -> bool:
        """Verifica se é uma pergunta factual (que, quem, qual, quando, onde)."""
        tipo = self.detectar_tipo_pergunta(pergunta)
        return tipo in ["qual", "quem", "onde", "quando", "quanto"]

    def e_pergunta_explicativa(self, pergunta: str) -> bool:
        """Verifica se é uma pergunta explicativa (como, por que)."""
        tipo = self.detectar_tipo_pergunta(pergunta)
        return tipo in ["como", "porque"]
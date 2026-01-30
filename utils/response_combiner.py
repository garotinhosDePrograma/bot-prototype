"""
Módulo para combinar respostas de múltiplas fontes de forma inteligente.
"""

import logging
from typing import Dict, List, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from utils.text_utils import extrair_sentencas, juntar_sentencas, limpar_texto

logger = logging.getLogger(__name__)


class CombinadorRespostas:
    """
    Classe para combinar múltiplas respostas de diferentes fontes
    em uma resposta coesa, sem usar modelo de IA.
    """

    def __init__(self):
        pass

    def calcular_relevancia(self, resposta: str, pergunta: str) -> float:
        """
        Calcula quão relevante uma resposta é para a pergunta.
        Retorna score de 0 a 1.
        """
        if not resposta or not pergunta:
            return 0.0

        try:
            vectorizer = TfidfVectorizer()
            textos = [pergunta.lower(), resposta.lower()]
            tfidf_matrix = vectorizer.fit_transform(textos)
            similaridade = cosine_similarity(tfidf_matrix[0], tfidf_matrix[1])[0][0]
            return similaridade
        except:
            return 0.0

    def ranquear_respostas(self, respostas: Dict[str, str], pergunta: str) -> List[tuple]:
        """
        Ranqueia respostas por relevância.
        Retorna lista de (fonte, resposta, score) ordenada.
        """
        ranking = []

        for fonte, resposta in respostas.items():
            if resposta and len(resposta.strip()) >= 10:
                score = self.calcular_relevancia(resposta, pergunta)
                ranking.append((fonte, resposta, score))

        # Ordena por score (maior primeiro)
        ranking.sort(key=lambda x: x[2], reverse=True)

        logger.info(f"Ranking de respostas: {[(fonte, round(score, 3)) for fonte, _, score in ranking]}")

        return ranking

    def remover_duplicatas(self, sentencas: List[str], limiar_similaridade: float = 0.8) -> List[str]:
        """
        Remove sentenças duplicadas ou muito similares.
        """
        if not sentencas:
            return []

        sentencas_unicas = []

        for sentenca in sentencas:
            e_duplicata = False

            for sentenca_existente in sentencas_unicas:
                # Calcula similaridade
                try:
                    vectorizer = TfidfVectorizer()
                    textos = [sentenca.lower(), sentenca_existente.lower()]
                    tfidf_matrix = vectorizer.fit_transform(textos)
                    similaridade = cosine_similarity(tfidf_matrix[0], tfidf_matrix[1])[0][0]

                    if similaridade >= limiar_similaridade:
                        e_duplicata = True
                        break
                except:
                    continue

            if not e_duplicata:
                sentencas_unicas.append(sentenca)

        return sentencas_unicas

    def extrair_sentencas_relevantes(self, resposta: str, pergunta: str, max_sentencas: int = 3) -> List[str]:
        """
        Extrai as sentenças mais relevantes de uma resposta.
        """
        sentencas = extrair_sentencas(resposta)

        if not sentencas:
            return []

        # Se já tem poucas sentenças, retorna todas
        if len(sentencas) <= max_sentencas:
            return sentencas

        # Calcula relevância de cada sentença
        sentencas_com_score = []
        for sentenca in sentencas:
            score = self.calcular_relevancia(sentenca, pergunta)
            sentencas_com_score.append((sentenca, score))

        # Ordena por relevância
        sentencas_com_score.sort(key=lambda x: x[1], reverse=True)

        # Pega as top N, mas mantém ordem original
        top_sentencas = [s for s, _ in sentencas_com_score[:max_sentencas]]

        # Reordena para manter ordem lógica (ordem original)
        sentencas_ordenadas = []
        for sentenca in sentencas:
            if sentenca in top_sentencas:
                sentencas_ordenadas.append(sentenca)

        return sentencas_ordenadas

    def combinar_respostas(
        self, 
        respostas: Dict[str, str], 
        pergunta: str, 
        tipo_pergunta: str = "geral",
        max_sentencas: int = 6
    ) -> Optional[str]:
        """
        Combina múltiplas respostas em uma resposta coesa.

        Args:
            respostas: Dicionário {fonte: resposta}
            pergunta: Pergunta original
            tipo_pergunta: Tipo da pergunta (qual, como, porque, etc)
            max_sentencas: Número máximo de sentenças na resposta final

        Returns:
            Resposta combinada ou None
        """
        # Remove respostas vazias
        respostas_validas = {k: v for k, v in respostas.items() if v and len(v.strip()) >= 10}

        if not respostas_validas:
            return None

        # Se só tem uma resposta, retorna ela processada
        if len(respostas_validas) == 1:
            unica_resposta = list(respostas_validas.values())[0]
            sentencas = self.extrair_sentencas_relevantes(unica_resposta, pergunta, max_sentencas)
            return juntar_sentencas(sentencas)

        # Ranqueia respostas por relevância
        ranking = self.ranquear_respostas(respostas_validas, pergunta)

        # Estratégia de combinação baseada no tipo de pergunta
        if tipo_pergunta in ["qual", "quem", "quanto"]:
            # Perguntas factuais: usa a resposta mais relevante
            melhor_fonte, melhor_resposta, melhor_score = ranking[0]
            sentencas = self.extrair_sentencas_relevantes(melhor_resposta, pergunta, max_sentencas)

            logger.info(f"Combinação (factual): usando apenas {melhor_fonte} (score: {melhor_score:.3f})")

        elif tipo_pergunta in ["como", "porque"]:
            # Perguntas explicativas: combina informações de múltiplas fontes
            todas_sentencas = []

            # Pega sentenças das top 2-3 fontes
            for fonte, resposta, score in ranking[:3]:
                if score > 0.1:  # Filtra respostas muito irrelevantes
                    sentencas = self.extrair_sentencas_relevantes(resposta, pergunta, max_sentencas=3)
                    todas_sentencas.extend(sentencas)

            # Remove duplicatas
            sentencas = self.remover_duplicatas(todas_sentencas, limiar_similaridade=0.7)

            # Limita ao máximo de sentenças
            sentencas = sentencas[:max_sentencas]

            logger.info(f"Combinação (explicativa): mescladas {len(sentencas)} sentenças de {len(ranking)} fontes")

        else:
            # Pergunta geral: mescla top 2 fontes
            todas_sentencas = []

            for fonte, resposta, score in ranking[:2]:
                if score > 0.05:
                    sentencas_fonte = self.extrair_sentencas_relevantes(resposta, pergunta, max_sentencas=2)
                    todas_sentencas.extend(sentencas_fonte)

            # Remove duplicatas
            sentencas = self.remover_duplicatas(todas_sentencas, limiar_similaridade=0.75)

            # Limita ao máximo de sentenças
            sentencas = sentencas[:max_sentencas]

            logger.info(f"Combinação (geral): mescladas {len(sentencas)} sentenças")

        # Junta sentenças em resposta final
        if not sentencas:
            return None

        resposta_final = juntar_sentencas(sentencas)

        # Limpa resposta final (remove datas, URLs, etc)
        resposta_final = limpar_texto(resposta_final)

        # Remove sentenças que são claramente lixo
        sentencas_limpas = extrair_sentencas(resposta_final)
        sentencas_filtradas = []

        for sentenca in sentencas_limpas:
            # Remove sentenças com muitos números (provavelmente datas/códigos)
            num_count = sum(c.isdigit() for c in sentenca)
            if num_count > len(sentenca) * 0.3:  # Mais de 30% são números
                continue

            # Remove sentenças muito curtas (menos de 20 caracteres)
            if len(sentenca) < 20:
                continue

            # Remove sentenças que começam com símbolos estranhos
            if sentenca and not sentenca[0].isalnum():
                continue

            sentencas_filtradas.append(sentenca)

        if not sentencas_filtradas:
            return None

        resposta_final = juntar_sentencas(sentencas_filtradas)

        return resposta_final

    def combinar_com_fonte_principal(
        self, 
        respostas: Dict[str, str], 
        pergunta: str,
        tipo_pergunta: str = "geral"
    ) -> tuple:
        """
        Combina respostas e retorna (resposta_combinada, fonte_principal).
        """
        resposta = self.combinar_respostas(respostas, pergunta, tipo_pergunta)

        if not resposta:
            return None, None

        # Determina fonte principal baseada no ranking
        ranking = self.ranquear_respostas(respostas, pergunta)

        if ranking:
            fonte_principal = ranking[0][0]

            # Se usou múltiplas fontes, indica isso
            if len(ranking) > 1 and tipo_pergunta in ["como", "porque"]:
                fontes_usadas = [f for f, _, s in ranking if s > 0.1][:3]
                fonte_principal = "+".join(fontes_usadas)
        else:
            fonte_principal = "desconhecido"

        return resposta, fonte_principal
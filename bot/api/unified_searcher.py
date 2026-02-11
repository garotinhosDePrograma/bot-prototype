"""
Buscador Unificado - Integra TODAS as fontes de conhecimento
Versão 2.0 - Com orquestração inteligente e paralelização
"""

import logging
import requests
from typing import Dict, Optional, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError
import time

logger = logging.getLogger(__name__)


class BuscadorUnificado:
    """
    Orquestra buscas em TODAS as fontes disponíveis de forma inteligente.
    """

    def __init__(
        self, 
        wolfram_app_id: str = None, 
        google_cx: str = None, 
        google_api_key: str = None
    ):
        self.wolfram_app_id = wolfram_app_id
        self.google_cx = google_cx
        self.google_api_key = google_api_key

        # Mapeia métodos de busca
        self.fontes_disponiveis = {
            "wolfram": self.buscar_wolfram,
            "google": self.buscar_google,
            "duckduckgo": self.buscar_duckduckgo,
            "wikipedia": self.buscar_wikipedia,
            "arxiv": self.buscar_arxiv,
            "dbpedia": self.buscar_dbpedia,
            "youtube": self.buscar_youtube_transcript,
        }

        # Configurações de timeout por fonte
        self.timeouts = {
            "wolfram": 5,
            "google": 5,
            "duckduckgo": 7,
            "wikipedia": 7,
            "arxiv": 10,
            "dbpedia": 5,
            "youtube": 10,
        }

    # ============================================
    # BUSCA ORQUESTRADA
    # ============================================

    def buscar_inteligente(
        self, 
        pergunta_en: str,
        fontes_priorizadas: List[str] = None,
        max_fontes: int = 4,
        timeout_total: int = 20
    ) -> Dict[str, Optional[str]]:
        """
        Busca inteligente que:
        1. Prioriza fontes ranqueadas por ML
        2. Executa em paralelo
        3. Para quando encontra resposta boa o suficiente

        Args:
            pergunta_en: Pergunta em inglês
            fontes_priorizadas: Lista ordenada de fontes (da melhor pra pior)
            max_fontes: Número máximo de fontes para consultar
            timeout_total: Timeout total em segundos

        Returns:
            Dict com resultados de cada fonte
        """
        start_time = time.time()
        resultados = {}

        # Se não tem priorização, usa todas
        if not fontes_priorizadas:
            fontes_priorizadas = list(self.fontes_disponiveis.keys())

        # Limita número de fontes
        fontes_a_buscar = fontes_priorizadas[:max_fontes]

        logger.info(f"Buscando em {len(fontes_a_buscar)} fontes: {fontes_a_buscar}")

        # Executa buscas em paralelo
        with ThreadPoolExecutor(max_workers=max_fontes) as executor:
            # Submete tarefas
            futures = {}
            for fonte in fontes_a_buscar:
                if fonte in self.fontes_disponiveis:
                    metodo = self.fontes_disponiveis[fonte]
                    timeout_fonte = self.timeouts.get(fonte, 10)

                    future = executor.submit(
                        self._buscar_com_timeout,
                        metodo,
                        pergunta_en,
                        timeout_fonte
                    )
                    futures[future] = fonte

            # Coleta resultados conforme completam
            tempo_decorrido = 0
            for future in as_completed(futures, timeout=timeout_total):
                tempo_decorrido = time.time() - start_time

                if tempo_decorrido >= timeout_total:
                    logger.warning(f"Timeout total atingido ({timeout_total}s)")
                    break

                fonte = futures[future]

                try:
                    resultado = future.result(timeout=1)
                    resultados[fonte] = resultado

                    if resultado:
                        logger.info(f"✓ {fonte}: obteve resposta ({len(resultado)} chars)")
                    else:
                        logger.info(f"✗ {fonte}: sem resposta")

                    # Early stopping: se já tem 2 respostas boas, para
                    respostas_boas = sum(
                        1 for r in resultados.values() 
                        if r and len(r) > 100
                    )

                    if respostas_boas >= 2:
                        logger.info("Early stopping: 2 respostas boas encontradas")
                        break

                except TimeoutError:
                    logger.warning(f"⏱ {fonte}: timeout")
                    resultados[fonte] = None
                except Exception as e:
                    logger.error(f"❌ {fonte}: erro - {str(e)}")
                    resultados[fonte] = None

        tempo_total = time.time() - start_time
        logger.info(f"Busca concluída em {tempo_total:.2f}s - {len(resultados)} fontes consultadas")

        return resultados

    def _buscar_com_timeout(self, metodo, pergunta, timeout):
        """Wrapper para executar busca com timeout."""
        try:
            return metodo(pergunta)
        except Exception as e:
            logger.error(f"Erro em busca: {str(e)}")
            return None

    # ============================================
    # FONTES DE BUSCA INDIVIDUAIS
    # ============================================

    def buscar_wolfram(self, pergunta_en: str) -> Optional[str]:
        """Busca no Wolfram Alpha - melhor para cálculos e fatos."""
        if not self.wolfram_app_id:
            return None

        # Tenta endpoint simples
        url_simple = (
            f"http://api.wolframalpha.com/v1/result"
            f"?i={requests.utils.quote(pergunta_en)}"
            f"&appid={self.wolfram_app_id}"
        )

        try:
            response = requests.get(url_simple, timeout=5)
            if response.status_code == 200:
                texto = response.text.strip()
                if len(texto) > 10 and "did not understand" not in texto.lower():
                    logger.info(f"Wolfram (simple): {texto[:80]}...")
                    return texto
        except Exception as e:
            logger.debug(f"Wolfram simple falhou: {str(e)}")

        # Tenta endpoint spoken
        url_spoken = (
            f"http://api.wolframalpha.com/v1/spoken"
            f"?i={requests.utils.quote(pergunta_en)}"
            f"&appid={self.wolfram_app_id}"
        )

        try:
            response = requests.get(url_spoken, timeout=5)
            if response.status_code == 200:
                texto = response.text.strip()
                if len(texto) > 10:
                    logger.info(f"Wolfram (spoken): {texto[:80]}...")
                    return texto
        except Exception as e:
            logger.debug(f"Wolfram spoken falhou: {str(e)}")

        return None

    def buscar_google(self, pergunta_en: str) -> Optional[str]:
        """Google Custom Search - melhor para informações gerais."""
        if not (self.google_cx and self.google_api_key):
            return None

        url = (
            f"https://www.googleapis.com/customsearch/v1"
            f"?q={requests.utils.quote(pergunta_en)}"
            f"&cx={self.google_cx}"
            f"&key={self.google_api_key}"
            f"&num=3"
        )

        try:
            response = requests.get(url, timeout=5)
            data = response.json()

            if "items" in data:
                snippets = [
                    item["snippet"] 
                    for item in data["items"][:3] 
                    if "snippet" in item
                ]

                if snippets:
                    texto = " ".join(snippets)
                    logger.info(f"Google ({len(snippets)} resultados): {texto[:80]}...")
                    return texto

        except Exception as e:
            logger.error(f"Erro Google: {str(e)}")

        return None

    def buscar_duckduckgo(self, pergunta_en: str) -> Optional[str]:
        """DuckDuckGo Instant Answer - sem tracking."""
        url = f"https://api.duckduckgo.com/?q={requests.utils.quote(pergunta_en)}&format=json"

        try:
            response = requests.get(url, timeout=7)
            data = response.json()

            # AbstractText (mais confiável)
            if data.get("AbstractText") and len(data["AbstractText"]) > 50:
                logger.info(f"DuckDuckGo (Abstract): {data['AbstractText'][:80]}...")
                return data["AbstractText"]

            # Definition
            if data.get("Definition") and len(data["Definition"]) > 50:
                logger.info(f"DuckDuckGo (Definition): {data['Definition'][:80]}...")
                return data["Definition"]

            # RelatedTopics
            if data.get("RelatedTopics"):
                textos = []
                for item in data["RelatedTopics"][:3]:
                    if isinstance(item, dict) and "Text" in item and len(item["Text"]) > 50:
                        textos.append(item["Text"])

                if textos:
                    texto_completo = " ".join(textos[:2])
                    logger.info(f"DuckDuckGo (Topics): {texto_completo[:80]}...")
                    return texto_completo

        except Exception as e:
            logger.error(f"Erro DuckDuckGo: {str(e)}")

        return None

    def buscar_wikipedia(self, pergunta_en: str) -> Optional[str]:
        """Wikipedia - enciclopédia livre."""
        # Remove palavras de pergunta
        query = pergunta_en.lower()
        for palavra in ["what is", "who is", "when was", "where is", "how does"]:
            query = query.replace(palavra, "")
        query = query.strip()

        # Busca artigos
        search_url = (
            f"https://en.wikipedia.org/w/api.php"
            f"?action=query&list=search"
            f"&srsearch={requests.utils.quote(query)}"
            f"&format=json&srlimit=3"
        )

        try:
            response = requests.get(search_url, timeout=7)
            data = response.json()

            if not data.get('query', {}).get('search'):
                return None

            # Tenta primeiros resultados
            for resultado in data['query']['search'][:2]:
                titulo = resultado['title']

                # Busca conteúdo
                content_url = (
                    f"https://en.wikipedia.org/api/rest_v1/page/summary/"
                    f"{titulo.replace(' ', '_')}"
                )

                content_response = requests.get(content_url, timeout=5)

                if content_response.status_code == 200:
                    content_data = content_response.json()
                    extract = content_data.get("extract", "")

                    if len(extract) > 100:
                        logger.info(f"Wikipedia: {extract[:80]}...")
                        return extract

        except Exception as e:
            logger.error(f"Erro Wikipedia: {str(e)}")

        return None

    def buscar_arxiv(self, pergunta_en: str) -> Optional[str]:
        """arXiv - artigos científicos."""
        try:
            import urllib.parse

            query = urllib.parse.quote(pergunta_en)
            url = f"http://export.arxiv.org/api/query?search_query=all:{query}&start=0&max_results=3"

            response = requests.get(url, timeout=10)

            if response.status_code != 200:
                return None

            # Parse XML
            import re
            summaries = re.findall(r'<summary>(.*?)</summary>', response.text, re.DOTALL)

            if summaries:
                textos = []
                for summary in summaries[:2]:
                    summary_clean = ' '.join(summary.split())
                    if len(summary_clean) > 100:
                        textos.append(summary_clean)

                if textos:
                    resultado = ' '.join(textos[:2])
                    logger.info(f"arXiv: {resultado[:80]}...")
                    return resultado

        except Exception as e:
            logger.error(f"Erro arXiv: {str(e)}")

        return None

    def buscar_dbpedia(self, pergunta_en: str) -> Optional[str]:
        """DBpedia - dados estruturados."""
        try:
            # Extrai entidade
            palavras = pergunta_en.split()
            palavras_relevantes = [p for p in palavras if p[0].isupper() and len(p) > 2]

            if not palavras_relevantes:
                return None

            entidade = '_'.join(palavras_relevantes[:2])

            url = f"http://dbpedia.org/data/{entidade}.json"
            response = requests.get(url, timeout=5)

            if response.status_code != 200:
                return None

            data = response.json()
            resource_uri = f"http://dbpedia.org/resource/{entidade}"

            if resource_uri in data:
                resource_data = data[resource_uri]
                abstract_key = "http://dbpedia.org/ontology/abstract"

                if abstract_key in resource_data:
                    abstracts = resource_data[abstract_key]

                    for abstract in abstracts:
                        if abstract.get('lang') == 'en' and len(abstract.get('value', '')) > 100:
                            texto = abstract['value']
                            logger.info(f"DBpedia: {texto[:80]}...")
                            return texto

        except Exception as e:
            logger.error(f"Erro DBpedia: {str(e)}")

        return None

    def buscar_youtube_transcript(self, pergunta_en: str) -> Optional[str]:
        """YouTube - transcrições de vídeos educacionais."""
        try:
            from youtube_search import YoutubeSearch
            from youtube_transcript_api import YouTubeTranscriptApi

            # Busca vídeos
            query = pergunta_en + " tutorial explanation"
            resultados = YoutubeSearch(query, max_results=3).to_dict()

            if not resultados:
                return None

            # Tenta pegar transcrição
            for video in resultados:
                video_id = video['id']

                try:
                    transcript = YouTubeTranscriptApi.get_transcript(
                        video_id, 
                        languages=['en']
                    )

                    # Junta primeiros segmentos
                    texto = ' '.join([t['text'] for t in transcript[:20]])

                    if len(texto) > 100:
                        logger.info(f"YouTube: {texto[:80]}...")
                        return texto

                except:
                    continue

        except Exception as e:
            logger.error(f"Erro YouTube: {str(e)}")

        return None

    # ============================================
    # FONTES ADICIONAIS (podem ser adicionadas)
    # ============================================

    def buscar_reddit(self, pergunta_en: str) -> Optional[str]:
        """Reddit - discussões comunitárias (requer API key)."""
        # TODO: Implementar se tiver Reddit API key
        pass

    def buscar_stackoverflow(self, pergunta_en: str) -> Optional[str]:
        """Stack Overflow - perguntas técnicas."""
        # TODO: Implementar Stack Exchange API
        pass

    def buscar_openai_search(self, pergunta_en: str) -> Optional[str]:
        """Bing/OpenAI Search (requer API key)."""
        # TODO: Implementar se tiver OpenAI API key
        pass

    def buscar_perplexity(self, pergunta_en: str) -> Optional[str]:
        """Perplexity AI (requer API key)."""
        # TODO: Implementar se tiver Perplexity API key
        pass
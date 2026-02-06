"""
Módulo para busca em múltiplas APIs de conhecimento.
"""

import logging
import requests
from typing import Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)


class BuscadorAPI:
    """Classe para buscar informações em múltiplas APIs."""

    def __init__(self, wolfram_app_id: str = None, google_cx: str = None, google_api_key: str = None):
        self.wolfram_app_id = wolfram_app_id
        self.google_cx = google_cx
        self.google_api_key = google_api_key

    def buscar_wolfram(self, pergunta_en: str) -> Optional[str]:
        """Busca resposta no Wolfram Alpha - tenta múltiplos endpoints."""
        if not self.wolfram_app_id:
            return None

        # Tenta primeiro o endpoint simples
        url_simple = f"http://api.wolframalpha.com/v1/result?i={requests.utils.quote(pergunta_en)}&appid={self.wolfram_app_id}"
        try:
            response = requests.get(url_simple, timeout=5)
            if response.status_code == 200:
                texto = response.text.strip()
                logger.info(f"Wolfram Alpha (simple): {texto[:100]}...")
                return texto
        except Exception as e:
            logger.error(f"Erro Wolfram Alpha (simple): {str(e)}")

        # Se falhou, tenta o endpoint spoken (mais detalhado)
        url_spoken = f"http://api.wolframalpha.com/v1/spoken?i={requests.utils.quote(pergunta_en)}&appid={self.wolfram_app_id}"
        try:
            response = requests.get(url_spoken, timeout=5)
            if response.status_code == 200:
                texto = response.text.strip()
                logger.info(f"Wolfram Alpha (spoken): {texto[:100]}...")
                return texto
        except Exception as e:
            logger.error(f"Erro Wolfram Alpha (spoken): {str(e)}")

        return None

    def buscar_google(self, pergunta_en: str) -> Optional[str]:
        """Busca resposta no Google Custom Search - combina múltiplos resultados."""
        if not (self.google_cx and self.google_api_key):
            return None

        url = f"https://www.googleapis.com/customsearch/v1?q={requests.utils.quote(pergunta_en)}&cx={self.google_cx}&key={self.google_api_key}&num=3"
        try:
            response = requests.get(url, timeout=5)
            data = response.json()
            if "items" in data and len(data["items"]) > 0:
                # Combina os snippets dos primeiros 3 resultados
                snippets = []
                for item in data["items"][:3]:
                    if "snippet" in item:
                        snippets.append(item["snippet"])

                if snippets:
                    texto_combinado = " ".join(snippets)
                    logger.info(f"Google ({len(snippets)} resultados): {texto_combinado[:100]}...")
                    return texto_combinado

            return None
        except Exception as e:
            logger.error(f"Erro Google: {str(e)}")
            return None

    def buscar_duckduckgo(self, pergunta_en: str) -> Optional[str]:
        """Busca resposta no DuckDuckGo."""
        url = f"https://api.duckduckgo.com/?q={requests.utils.quote(pergunta_en)}&format=json"
        try:
            response = requests.get(url, timeout=7)
            data = response.json()

            # Tenta AbstractText primeiro (mais confiável)
            if data.get("AbstractText") and len(data["AbstractText"]) > 50:
                texto = data["AbstractText"]
                logger.info(f"DuckDuckGo (Abstract): {texto[:100]}...")
                return texto

            # Tenta Definition
            if data.get("Definition") and len(data["Definition"]) > 50:
                texto = data["Definition"]
                logger.info(f"DuckDuckGo (Definition): {texto[:100]}...")
                return texto

            # Tenta RelatedTopics - pega os primeiros 2-3 mais relevantes
            if data.get("RelatedTopics") and len(data["RelatedTopics"]) > 0:
                textos = []
                for item in data["RelatedTopics"][:3]:
                    if isinstance(item, dict) and "Text" in item:
                        texto_item = item["Text"]
                        # Filtra textos muito curtos ou irrelevantes
                        if len(texto_item) > 50:
                            textos.append(texto_item)

                if textos:
                    texto_completo = " ".join(textos[:2])  # Máximo 2 tópicos
                    logger.info(f"DuckDuckGo (RelatedTopics): {texto_completo[:100]}...")
                    return texto_completo

            logger.info("DuckDuckGo: nenhum resultado útil encontrado")
            return None
        except Exception as e:
            logger.error(f"Erro DuckDuckGo: {str(e)}")
            return None

    def buscar_wikipedia(self, pergunta_en: str) -> Optional[str]:
        """Busca resposta na Wikipedia usando busca de texto."""
        # Remove palavras de pergunta para melhorar a busca
        query_limpa = pergunta_en.lower()
        palavras_remover = ["what is", "who is", "who was", "when was", "where is", "how does", "why is"]
        for palavra in palavras_remover:
            query_limpa = query_limpa.replace(palavra, "")
        query_limpa = query_limpa.strip()

        # Primeiro, faz busca para encontrar o artigo correto
        search_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={requests.utils.quote(query_limpa)}&format=json&srlimit=3"

        try:
            # Busca pelo artigo
            response = requests.get(search_url, timeout=7)
            if response.status_code != 200:
                return None

            data = response.json()

            # Verifica se encontrou resultados
            if not data.get('query', {}).get('search'):
                logger.info("Wikipedia: nenhum resultado encontrado")
                return None

            # Tenta os primeiros 2 resultados
            for resultado in data['query']['search'][:2]:
                titulo = resultado['title']
                logger.info(f"Wikipedia: tentando artigo '{titulo}'")

                # Busca o conteúdo do artigo
                content_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{titulo.replace(' ', '_')}"
                content_response = requests.get(content_url, timeout=5)

                if content_response.status_code == 200:
                    content_data = content_response.json()
                    extract = content_data.get("extract", "")
                    if extract and len(extract) > 100:
                        logger.info(f"Wikipedia: {extract[:100]}...")
                        return extract

            logger.info("Wikipedia: nenhum conteúdo útil encontrado")
            return None
        except Exception as e:
            logger.error(f"Erro Wikipedia: {str(e)}")
            return None

    def buscar_todas(self, pergunta_en: str, timeout: int = 15) -> Dict[str, Optional[str]]:
        """
        Busca em TODAS as APIs simultaneamente usando threads.
        Retorna um dicionário com os resultados de cada fonte.
        """
        resultados = {
            "wolfram": None,
            "google": None,
            "duckduckgo": None,
            "wikipedia": None
        }

        # Dicionário de funções de busca
        buscadores = {
            "wolfram": self.buscar_wolfram,
            "google": self.buscar_google,
            "duckduckgo": self.buscar_duckduckgo,
            "wikipedia": self.buscar_wikipedia
        }

        # Executa todas as buscas em paralelo
        with ThreadPoolExecutor(max_workers=4) as executor:
            # Submete todas as tarefas
            futures = {
                executor.submit(func, pergunta_en): nome 
                for nome, func in buscadores.items()
            }

            # Coleta resultados conforme completam
            for future in as_completed(futures, timeout=timeout):
                nome_fonte = futures[future]
                try:
                    resultado = future.result()
                    resultados[nome_fonte] = resultado
                    if resultado:
                        logger.info(f"✓ {nome_fonte}: obteve resposta")
                    else:
                        logger.info(f"✗ {nome_fonte}: sem resposta")
                except Exception as e:
                    logger.error(f"Erro em {nome_fonte}: {str(e)}")
                    resultados[nome_fonte] = None

        return resultados

    def buscar_melhor(self, pergunta_en: str) -> tuple:
        """
        Busca em todas as APIs e retorna a melhor resposta.
        Retorna (resposta, fonte).
        """
        resultados = self.buscar_todas(pergunta_en)

        # Ordem de preferência (do mais confiável ao menos)
        ordem_preferencia = ["wolfram", "wikipedia", "google", "duckduckgo"]

        for fonte in ordem_preferencia:
            if resultados.get(fonte):
                return resultados[fonte], fonte

        return None, None

    def buscar_wikipedia_avancado(self, pergunta_en: str, lingua: str = "pt") -> Optional[str]:
        """
        Busca avançada na Wikipedia com múltiplas estratégias.
        """
        # 1. Tenta busca em português primeiro
        resultado_pt = self._buscar_wikipedia_idioma(pergunta_en, "pt")
        if resultado_pt:
            return resultado_pt
        
        # 2. Se falhou, tenta em inglês
        resultado_en = self._buscar_wikipedia_idioma(pergunta_en, "en")
        if resultado_en:
            # Traduz resultado
            from bot.utils.text_utils import traduzir
            return traduzir(resultado_en, origem="en", destino="pt")
        
        return None
    
    def _buscar_wikipedia_idioma(self, query: str, idioma: str) -> Optional[str]:
        """Busca Wikipedia em idioma específico."""
        try:
            api_url = f"https://{idioma}.wikipedia.org/w/api.php"
            
            # Busca artigos
            search_params = {
                "action": "query",
                "list": "search",
                "srsearch": query,
                "format": "json",
                "srlimit": 3
            }
            
            response = requests.get(api_url, params=search_params, timeout=5)
            data = response.json()
            
            if not data.get('query', {}).get('search'):
                return None
            
            # Pega primeiro resultado
            primeiro_resultado = data['query']['search'][0]
            titulo = primeiro_resultado['title']
            
            # Busca conteúdo do artigo
            content_params = {
                "action": "query",
                "prop": "extracts",
                "exintro": True,
                "explaintext": True,
                "titles": titulo,
                "format": "json"
            }
            
            content_response = requests.get(api_url, params=content_params, timeout=5)
            content_data = content_response.json()
            
            pages = content_data.get('query', {}).get('pages', {})
            if pages:
                page = list(pages.values())[0]
                extract = page.get('extract', '')
                
                if extract and len(extract) > 100:
                    logger.info(f"Wikipedia ({idioma}): {extract[:100]}...")
                    return extract
            
            return None
        except Exception as e:
            logger.error(f"Erro Wikipedia ({idioma}): {str(e)}")
            return None
    
    def buscar_arxiv(self, pergunta_en: str) -> Optional[str]:
        """
        Busca em artigos científicos do arXiv.
        Útil para perguntas acadêmicas/científicas.
        """
        try:
            import urllib.parse
            
            # Monta query para arXiv
            query = urllib.parse.quote(pergunta_en)
            url = f"http://export.arxiv.org/api/query?search_query=all:{query}&start=0&max_results=3"
            
            response = requests.get(url, timeout=7)
            
            if response.status_code != 200:
                return None
            
            # Parse XML simples (pode usar BeautifulSoup para melhor parsing)
            content = response.text
            
            # Extrai summaries (resumos)
            import re
            summaries = re.findall(r'<summary>(.*?)</summary>', content, re.DOTALL)
            
            if summaries:
                # Pega primeiros 2-3 resumos
                textos = []
                for summary in summaries[:2]:
                    # Remove whitespace extra
                    summary_clean = ' '.join(summary.split())
                    if len(summary_clean) > 100:
                        textos.append(summary_clean)
                
                if textos:
                    resultado = ' '.join(textos[:2])
                    logger.info(f"arXiv: {resultado[:100]}...")
                    return resultado
            
            return None
        except Exception as e:
            logger.error(f"Erro arXiv: {str(e)}")
            return None
    
    def buscar_dbpedia(self, pergunta_en: str) -> Optional[str]:
        """
        Busca em DBpedia (base de conhecimento estruturado).
        Ótimo para fatos estruturados.
        """
        try:
            # Extrai entidade principal da pergunta
            # (simplificado - pode melhorar com NER)
            palavras = pergunta_en.split()
            palavras_relevantes = [p for p in palavras if p[0].isupper() and len(p) > 2]
            
            if not palavras_relevantes:
                return None
            
            entidade = '_'.join(palavras_relevantes[:2])
            
            # Busca no DBpedia
            url = f"http://dbpedia.org/data/{entidade}.json"
            response = requests.get(url, timeout=5)
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            
            # Extrai abstracts
            resource_uri = f"http://dbpedia.org/resource/{entidade}"
            if resource_uri in data:
                resource_data = data[resource_uri]
                
                # Procura por abstract
                abstract_key = "http://dbpedia.org/ontology/abstract"
                if abstract_key in resource_data:
                    abstracts = resource_data[abstract_key]
                    
                    # Pega abstract em inglês
                    for abstract in abstracts:
                        if abstract.get('lang') == 'en':
                            texto = abstract.get('value', '')
                            if len(texto) > 100:
                                logger.info(f"DBpedia: {texto[:100]}...")
                                return texto
            
            return None
        except Exception as e:
            logger.error(f"Erro DBpedia: {str(e)}")
            return None
    
    def buscar_youtube_transcript(self, pergunta_en: str) -> Optional[str]:
        """
        Busca vídeos educacionais no YouTube e tenta extrair transcrições.
        Útil para tutoriais e explicações.
        """
        try:
            from youtube_search import YoutubeSearch
            from youtube_transcript_api import YouTubeTranscriptApi
            
            # Busca vídeos
            query = pergunta_en + " tutorial explanation"
            resultados = YoutubeSearch(query, max_results=3).to_dict()
            
            if not resultados:
                return None
            
            # Tenta pegar transcrição do primeiro vídeo
            for video in resultados:
                video_id = video['id']
                
                try:
                    # Pega transcrição
                    transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['pt', 'en'])
                    
                    # Junta textos
                    texto_completo = ' '.join([t['text'] for t in transcript_list[:20]])  # Primeiros 20 segmentos
                    
                    if len(texto_completo) > 100:
                        logger.info(f"YouTube: {texto_completo[:100]}...")
                        return texto_completo
                except:
                    continue
            
            return None
        except Exception as e:
            logger.error(f"Erro YouTube: {str(e)}")
            return None

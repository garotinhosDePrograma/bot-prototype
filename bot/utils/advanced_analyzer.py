"""
Análise avançada de perguntas com extração de entidades e contexto semântico.
"""

import logging
import spacy
from typing import Dict, List, Optional, Tuple
import re

logger = logging.getLogger(__name__)

class AnalisadorAvancado:
    """Análise profunda de perguntas com NER e análise semântica."""
    
    def __init__(self):
        self.nlp = spacy.load("pt_core_news_sm")
        
        # Padrões de perguntas especializadas
        self.padroes_especializados = {
            "calculo": re.compile(r'\d+\s*[\+\-\*\/\^]\s*\d+|quanto\s+é|calcule|some|multiplique', re.IGNORECASE),
            "conversao": re.compile(r'convert|converta|transforme|de\s+\w+\s+para\s+\w+', re.IGNORECASE),
            "comparacao": re.compile(r'diferença|comparar|versus|vs\.|melhor|maior|menor', re.IGNORECASE),
            "definicao": re.compile(r'o que é|definição de|defina|significado de|conceito de', re.IGNORECASE),
            "lista": re.compile(r'liste|listar|quais são|enumere|principais', re.IGNORECASE),
            "causa": re.compile(r'por que|porque|motivo|razão|causa', re.IGNORECASE),
            "processo": re.compile(r'como funciona|como é feito|processo|etapas|passo a passo', re.IGNORECASE),
            "historico": re.compile(r'quando|história|origem|descoberto|inventado|criado', re.IGNORECASE),
            "localizacao": re.compile(r'onde|localização|fica|localizado|encontrar', re.IGNORECASE),
        }
    
    def extrair_entidades(self, pergunta: str) -> Dict[str, List[str]]:
        """
        Extrai entidades nomeadas (pessoas, lugares, organizações, etc).
        """
        doc = self.nlp(pergunta)
        
        entidades = {
            "PERSON": [],  # Pessoas
            "LOC": [],     # Lugares
            "ORG": [],     # Organizações
            "DATE": [],    # Datas
            "MISC": [],    # Miscelânea
        }
        
        for ent in doc.ents:
            if ent.label_ in entidades:
                entidades[ent.label_].append(ent.text)
        
        logger.info(f"Entidades extraídas: {entidades}")
        return entidades
    
    def detectar_tipo_especializado(self, pergunta: str) -> str:
        """
        Detecta tipo especializado de pergunta para busca otimizada.
        """
        for tipo, padrao in self.padroes_especializados.items():
            if padrao.search(pergunta):
                logger.info(f"Tipo especializado detectado: {tipo}")
                return tipo
        
        return "geral"
    
    def extrair_numeros_e_unidades(self, pergunta: str) -> Dict:
        """
        Extrai números e unidades de medida para cálculos/conversões.
        """
        doc = self.nlp(pergunta)
        
        numeros = []
        unidades = []
        
        # Padrões de unidades comuns
        unidades_conhecidas = {
            "metro", "metros", "km", "quilômetro", "centímetro", "cm",
            "litro", "litros", "ml", "mililitro",
            "kg", "quilograma", "grama", "gramas", "tonelada",
            "celsius", "fahrenheit", "kelvin",
            "dólar", "dólares", "real", "reais", "euro", "euros",
            "segundo", "segundos", "minuto", "minutos", "hora", "horas"
        }
        
        for token in doc:
            # Detecta números
            if token.like_num or token.pos_ == "NUM":
                try:
                    numeros.append(float(token.text.replace(",", ".")))
                except:
                    pass
            
            # Detecta unidades
            if token.lemma_.lower() in unidades_conhecidas:
                unidades.append(token.lemma_.lower())
        
        return {
            "numeros": numeros,
            "unidades": unidades,
            "tem_calculo": len(numeros) >= 2,
            "tem_conversao": len(unidades) >= 1
        }
    
    def analisar_complexidade(self, pergunta: str) -> Dict:
        """
        Analisa complexidade da pergunta para decidir estratégia de busca.
        """
        doc = self.nlp(pergunta)
        
        # Métricas de complexidade
        num_palavras = len([t for t in doc if not t.is_punct])
        num_verbos = len([t for t in doc if t.pos_ == "VERB"])
        num_substantivos = len([t for t in doc if t.pos_ == "NOUN"])
        num_clausulas = len([t for t in doc if t.dep_ == "ccomp"])  # Orações subordinadas
        
        # Classifica complexidade
        if num_palavras <= 5 and num_clausulas == 0:
            complexidade = "simples"
            estrategia = "busca_direta"
        elif num_palavras <= 10 and num_clausulas <= 1:
            complexidade = "media"
            estrategia = "busca_multipla"
        else:
            complexidade = "complexa"
            estrategia = "busca_decomposicao"
        
        return {
            "complexidade": complexidade,
            "estrategia_recomendada": estrategia,
            "metricas": {
                "palavras": num_palavras,
                "verbos": num_verbos,
                "substantivos": num_substantivos,
                "clausulas": num_clausulas
            }
        }
    
    def decompor_pergunta_complexa(self, pergunta: str) -> List[str]:
        """
        Decompõe pergunta complexa em sub-perguntas mais simples.
        Exemplo: "Quem inventou a internet e quando?" -> 
                 ["Quem inventou a internet?", "Quando a internet foi inventada?"]
        """
        doc = self.nlp(pergunta)
        
        subperguntas = []
        
        # Detecta conectores (e, mas, ou, etc)
        conectores_encontrados = [t for t in doc if t.pos_ == "CCONJ"]
        
        if conectores_encontrados:
            # Tenta dividir pela conjunção
            texto_pergunta = pergunta
            
            for conector in conectores_encontrados:
                partes = texto_pergunta.split(f" {conector.text} ", 1)
                
                if len(partes) == 2:
                    # Primeira parte mantém estrutura
                    subperguntas.append(partes[0].strip() + "?")
                    
                    # Segunda parte precisa reconstruir contexto
                    # Exemplo: "quando?" -> "Quando a internet foi inventada?"
                    parte2 = partes[1].strip().rstrip("?")
                    
                    # Tenta reconstruir pergunta completa
                    # (isso é simplificado - pode ser melhorado)
                    if len(parte2.split()) <= 2:  # Só palavra interrogativa
                        # Pega substantivo da primeira parte
                        try:
                            doc_parte1 = self.nlp(partes[0])
                            substantivos = [t.text for t in doc_parte1 if t.pos_ in ["NOUN", "PROPN"]]
                            if substantivos:
                                parte2 = f"{parte2} {' '.join(substantivos[-2:])}"
                        except Exception as e:
                            logger.error(f"Erro ao processar parte da pergunta: {e}")
                    
                    subperguntas.append(parte2.strip() + "?")
        
        # Se não conseguiu decompor, retorna pergunta original
        if not subperguntas:
            subperguntas = [pergunta]
        
        logger.info(f"Decomposição: {pergunta} -> {subperguntas}")
        return subperguntas
    
    def identificar_contexto_temporal(self, pergunta: str) -> Dict:
        """
        Identifica se pergunta requer informação atual ou histórica.
        """
        palavras_atual = ["atual", "hoje", "agora", "atualmente", "recente", "último", "última"]
        palavras_historico = ["história", "antigamente", "passado", "origem", "quando foi", "descoberto"]
        
        pergunta_lower = pergunta.lower()
        
        e_atual = any(palavra in pergunta_lower for palavra in palavras_atual)
        e_historico = any(palavra in pergunta_lower for palavra in palavras_historico)
        
        if e_atual and not e_historico:
            contexto = "atual"
            prioridade_fontes = ["google", "duckduckgo", "wikipedia", "wolfram"]
        elif e_historico and not e_atual:
            contexto = "historico"
            prioridade_fontes = ["wikipedia", "google", "wolfram", "duckduckgo"]
        else:
            contexto = "neutro"
            prioridade_fontes = ["wolfram", "wikipedia", "google", "duckduckgo"]
        
        return {
            "contexto_temporal": contexto,
            "prioridade_fontes": prioridade_fontes
        }
    
    def analisar_completo(self, pergunta: str) -> Dict:
        """
        Análise completa combinando todos os métodos.
        """
        return {
            "entidades": self.extrair_entidades(pergunta),
            "tipo_especializado": self.detectar_tipo_especializado(pergunta),
            "numeros_unidades": self.extrair_numeros_e_unidades(pergunta),
            "complexidade": self.analisar_complexidade(pergunta),
            "subperguntas": self.decompor_pergunta_complexa(pergunta),
            "contexto_temporal": self.identificar_contexto_temporal(pergunta),
        }

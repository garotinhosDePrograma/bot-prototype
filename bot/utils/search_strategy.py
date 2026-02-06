"""
Estratégias inteligentes de busca baseadas no tipo de pergunta.
"""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class EstrategiaBusca:
    """
    Determina COMO buscar baseado na análise da pergunta.
    """
    
    def __init__(self):
        # Mapeamento de tipos para fontes prioritárias
        self.prioridades = {
            "calculo": ["wolfram"],  # Wolfram Alpha é melhor para cálculos
            "conversao": ["wolfram", "google"],
            "definicao": ["wikipedia", "duckduckgo", "google"],
            "historico": ["wikipedia", "google", "duckduckgo"],
            "cientifico": ["arxiv", "wikipedia", "google"],
            "processo": ["youtube", "wikipedia", "google"],
            "localizacao": ["google", "wikipedia"],
            "comparacao": ["google", "wikipedia"],
            "lista": ["wikipedia", "google"],
            "atual": ["google", "duckduckgo"],
        }
    
    def selecionar_fontes(self, analise: Dict) -> List[str]:
        """
        Seleciona quais fontes buscar baseado na análise.
        """
        tipo_especializado = analise.get("tipo_especializado", "geral")
        contexto_temporal = analise.get("contexto_temporal", {}).get("contexto_temporal", "neutro")
        
        # Prioridade por tipo especializado
        if tipo_especializado in self.prioridades:
            fontes = self.prioridades[tipo_especializado]
        elif contexto_temporal == "atual":
            fontes = ["google", "duckduckgo", "wikipedia"]
        elif contexto_temporal == "historico":
            fontes = ["wikipedia", "google"]
        else:
            # Busca em todas
            fontes = ["wolfram", "google", "wikipedia", "duckduckgo"]
        
        logger.info(f"Fontes selecionadas para busca: {fontes}")
        return fontes
    
    def criar_queries_multiplas(self, pergunta: str, analise: Dict) -> List[str]:
        """
        Cria múltiplas queries reformuladas para melhor cobertura.
        """
        queries = [pergunta]  # Query original
        
        entidades = analise.get("entidades", {})
        tipo = analise.get("tipo_especializado", "geral")
        
        # Para definições, adiciona variações
        if tipo == "definicao":
            # Extrai termo principal
            doc = analise.get("doc")  # Assumindo que salvamos doc na análise
            substantivos = [ent for ent in entidades.get("MISC", [])]
            
            if substantivos:
                termo = substantivos[0]
                queries.append(f"what is {termo}")
                queries.append(f"{termo} definition")
                queries.append(f"{termo} meaning")
        
        # Para comparações, separa em queries individuais
        elif tipo == "comparacao":
            # Ex: "diferença entre X e Y" -> ["what is X", "what is Y", "X vs Y"]
            if " e " in pergunta or " and " in pergunta:
                partes = pergunta.replace(" e ", " and ").split(" and ")
                if len(partes) == 2:
                    queries.append(partes[0].strip())
                    queries.append(partes[1].strip())
        
        # Para perguntas complexas, usa subperguntas
        subperguntas = analise.get("subperguntas", [])
        if len(subperguntas) > 1:
            queries.extend(subperguntas)
        
        # Remove duplicatas mantendo ordem
        queries_unicas = []
        for q in queries:
            if q not in queries_unicas:
                queries_unicas.append(q)
        
        logger.info(f"Queries geradas: {queries_unicas}")
        return queries_unicas[:5]  # Máximo 5 queries

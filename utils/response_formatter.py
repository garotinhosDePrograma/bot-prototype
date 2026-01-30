"""
Módulo para formatação final de respostas.
"""

import logging
from utils.text_utils import limpar_texto

logger = logging.getLogger(__name__)

# Respostas para diferentes intenções
RESPOSTAS_INTENCAO = {
    "saudacao": ["Oi! Tudo certo por aí?", "Olá, como posso ajudar hoje?", "E aí, pronto para conversar?"],
    "status": ["Estou de boa, e você?", "Tudo ótimo por aqui! Como posso ajudar?"],
    "nome": ["Sou um bot simples, criado por um dev curioso!", "Não tenho um nome chique, só me chama de Bot!"],
    "funcao": ["Eu respondo perguntas, busco curiosidades e converso sobre quase tudo!"],
    "despedida": ["Tchau! Até a próxima!", "Valeu, até logo!"],
    "desconhecida": ["Ops, não sei responder isso ainda. Tenta outra pergunta?", "Hmm, essa é nova pra mim!"]
}


class FormatadorResposta:
    """Classe para formatar respostas de acordo com o contexto."""

    def __init__(self):
        pass

    def formatar(self, resposta: str, tipo_pergunta: str) -> str:
        """
        Formata a resposta de acordo com o tipo de pergunta.
        """
        if not resposta:
            return ""

        resposta = limpar_texto(resposta)

        # Para perguntas factuais, mantém resposta direta
        if tipo_pergunta in ["qual", "quem", "onde", "quando", "quanto"]:
            return resposta

        # Para perguntas explicativas (como)
        elif tipo_pergunta == "como":
            # Verifica se já começa com palavra de introdução
            inicio_baixo = resposta.lower()
            palavras_intro = ["basicamente", "geralmente", "normalmente", "tipicamente", "essencialmente"]

            if any(inicio_baixo.startswith(palavra) for palavra in palavras_intro):
                return resposta

            # Adiciona introdução apropriada
            return f"Basicamente, {resposta[0].lower()}{resposta[1:]}"

        # Para perguntas causais (por que)
        elif tipo_pergunta == "porque":
            inicio_baixo = resposta.lower()

            if inicio_baixo.startswith(("isso acontece", "isso ocorre", "porque", "devido")):
                return resposta

            return f"Isso acontece porque {resposta[0].lower()}{resposta[1:]}"

        # Para outros tipos, retorna sem modificação
        return resposta

    def garantir_pontuacao(self, texto: str) -> str:
        """Garante que o texto termina com pontuação adequada."""
        if not texto:
            return texto

        if texto[-1] not in '.!?':
            texto += '.'

        return texto

    def formatar_final(self, resposta: str, tipo_pergunta: str) -> str:
        """Aplica formatação completa."""
        if not resposta:
            return ""

        # Formata de acordo com tipo
        resposta_formatada = self.formatar(resposta, tipo_pergunta)

        # Garante pontuação
        resposta_formatada = self.garantir_pontuacao(resposta_formatada)

        # Capitaliza primeira letra se necessário
        if resposta_formatada and resposta_formatada[0].islower():
            resposta_formatada = resposta_formatada[0].upper() + resposta_formatada[1:]

        return resposta_formatada
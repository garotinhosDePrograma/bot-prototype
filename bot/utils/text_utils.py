"""
Utilitários para processamento de texto.
"""

import logging
import unicodedata
import re
from langdetect import detect
from deep_translator import GoogleTranslator

logger = logging.getLogger(__name__)


def normalizar_texto(texto: str) -> str:
    """Normaliza texto removendo acentos e convertendo para minúsculas."""
    texto = texto.lower()
    texto = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('ASCII')
    return texto


def detectar_idioma(texto: str) -> str:
    """
    Detecta o idioma do texto.
    Assume português para textos curtos ou com nomes próprios.
    """
    try:
        # Para textos muito curtos, assume português
        if len(texto.split()) <= 3:
            return "pt"

        idioma = detect(texto)

        # Se detectou idioma estranho mas tem palavras em português, corrige
        if idioma not in ["pt", "en", "es", "fr"]:
            palavras_pt = ["qual", "quem", "como", "por", "que", "quando", "onde", "foi", "é", "são"]
            texto_lower = texto.lower()
            if any(palavra in texto_lower for palavra in palavras_pt):
                return "pt"

        return idioma
    except:
        return "pt"


def traduzir(texto: str, origem: str = "auto", destino: str = "pt") -> str:
    """
    Traduz texto entre idiomas com melhorias para evitar perda de sentido.
    """
    try:
        if not texto or origem == destino:
            return texto

        # Remove espaços extras antes de traduzir
        texto = texto.strip()

        # Traduz
        traducao = GoogleTranslator(source=origem, target=destino).translate(texto)

        if not traducao:
            return texto

        logger.info(f"Tradução ({origem}->{destino}): '{texto[:50]}...' -> '{traducao[:50]}...'")

        # Capitaliza primeira letra
        traducao = traducao.strip()
        if traducao:
            return traducao[0].upper() + traducao[1:] if len(traducao) > 1 else traducao.upper()

        return texto
    except Exception as e:
        logger.error(f"Erro ao traduzir: {str(e)}")
        return texto


def limpar_texto(texto: str) -> str:
    """Remove formatação ruim, espaços extras, datas, URLs e emojis."""
    if not texto:
        return ""

    # Remove URLs
    texto = re.sub(r'https?://\S+|www\.\S+', '', texto)

    # Remove emojis e caracteres especiais Unicode
    texto = re.sub(r'[^\w\s\.,!?;:()\-áàâãéèêíïóôõöúçñÁÀÂÃÉÈÊÍÏÓÔÕÖÚÇÑ]', '', texto)

    # Remove datas no formato "DD de MMM de YYYY" ou variações
    texto = re.sub(r'\d{1,2}\s+de\s+\w+\s+de\s+\d{4}', '', texto)
    texto = re.sub(r'\d{1,2}\s+de\s+\w+,?\s+\d{4}', '', texto)
    texto = re.sub(r'[A-Z][a-z]{2}\s+\d{1,2},\s+\d{4}', '', texto)

    # Remove padrões como "Oct 28, 2020 ..."
    texto = re.sub(r'[A-Z][a-z]{2}\s+\d{1,2},\s+\d{4}\s*\.{3}', '', texto)

    # Remove múltiplas reticências
    texto = re.sub(r'\.{2,}', '.', texto)

    # Remove múltiplos espaços e quebras de linha
    texto = re.sub(r'\s+', ' ', texto).strip()

    # Remove caracteres de controle ASCII
    texto = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', texto)

    return texto


def extrair_sentencas(texto: str, max_sentencas: int = None) -> list:
    """
    Extrai sentenças de um texto.
    Retorna lista de sentenças completas.
    """
    if not texto:
        return []

    texto = limpar_texto(texto)

    # Separa em sentenças de forma mais robusta
    # Considera . ! ? seguidos de espaço e letra maiúscula
    sentencas = re.split(r'(?<=[.!?])\s+(?=[A-Z])', texto)

    # Filtra sentenças muito curtas (menos de 10 caracteres)
    sentencas = [s.strip() for s in sentencas if len(s.strip()) > 10]

    if max_sentencas:
        sentencas = sentencas[:max_sentencas]

    return sentencas


def juntar_sentencas(sentencas: list) -> str:
    """Junta sentenças em um único texto."""
    if not sentencas:
        return ""

    texto = ' '.join(sentencas)

    # Garante que termina com pontuação
    if texto and texto[-1] not in '.!?':
        texto += '.'

    return texto


def limitar_texto(texto: str, max_chars: int = 500) -> str:
    """
    Limita texto a um número máximo de caracteres,
    cortando em fronteiras de sentenças quando possível.
    """
    if not texto or len(texto) <= max_chars:
        return texto

    sentencas = extrair_sentencas(texto)

    resultado = []
    tamanho_atual = 0

    for sentenca in sentencas:
        if tamanho_atual + len(sentenca) + 1 <= max_chars:
            resultado.append(sentenca)
            tamanho_atual += len(sentenca) + 1
        else:
            break

    return juntar_sentencas(resultado)
"""
Testes para utilitários de texto.
"""

import pytest
from bot.utils.text_utils import (
    normalizar_texto,
    detectar_idioma,
    traduzir,
    limpar_texto,
    extrair_sentencas,
    juntar_sentencas,
    limitar_texto
)

class TestNormalizarTexto:
    """Testes para normalizar_texto."""

    def test_remove_acentos(self):
        assert normalizar_texto("José") == "jose"
        assert normalizar_texto("çãõ") == "cao"

    def test_converte_minuscula(self):
        assert normalizar_texto("MAIÚSCULA") == "maiuscula"

    def test_mantem_espacos(self):
        assert normalizar_texto("oi tudo bem") == "oi tudo bem"

    def test_texto_vazio(self):
        assert normalizar_texto("") == ""

class TestDetectarIdioma:
    """Testes para detectar_idioma."""

    def test_portugues(self):
        assert detectar_idioma("Olá, como vai você?") == "pt"

    def test_ingles(self):
        assert detectar_idioma("Hello, how are you?") == "en"

    def test_espanhol(self):
        assert detectar_idioma("Hola, cómo estás?") == "es"

    def test_texto_curto_assume_portugues(self):
        assert detectar_idioma("oi") == "pt"

    def test_texto_vazio_assume_portugues(self):
        assert detectar_idioma("") == "pt"

class TestTraduzir:
    """Testes para traduzir."""

    @pytest.mark.api
    def test_traduz_en_para_pt(self):
        resultado = traduzir("Hello world", origem="en", destino="pt")
        assert "mundo" in resultado.lower() or "olá" in resultado.lower()

    @pytest.mark.api
    def test_traduz_pt_para_en(self):
        resultado = traduzir("Olá mundo", origem="pt", destino="en")
        assert "hello" in resultado.lower() or "world" in resultado.lower()

    def test_mesmo_idioma_retorna_original(self):
        texto = "Não precisa traduzir"
        assert traduzir(texto, origem="pt", destino="pt") == texto

    def test_texto_vazio(self):
        assert traduzir("", origem="en", destino="pt") == ""

    def test_capitaliza_primeira_letra(self):
        resultado = traduzir("hello", origem="en", destino="pt")
        assert resultado[0].isupper()

class TestLimparTexto:
    """Testes para limpar_texto."""

    def test_remove_urls(self):
        texto = "Veja mais em https://example.com aqui"
        resultado = limpar_texto(texto)
        assert "https" not in resultado
        assert "example.com" not in resultado

    def test_remove_datas(self):
        texto = "Em 25 de dezembro de 2023 aconteceu isso"
        resultado = limpar_texto(texto)
        assert "25 de dezembro de 2023" not in resultado

    def test_remove_espacos_extras(self):
        texto = "muito    espaço    aqui"
        resultado = limpar_texto(texto)
        assert "  " not in resultado

    def test_remove_reticencias_multiplas(self):
        texto = "Isso é.... interessante..."
        resultado = limpar_texto(texto)
        assert "..." not in resultado

    def test_texto_vazio(self):
        assert limpar_texto("") == ""

class TestExtrairSentencas:
    """Testes para extrair_sentencas."""

    def test_extrai_sentencas_simples(self):
        texto = "Primeira sentença. Segunda sentença. Terceira sentença."
        sentencas = extrair_sentencas(texto)
        assert len(sentencas) == 3

    def test_filtra_sentencas_curtas(self):
        texto = "OK. Esta é uma sentença normal. Sim."
        sentencas = extrair_sentencas(texto)
        assert len(sentencas) == 1  # Só a do meio

    def test_limita_numero_sentencas(self):
        texto = "Um. Dois. Três. Quatro. Cinco. Seis."
        sentencas = extrair_sentencas(texto, max_sentencas=3)
        assert len(sentencas) == 3

    def test_texto_vazio(self):
        assert extrair_sentencas("") == []

class TestJuntarSentencas:
    """Testes para juntar_sentencas."""

    def test_junta_com_espacos(self):
        sentencas = ["Primeira", "Segunda", "Terceira"]
        resultado = juntar_sentencas(sentencas)
        assert resultado == "Primeira Segunda Terceira."

    def test_adiciona_ponto_final(self):
        sentencas = ["Sem ponto"]
        resultado = juntar_sentencas(sentencas)
        assert resultado.endswith(".")

    def test_lista_vazia(self):
        assert juntar_sentencas([]) == ""

class TestLimitarTexto:
    """Testes para limitar_texto."""

    def test_limita_por_sentencas(self):
        texto = "Primeira sentença muito longa. Segunda sentença. Terceira sentença."
        resultado = limitar_texto(texto, max_chars=50)
        assert len(resultado) <= 50

    def test_mantem_texto_curto(self):
        texto = "Texto curto."
        resultado = limitar_texto(texto, max_chars=100)
        assert resultado == texto
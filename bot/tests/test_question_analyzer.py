"""
Testes para o analisador de perguntas.
"""

import pytest
from bot.utils.question_analyzer import AnalisadorPergunta

class TestDetectarIntencao:
    """Testes para detectar_intencao."""

    def test_saudacao(self, analisador):
        assert analisador.detectar_intencao("Oi") == "saudacao"
        assert analisador.detectar_intencao("Olá, tudo bem?") == "saudacao"
        assert analisador.detectar_intencao("Bom dia!") == "saudacao"

    def test_status(self, analisador):
        assert analisador.detectar_intencao("Como você está?") == "status"
        assert analisador.detectar_intencao("Tudo bem?") == "status"

    def test_nome(self, analisador):
        assert analisador.detectar_intencao("Qual seu nome?") == "nome"
        assert analisador.detectar_intencao("Como você se chama?") == "nome"

    def test_conhecimento(self, analisador):
        assert analisador.detectar_intencao("Qual a capital da França?") == "conhecimento"
        assert analisador.detectar_intencao("Como funciona a fotossíntese?") == "conhecimento"

class TestDetectarTipoPergunta:
    """Testes para detectar_tipo_pergunta."""

    def test_qual(self, analisador):
        assert analisador.detectar_tipo_pergunta("Qual a capital?") == "qual"
        assert analisador.detectar_tipo_pergunta("Quais são os planetas?") == "qual"

    def test_quem(self, analisador):
        assert analisador.detectar_tipo_pergunta("Quem descobriu o Brasil?") == "quem"

    def test_quando(self, analisador):
        assert analisador.detectar_tipo_pergunta("Quando aconteceu?") == "quando"

    def test_onde(self, analisador):
        assert analisador.detectar_tipo_pergunta("Onde fica Paris?") == "onde"

    def test_como(self, analisador):
        assert analisador.detectar_tipo_pergunta("Como funciona isso?") == "como"

    def test_porque(self, analisador):
        assert analisador.detectar_tipo_pergunta("Por que o céu é azul?") == "porque"

    def test_quanto(self, analisador):
        assert analisador.detectar_tipo_pergunta("Quantos países existem?") == "quanto"

    def test_geral(self, analisador):
        assert analisador.detectar_tipo_pergunta("Me fale sobre isso") == "geral"

class TestExtrairPalavrasChave:
    """Testes para extrair_palavras_chave."""

    def test_extrai_substantivos(self, analisador):
        palavras = analisador.extrair_palavras_chave("Qual a capital da França?")
        assert "capital" in palavras or "frança" in palavras.lower()

    def test_limita_quantidade(self, analisador):
        texto = " ".join([f"palavra{i}" for i in range(20)])
        palavras = analisador.extrair_palavras_chave(texto, max_palavras=5)
        assert len(palavras) <= 5

class TestCriarQueryBusca:
    """Testes para criar_query_busca."""

    def test_mantem_pergunta_curta(self, analisador):
        pergunta = "Qual a capital?"
        query = analisador.criar_query_busca(pergunta)
        assert query == pergunta

    def test_simplifica_pergunta_longa(self, analisador):
        pergunta = "Eu gostaria de saber qual é exatamente a capital da França?"
        query = analisador.criar_query_busca(pergunta)
        assert len(query) < len(pergunta)
        assert "frança" in query.lower() or "capital" in query.lower()

class TestPerguntas:
    """Testes de classificação de perguntas."""

    def test_e_pergunta_factual(self, analisador):
        assert analisador.e_pergunta_factual("Qual a capital?") == True
        assert analisador.e_pergunta_factual("Quem foi Einstein?") == True
        assert analisador.e_pergunta_factual("Como funciona?") == False

    def test_e_pergunta_explicativa(self, analisador):
        assert analisador.e_pergunta_explicativa("Como funciona?") == True
        assert analisador.e_pergunta_explicativa("Por que acontece?") == True
        assert analisador.e_pergunta_explicativa("Qual é?") == False
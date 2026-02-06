"""
Testes para o analisador avançado.
"""

import pytest
from bot.utils.advanced_analyzer import AnalisadorAvancado

class TestExtrairEntidades:
    """Testes para extrair_entidades."""

    def test_extrai_pessoa(self, analisador_avancado):
        entidades = analisador_avancado.extrair_entidades("Albert Einstein foi um físico")
        # spaCy pode ou não detectar dependendo do contexto
        assert "PERSON" in entidades or "MISC" in entidades

    def test_extrai_local(self, analisador_avancado):
        entidades = analisador_avancado.extrair_entidades("Paris é a capital da França")
        # Deve detectar Paris e/ou França
        assert any(entidades.values())

class TestDetectarTipoEspecializado:
    """Testes para detectar_tipo_especializado."""

    def test_calculo(self, analisador_avancado):
        assert analisador_avancado.detectar_tipo_especializado("Quanto é 2 + 2?") == "calculo"
        assert analisador_avancado.detectar_tipo_especializado("Calcule 10 * 5") == "calculo"

    def test_conversao(self, analisador_avancado):
        assert analisador_avancado.detectar_tipo_especializado("Converta 10 km em metros") == "conversao"

    def test_comparacao(self, analisador_avancado):
        assert analisador_avancado.detectar_tipo_especializado("Qual a diferença entre X e Y?") == "comparacao"

    def test_definicao(self, analisador_avancado):
        assert analisador_avancado.detectar_tipo_especializado("O que é fotossíntese?") == "definicao"

    def test_processo(self, analisador_avancado):
        assert analisador_avancado.detectar_tipo_especializado("Como funciona um motor?") == "processo"

    def test_geral(self, analisador_avancado):
        assert analisador_avancado.detectar_tipo_especializado("Me fale sobre isso") == "geral"

class TestExtrairNumerosUnidades:
    """Testes para extrair_numeros_e_unidades."""

    def test_extrai_numeros(self, analisador_avancado):
        resultado = analisador_avancado.extrair_numeros_e_unidades("Converta 10 metros em centímetros")
        assert 10.0 in resultado["numeros"]

    def test_extrai_unidades(self, analisador_avancado):
        resultado = analisador_avancado.extrair_numeros_e_unidades("Converta 10 metros em centímetros")
        assert "metro" in resultado["unidades"] or "centímetro" in resultado["unidades"]

    def test_detecta_calculo(self, analisador_avancado):
        resultado = analisador_avancado.extrair_numeros_e_unidades("Quanto é 2 + 3?")
        assert resultado["tem_calculo"] == True

class TestAnalisarComplexidade:
    """Testes para analisar_complexidade."""

    def test_pergunta_simples(self, analisador_avancado):
        resultado = analisador_avancado.analisar_complexidade("Qual a capital?")
        assert resultado["complexidade"] == "simples"

    def test_pergunta_media(self, analisador_avancado):
        resultado = analisador_avancado.analisar_complexidade("Como funciona a fotossíntese nas plantas?")
        assert resultado["complexidade"] in ["media", "complexa"]

    def test_pergunta_complexa(self, analisador_avancado):
        resultado = analisador_avancado.analisar_complexidade(
            "Explique detalhadamente como funciona o processo de fotossíntese e qual sua importância para o ecossistema"
        )
        assert resultado["complexidade"] == "complexa"

class TestDecomporPergunta:
    """Testes para decompor_pergunta_complexa."""

    def test_decompoe_pergunta_com_e(self, analisador_avancado):
        pergunta = "Quem inventou a internet e quando?"
        subperguntas = analisador_avancado.decompor_pergunta_complexa(pergunta)
        assert len(subperguntas) >= 2

    def test_nao_decompoe_simples(self, analisador_avancado):
        pergunta = "Qual a capital?"
        subperguntas = analisador_avancado.decompor_pergunta_complexa(pergunta)
        assert subperguntas == [pergunta]

class TestIdentificarContextoTemporal:
    """Testes para identificar_contexto_temporal."""

    def test_contexto_atual(self, analisador_avancado):
        resultado = analisador_avancado.identificar_contexto_temporal("Qual o preço atual do dólar?")
        assert resultado["contexto_temporal"] == "atual"

    def test_contexto_historico(self, analisador_avancado):
        resultado = analisador_avancado.identificar_contexto_temporal("Quando foi descoberto o Brasil?")
        assert resultado["contexto_temporal"] == "historico"

    def test_contexto_neutro(self, analisador_avancado):
        resultado = analisador_avancado.identificar_contexto_temporal("Qual a capital da França?")
        assert resultado["contexto_temporal"] == "neutro"
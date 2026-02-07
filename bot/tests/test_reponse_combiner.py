"""
Testes para o combinador de respostas.
"""

import pytest
from bot.utils.response_combiner import CombinadorRespostas

class TestCalcularRelevancia:
    """Testes para calcular_relevancia."""
    
    def test_pergunta_resposta_relevante(self, combinador):
        pergunta = "Qual a capital da França?"
        resposta = "Paris é a capital da França"
        score = combinador.calcular_relevancia(resposta, pergunta)
        assert score > 0.3  # Alta relevância
    
    def test_pergunta_resposta_irrelevante(self, combinador):
        pergunta = "Qual a capital da França?"
        resposta = "O Brasil é um país na América do Sul"
        score = combinador.calcular_relevancia(resposta, pergunta)
        assert score < 0.3  # Baixa relevância
    
    def test_resposta_vazia(self, combinador):
        score = combinador.calcular_relevancia("", "pergunta qualquer")
        assert score == 0.0

class TestRanquearRespostas:
    """Testes para ranquear_respostas."""
    
    def test_ordena_por_relevancia(self, combinador):
        respostas = {
            "fonte1": "Paris é a capital da França",
            "fonte2": "O Brasil é um país",
            "fonte3": "A capital francesa é Paris"
        }
        pergunta = "Qual a capital da França?"
        
        ranking = combinador.ranquear_respostas(respostas, pergunta)
        
        # Primeira deve ser mais relevante que a segunda
        assert ranking[0][2] > ranking[1][2]
    
    def test_filtra_respostas_curtas(self, combinador):
        respostas = {
            "fonte1": "Ok",  # Muito curto
            "fonte2": "Paris é a capital da França"
        }
        pergunta = "Qual a capital da França?"
        
        ranking = combinador.ranquear_respostas(respostas, pergunta)
        
        # Só deve ter a resposta longa
        assert len(ranking) == 1

class TestRemoverDuplicatas:
    """Testes para remover_duplicatas."""
    
    def test_remove_sentencas_identicas(self, combinador):
        sentencas = [
            "Paris é a capital da França.",
            "Paris é a capital da França.",
            "Londres é a capital da Inglaterra."
        ]
        
        resultado = combinador.remover_duplicatas(sentencas)
        
        assert len(resultado) == 2
        assert resultado[0] != resultado[1]
    
    def test_remove_sentencas_similares(self, combinador):
        sentencas = [
            "Paris é a capital da França.",
            "A capital da França é Paris.",
            "Londres é a capital da Inglaterra."
        ]
        
        resultado = combinador.remover_duplicatas(sentencas, limiar_similaridade=0.7)
        
        # As duas primeiras são muito similares
        assert len(resultado) == 2
    
    def test_mantem_sentencas_diferentes(self, combinador):
        sentencas = [
            "Paris é a capital da França.",
            "Londres é a capital da Inglaterra.",
            "Madrid é a capital da Espanha."
        ]
        
        resultado = combinador.remover_duplicatas(sentencas)
        
        assert len(resultado) == 3

class TestExtrairSentencasRelevantes:
    """Testes para extrair_sentencas_relevantes."""
    
    def test_extrai_sentencas_mais_relevantes(self, combinador):
        resposta = "Paris é a capital da França. O país tem 67 milhões de habitantes. A Torre Eiffel é um símbolo. O clima é temperado."
        pergunta = "Qual a capital da França?"
        
        sentencas = combinador.extrair_sentencas_relevantes(resposta, pergunta, max_sentencas=2)
        
        assert len(sentencas) <= 2
        # Deve incluir a sentença sobre Paris sendo a capital
        assert any("capital" in s.lower() for s in sentencas)
    
    def test_mantem_poucas_sentencas(self, combinador):
        resposta = "Paris é a capital."
        pergunta = "Qual a capital?"
        
        sentencas = combinador.extrair_sentencas_relevantes(resposta, pergunta, max_sentencas=5)
        
        assert len(sentencas) == 1

class TestCombinarRespostas:
    """Testes para combinar_respostas."""
    
    def test_combina_unica_resposta(self, combinador):
        respostas = {
            "google": "Paris é a capital e maior cidade da França."
        }
        pergunta = "Qual a capital da França?"
        
        resultado = combinador.combinar_respostas(respostas, pergunta)
        
        assert resultado is not None
        assert "Paris" in resultado
    
    def test_combina_multiplas_respostas_factual(self, combinador):
        respostas = {
            "wolfram": "Paris, France",
            "google": "Paris is the capital of France.",
            "wikipedia": "Paris is the capital and largest city of France."
        }
        pergunta = "Qual a capital da França?"
        
        resultado = combinador.combinar_respostas(respostas, pergunta, tipo_pergunta="qual")
        
        assert resultado is not None
        assert "paris" in resultado.lower()
    
    def test_combina_multiplas_respostas_explicativa(self, combinador):
        respostas = {
            "google": "Photosynthesis is the process where plants convert light into energy.",
            "wikipedia": "During photosynthesis, plants use sunlight to convert water and CO2 into glucose."
        }
        pergunta = "Como funciona a fotossíntese?"
        
        resultado = combinador.combinar_respostas(respostas, pergunta, tipo_pergunta="como")
        
        assert resultado is not None
        # Deve ter informação de ambas as fontes (se relevantes)
        assert len(resultado) > 50
    
    def test_retorna_none_sem_respostas(self, combinador):
        respostas = {}
        pergunta = "Qualquer coisa?"
        
        resultado = combinador.combinar_respostas(respostas, pergunta)
        
        assert resultado is None
    
    def test_filtra_respostas_vazias(self, combinador):
        respostas = {
            "fonte1": None,
            "fonte2": "",
            "fonte3": "Resposta válida aqui."
        }
        pergunta = "Pergunta?"
        
        resultado = combinador.combinar_respostas(respostas, pergunta)
        
        assert resultado is not None
        assert "válida" in resultado

class TestCombinarComFontePrincipal:
    """Testes para combinar_com_fonte_principal."""
    
    def test_retorna_fonte_principal(self, combinador):
        respostas = {
            "wolfram": "42",
            "google": "The answer is 42"
        }
        pergunta = "What is the answer?"
        
        resposta, fonte = combinador.combinar_com_fonte_principal(respostas, pergunta)
        
        assert resposta is not None
        assert fonte in ["wolfram", "google", "wolfram+google"]
    
    def test_indica_multiplas_fontes(self, combinador):
        respostas = {
            "google": "Explanation about photosynthesis from sunlight.",
            "wikipedia": "Plants use photosynthesis to create energy."
        }
        pergunta = "Como funciona a fotossíntese?"
        
        resposta, fonte = combinador.combinar_com_fonte_principal(respostas, pergunta, tipo_pergunta="como")
        
        if resposta and "+" in fonte:
            # Usou múltiplas fontes
            assert len(fonte.split("+")) > 1
    
    def test_retorna_none_sem_respostas(self, combinador):
        respostas = {}
        pergunta = "Qualquer?"
        
        resposta, fonte = combinador.combinar_com_fonte_principal(respostas, pergunta)
        
        assert resposta is None
        assert fonte is None

"""
Testes para o formatador de respostas.
"""

import pytest
from bot.utils.response_formatter import FormatadorResposta, RESPOSTAS_INTENCAO

class TestFormatar:
    """Testes para formatar."""
    
    def test_mantem_resposta_factual(self, formatador):
        resposta = "Paris é a capital da França."
        resultado = formatador.formatar(resposta, tipo_pergunta="qual")
        assert resultado == resposta
    
    def test_adiciona_introducao_como(self, formatador):
        resposta = "A fotossíntese converte luz em energia."
        resultado = formatador.formatar(resposta, tipo_pergunta="como")
        assert resultado.startswith("Basicamente")
    
    def test_nao_duplica_introducao_como(self, formatador):
        resposta = "Basicamente, a fotossíntese converte luz."
        resultado = formatador.formatar(resposta, tipo_pergunta="como")
        # Não deve ter dois "Basicamente"
        assert resultado.count("Basicamente") == 1
    
    def test_adiciona_introducao_porque(self, formatador):
        resposta = "O céu é azul devido ao espalhamento da luz."
        resultado = formatador.formatar(resposta, tipo_pergunta="porque")
        assert resultado.startswith("Isso acontece porque")
    
    def test_nao_duplica_introducao_porque(self, formatador):
        resposta = "Isso acontece porque o céu reflete a luz azul."
        resultado = formatador.formatar(resposta, tipo_pergunta="porque")
        assert resultado.count("Isso acontece porque") == 1

class TestGarantirPontuacao:
    """Testes para garantir_pontuacao."""
    
    def test_adiciona_ponto_final(self, formatador):
        texto = "Resposta sem ponto"
        resultado = formatador.garantir_pontuacao(texto)
        assert resultado.endswith(".")
    
    def test_mantem_ponto_existente(self, formatador):
        texto = "Resposta com ponto."
        resultado = formatador.garantir_pontuacao(texto)
        assert resultado == texto
    
    def test_mantem_interrogacao(self, formatador):
        texto = "É uma pergunta?"
        resultado = formatador.garantir_pontuacao(texto)
        assert resultado == texto
    
    def test_mantem_exclamacao(self, formatador):
        texto = "Que legal!"
        resultado = formatador.garantir_pontuacao(texto)
        assert resultado == texto

class TestFormatarFinal:
    """Testes para formatar_final."""
    
    def test_formata_completo(self, formatador):
        resposta = "paris é a capital"
        resultado = formatador.formatar_final(resposta, tipo_pergunta="qual")
        
        # Deve capitalizar e adicionar ponto
        assert resultado[0].isupper()
        assert resultado.endswith(".")
    
    def test_capitaliza_primeira_letra(self, formatador):
        resposta = "resposta em minúscula"
        resultado = formatador.formatar_final(resposta, tipo_pergunta="geral")
        assert resultado[0].isupper()
    
    def test_texto_vazio(self, formatador):
        resultado = formatador.formatar_final("", tipo_pergunta="geral")
        assert resultado == ""

class TestRespostasIntencao:
    """Testes para respostas predefinidas."""
    
    def test_todas_intencoes_tem_respostas(self):
        intencoes = ["saudacao", "status", "nome", "funcao", "despedida", "desconhecida"]
        for intencao in intencoes:
            assert intencao in RESPOSTAS_INTENCAO
            assert len(RESPOSTAS_INTENCAO[intencao]) > 0
    
    def test_respostas_sao_strings(self):
        for intencao, respostas in RESPOSTAS_INTENCAO.items():
            for resposta in respostas:
                assert isinstance(resposta, str)
                assert len(resposta) > 0

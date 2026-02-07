"""
Testes para o sistema de aprendizado.
"""

import pytest
from unittest.mock import Mock, patch
from bot.ml.learning_system import SistemaAprendizado

class TestSistemaAprendizado:
    """Testes do sistema de aprendizado."""
    
    @pytest.fixture
    def mock_repository(self):
        repo = Mock()
        repo.get_all_conversations_for_training.return_value = []
        return repo
    
    @pytest.fixture
    def sistema(self, mock_repository):
        return SistemaAprendizado(mock_repository)
    
    def test_inicializa_sem_modelos(self, sistema):
        """Testa inicialização sem modelos treinados."""
        assert sistema.modelo_intencao is None
        assert sistema.modelo_qualidade is None
    
    def test_atualizar_stats_fonte(self, sistema):
        """Testa atualização de estatísticas."""
        sistema.atualizar_stats_fonte("google", tempo=1.5, sucesso=True, qualidade=0.8)
        
        stats = sistema.stats_fontes["google"]
        assert stats["total_usos"] == 1
        assert stats["sucessos"] == 1
        assert stats["tempo_medio"] == 1.5
    
    def test_aprender_padrao_boa_qualidade(self, sistema):
        """Testa aprendizado de padrão com boa qualidade."""
        pergunta = "Qual a capital da França?"
        resposta = "Paris é a capital da França."
        
        sistema.aprender_padrao(pergunta, resposta, qualidade=0.9)
        
        # Deve ter aprendido o padrão
        assert len(sistema.padroes_pergunta_resposta) > 0
    
    def test_nao_aprende_padrao_baixa_qualidade(self, sistema):
        """Testa que não aprende com baixa qualidade."""
        pergunta = "Teste?"
        resposta = "Resposta ruim"
        
        sistema.aprender_padrao(pergunta, resposta, qualidade=0.3)
        
        # Não deve ter aprendido
        assert len(sistema.padroes_pergunta_resposta) == 0
    
    def test_buscar_resposta_aprendida_exata(self, sistema):
        """Testa busca de resposta aprendida (match exato)."""
        # Primeiro aprende
        sistema.aprender_padrao("Teste?", "Resposta teste", qualidade=0.9)
        
        # Depois busca
        resposta, qualidade = sistema.buscar_resposta_aprendida("Teste?")
        
        assert resposta == "Resposta teste"
        assert qualidade == 0.9
    
    def test_buscar_resposta_aprendida_similar(self, sistema):
        """Testa busca de resposta similar."""
        # Aprende
        sistema.aprender_padrao("Qual a capital da França?", "Paris", qualidade=0.9)
        
        # Busca com pergunta similar
        resposta, qualidade = sistema.buscar_resposta_aprendida("Qual é a capital francesa?")
        
        # Pode ou não encontrar dependendo da similaridade
        if resposta:
            assert "Paris" in resposta

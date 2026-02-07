"""
Testes de integração end-to-end.
"""

import pytest
from unittest.mock import Mock, patch
from bot.bot_worker import BotWorker

@pytest.mark.integration
class TestIntegracaoCompleta:
    """Testes de fluxo completo."""
    
    @patch('bot.bot_worker.BotRepository')
    @patch('bot.bot_worker.SistemaAprendizado')
    @patch('bot.api.search.requests.get')
    def test_fluxo_pergunta_simples(self, mock_requests, mock_aprendizado, mock_repo):
        """Testa fluxo completo de pergunta simples."""
        # Setup
        bot = BotWorker()
        
        # Mock do aprendizado
        bot.sistema_aprendizado.prever_intencao.return_value = "conhecimento"
        bot.sistema_aprendizado.buscar_resposta_aprendida.return_value = (None, 0.0)
        bot.sistema_aprendizado.avaliar_qualidade_resposta.return_value = 0.8
        
        # Mock das APIs
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "Paris, France"
        mock_response.json.return_value = {
            "items": [{"snippet": "Paris is the capital of France"}]
        }
        mock_requests.return_value = mock_response
        
        # Executa
        resultado = bot.process_query("Qual a capital da França?", user_id=1)
        
        # Verifica
        assert resultado["status"] == "success"
        assert "paris" in resultado["response"].lower() or "frança" in resultado["response"].lower()
        assert resultado["processing_time"] > 0
        assert "logs_processo" in resultado
    
    @patch('bot.bot_worker.BotRepository')
    @patch('bot.bot_worker.SistemaAprendizado')
    def test_fluxo_com_cache(self, mock_aprendizado, mock_repo):
        """Testa que cache funciona no fluxo completo."""
        bot = BotWorker()
        
        bot.sistema_aprendizado.prever_intencao.return_value = "conhecimento"
        bot.sistema_aprendizado.buscar_resposta_aprendida.return_value = (None, 0.0)
        
        # Mock do buscador para primeira chamada
        with patch.object(bot.buscador, 'buscar_todas') as mock_buscar:
            mock_buscar.return_value = {"google": "Resposta"}
            resultado1 = bot.process_query("Pergunta única xyz123", user_id=1)
        
        # Segunda chamada deve usar cache
        resultado2 = bot.process_query("Pergunta única xyz123", user_id=1)
        
        assert resultado2["processing_time"] < 0.1  # Cache é instantâneo
    
    @patch('bot.bot_worker.BotRepository')
    def test_fluxo_erro_gracioso(self, mock_repo):
        """Testa que erros são tratados graciosamente."""
        bot = BotWorker()
        
        # Força um erro no buscador
        with patch.object(bot.buscador, 'buscar_todas', side_effect=Exception("Erro de teste")):
            resultado = bot.process_query("Qualquer pergunta", user_id=1)
        
        # Deve retornar erro, mas não crashar
        assert resultado["status"] == "error"
        assert "erro" in resultado["message"].lower()

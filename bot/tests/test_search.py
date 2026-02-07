"""
Testes para as APIs de busca.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from bot.api.search import BuscadorAPI

class TestBuscadorAPI:
    """Testes para o BuscadorAPI."""
    
    @pytest.fixture
    def buscador(self):
        return BuscadorAPI(
            wolfram_app_id="test_wolfram",
            google_cx="test_cx",
            google_api_key="test_key"
        )
    
    @pytest.mark.api
    @pytest.mark.slow
    def test_buscar_wolfram_real(self, buscador):
        """Teste real (pode falhar sem credenciais válidas)."""
        resultado = buscador.buscar_wolfram("what is 2+2")
        # Se tiver credenciais válidas, deve retornar algo
        if resultado:
            assert len(resultado) > 0
    
    @patch('bot.api.search.requests.get')
    def test_buscar_wolfram_mock(self, mock_get, buscador):
        """Teste com mock."""
        # Simula resposta da API
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "4"
        mock_get.return_value = mock_response
        
        resultado = buscador.buscar_wolfram("what is 2+2")
        
        assert resultado == "4"
        mock_get.assert_called_once()
    
    @patch('bot.api.search.requests.get')
    def test_buscar_wolfram_erro(self, mock_get, buscador):
        """Teste de tratamento de erro."""
        mock_get.side_effect = Exception("Network error")
        
        resultado = buscador.buscar_wolfram("query")
        
        assert resultado is None
    
    @patch('bot.api.search.requests.get')
    def test_buscar_google_mock(self, mock_get, buscador):
        """Teste Google com mock."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "items": [
                {"snippet": "Result 1"},
                {"snippet": "Result 2"}
            ]
        }
        mock_get.return_value = mock_response
        
        resultado = buscador.buscar_google("test query")
        
        assert "Result 1" in resultado
        assert "Result 2" in resultado
    
    @patch('bot.api.search.requests.get')
    def test_buscar_google_sem_resultados(self, mock_get, buscador):
        """Teste Google sem resultados."""
        mock_response = Mock()
        mock_response.json.return_value = {"items": []}
        mock_get.return_value = mock_response
        
        resultado = buscador.buscar_google("test query")
        
        assert resultado is None
    
    @patch('bot.api.search.requests.get')
    def test_buscar_duckduckgo_abstract(self, mock_get, buscador):
        """Teste DuckDuckGo com AbstractText."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "AbstractText": "This is a detailed abstract with more than 50 characters to pass the filter."
        }
        mock_get.return_value = mock_response
        
        resultado = buscador.buscar_duckduckgo("test query")
        
        assert resultado is not None
        assert len(resultado) > 50
    
    @patch('bot.api.search.requests.get')
    def test_buscar_wikipedia_mock(self, mock_get, buscador):
        """Teste Wikipedia com mock."""
        # Mock para a busca
        mock_search_response = Mock()
        mock_search_response.status_code = 200
        mock_search_response.json.return_value = {
            "query": {
                "search": [
                    {"title": "Test Article"}
                ]
            }
        }
        
        # Mock para o conteúdo
        mock_content_response = Mock()
        mock_content_response.status_code = 200
        mock_content_response.json.return_value = {
            "extract": "This is a test article with enough content to be valid and useful for the test."
        }
        
        mock_get.side_effect = [mock_search_response, mock_content_response]
        
        resultado = buscador.buscar_wikipedia("test query")
        
        assert resultado is not None
        assert "test article" in resultado.lower()
    
    @patch('bot.api.search.requests.get')
    def test_buscar_todas_paralelo(self, mock_get, buscador):
        """Teste de busca paralela em todas as APIs."""
        # Mock de resposta genérica
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "Result"
        mock_response.json.return_value = {"items": []}
        mock_get.return_value = mock_response
        
        resultados = buscador.buscar_todas("test query", timeout=5)
        
        # Deve ter tentado buscar em todas as 4 fontes
        assert len(resultados) == 4
        assert "wolfram" in resultados
        assert "google" in resultados
        assert "duckduckgo" in resultados
        assert "wikipedia" in resultados
    
    def test_buscar_melhor_ordem_preferencia(self, buscador):
        """Teste da ordem de preferência de fontes."""
        # Simula resultados
        with patch.object(buscador, 'buscar_todas') as mock_buscar:
            mock_buscar.return_value = {
                "wolfram": "Wolfram result",
                "google": "Google result",
                "wikipedia": None,
                "duckduckgo": None
            }
            
            resposta, fonte = buscador.buscar_melhor("test")
            
            # Wolfram tem prioridade
            assert fonte == "wolfram"
            assert resposta == "Wolfram result"
    
    def test_buscar_melhor_fallback(self, buscador):
        """Teste de fallback para outras fontes."""
        with patch.object(buscador, 'buscar_todas') as mock_buscar:
            mock_buscar.return_value = {
                "wolfram": None,
                "wikipedia": None,
                "google": "Google result",
                "duckduckgo": "DuckDuckGo result"
            }
            
            resposta, fonte = buscador.buscar_melhor("test")
            
            # Google vem antes do DuckDuckGo na ordem
            assert fonte == "google"

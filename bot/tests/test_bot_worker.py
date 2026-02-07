"""
Testes para o BotWorker principal.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from bot.bot_worker import BotWorker

class TestBotWorkerInit:
    """Testes de inicialização."""
    
    @patch('bot.bot_worker.BotRepository')
    @patch('bot.bot_worker.SistemaAprendizado')
    def test_inicializa_componentes(self, mock_aprendizado, mock_repo):
        """Testa se todos os componentes são inicializados."""
        bot = BotWorker()
        
        assert bot.buscador is not None
        assert bot.analisador is not None
        assert bot.combinador is not None
        assert bot.formatador is not None
        assert bot.repository is not None

class TestValidateInput:
    """Testes de validação de entrada."""
    
    @patch('bot.bot_worker.BotRepository')
    def test_aceita_mensagem_valida(self, mock_repo):
        bot = BotWorker()
        valido, mensagem = bot._validate_input("Qual a capital da França?")
        assert valido == True
    
    @patch('bot.bot_worker.BotRepository')
    def test_rejeita_mensagem_longa(self, mock_repo):
        bot = BotWorker()
        mensagem_longa = "a" * 501
        valido, mensagem = bot._validate_input(mensagem_longa)
        assert valido == False
        assert "longa" in mensagem.lower()
    
    @patch('bot.bot_worker.BotRepository')
    def test_rejeita_mensagem_invalida(self, mock_repo):
        bot = BotWorker()
        valido, mensagem = bot._validate_input("!@#$%^&*()")
        assert valido == False

class TestProcessQuery:
    """Testes do método principal process_query."""
    
    @patch('bot.bot_worker.BotRepository')
    @patch('bot.bot_worker.SistemaAprendizado')
    def test_processa_saudacao(self, mock_aprendizado, mock_repo):
        """Testa processamento de saudação."""
        bot = BotWorker()
        
        # Mock do sistema de aprendizado
        mock_aprendizado.return_value.prever_intencao.return_value = "saudacao"
        mock_aprendizado.return_value.buscar_resposta_aprendida.return_value = (None, 0.0)
        
        resultado = bot.process_query("Oi, tudo bem?", user_id=1)
        
        assert resultado["status"] == "success"
        assert resultado["source"] in ["saudacao", "status"]
        assert len(resultado["response"]) > 0
    
    @patch('bot.bot_worker.BotRepository')
    @patch('bot.bot_worker.SistemaAprendizado')
    @patch('bot.bot_worker.BuscadorAPI')
    def test_processa_pergunta_conhecimento(self, mock_buscador_class, mock_aprendizado, mock_repo):
        """Testa processamento de pergunta de conhecimento."""
        bot = BotWorker()
        
        # Mock do aprendizado
        bot.sistema_aprendizado.prever_intencao.return_value = "conhecimento"
        bot.sistema_aprendizado.buscar_resposta_aprendida.return_value = (None, 0.0)
        bot.sistema_aprendizado.avaliar_qualidade_resposta.return_value = 0.8
        
        # Mock do buscador
        bot.buscador.buscar_todas.return_value = {
            "google": "Paris is the capital of France",
            "wolfram": "Paris, France",
            "wikipedia": None,
            "duckduckgo": None
        }
        
        resultado = bot.process_query("Qual a capital da França?", user_id=1)
        
        assert resultado["status"] == "success"
        assert "paris" in resultado["response"].lower() or "frança" in resultado["response"].lower()
    
    @patch('bot.bot_worker.BotRepository')
    def test_retorna_erro_para_entrada_invalida(self, mock_repo):
        """Testa tratamento de entrada inválida."""
        bot = BotWorker()
        
        resultado = bot.process_query("!@#$%", user_id=1)
        
        assert resultado["status"] == "error"
    
    @patch('bot.bot_worker.BotRepository')
    @patch('bot.bot_worker.SistemaAprendizado')
    def test_usa_cache(self, mock_aprendizado, mock_repo):
        """Testa uso de cache."""
        bot = BotWorker()
        
        # Mock
        bot.sistema_aprendizado.prever_intencao.return_value = "conhecimento"
        bot.sistema_aprendizado.buscar_resposta_aprendida.return_value = (None, 0.0)
        
        # Primeira chamada
        with patch.object(bot.buscador, 'buscar_todas') as mock_buscar:
            mock_buscar.return_value = {"google": "Cached response"}
            resultado1 = bot.process_query("Teste cache", user_id=1)
        
        # Segunda chamada (deve usar cache)
        with patch.object(bot.buscador, 'buscar_todas') as mock_buscar:
            mock_buscar.return_value = {"google": "Should not be called"}
            resultado2 = bot.process_query("Teste cache", user_id=1)
        
        # Segunda chamada deve ser muito mais rápida (cache)
        assert resultado2["processing_time"] < resultado1["processing_time"]

class TestHistoryMethods:
    """Testes dos métodos de histórico."""
    
    @patch('bot.bot_worker.BotRepository')
    def test_get_user_history(self, mock_repo_class):
        """Testa busca de histórico."""
        bot = BotWorker()
        
        # Mock do repository
        bot.repository.get_user_conversations.return_value = []
        bot.repository.get_total_conversations_count.return_value = 0
        
        resultado = bot.get_user_history(user_id=1, limit=20, offset=0)
        
        assert resultado["status"] == "success"
        assert "conversations" in resultado
        assert "pagination" in resultado
    
    @patch('bot.bot_worker.BotRepository')
    def test_search_conversations(self, mock_repo_class):
        """Testa busca de conversas."""
        bot = BotWorker()
        
        bot.repository.search_conversations.return_value = []
        
        resultado = bot.search_conversations(user_id=1, query="capital", limit=20)
        
        assert resultado["status"] == "success"
        assert "results" in resultado

class TestFeedbackMethods:
    """Testes dos métodos de feedback."""
    
    @patch('bot.bot_worker.BotRepository')
    @patch('bot.bot_worker.SistemaFeedback')
    def test_registrar_feedback(self, mock_feedback_class, mock_repo):
        """Testa registro de feedback."""
        bot = BotWorker()
        
        bot.sistema_feedback.registrar_feedback.return_value = True
        
        resultado = bot.registrar_feedback(
            conversation_id=1,
            tipo="positivo",
            detalhes="Resposta útil"
        )
        
        assert resultado == True
    
    @patch('bot.bot_worker.BotRepository')
    @patch('bot.bot_worker.SistemaFeedback')
    def test_registrar_correcao(self, mock_feedback_class, mock_repo):
        """Testa registro de correção."""
        bot = BotWorker()
        
        bot.sistema_feedback.registrar_correcao.return_value = True
        
        resultado = bot.registrar_correcao(
            conversation_id=1,
            resposta_correta="A resposta correta é esta"
        )
        
        assert resultado == True

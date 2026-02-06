"""
Fixtures compartilhadas para todos os testes.
"""

import pytest
import json
from unittest.mock import Mock, MagicMock
from pathlib import Path

# Fixtures de dados de teste

@pytest.fixture
def sample_questions():
    """Perguntas de exemplo para testes."""
    return [
        "Qual a capital da França?",
        "Como funciona a fotossíntese?",
        "Por que o céu é azul?",
        "Quem foi Albert Einstein?",
        "Quando foi descoberto o Brasil?",
        "Quanto é 2 + 2?",
        "Oi, tudo bem?",
        "Qual a diferença entre Python e Java?",
    ]

@pytest.fixture
def sample_responses():
    """Respostas de exemplo."""
    return {
        "wolfram": "Paris, Île-de-France, France",
        "google": "Paris is the capital and most populous city of France. Situated on the Seine River.",
        "wikipedia": "Paris is the capital and largest city of France. With an official population of 2,102,650.",
        "duckduckgo": "Paris, city and capital of France, located in the north-central part of the country."
    }

@pytest.fixture
def mock_repository():
    """Mock do repositório de banco de dados."""
    repo = Mock()

    # Mock de métodos comuns
    repo.create_conversation.return_value = Mock(id=1)
    repo.get_conversation_by_id.return_value = Mock(
        id=1,
        user_id=1,
        pergunta="Teste",
        resposta="Resposta teste",
        fonte="google",
        tempo_processamento=1.0,
        metadata={}
    )
    repo.get_user_conversations.return_value = []
    repo.get_total_conversations_count.return_value = 0

    return repo

@pytest.fixture
def mock_buscador():
    """Mock do buscador de APIs."""
    buscador = Mock()

    # Respostas padrão para cada API
    buscador.buscar_wolfram.return_value = "42"
    buscador.buscar_google.return_value = "Google search result"
    buscador.buscar_wikipedia.return_value = "Wikipedia article"
    buscador.buscar_duckduckgo.return_value = "DuckDuckGo result"
    buscador.buscar_todas.return_value = {
        "wolfram": "42",
        "google": "Google result",
        "wikipedia": None,
        "duckduckgo": None
    }

    return buscador

@pytest.fixture
def mock_config(monkeypatch):
    """Mock das configurações."""
    monkeypatch.setenv("WOLFRAM_APP_ID", "test_wolfram_id")
    monkeypatch.setenv("GOOGLE_CX", "test_google_cx")
    monkeypatch.setenv("GOOGLE_API_KEY", "test_google_key")

@pytest.fixture
def temp_cache_dir(tmp_path):
    """Diretório temporário para cache."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    return cache_dir

# Fixtures de componentes

@pytest.fixture
def analisador():
    """Instância do AnalisadorPergunta."""
    from bot.utils.question_analyzer import AnalisadorPergunta
    return AnalisadorPergunta()

@pytest.fixture
def analisador_avancado():
    """Instância do AnalisadorAvancado."""
    from bot.utils.advanced_analyzer import AnalisadorAvancado
    return AnalisadorAvancado()

@pytest.fixture
def combinador():
    """Instância do CombinadorRespostas."""
    from bot.utils.response_combiner import CombinadorRespostas
    return CombinadorRespostas()

@pytest.fixture
def formatador():
    """Instância do FormatadorResposta."""
    from bot.utils.response_formatter import FormatadorResposta
    return FormatadorResposta()

# Helpers

@pytest.fixture
def assert_similar():
    """Helper para comparar strings com similaridade."""
    def _assert_similar(str1, str2, threshold=0.8):
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity

        vectorizer = TfidfVectorizer()
        tfidf = vectorizer.fit_transform([str1.lower(), str2.lower()])
        similarity = cosine_similarity(tfidf[0], tfidf[1])[0][0]

        assert similarity >= threshold, f"Strings não são similares o suficiente: {similarity:.2f} < {threshold}"

    return _assert_similar
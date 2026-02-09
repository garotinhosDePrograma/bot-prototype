import os
import logging

logger = logging.getLogger(__name__)

MODO_PRODUCAO = os.getenv("PRODUCAO").lower == "true"

if MODO_PRODUCAO:
    DEEP_LEARNING_AVAILABLE = False
    MAX_FEATURES_TFIDF = 500
    SPACY_PIPELINE_DISABLED = ["parser", "lemmatizer"]
    CACHE_SIZE = 200
    MAX_WORKERS_BUSCA = 3

    logger.info("=" * 60)
    logger.info("MODO PRODUÇÃO ATIVADO")
    logger.info("Deep learning: DESABILITADO")
    logger.info("spaCy: Modo ultra-leve")
    logger.info("=" * 60)
else:
    try:
        import tensorflow
        DEEP_LEARNING_AVAILABLE = True
    except ImportError:
        DEEP_LEARNING_AVAILABLE = False

    MAX_FEATURES_TFIDF = 1000
    SPACY_PIPELINE_DISABLED = []
    CACHE_SIZE = 200
    MAX_FEATURES_TFIDF = 4

    logger.info("MODO DESENVOLVIMENTO")

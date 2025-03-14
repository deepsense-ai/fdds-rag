import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


class Config:
    """
    Application configuration settings.
    Manages API keys, model names, paths, and retrieval parameters.
    """

    # API KEYS
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    COHERE_API_KEY = os.getenv("COHERE_API_KEY")
    QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")

    # MODELS
    EMBEDDING_MODEL = "text-embedding-3-small"
    MODEL_NAME = "gpt-4o-mini"
    RERANKER_MODEL = "cohere/rerank-english-v3.0"

    # DATA
    DOCUMENTS_PATH = Path(__file__).parent.parent / "data" / "pdfs"
    COLLECTION_NAME = "fdds"

    # RETRIEVE PARAMETERS
    TOP_K = 20
    TOP_N = 5

    @classmethod
    def validate(cls):
        """Validates required configuration settings."""
        missing_keys = [
            key for key in ["OPENAI_API_KEY", "COHERE_API_KEY"] if not getattr(cls, key)
        ]
        if missing_keys:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_keys)}"
            )

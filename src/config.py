from pathlib import Path
from pydantic import constr, PositiveInt
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    """
    Application configuration settings.
    Manages API keys, model names, paths, and retrieval parameters.
    """

    # API KEYS
    OPENAI_API_KEY: str
    COHERE_API_KEY: str
    QDRANT_URL: str = "http://localhost:6333"

    # MODELS
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    MODEL_NAME: str = "gpt-4o-mini"
    RERANKER_MODEL: str = "cohere/rerank-english-v3.0"

    # DATA
    DOCUMENTS_PATH: Path = Path(__file__).parent.parent / "data" / "pdfs"
    COLLECTION_NAME: constr(min_length=1) = "fdds"

    # RETRIEVE PARAMETERS
    TOP_K: PositiveInt = 20
    TOP_N: PositiveInt = 5

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

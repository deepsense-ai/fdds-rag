import logging
from pathlib import Path

from pydantic import PositiveInt
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    """
    Application configuration settings.
    Manages API keys, model names, paths, and retrieval parameters.
    """

    # API KEYS
    OPENAI_API_KEY: str
    NEPTUNE_API_KEY: str
    QDRANT_API_KEY: str

    # MODELS
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    MODEL_NAME: str = "gpt-4o-mini"
    MAX_NEW_TOKENS: PositiveInt = 500

    # API
    API_URL: str = "http://localhost:8000"

    # DATA
    QDRANT_URL: str = "http://localhost"  # "http://qdrant"
    QDRANT_PORT: int = 6333
    QDRANT_INGEST_URL: str = "http://localhost"
    COLLECTION_NAME: str = "fdds"

    EVAL_DATASET: Path = (
        Path(__file__).parent.parent.parent / "data" / "eval_dataset.json"
    )
    EVAL_CONFIG: Path = (
        Path(__file__).parent.parent.parent / "data" / "eval_config.yaml"
    )

    # RETRIEVE PARAMETERS
    TOP_K: PositiveInt = 5
    TOP_N: PositiveInt = 5

    # LOGS AND MONITORING
    JAEGER_ENABLED: bool = False
    JAEGER_URL: str = "http://jaeger:4317"
    logging.getLogger("LiteLLM").setLevel(logging.WARNING)

    class Config:
        env_file = Path(__file__).parent.parent.parent / ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

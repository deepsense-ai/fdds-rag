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

    # MODELS
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    MODEL_NAME: str = "gpt-4o-mini"

    # DATA
    QDRANT_URL: str = "http://localhost:6333"
    COLLECTION_NAME: str = "fdds"
    DOCUMENTS_PATH: Path = Path(__file__).parent.parent / "data" / "pdfs.txt"
    EVAL_DATASET: Path = Path(__file__).parent.parent / "data" / "eval_dataset.json"
    EVAL_CONFIG: Path = Path(__file__).parent.parent / "data" / "eval_config.yaml"

    # RETRIEVE PARAMETERS
    TOP_K: PositiveInt = 5
    TOP_N: PositiveInt = 5

    class Config:
        env_file = Path(__file__).parent.parent / ".env"
        env_file_encoding = "utf-8"

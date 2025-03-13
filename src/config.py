import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")
DOCUMENTS_PATH = Path(__file__).parent.parent / "data" / "pdfs"
COLLECTION_NAME = "fdds"

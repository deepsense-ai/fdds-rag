from collections.abc import Sequence
import asyncio
from qdrant_client import AsyncQdrantClient, QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from pathlib import Path

from ragbits.core.vector_stores.qdrant import QdrantVectorStore
from ragbits.core.vector_stores.in_memory import InMemoryVectorStore
from ragbits.core.embeddings.litellm import LiteLLMEmbeddings
from ragbits.document_search import DocumentSearch
from ragbits.document_search.documents.sources import LocalFileSource
from ragbits.document_search.ingestion.document_processor import DocumentProcessorRouter
from ragbits.document_search.documents.document import DocumentType
from ragbits.document_search.ingestion.providers.unstructured import UnstructuredDefaultProvider, UnstructuredPdfProvider
from ragbits.document_search.documents.document import DocumentMeta
from ragbits.core.vector_stores.base import WhereQuery, VectorStoreOptions
from ragbits.core.audit import traceable
from ragbits.document_search.ingestion.processor_strategies.distributed import DistributedProcessing

from config import QDRANT_URL, COLLECTION_NAME, MODEL_NAME, DOCUMENTS_PATH, OPENAI_API_KEY


async def ingest_documents(documents: Sequence["LocalFileSource"], document_search: DocumentSearch) -> None:
    if not documents:
        raise ValueError("No documents to ingest")
    print(f"Sending {len(documents)} documents to Qdrant")
    await document_search.ingest(documents)

async def get_limit(client):
    return (await client.count(collection_name=COLLECTION_NAME)).count

def ingest_pdf_documents() -> None:
    embedder = LiteLLMEmbeddings(
        model="text-embedding-3-small",
    )

    qdrant_client = AsyncQdrantClient(url=QDRANT_URL)
    vector_store = QdrantVectorStore(
        client=qdrant_client,
        index_name=COLLECTION_NAME,
    )

    document_search = DocumentSearch(
        embedder=embedder,
        vector_store=vector_store,
    )

    documents = LocalFileSource.list_sources(DOCUMENTS_PATH, file_pattern="*.pdf")
    if len(documents) == 0:
        raise ValueError("No documents found")
    else:
        print(f"Ingesting {len(documents)} documents...")
        asyncio.run(ingest_documents(documents, document_search))


# def prepare_qdrant() -> None:
#     qdrant_client = QdrantClient(url=QDRANT_URL)
#     if not qdrant_client.collection_exists(COLLECTION_NAME):
#         print("[CREATING COLLECTION]")
#         qdrant_client.create_collection(
#             collection_name=COLLECTION_NAME,
#             vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
#         )
#         print("[COLLECTION CREATED]")
#     else:
#         print("[COLLECTION ALREADY EXISTS]")
#     collection_info = qdrant_client.get_collection(COLLECTION_NAME)
#     print(collection_info)

if __name__ == "__main__":

    print(ingest_pdf_documents())



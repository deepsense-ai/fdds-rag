import asyncio
import argparse

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from ragbits.core.embeddings.litellm import LiteLLMEmbedder
from ragbits.core.vector_stores.qdrant import QdrantVectorStore
from ragbits.document_search import DocumentSearch
from ragbits.core.sources.web import WebSource
from ragbits.document_search.ingestion.enrichers import ElementEnricherRouter
from ragbits.document_search.documents.element import ImageElement

from fdds import config
from fdds.handlers import NoImageIntermediateHandler


async def ingest_pdf_documents(documents_path: str) -> None:
    """
    Ingest PDF documents from a local source into a vector store for searching.

    This function uses an async Qdrant client to perform ingestion of PDF documents.
    The documents are embedded using a specified embedding model and stored in a Qdrant
    vector store for efficient searching.

    The function performs the following steps:
    1. Initializes an embedder with a predefined model.
    2. Sets up an asynchronous Qdrant client and a vector store.
    3. Lists all PDF documents from a specified local path.
    4. Validates that there are documents to ingest.
    5. If documents are found, it asynchronously ingests them into the vector store.

    Args:
        documents_path (str):
            Path to a .txt file containing URLs of PDF documents to process.

    Raises:
        ValueError: If no documents are found at the specified path.

    Prints:
        A message indicating the number of documents being ingested.

    """
    embedder = LiteLLMEmbedder(
        model_name=config.EMBEDDING_MODEL,
    )
    qdrant_client = AsyncQdrantClient(
        url=config.QDRANT_INGEST_URL,
        port=config.QDRANT_PORT,
        api_key=config.QDRANT_API_KEY,
    )
    vector_store = QdrantVectorStore(
        client=qdrant_client,
        index_name=config.COLLECTION_NAME,
        embedder=embedder,
    )
    enricher_router = ElementEnricherRouter(
        {ImageElement: NoImageIntermediateHandler()}
    )
    document_search = DocumentSearch(
        vector_store=vector_store,
        enricher_router=enricher_router,
    )

    with open(documents_path, "r") as f:
        urls = f.read().splitlines()
    documents = []
    for url in urls:
        documents.extend(await WebSource.list_sources(url))

    if len(documents):
        print(f"[Ingesting {len(documents)} documents]")
        await document_search.ingest(documents)
    else:
        raise ValueError("No documents to ingest.")


async def delete_url(qdrant_client, url):
    filter_condition = Filter(
        must=[
            FieldCondition(
                key="metadata.document_meta.source.url", match=MatchValue(value=url)
            )
        ]
    )
    try:
        await qdrant_client.delete(
            collection_name=config.COLLECTION_NAME, points_selector=filter_condition
        )
        print(f"Deleted: {url}")
    except Exception as e:
        print(f"Error deleting {url}: {e}")


async def delete_pdf_documents(documents_path: str) -> None:
    with open(documents_path, "r") as f:
        urls = f.read().splitlines()
    qdrant_client = AsyncQdrantClient(
        url=config.QDRANT_INGEST_URL,
        port=config.QDRANT_PORT,
        api_key=config.QDRANT_API_KEY,
    )
    await asyncio.gather(*(delete_url(qdrant_client, url) for url in urls))


def main():
    """
    CLI tool to ingest or delete PDF documents based on a list of URLs.

    Usage:
        - To ingest:  python script.py --ingest path/to/file.txt
        - To delete:  python script.py --delete path/to/file.txt
    """
    parser = argparse.ArgumentParser(description="Manage PDF documents.")

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--ingest",
        "-i",
        help="Path to a .txt file with URLs of PDF documents to ingest.",
    )
    group.add_argument(
        "--delete",
        "-d",
        help="Path to a .txt file with URLs of PDF documents to delete.",
    )

    args = parser.parse_args()

    if args.ingest:
        asyncio.run(ingest_pdf_documents(args.ingest))
    elif args.delete:
        asyncio.run(delete_pdf_documents(args.delete))


if __name__ == "__main__":
    main()

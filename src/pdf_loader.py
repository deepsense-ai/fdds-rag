import asyncio
import argparse
from collections.abc import Sequence

from qdrant_client import AsyncQdrantClient
from ragbits.core.embeddings.litellm import LiteLLMEmbedder
from ragbits.core.vector_stores.qdrant import QdrantVectorStore
from ragbits.document_search import DocumentSearch
from ragbits.document_search.documents.sources import LocalFileSource, WebSource, Source
from ragbits.document_search.documents.element import IntermediateImageElement

from src.config import Config
from src.handlers import NoImageIntermediateHandler

config = Config()


async def ingest_documents(
    documents: Sequence["Source"], document_search: DocumentSearch
) -> None:
    """
    Ingests a sequence of local file source documents into a document search system.

    This function takes a list of local file sources and asynchronously sends
    them to the specified document search engine (e.g., Qdrant) for ingestion.
    It raises an error if no documents are provided.

    Args:
        documents (Sequence["LocalFileSource"]):
            A sequence of local file sources to be ingested.
        document_search (DocumentSearch):
            An instance of the document search system that handles ingestion.

    Raises:
        ValueError: If the documents list is empty.


    """
    if not documents:
        raise ValueError("No documents to ingest.")
    await document_search.ingest(documents)


async def ingest_pdf_documents(source_type: str) -> None:
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
        source_type (str):
            The source type, either 'pdf' for directory of PDF files or
            'txt' for a text file with URLs.

    Raises:
        ValueError: If no documents are found at the specified path.

    Prints:
        A message indicating the number of documents being ingested.

    """
    embedder = LiteLLMEmbedder(
        model=config.EMBEDDING_MODEL,
    )
    qdrant_client = AsyncQdrantClient(
        url=config.QDRANT_INGEST_URL, api_key=config.QDRANT_API_KEY
    )
    vector_store = QdrantVectorStore(
        client=qdrant_client,
        index_name=config.COLLECTION_NAME,
        embedder=embedder,
    )

    document_search = DocumentSearch(
        vector_store=vector_store,
        enricher_router={IntermediateImageElement: NoImageIntermediateHandler()},
    )

    if source_type == "txt":
        with open(config.DOCUMENTS_PATH, "r") as f:
            urls = f.read().splitlines()
        documents = []
        for url in urls:
            documents.extend(await WebSource.list_sources(url))

    elif source_type == "pdf":
        documents = LocalFileSource.list_sources(
            config.DOCUMENTS_PATH, file_pattern="*.pdf"
        )
    else:
        raise ValueError("Invalid source_type. Must be 'pdf' or 'txt'.")

    if len(documents) == 0:
        raise ValueError("No documents found")
    else:
        print(f"Ingesting {len(documents)} documents...")
    await ingest_documents(documents, document_search)


def main():
    """
    Parses the command-line arguments to determine the source type ('txt' or 'pdf')
    and calls the appropriate ingestion function.

    The command-line argument `-s` or `--source_type` specifies the type of document
    to ingest. The function then runs the ingestion process asynchronously.

    """
    parser = argparse.ArgumentParser(description="Ingest documents (PDF or TXT).")
    parser.add_argument(
        "-s",
        "--source_type",
        choices=["txt", "pdf"],
        required=True,
        help="Specify the source type (either 'txt' or 'pdf')",
    )

    args = parser.parse_args()

    asyncio.run(ingest_pdf_documents(args.source_type))


if __name__ == "__main__":
    main()

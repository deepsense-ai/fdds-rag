import asyncio
import sys

from pydantic import BaseModel
from ragbits.core.embeddings.litellm import LiteLLMEmbedder
from ragbits.core.llms.litellm import LiteLLM
from ragbits.core.prompt import ChatFormat, Prompt
from ragbits.core.vector_stores.qdrant import QdrantVectorStore
from ragbits.document_search import DocumentSearch, SearchConfig
from ragbits.document_search.documents.element import Element
from ragbits.conversations.history.compressors.llm import StandaloneMessageCompressor
from typing import AsyncGenerator
from qdrant_client import AsyncQdrantClient

from src.config import Config

config = Config()


class QueryWithContext(BaseModel):
    """
    Represents a query with associated context for
    retrieval-augmented generation workflows.

    This class models a user query along with a list of context strings.
    The context provides relevant background information
    that the assistant can use to generate a response.

    Attributes:
        query (str): The user's question or input.
        context (list[str]):
        A list of context strings containing information relevant to the query.

    """

    query: str
    context: list[str]


class RAGPrompt(Prompt[QueryWithContext]):
    """
    A prompt template for a retrieval-augmented generation (RAG) assistant.

    This class defines both the system and user prompts for guiding
    the assistant's behavior. The assistant answers questions using
    the provided context and refuses to answer
    if the context lacks enough information.

    Attributes:
        system_prompt (str): The system-level instructions for the assistant.
        user_prompt (str): The template for rendering the user's query and context.

    """

    system_prompt = """
    You are a helpful assistant.
    Answer the QUESTION that will be provided using CONTEXT.
    If the QUESTION asks where something is located, if possible,
    try to provide the file url.

    DO NOT INFORM THAT INFORMATION IS PROVIDED IN CONTEXT!
    If in the given CONTEXT there is not enough information refuse to answer.
    """

    user_prompt = """
    QUESTION:
    {{ query }}

    CONTEXT:
    {% for item in context %}
        {{ item }}
    {% endfor %}
    """


def prepare_context(context: Element) -> str:
    text = (
        f"{context.text_representation} "
        f"(source: {context.document_meta.source.url}, "
        f"page: {context.location.page_number})"
    )
    return text


async def get_contexts(question: str, top_k: int, top_n: int) -> list[str]:
    """
    Retrieve the most relevant context documents for a given question
    using a vector store.

    This function embeds the input question, searches the Qdrant vector store,
    and retrieves the top-k most relevant document contexts.
    The results are returned as a list of text representations.

    Args:
        question (str):
            The question to search for relevant contexts.
        top_k (int):
            The number of top relevant contexts to retrieve from the vector store.
        top_n (int):
            The number of top reranked contexts to return.

    Returns:
        list[str]: A list of the top-n reranked context strings.

    Dependencies:
        - LiteLLMEmbedder: Generates embeddings for the question.
        - AsyncQdrantClient: Connects to the Qdrant vector store.
        - QdrantVectorStore: Manages document storage and retrieval.
        - DocumentSearch: Executes the search in the vector store.
        - LiteLLMReranker: Reranks the retrieved contexts for better relevance.
    """
    embedder = LiteLLMEmbedder(
        model=config.EMBEDDING_MODEL,
    )
    qdrant_client = AsyncQdrantClient(
        url=config.QDRANT_URL, api_key=config.QDRANT_API_KEY
    )
    vector_store = QdrantVectorStore(
        client=qdrant_client,
        index_name=config.COLLECTION_NAME,
        embedder=embedder,
    )
    document_search = DocumentSearch(vector_store=vector_store)
    contexts = await document_search.search(
        question,
        SearchConfig(vector_store_kwargs={"k": top_k}),
    )

    texts = [prepare_context(context) for context in contexts]
    return texts


async def inference(query_with_history: ChatFormat) -> AsyncGenerator[str, None]:
    """
    Generate an AI-powered response to a query using retrieval-augmented generation.

    This function retrieves relevant contexts for the input query, optionally compresses
    and includes the conversation history, constructs a prompt using the `RAGPrompt`
    class, and generates a response using a language model. The response is streamed in
    real-time in chunks.

    Args:
        query_with_history (ChatFormat):
            The combined conversation history and current query
            to be included in the response generation.

    Yields:
        str: Chunks of the generated response.

    Dependencies:
        - LiteLLM: Handles response generation from the language model.
        - get_contexts: Fetches relevant contexts for the query.
        - RAGPrompt: Creates a structured prompt with the query and contexts.
        - StandaloneMessageCompressor:
            Compresses the conversation input (history + query)
            before appending it to the context.
    """
    llm = LiteLLM(model_name=config.MODEL_NAME, api_key=config.OPENAI_API_KEY)

    compressor = StandaloneMessageCompressor(llm=llm)
    query = await compressor.compress(query_with_history)

    context = await get_contexts(query, top_k=config.TOP_K, top_n=config.TOP_N)
    stream = llm.generate_streaming(
        prompt=RAGPrompt(QueryWithContext(query=query, context=context)),
    )
    async for chunk in stream:
        yield chunk


def parse_query() -> ChatFormat:
    """Parses the query from command line arguments.

    Returns:
        ChatFormat: A list containing a single message dictionary with the user's query.

    Raises:
        SystemExit: If no query is provided in the command line arguments.
    """
    if len(sys.argv) < 2:
        print('Usage: uv run inference.py "<Your query here>"')
        sys.exit(1)

    conversation = [
        {
            "role": "user",
            "content": sys.argv[1],
        }
    ]
    return conversation


async def main() -> None:
    """
    Main function that orchestrates the inference process.

    This function parses the query, and then performs inference
    asynchronously based on the parsed query.
    The result of the inference is printed to the console.

    Returns:
        None
    """
    conversation = parse_query()
    async for chunk in inference(conversation):
        print(chunk, end="", flush=True)
    print()


if __name__ == "__main__":
    asyncio.run(main())

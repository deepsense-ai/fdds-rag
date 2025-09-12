import asyncio
import logging
import sys
from typing import AsyncGenerator

from pydantic import BaseModel
from qdrant_client import AsyncQdrantClient
from ragbits.chat.history.compressors.llm import (
    LastMessageAndHistory,
    StandaloneMessageCompressor,
)
from ragbits.core.embeddings import LiteLLMEmbedder
from ragbits.core.llms.litellm import LiteLLM, LiteLLMOptions
from ragbits.core.prompt import ChatFormat, Prompt
from ragbits.core.vector_stores.qdrant import QdrantVectorStore
from ragbits.document_search import DocumentSearch, DocumentSearchOptions
from ragbits.document_search.documents.element import Element

from fdds import config
from fdds.reranker import LLMReranker

logger = logging.getLogger(__name__)
options = LiteLLMOptions(max_tokens=config.MAX_NEW_TOKENS)


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
    If the QUESTION asks where something is located,
    if possible, try to provide the file url.

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


class CompressorPrompt(Prompt[LastMessageAndHistory, str]):
    """
    A prompt for recontextualizing the last message in the history.
    """

    system_prompt = """
    Your task is to rewrite the most recent user message so that
    it is fully self-contained and understandable on its own.

    You are provided with:
    - The most recent user message ("Message").
    - A list of previous messages ("History"), ordered from most recent to oldest.

    If the latest message contains references to previous messages
    (e.g., using pronouns like "he", "it", or phrases like "as I said earlier"),
    you must resolve those references using the history.
    When resolving ambiguous references,
    always prefer the most recent applicable message.

    Return ONLY the rewritten, self-contained version of the latest message.

    Do NOT include the message history in your output.
    Do NOT answer the message.
    Do NOT change the meaning or add new information.
    """

    user_prompt = """
    Message:
    {{ last_message }}

    History:
    {% for message in history[::-1] %}
    - {{ message }}
    {% endfor %}
    """


def prepare_context(context: Element) -> str:
    text = (
        f"{context.text_representation} "
        f"(source: {context.document_meta.source.url}, "
        f"page: {context.location.page_number})"
    )
    return text


async def get_contexts(
    question: str, top_k: int, top_n: int
) -> tuple[list[str], set[str]]:
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
            The maximum number of reranked contexts to return
            after applying the reranker. The actual number returned may be fewer,
            depending on relevance.

    Returns:
        tuple[list[str], set[str]]: A tuple containing two elements:
            - A list of the top-k context strings.
            - A set of unique sources (`set[str]`) corresponding to the context strings,
            ensuring no duplicates.

    Dependencies:
        - LiteLLMEmbedder: Generates embeddings for the question.
        - AsyncQdrantClient: Connects to the Qdrant vector store.
        - QdrantVectorStore: Manages document storage and retrieval.
        - DocumentSearch: Executes the search in the vector store.
        - LiteLLMReranker: Reranks the retrieved contexts for better relevance.
    """
    embedder = LiteLLMEmbedder(
        model_name=config.EMBEDDING_MODEL,
    )
    reranker = LLMReranker(
        model_name=config.MODEL_NAME,
    )

    qdrant_client = AsyncQdrantClient(
        url=config.QDRANT_URL,
        port=config.QDRANT_PORT,
        api_key=config.QDRANT_API_KEY,
        check_compatibility=False,
    )
    vector_store = QdrantVectorStore(
        client=qdrant_client,
        index_name=config.COLLECTION_NAME,
        embedder=embedder,
    )
    document_search = DocumentSearch(vector_store=vector_store, reranker=reranker)
    contexts = await document_search.search(
        question,
        DocumentSearchOptions(
            vector_store_options={"k": top_k},
            reranker_options={"top_n": top_n},
        ),
    )

    texts = [prepare_context(context) for context in contexts]
    sources = set([context.document_meta.source.url for context in contexts])
    return texts, sources


async def inference(query_with_history: ChatFormat) -> AsyncGenerator[str, None]:
    llm = LiteLLM(
        model_name=config.MODEL_NAME,
        api_key=config.OPENAI_API_KEY,
        default_options=options,
    )

    compressor = StandaloneMessageCompressor(llm=llm, prompt=CompressorPrompt)
    query = await compressor.compress(query_with_history)
    logger.info(
        f"Query: {query_with_history[-1]['content']} -- "
        f"Compressed query: {query} -- "
        f"Without history: {len(query_with_history) == 1}"
    )

    context, sources = await get_contexts(query, top_k=config.TOP_K, top_n=config.TOP_N)
    stream = llm.generate_streaming(
        prompt=RAGPrompt(QueryWithContext(query=query, context=context)),
    )
    async for chunk in stream:
        yield chunk

    if sources:
        sources_str = "\n\nPowiązane materiały: \n" + "\n".join(
            [f"- {source}" for source in sources]
        )
        yield sources_str


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

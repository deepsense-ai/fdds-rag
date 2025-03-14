import asyncio

from pydantic import BaseModel
from qdrant_client import AsyncQdrantClient
from ragbits.core.embeddings.litellm import LiteLLMEmbedder
from ragbits.core.llms.litellm import LiteLLM
from ragbits.core.prompt import Prompt
from ragbits.core.vector_stores.qdrant import QdrantVectorStore
from ragbits.document_search import DocumentSearch, SearchConfig
from ragbits.document_search.retrieval.rerankers.litellm import LiteLLMReranker

from config import Config


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
        model=Config.EMBEDDING_MODEL,
    )
    qdrant_client = AsyncQdrantClient(url=Config.QDRANT_URL)
    vector_store = QdrantVectorStore(
        client=qdrant_client,
        index_name=Config.COLLECTION_NAME,
        embedder=embedder,
    )
    reranker = LiteLLMReranker(Config.RERANKER_MODEL)
    document_search = DocumentSearch(vector_store=vector_store, reranker=reranker)
    contexts = await document_search.search(
        question,
        SearchConfig(
            vector_store_kwargs={"k": top_k}, reranker_kwargs={"top_n": top_n}
        ),
    )

    texts = [context.text_representation for context in contexts]
    return texts


async def inference(query: str) -> str:
    """
    Generate an AI-powered response to a query using retrieval-augmented generation.

    This function retrieves relevant contexts for the input query,
    constructs a prompt using the `RAGPrompt` class,
    and generates a response using a language model.

    Args:
        query (str): The user’s question or input.

    Returns:
        str: The generated response from the language model.

    Dependencies:
        - LiteLLM:
            Handles response generation from the language model.
        - get_contexts:
            Fetches relevant contexts for the query.
        - RAGPrompt:
            Creates a structured prompt with the query and contexts.
    """
    llm = LiteLLM(model_name=Config.MODEL_NAME, api_key=Config.OPENAI_API_KEY)
    context = await get_contexts(query, top_k=Config.TOP_K, top_n=Config.TOP_N)
    prompt = RAGPrompt(QueryWithContext(query=query, context=context))
    response = await llm.generate(prompt)
    return response


async def main() -> None:
    Config.validate()
    questions = [
        "Kto jest administratorem danych osobowych uczestników szkoleń?",
    ]

    for q in questions:
        print(q)
        print(await inference(q))


if __name__ == "__main__":
    asyncio.run(main())

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from ragbits.core.prompt import ChatFormat

from fdds.inference import inference

app = FastAPI()


class QueryRequest(BaseModel):
    query_with_history: ChatFormat


@app.get("/", summary="Welcome Endpoint", description="Returns a welcome message.")
async def read_root():
    return {"message": "Welcome to the model inference service"}


@app.post(
    "/chat/",
    summary="Inference Endpoint",
    description="Performs inference based on input query and "
    "optionally provided conversation history",
)
async def chat(request: QueryRequest):
    """
    Perform model inference on the input query and provide a streaming response.

    This function receives a query and optionally a conversation history, invokes the
    `inference` method to generate a response using retrieval-augmented generation,
    and streams the response in real-time as chunks.

    Args:
        request (QueryRequest): The request object containing the query and optional
                                 conversation history.

    Returns:
        StreamingResponse: A streaming response yielding real-time chunks of the
                           generated model output.

    - **conversation_input**:
        The combined input of the current query and optional conversation history
        to provide context for the query. If history is provided, it will be
        compressed and included in the context.
    """
    response_generator = inference(request.query_with_history)
    return StreamingResponse(response_generator, media_type="text/event-stream")

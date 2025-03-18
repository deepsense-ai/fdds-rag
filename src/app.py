from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from src.inference import inference

app = FastAPI()


class QueryRequest(BaseModel):
    query: str


@app.get("/", summary="Welcome Endpoint", description="Returns a welcome message.")
async def read_root():
    return {"message": "Welcome to the model inference service"}


@app.post(
    "/inference/",
    summary="Inference Endpoint",
    description="Performs inference based on input query.",
)
async def get_inference(request: QueryRequest):
    """
    Perform model inference on the input query and provide a streaming response.

    - **query**: The input to be processed by the model.
    """
    query = request.query
    response_generator = inference(query)

    return StreamingResponse(response_generator, media_type="text/event-stream")

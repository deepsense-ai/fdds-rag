from collections.abc import AsyncGenerator
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from ragbits.chat.interface import ChatInterface
from ragbits.chat.interface.types import (
    ChatResponse,
    Message,
)
from ragbits.core import audit
from ragbits.core.audit import traceable

from fdds import config
from fdds.inference import inference

provider = TracerProvider(resource=Resource({SERVICE_NAME: "FDDS-RAG-INFERENCE"}))
provider.add_span_processor(
    BatchSpanProcessor(OTLPSpanExporter(config.JAEGER_URL, insecure=True))
)
trace.set_tracer_provider(provider)

audit.set_trace_handlers("otel")


class MyChat(ChatInterface):
    """Implementation of the ChatInterface."""

    @traceable
    async def chat(
        self,
        message: str,
        history: list[Message] | None = None,
        context: dict | None = None,
    ) -> AsyncGenerator[ChatResponse, None]:
        async for chunk in inference(
            [
                *[
                    {"role": element["role"].value, "content": element["content"]}
                    for element in history
                ],
                {"role": "user", "content": message},
            ]
        ):
            yield self.create_text_response(chunk)

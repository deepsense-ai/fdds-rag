from collections.abc import AsyncGenerator

from ragbits.chat.interface import ChatInterface
from ragbits.chat.interface.types import (
    ChatContext,
    ChatResponse,
)
from ragbits.chat.interface.ui_customization import HeaderCustomization, UICustomization
from ragbits.core import audit
from ragbits.core.prompt import ChatFormat

from fdds import config
from fdds.inference import inference

# Conditionally setup Jaeger tracing
if config.JAEGER_ENABLED:
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.resources import SERVICE_NAME, Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from ragbits.core.audit import traceable

    provider = TracerProvider(resource=Resource({SERVICE_NAME: "FDDS-RAG-INFERENCE"}))
    provider.add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter(config.JAEGER_URL, insecure=True))
    )
    trace.set_tracer_provider(provider)
    audit.set_trace_handlers("otel")
else:

    def traceable(func):
        return func


class MyChat(ChatInterface):
    """Implementation of the ChatInterface."""

    conversation_history = True
    ui_customization = UICustomization(
        header=HeaderCustomization(
            title="Czatbot Fundacja Dajemy Dzieciom Siłę",
            subtitle="by deepsense.ai",
            logo="static/fdds.png",
        ),
        welcome_message="""
            Cześć! Jestem asystentem AI Fundacji Dajemy Dzieciom Siłę.
            Możesz zapytać mnie o treści dostępne na naszej platformie edukacyjnej, takie jak scenariusze, poradniki, broszury czy inne publikacje.
            Jeśli czegoś szukasz lub masz pytanie dotyczące bezpieczeństwa i wsparcia dzieci, śmiało napisz je poniżej - chętnie pomogę!
        """,
    )

    @traceable
    async def chat(
        self,
        message: str,
        history: ChatFormat,
        context: ChatContext,
    ) -> AsyncGenerator[ChatResponse, None]:
        async for chunk in inference([*history, {"role": "user", "content": message}]):
            yield self.create_text_response(chunk)

from collections.abc import AsyncGenerator

from ragbits.api.interface import ChatInterface
from ragbits.api.interface.types import (
    ChatResponse,
    Message,
)
from fdds.inference import inference


class MyChat(ChatInterface):
    """Implementation of the ChatInterface."""

    async def chat(
        self,
        message: str,
        history: list[Message] | None = None,
        context: dict | None = None,
    ) -> AsyncGenerator[ChatResponse, None]:
        async for chunk in inference(
            [
                *[
                    {"role": element.role.value, "content": element.content}
                    for element in history
                ],
                {"role": "user", "content": message},
            ]
        ):
            yield self.create_text_response(chunk)

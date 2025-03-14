from ragbits.document_search.documents.element import Element, IntermediateElement
from ragbits.document_search.ingestion.intermediate_handlers.base import (
    BaseIntermediateHandler,
)


class NoImageIntermediateHandler(BaseIntermediateHandler):
    """
    A handler for intermediate image elements that prevents their ingestion
    into the vector store by always returning an empty list.

    Inherits from BaseIntermediateHandler.
    """

    async def process(
        self, intermediate_elements: list[IntermediateElement]
    ) -> list[Element]:
        """
        Processes a list of intermediate elements.

        Args:
            intermediate_elements (list[IntermediateElement]):
                The list of intermediate elements to process.

        Returns:
            list[Element]: An empty list, indicating that image elements are not
            to be ingested into the vector store.
        """
        return []

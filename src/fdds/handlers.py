from ragbits.document_search.documents.element import ImageElement

from ragbits.document_search.ingestion.enrichers import (
    ImageElementEnricher,
)


class NoImageIntermediateHandler(ImageElementEnricher):
    """
    A handler for intermediate image elements that prevents their ingestion
    into the vector store by always returning an empty list.

    Inherits from BaseIntermediateHandler.
    """

    async def enrich(self, elements: list[ImageElement]) -> list[ImageElement]:
        """
        Skips processing of image elements, as they are excluded
        from storage in Qdrant.

        Args:
            elements (list[ImageElement]):
                The list of image elements to process.

        Returns:
            list[ImageElement]:
                An empty list, as image elements are intentionally
                excluded from being stored in Qdrant.
        """
        return []

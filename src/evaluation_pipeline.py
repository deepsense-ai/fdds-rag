from dataclasses import dataclass
from functools import cached_property

from ragbits.document_search import DocumentSearch
from ragbits.evaluate.pipelines.base import EvaluationPipeline, EvaluationResult


@dataclass
class SearchResult(EvaluationResult):
    query: str
    reference_passages: list[str]
    predicted_passages: list[str]


class Pipeline(EvaluationPipeline):
    @cached_property
    def document_search(self) -> "DocumentSearch":
        """
        Returns the document search instance.

        Returns:
            The document search instance.
        """

        return DocumentSearch.from_config(self.config)  # type: ignore[arg-type]

    async def __call__(self, data: dict) -> SearchResult:
        """
        Runs the report search evaluation pipeline.

        Args:
            data: The evaluation data.

        Returns:
            The evaluation result.
        """
        print(data)
        query = data["question"]
        elements = await self.document_search.search(query, self.config)
        predicted_passages = [element.text_representation or "" for element in elements]

        return SearchResult(
            query=query,
            reference_passages=data["gt_passages"],
            predicted_passages=predicted_passages,
        )

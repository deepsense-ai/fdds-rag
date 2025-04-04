import asyncio
import os

from omegaconf import DictConfig, OmegaConf
from ragbits.evaluate.dataloaders.local import LocalDataLoader
from ragbits.evaluate.evaluator import Evaluator
from ragbits.evaluate.metrics.base import MetricSet
from ragbits.evaluate.utils import log_evaluation_to_neptune

from evaluation_pipeline import Pipeline
from fdds import config


def export_variables(variables: dict[str, str]):
    """
    Exports a set of key-value pairs as environment variables.

    Args:
        variables (dict[str, str]):
            A dictionary where the key is the variable name
            and the value is the corresponding environment variable value.

    """
    for variable_name, value in variables.items():
        os.environ[variable_name] = value


async def main(evaluation_config: DictConfig) -> None:
    """
    Main function for running the evaluation pipeline, loading the dataset,
    computing metrics, and logging the results to Neptune.

    Args:
        evaluation_config (DictConfig):
            A configuration object containing the parameters
            for the evaluation pipeline, dataset, and metrics.
    """
    export_variables(
        {
            "NEPTUNE_PROJECT": evaluation_config.neptune.project,
            "NEPTUNE_API_TOKEN": config.NEPTUNE_API_KEY,
        }
    )
    evaluation_config.pipeline.vector_store.config.client.config.api_key = (
        config.QDRANT_API_KEY
    )

    pipeline = Pipeline(evaluation_config.pipeline)
    pipeline.config = evaluation_config.pipeline

    evaluator = Evaluator()
    dataloader = LocalDataLoader(
        path=str(config.EVAL_DATASET), split="train", builder="json"
    )
    metrics = MetricSet.from_config(evaluation_config.metrics)

    results = await evaluator.compute(
        pipeline=pipeline, dataloader=dataloader, metrics=metrics
    )

    log_evaluation_to_neptune(results, evaluation_config.pipeline)


if __name__ == "__main__":
    eval_config = OmegaConf.load(config.EVAL_CONFIG)
    asyncio.run(main(eval_config))

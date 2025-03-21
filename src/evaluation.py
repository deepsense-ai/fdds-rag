import asyncio

from ragbits.evaluate.evaluator import Evaluator
from ragbits.evaluate.dataloaders.local import LocalDataLoader
from omegaconf import DictConfig, OmegaConf
from ragbits.evaluate.metrics.base import MetricSet

from evaluation_pipeline import Pipeline
from config import Config

config = Config()


async def main(evaluation_config: DictConfig) -> None:
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
    print(results)


if __name__ == "__main__":
    eval_config = OmegaConf.load(config.EVAL_CONFIG)
    asyncio.run(main(eval_config))

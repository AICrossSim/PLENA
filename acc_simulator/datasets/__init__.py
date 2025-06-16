import logging

import datasets

from .wikitext2 import get_raw_data_module_wikitext2 as get_raw_dataset_dict_wikitext2
from .wikitext2 import preprocess_data_module_wikitext2 as preprocess_dataset_dict_wikitext2

logger = logging.getLogger(__name__)


def get_num_labels(task: str):
    if task == "wikitext2":
        logger.warning(
            "returning None for num_labels for language modeling dataset wikitext2"
        )
        return None
    else:
        raise ValueError(f"task {task} not supported")


def get_raw_dataset_dict(task: str) -> datasets.DatasetDict:
    if task == "wikitext2":
        return get_raw_dataset_dict_wikitext2()
    else:
        raise ValueError(f"task {task} not supported")


def preprocess_dataset_dict(
    raw_dataset_dict, tokenizer, max_length, num_proc
) -> datasets.DatasetDict:
    return preprocess_dataset_dict_wikitext2(
        raw_dataset_dict,
        tokenizer=tokenizer,
        max_length=max_length,
        num_proc=num_proc,
    )



def is_regression_task(task: str) -> bool:
    if task == "wikitext2":
        return False
    else:
        raise ValueError(f"task {task} not supported")
from lm_eval import simple_evaluate
from lm_eval.models.huggingface import HFLM
from lm_eval.utils import make_table
from transformers import PreTrainedModel, PreTrainedTokenizer
from typing import Union, List, Dict

def evaluate_with_lm_eval(
    model: PreTrainedModel,
    tokenizer: PreTrainedTokenizer,
    tasks: Union[str, List[str]],
    max_length: int = 2048,
    batch_size: Union[int, str] = "auto",
    log_samples: bool = False,
) -> Dict:
    """
    Evaluate a HuggingFace model using EleutherAI's lm-eval harness.

    Args:
        model: HuggingFace model.
        tokenizer: Corresponding tokenizer.
        tasks: A single task or a list of evaluation tasks.
        max_length: Context window for the model.
        batch_size: Evaluation batch size (default to "auto").
        log_samples: Whether to log individual sample outputs.

    Returns:
        Dictionary of evaluation results.
    """
    if isinstance(tasks, str):
        tasks = [tasks]

    model_lm_eval = HFLM(pretrained=model, tokenizer=tokenizer, max_length=max_length)

    results = simple_evaluate(
        model=model_lm_eval,
        tasks=tasks,
        batch_size=batch_size,
        log_samples=log_samples,
    )

    table = make_table(results)
    print(table)

    return results

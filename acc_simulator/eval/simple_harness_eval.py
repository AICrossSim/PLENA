from typing import List, Optional, Dict, Any, Union
from transformers import AutoModelForCausalLM, AutoTokenizer
from lm_eval.models.huggingface import HFLM
from lm_eval.evaluator import simple_evaluate
from lm_eval.utils import make_table
import torch


def evaluate_model_on_tasks(
    model_name_or_path: str,
    tasks: List[str],
    batch_size: Optional[Union[int, str]] = "auto",
    torch_dtype: torch.dtype = torch.float16,
    device_map: str = "auto",
    device: str = "cuda",
    return_table: bool = True,
    verbose: bool = True,
) -> Dict[str, Any]:
    """
    Load a HuggingFace model, wrap it with HFLM, and run lm-eval-harness evaluation on the given tasks.

    Args:
        model_name_or_path: HF model name or local path
        tasks: List of task names (e.g., ["wikitext", "lambada"])
        batch_size: Batch size or "auto" to determine max fitting batch
        torch_dtype: torch.float16, torch.bfloat16, etc.
        device_map: "auto", or custom map (used by HF accelerate)
        device: "cuda", "cpu"
        return_table: If True, also return `make_table(results)`
        verbose: If True, print summary table to stdout

    Returns:
        Dictionary containing evaluation results
    """
    # Load tokenizer and qauntized model
    tokenizer = AutoTokenizer.from_pretrained(model_name_or_path)
    model = AutoModelForCausalLM.from_pretrained(
        model_name_or_path,
        torch_dtype=torch_dtype,
        device_map=device_map,
    )
    model.eval()

    # Wrap with HFLM
    wrapped_model = HFLM(pretrained=model, tokenizer=tokenizer)

    # Evaluate
    results = simple_evaluate(
        model=wrapped_model,
        tasks=tasks,
        batch_size=batch_size,
        device=device
    )

    if verbose:
        print(make_table(results))

    if return_table:
        results["table"] = make_table(results)

    return results

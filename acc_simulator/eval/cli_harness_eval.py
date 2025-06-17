import json
from argparse import ArgumentParser
from pathlib import Path

import torch
from accelerate import dispatch_model
from transformers import AutoModelForCausalLM

from lm_eval.models.huggingface import HFLM
from lm_eval.evaluator import simple_evaluate
from lm_eval.utils import make_table

from ..models import get_config_cls, get_model_cls
from ..utils.config_load import create_device_map

def eval_wrapper(model, task, max_batch_size):
    print("[INFO] Wrapping model for lm-eval...")
    wrapped_model = HFLM(pretrained=model)

    print("[INFO] Running evaluation...")
    results = simple_evaluate(
        model=wrapped_model,
        tasks=[task],
        max_batch_size=max_batch_size
    )

    print(make_table(results))
    return results


def cli_eval():
    parser = ArgumentParser()
    parser.add_argument("--model_arch", type=str, required=True)
    parser.add_argument("--model_name", type=str, required=True)
    parser.add_argument("--task", type=str, choices=["wikitext", "mmlu"], default="wikitext")
    parser.add_argument("--quant_config", type=str, required=True)
    parser.add_argument("--save_dir", type=str, default=None)
    parser.add_argument("--max_batch_size", type=int, default=4)
    parser.add_argument("--device_map", type=str, default="auto")
    parser.add_argument("--run_pytorch", action="store_true")
    args = parser.parse_args()

    model_cls = get_model_cls(args.model_arch, "lm")
    config_cls = get_config_cls(args.model_arch)

    if not args.run_pytorch:
        config = config_cls.from_pretrained(args.model_name, quant_config=args.quant_config)
        model = model_cls.from_pretrained(
            args.model_name,
            config=config,
            torch_dtype=torch.float16
        )
        device_map = create_device_map(model, args.device_map)
        model = dispatch_model(model, device_map=device_map)
    else:
        model = AutoModelForCausalLM.from_pretrained(
            args.model_name,
            device_map="auto",
            torch_dtype=torch.float16
        )

    model.eval()

    results = eval_wrapper(model, args.task, args.max_batch_size)

    if args.save_dir:
        save_dir = Path(args.save_dir)
        save_dir.mkdir(parents=True, exist_ok=True)

        with open(save_dir / "eval_results.json", "w") as f:
            json.dump(results, f, indent=4)
        print(f"[INFO] Results saved to {save_dir / 'eval_results.json'}")


if __name__ == "__main__":
    cli_eval()

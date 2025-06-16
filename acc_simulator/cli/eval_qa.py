import ast
import json
import logging
import os
from argparse import ArgumentParser
from pathlib import Path

import torch

from transformers import AutoTokenizer, AutoModelForCausalLM

from ..eval import eval_qa_mmlu
from ..models import get_config_cls, get_model_cls

os.environ["PYTHONBREAKPOINT"] = "ipdb.set_trace"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

logger = logging.getLogger(__name__)


def cli_eval_qa_mmlu():
    logger.info("Evaluation started")

    parser = ArgumentParser()
    parser.add_argument("--model_arch", type=str, required=True)
    parser.add_argument("--model_name", type=str, required=True)
    parser.add_argument("--task", type=str, choices=["mmlu_whole", "mmlu_short"], default="mmlu_short")
    parser.add_argument("--quant_config", type=str, default=None)
    parser.add_argument("--save_dir", type=str, default=None)

    parser.add_argument("--batch_size", type=int, default=8)
    parser.add_argument("--max_length", type=int, default=2048)
    # If the flag is present on the command line, set the corresponding variable to True; otherwise, default it to False.
    parser.add_argument("--model_parallelism", action="store_true")
    parser.add_argument("--device_map", type=str, default="auto")
    parser.add_argument("--run_pytorch", action="store_true")
    parser.add_argument(
        "--dataset_split",
        type=str,
        default="test",
        choices=["train", "validation", "test"],
    )

    args = parser.parse_args()
    if args.quant_config is None:
        args.quant_config = {
            "default": {
                "name": "mxfp",
                "bypass": True,
            }
        }

    model_cls = get_model_cls(args.model_arch, "lm")
    config_cls = get_config_cls(args.model_arch)

    config = config_cls.from_pretrained(args.model_name, quant_config=args.quant_config)
    print(config)

    selected_device = "cuda:1"
    if not args.run_pytorch:
        model = model_cls.from_pretrained(
            args.model_name, 
            config=config, 
            device_map=selected_device, 
            torch_dtype=torch.float16
        )
    else:
        model = AutoModelForCausalLM.from_pretrained(
            args.model_name,
            device_map=selected_device, 
            torch_dtype=torch.float16
        )
    
    tokenizer = AutoTokenizer.from_pretrained(args.model_name)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token


    long_subs=["philosophy", "abstract_algebra", "econometrics","college_computer_science", "marketing"]
    short_subs = ["philosophy", "abstract_algebra"]
    
    results = eval_qa_mmlu(
        model=model,
        tokenizer=tokenizer,
        subject_lst=short_subs if args.task == "mmlu_short" else long_subs
    )

    logger.info(results)

    if args.save_dir:
        save_dir = Path(args.save_dir)
        save_dir.mkdir(parents=True, exist_ok=True)

        with open(save_dir / "Final_gt_b7_final.json", "w") as f:
            json.dump(results, f, indent=4)

    logger.info("Evaluation finished")

if __name__ == "__main__":
    cli_eval_qa_mmlu()

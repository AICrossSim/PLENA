import ast
import json
import logging
import os
from argparse import ArgumentParser
from pathlib import Path

import torch
from accelerate import dispatch_model, infer_auto_device_map

from torch.utils.data import DataLoader
from transformers import DataCollatorForLanguageModeling, AutoModelForCausalLM

from ..datasets import get_raw_dataset_dict, preprocess_dataset_dict
from ..eval import eval_lm_wikitext2
from ..models import get_config_cls, get_model_cls, get_tokenizer_cls

os.environ["PYTHONBREAKPOINT"] = "ipdb.set_trace"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

logger = logging.getLogger(__name__)
DEVICE = "cuda:1"

def cli_eval_lm_wikitext2():
    logger.info("Evaluation started")

    parser = ArgumentParser()
    parser.add_argument("--model_arch", type=str, required=True)
    parser.add_argument("--model_name", type=str, required=True)
    parser.add_argument("--task", type=str, choices=["wikitext2"], required=True)
    parser.add_argument("--quant_config", type=str, default=None)
    parser.add_argument("--save_dir", type=str, default=None)

    parser.add_argument("--batch_size", type=int, default=1)
    parser.add_argument("--max_length", type=int, default=2048)
    # If the flag is present on the command line, set the corresponding variable to True; otherwise, default it to False.
    parser.add_argument("--model_parallelism", action="store_true")
    parser.add_argument("--device_map", type=str, default="auto")
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
                "name": "mxint",
                "bypass": True,
            }
        }

    model_cls = get_model_cls(args.model_arch, "lm")
    config_cls = get_config_cls(args.model_arch)

    config = config_cls.from_pretrained(args.model_name, quant_config=args.quant_config)
    print(config)
    tokenizer = get_tokenizer_cls(args.model_arch).from_pretrained(
        args.model_name, legacy=False
    )
    print("/n printing tokenzier context length", tokenizer.model_max_length)

    if not args.model_parallelism:
        # pass
        # print("===========================")
        device = torch.device(DEVICE if torch.cuda.is_available() else "cpu")
        print(f"Using device: {device}")
        print(f"Using model{args.model_name}")
        model = model_cls.from_pretrained(args.model_name, config=config, torch_dtype=torch.float16).to(device)
        # print("============================")
    else:
        # model = model_cls.from_pretrained(args.model_name, 
        #                                   config=config, 
        #                                   device_map="auto", 
        #       
        #                            torch_dtype=torch.float16)
        pass
        
    # model_name = "huggyllama/llama-7b"
    # model = AutoModelForCausalLM.from_pretrained(
    #     args.model_name,
    #     device_map=DEVICE, 
    #     torch_dtype=torch.float16
    # )

    print("**Printing the args.task: ", args.task)
    raw_dataset = get_raw_dataset_dict(args.task)
    preprocessed_dataset_dict = preprocess_dataset_dict(
        raw_dataset,
        tokenizer=tokenizer,
        max_length= 2048,
        num_proc=os.cpu_count(),
    )
    data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)

    eval_dataloader = DataLoader(
        preprocessed_dataset_dict[args.dataset_split],
        batch_size=args.batch_size,
        shuffle=False,
        collate_fn=data_collator,
        num_workers=os.cpu_count(),
    )

    results = eval_lm_wikitext2(
        model,
        eval_dataloader=eval_dataloader,
        num_samples=None,
        progress_bar=True,
        input_device=DEVICE,
    )
    print(results)
    logger.info(results)

    if args.save_dir:
        save_dir = Path(args.save_dir)
        save_dir.mkdir(parents=True, exist_ok=True)

        with open(save_dir / "results_temp_E4M3_FP16.json", "w") as f:
        # with open(save_dir / "results_temp_GT.json", "w") as f:
            json.dump(results, f, indent=4)

    logger.info("Evaluation finished")

if __name__ == "__main__":
    cli_eval_lm_wikitext2()

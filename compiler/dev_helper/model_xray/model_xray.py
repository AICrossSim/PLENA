import argparse
import inspect
import contextlib
import torch
from transformers import Qwen3VLModel, AutoProcessor

def _print_model_xray(model, max_modules=80, max_params=80):
    print("=== TYPE ===")
    print(type(model))
    print("module:", model.__class__.__module__)
    print()

    print("=== MRO (inheritance) ===")
    for c in model.__class__.__mro__[:8]:
        print(" ", c)
    print()

    print("=== INSTANCE __dict__ keys (dynamic attrs) ===")
    print(sorted(list(model.__dict__.keys()))[:80])
    print()

    print("=== TOP-LEVEL _modules keys ===")
    print(sorted(list(model._modules.keys())))
    print()

    print("=== named_modules (first few) ===")
    i = 0
    for name, mod in model.named_modules():
        if name == "":
            continue
        print(f"{name:60s} {type(mod).__name__}")
        i += 1
        if max_modules is not None and i >= max_modules:
            print("... truncated ...")
            break
    print()

    print("=== named_parameters (first few) ===")
    i = 0
    for name, p in model.named_parameters():
        print(f"{name:70s} shape={tuple(p.shape)} dtype={p.dtype} req_grad={p.requires_grad}")
        i += 1
        if max_params is not None and i >= max_params:
            print("... truncated ...")
            break
    print()

    print("=== named_buffers (first few) ===")
    for name, b in list(model.named_buffers())[:40]:
        print(f"{name:70s} shape={tuple(b.shape)} dtype={b.dtype}")
    print()

    print("=== SOURCE FILES ===")
    try:
        print("class file:", inspect.getsourcefile(model.__class__))
    except Exception as e:
        print("class file: <unavailable>", e)
    try:
        print("forward file:", inspect.getsourcefile(model.forward),
              "line", inspect.getsourcelines(model.forward)[1])
    except Exception as e:
        print("forward file: <unavailable>", e)

    print()
    if hasattr(model, "config"):
        print("=== CONFIG ===")
        d = model.config.to_dict()
        print("config class:", type(model.config))
        print("config keys (sample):", list(d.keys())[:80])


def model_xray(model, max_modules=80, max_params=80, report_path=None):
    if report_path:
        with open(report_path, "w", encoding="utf-8") as f:
            with contextlib.redirect_stdout(f):
                _print_model_xray(model, max_modules=max_modules, max_params=max_params)
        return
    _print_model_xray(model, max_modules=max_modules, max_params=max_params)


def _parse_args():
    parser = argparse.ArgumentParser(description="Inspect a HF model and print a report.")
    parser.add_argument("--model", default="Qwen/Qwen3-VL-2B-Instruct",
                        help="HuggingFace model name or path.")
    parser.add_argument("--report-path", default="model_xray_report.txt",
                        help="Write report to this file instead of stdout.")
    parser.add_argument("--max-modules", type=int, default=None,
                        help="Limit number of named_modules printed; omit for no limit.")
    parser.add_argument("--max-params", type=int, default=None,
                        help="Limit number of named_parameters printed; omit for no limit.")
    return parser.parse_args()

if __name__ == "__main__":
    args = _parse_args()
    MODEL_NAME = args.model
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")

    if device == "cuda":
        torch.backends.cudnn.benchmark = True

    print("Loading processor & model...")

    model = Qwen3VLModel.from_pretrained(
        MODEL_NAME,
        torch_dtype=torch.float16 if device == "cuda" else torch.float32,
        device_map=None,
    ).to(device)
    model_xray(model, max_modules=args.max_modules, max_params=args.max_params,
               report_path=args.report_path)
    if args.report_path:
        print(f"Report saved to: {args.report_path}")

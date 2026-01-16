import inspect
import torch
from transformers import Qwen3VLModel, AutoProcessor

def model_xray(model, max_modules=80, max_params=80):
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
        if i >= max_modules:
            print("... truncated ...")
            break
    print()

    print("=== named_parameters (first few) ===")
    i = 0
    for name, p in model.named_parameters():
        print(f"{name:70s} shape={tuple(p.shape)} dtype={p.dtype} req_grad={p.requires_grad}")
        i += 1
        if i >= max_params:
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

if __name__ == "__main__":
    MODEL_NAME = "Qwen/Qwen3-VL-2B-Instruct"
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")

    if device == "cuda":
        torch.backends.cudnn.benchmark = True

    print("Loading processor & model...")
    processor = AutoProcessor.from_pretrained(MODEL_NAME)
    model = Qwen3VLModel.from_pretrained(
        MODEL_NAME,
        torch_dtype=torch.float16 if device == "cuda" else torch.float32,
        device_map=None,
    ).to(device)
    model_xray(model)
import torch
import torch.nn as nn
from datasets import load_dataset
import tqdm

def evaluate_perplexity(
        model, 
        tokenizer, 
        dataset_name: str = "wikitext", 
        subset: str | None = None,
        max_length: int = 2048,
        verbose: bool = False
    ):
    if subset:
        test_data = load_dataset(dataset_name, subset, split="test")
    else:
        # Default to use wikitext-2-raw-v1 for wikitext if subset is not set
        if dataset_name == "wikitext":
            subset = "wikitext-2-raw-v1"
            test_data = load_dataset(dataset_name, subset, split="test")
        else:
            test_data = load_dataset(dataset_name, split="test")

    encoded = tokenizer("\n\n".join(test_data["text"]), return_tensors="pt")
    input_ids = encoded.input_ids.to(model.device)

    model.seqlen = max_length
    model.eval()

    nsamples = input_ids.numel() // max_length
    nlls = []

    for i in tqdm.tqdm(range(nsamples), desc="Evaluating PPL", disable=not verbose):
        batch = input_ids[:, i * max_length : (i + 1) * max_length]
        with torch.no_grad():
            logits = model(batch).logits

        shift_logits = logits[:, :-1, :].contiguous().float()
        shift_labels = batch[:, 1:]
        loss_fct = nn.CrossEntropyLoss()
        loss = loss_fct(shift_logits.view(-1, shift_logits.size(-1)), shift_labels.view(-1))

        nll = loss * max_length
        nlls.append(nll)

    ppl = torch.exp(torch.stack(nlls).sum() / (nsamples * max_length))
    print(f"Perplexity: {ppl.item():.4f}")
    return {"ppl": ppl.item()}
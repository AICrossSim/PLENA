import re
import random
import time

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from datasets import load_dataset
from tqdm import tqdm


SYSTEM_PROMPT = (
    "You are a knowledgeable and trustworthy assistant specialized in solving multiple-choice questions. "
    "Always select and state the most accurate and logically sound answer from the given options: A, B, C, or D.\n\n"
)

SYS_TEMPLATE = "<<SYS>>\n{system_prompt}\n<</SYS>>\n\n"
INST_TEMPLATE = "[INST] {content} [/INST]"

def format_mcq(question: str, choices: list[str], answer_idx: int | None = None) -> str:
    """
    Format a multiple-choice question. Include the correct answer if provided for prompting.
    """
    base = (
        f"{question.strip()}\n"
        f"A. {choices[0].strip()}\n"
        f"B. {choices[1].strip()}\n"
        f"C. {choices[2].strip()}\n"
        f"D. {choices[3].strip()}\n"
    )
    if answer_idx is not None:
        answer_letter = chr(ord("A") + answer_idx)
        base += f"Answer: {answer_letter}\n\n"
    else:
        base += "Answer:"
    return base


def format_instruction_prompt(target_example: dict, dev_set: list[dict] = None, k: int = 0) -> str:
    system_block = SYS_TEMPLATE.format(system_prompt=SYSTEM_PROMPT)

    if k == 0 or not dev_set:
        user_prompt = (
            "Read the following question and choose the correct answer from the given options.\n\n"
            f"{format_mcq(target_example['question'], target_example['choices'])}"
        )
    else:
        shots = random.sample(list(dev_set), k=k)
        few_shot_examples = "\n".join(
            f"Example {i + 1}:\n" + format_mcq(shot["question"], shot["choices"], shot["answer"])
            for i, shot in enumerate(shots)
        )

        final_question = (
            "Now answer the following question:\n" +
            format_mcq(target_example["question"], target_example["choices"])
        )

        user_prompt = (
            "Here are some examples of correctly answered multiple-choice questions:\n\n"
            f"{few_shot_examples}\n{final_question}"
        )

    return INST_TEMPLATE.format(content=system_block + user_prompt)


def extract_choice(output):
    match = re.search(r"\b([ABCD])\b", output)
    # return in index rather than A/B/C/D
    return ord(match.group(1)) - ord('A') if match else None


def eval_qa_mmlu(model, tokenizer, subject_lst, sample_n=None, batch_size=16, k=5):
    model.eval()
    results = {}

    for subject in subject_lst:
        start_time = time.time()
        print(f"\nEvaluating subject: {subject}")
        dataset = load_dataset("cais/mmlu", subject)
        test_set = dataset["test"]
        dev_set = dataset["dev"]

        correct = 0
        total = 0

        test_subset = test_set.select(range(sample_n)) if sample_n else test_set
        all_prompts = []

        for example in test_subset:
            prompt = format_instruction_prompt(example, dev_set, k=k)
            all_prompts.append((prompt, example["answer"]))

        for i in tqdm(range(0, len(all_prompts), batch_size), desc=f"[{subject}]"):
            batch = all_prompts[i:i + batch_size]
            prompts, answers = zip(*batch)

            print(f"\n🔹 Generating answers for batch {i // batch_size + 1}...")

            tokenized = tokenizer(
                list(prompts),
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=2048
            ).to(model.device)

            with torch.no_grad():
                outputs = model.generate(
                    input_ids=tokenized["input_ids"],
                    attention_mask=tokenized["attention_mask"],
                    max_new_tokens=300,
                    pad_token_id=tokenizer.pad_token_id,
                    temperature=0.0,
                    do_sample=False
                )

            # Extract only generated part (exclude prompt)
            generated_tokens = outputs[:, tokenized["input_ids"].shape[1]:]
            decoded_outputs = tokenizer.batch_decode(generated_tokens, skip_special_tokens=True)

            for j, generated in enumerate(decoded_outputs):
                prediction = extract_choice(generated)

                if prediction == answers[j]:
                    correct += 1
                total += 1

        accuracy = correct / total if total > 0 else 0.0
        results[subject] = {
            "accuracy": accuracy,
            "correct": correct,
            "total": total,
            "num_samples": len(test_subset),
            "elapsed_time_sec": time.time() - start_time
        }
        print(results)
    return results

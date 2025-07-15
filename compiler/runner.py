#!/usr/bin/env python3

import sys
from parser import LLMModelParser
from passes.code_gen import code_gen_pass


def run():
    if len(sys.argv) < 3:
        print("Usage: python runner.py <model_name_or_path> <output_file.asm>")
        print("Example: python runner.py AICrossSim/clm-60m output.asm")
        return

    model_path = sys.argv[1]
    output_file = sys.argv[2]

    # Validate that output file ends with .asm
    if not output_file.endswith(".asm"):
        print("Error: Output file must end with .asm extension")
        print("Example: python runner.py AICrossSim/clm-60m output.asm")
        return

    print(f"Loading model: {model_path}")
    parser = LLMModelParser(model_path)

    parser.load_model()
    parser.print_summary()

    # Create symbolic graph
    symbolic_graph = parser.create_symbolic_graph()

    dimensions = parser.extract_critical_dimensions()

    # Print detailed symbolic graph
    parser.print_symbolic_graph_details()

    # Prepare model info for code generation
    model_info = {
        "model_name": model_path,
        "architecture": getattr(parser.config, "architectures", ["Unknown"])[0] if parser.config else "Unknown",
        "hidden_size": dimensions.get("hidden_size", "Unknown"),
        "num_layers": dimensions.get("num_hidden_layers", "Unknown"),
    }

    # Run code generation pass
    print(f"\nRunning code generation pass...")
    generated_asm = code_gen_pass(symbolic_graph, model_info)

    # Save generated code
    with open(output_file, "w") as f:
        f.write(generated_asm)

    print(f"Generated assembly code saved to: {output_file}")

    # Print a preview of the generated code
    print(f"\nGenerated code preview (first 20 lines):")
    print("=" * 50)
    lines = generated_asm.split("\n")
    for i, line in enumerate(lines[:20]):
        print(f"{i + 1:3d}: {line}")
    if len(lines) > 20:
        print(f"... and {len(lines) - 20} more lines")
    print("=" * 50)


if __name__ == "__main__":
    sys.exit(run())
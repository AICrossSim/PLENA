import math
import re
import shutil
import subprocess
import sys
from pathlib import Path

from config_utils import update_plena_config, reset_plena_config


LATENCY_RE = re.compile(r"Simulation completed\. Latency (\d+)\.(\d{3})ns")


def parse_latency_ns(output: str) -> float:
    match = LATENCY_RE.search(output)
    if not match:
        raise RuntimeError("Could not find latency in simulator output.")
    ns_whole = int(match.group(1))
    ns_frac = int(match.group(2))
    return ns_whole + (ns_frac / 1000.0)


def required_vsram_rows(
    seq_len: int,
    num_q_heads: int,
    num_kv_heads: int,
    head_dim: int,
    vlen: int,
    mlen: int,
) -> int:
    q_index_ratio = num_q_heads // num_kv_heads
    q_base = 0
    s_base = q_base + num_q_heads * num_kv_heads * seq_len
    pv_base = s_base + mlen * mlen * q_index_ratio
    o_base = pv_base + mlen * mlen * q_index_ratio
    o_size = seq_len * head_dim * num_q_heads
    total_elements = o_base + o_size
    return math.ceil(total_elements / vlen)


def required_vsram_rows_elementwise(
    hidden_size: int,
    batch_size: int,
    vlen: int,
) -> int:
    loop_iteration = hidden_size // vlen
    total_iters = batch_size * loop_iteration
    if total_iters <= 0:
        return max(1, math.ceil((hidden_size * batch_size) / vlen))
    base = hidden_size * batch_size
    max_addr = base + hidden_size * (total_iters - 1)
    return math.ceil((max_addr + vlen) / vlen)


def required_vsram_rows_ffn(
    hidden_size: int,
    intermediate_size: int,
    batch_size: int,
    seq_len: int,
    vlen: int,
) -> int:
    total_elements = batch_size * seq_len * (hidden_size + 2 * intermediate_size)
    return math.ceil(total_elements / vlen)


def run_kernel(
    name: str,
    test_file: Path,
    test_args: list[str],
    repo_root: Path,
) -> float:
    build_dir = repo_root / "behavioral_simulator" / "testbench" / "build"
    shutil.rmtree(build_dir, ignore_errors=True)

    subprocess.run([sys.executable, str(test_file), *test_args], check=True)

    asm_path = build_dir / "generated_machine_code.mem"
    hbm_path = build_dir / "hbm_for_behave_sim.bin"
    fp_sram_path = build_dir / "fp_sram.bin"
    int_sram_path = build_dir / "int_sram.bin"

    cargo_cmd = [
        "cargo",
        "run",
        "--release",
        "--",
        "--opcode",
        str(asm_path),
        "--hbm",
        str(hbm_path),
        "--fpsram",
        str(fp_sram_path),
        "--intsram",
        str(int_sram_path),
        "--quiet",
    ]
    result = subprocess.run(
        cargo_cmd,
        cwd=repo_root / "behavioral_simulator",
        capture_output=True,
        text=True,
    )
    output = (result.stdout or "") + (result.stderr or "")
    if result.returncode != 0:
        raise RuntimeError(f"{name} failed:\n{output}")

    return parse_latency_ns(output)


def main() -> None:
    reset_plena_config(verbose=True)
    # Fast, ratio-preserving scaled config for prefill latency.
    seq_len = 64
    batch_size = 1
    vlen = 64
    mlen = 64
    blen = 4
    hidden_size = 64
    intermediate_size = 256
    num_attention_heads = 4
    num_kv_heads = 4
    head_dim = 16
    num_hidden_layers = 16
    rms_norm_eps = 1e-5

    repo_root = Path(__file__).resolve().parents[2]
    testbench_dir = repo_root / "behavioral_simulator" / "testbench"

    effective_batch = batch_size * seq_len
    vsram_rows_attn = required_vsram_rows(
        seq_len=seq_len,
        num_q_heads=num_attention_heads,
        num_kv_heads=num_kv_heads,
        head_dim=head_dim,
        vlen=vlen,
        mlen=mlen,
    )
    vsram_rows_residual = required_vsram_rows_elementwise(
        hidden_size=hidden_size,
        batch_size=effective_batch,
        vlen=vlen,
    )
    vsram_rows_ffn = required_vsram_rows_ffn(
        hidden_size=hidden_size,
        intermediate_size=intermediate_size,
        batch_size=batch_size,
        seq_len=seq_len,
        vlen=vlen,
    )
    vsram_rows = max(vsram_rows_attn, vsram_rows_residual, vsram_rows_ffn)
    update_plena_config(
        vlen=vlen,
        mlen=mlen,
        blen=blen,
        hbm_m_prefetch_amount=mlen,
        vector_sram_size=vsram_rows,
    )

    kv_dim = num_kv_heads * head_dim
    kernels = [
        (
            "rms_norm",
            testbench_dir / "rms_test.py",
            [
                "--hidden-size",
                str(hidden_size),
                "--batch-size",
                str(effective_batch),
                "--vlen",
                str(vlen),
                "--mlen",
                str(mlen),
                "--eps",
                str(rms_norm_eps),
            ],
            2,
        ),
        (
            "proj_q",
            testbench_dir / "linear_test.py",
            [
                "--in-features",
                str(hidden_size),
                "--out-features",
                str(hidden_size),
                "--batch-size",
                str(effective_batch),
                "--vlen",
                str(vlen),
                "--mlen",
                str(mlen),
                "--blen",
                str(blen),
            ],
            1,
        ),
        (
            "proj_kv",
            testbench_dir / "linear_test.py",
            [
                "--in-features",
                str(hidden_size),
                "--out-features",
                str(kv_dim),
                "--batch-size",
                str(effective_batch),
                "--vlen",
                str(vlen),
                "--mlen",
                str(mlen),
                "--blen",
                str(blen),
            ],
            2,
        ),
        (
            "attention",
            testbench_dir / "attn_test.py",
            [
                "--batch-size",
                str(batch_size),
                "--s-q",
                str(seq_len),
                "--s-kv",
                str(seq_len),
                "--num-q-heads",
                str(num_attention_heads),
                "--num-kv-heads",
                str(num_kv_heads),
                "--head-dim",
                str(head_dim),
                "--vlen",
                str(vlen),
                "--mlen",
                str(mlen),
                "--blen",
                str(blen),
            ],
            1,
        ),
        (
            "residual_add",
            testbench_dir / "elementwise_add_test.py",
            [
                "--hidden-size",
                str(hidden_size),
                "--batch-size",
                str(effective_batch),
                "--vlen",
                str(vlen),
                "--mlen",
                str(mlen),
                "--blen",
                str(blen),
            ],
            2,
        ),
        (
            "ffn",
            testbench_dir / "ffn_test.py",
            [
                "--hidden-size",
                str(hidden_size),
                "--inter-dim",
                str(intermediate_size),
                "--batch-size",
                str(batch_size),
                "--seq-len",
                str(seq_len),
                "--vlen",
                str(vlen),
                "--mlen",
                str(mlen),
                "--blen",
                str(blen),
            ],
            1,
        ),
    ]

    total_ns = 0.0
    print("Kernel latency breakdown (ns):")
    try:
        for name, test_file, test_args, count in kernels:
            latency_ns = run_kernel(name, test_file, test_args, repo_root)
            total_ns += latency_ns * count
            count_suffix = f" x{count}" if count > 1 else ""
            print(f"- {name}{count_suffix}: {latency_ns:.3f} ns")
    finally:
        reset_plena_config(verbose=True)

    print(f"Total single-layer prefill latency: {total_ns:.3f} ns")
    full_latency_ns = total_ns * num_hidden_layers
    total_tokens = batch_size * seq_len
    throughput_tps = total_tokens / (full_latency_ns * 1e-9)
    print(f"Total prefill latency ({num_hidden_layers} layers): {full_latency_ns:.3f} ns")
    print(f"Prefill throughput: {throughput_tps:.3f} tokens/s (batch={batch_size}, seq_len={seq_len})")


if __name__ == "__main__":
    main()

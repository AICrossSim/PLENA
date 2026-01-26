"""
Utility functions for managing hardware configuration across tests.
"""

import re
from pathlib import Path
from typing import Optional


def update_plena_config(
    vlen: Optional[int] = None,
    mlen: Optional[int] = None,
    blen: Optional[int] = None,
    hlen: Optional[int] = None,
    broadcast_amount: Optional[int] = None,
    matrix_sram_size: Optional[int] = None,
    vector_sram_size: Optional[int] = None,
    hbm_m_prefetch_amount: Optional[int] = None,
    verbose: bool = True
) -> None:
    """
    Update plena_settings.toml with test-specific hardware parameters.
    Uses simple string replacement to avoid tomlkit dependency.
    """
    plena_settings_path = Path(__file__).parent.parent.parent / "src" / "definitions" / "plena_settings.toml"

    with open(plena_settings_path, 'r') as f:
        content = f.read()

    def require_positive(name: str, value: Optional[int]) -> None:
        if value is not None and value <= 0:
            raise ValueError(f"{name} must be a positive integer, got {value}")

    def get_config_value(key: str) -> int:
        match = re.search(rf'\[CONFIG\.{re.escape(key)}\]\s*\nvalue\s*=\s*(\d+)', content)
        if not match:
            raise ValueError(f"Missing CONFIG.{key} value in plena_settings.toml")
        return int(match.group(1))

    def replace_config_value(updated_content: str, key: str, value: int) -> str:
        return re.sub(
            rf'(\[CONFIG\.{re.escape(key)}\]\s*\nvalue\s*=\s*)\d+',
            f'\\g<1>{value}',
            updated_content
        )

    require_positive("vlen", vlen)
    require_positive("mlen", mlen)
    require_positive("blen", blen)
    require_positive("hlen", hlen)
    require_positive("broadcast_amount", broadcast_amount)
    require_positive("matrix_sram_size", matrix_sram_size)
    require_positive("vector_sram_size", vector_sram_size)
    require_positive("hbm_m_prefetch_amount", hbm_m_prefetch_amount)

    current_mlen = get_config_value("MLEN")
    next_mlen = mlen if mlen is not None else current_mlen
    current_hlen = get_config_value("HLEN")
    next_hlen = hlen if hlen is not None else current_hlen
    current_broadcast_amount = get_config_value("BROADCAST_AMOUNT")
    next_broadcast_amount = (
        broadcast_amount if broadcast_amount is not None else current_broadcast_amount
    )

    if next_broadcast_amount * next_hlen != next_mlen:
        raise ValueError(
            "BROADCAST_AMOUNT * HLEN must equal MLEN "
            f"(got BROADCAST_AMOUNT={next_broadcast_amount}, HLEN={next_hlen}, MLEN={next_mlen})"
        )

    current_hbm_m_prefetch_amount = get_config_value("HBM_M_Prefetch_Amount")
    next_hbm_m_prefetch_amount = (
        hbm_m_prefetch_amount
        if hbm_m_prefetch_amount is not None
        else current_hbm_m_prefetch_amount
    )

    if next_hbm_m_prefetch_amount % next_mlen != 0:
        raise ValueError(
            "HBM_M_Prefetch_Amount must be a multiple of MLEN "
            f"(got HBM_M_Prefetch_Amount={next_hbm_m_prefetch_amount}, MLEN={next_mlen})"
        )

    updated = []

    if vlen is not None:
        content = replace_config_value(content, "VLEN", vlen)
        updated.append(f"VLEN={vlen}")

    if mlen is not None:
        content = replace_config_value(content, "MLEN", mlen)
        updated.append(f"MLEN={mlen}")

    if blen is not None:
        content = replace_config_value(content, "BLEN", blen)
        updated.append(f"BLEN={blen}")
    if hlen is not None:
        content = replace_config_value(content, "HLEN", hlen)
        updated.append(f"HLEN={hlen}")
    if broadcast_amount is not None:
        content = replace_config_value(content, "BROADCAST_AMOUNT", broadcast_amount)
        updated.append(f"BROADCAST_AMOUNT={broadcast_amount}")
    if matrix_sram_size is not None:
        content = replace_config_value(content, "MATRIX_SRAM_SIZE", matrix_sram_size)
        updated.append(f"MATRIX_SRAM_SIZE={matrix_sram_size}")
    if vector_sram_size is not None:
        content = replace_config_value(content, "VECTOR_SRAM_SIZE", vector_sram_size)
        updated.append(f"VECTOR_SRAM_SIZE={vector_sram_size}")
    if hbm_m_prefetch_amount is not None:
        content = replace_config_value(content, "HBM_M_Prefetch_Amount", hbm_m_prefetch_amount)
        updated.append(f"HBM_M_Prefetch_Amount={hbm_m_prefetch_amount}")

    with open(plena_settings_path, 'w') as f:
        f.write(content)

    if verbose and updated:
        print(f"Updated plena_settings.toml: {', '.join(updated)}")


def get_comparison_params(
    vlen: int,
    batch_size: int,
    hidden_size: int,
    result_vram_offset: int = 0,
    use_stride_mode: Optional[bool] = None
) -> dict:
    """
    Generate comparison parameters for view_mem.py based on test configuration.
    """
    result_start_row = result_vram_offset // vlen
    num_result_rows = (batch_size * hidden_size) // vlen

    if use_stride_mode is None:
        use_stride_mode = (hidden_size > vlen)

    return {
        "start_row_idx": result_start_row,
        "num_rows": num_result_rows,
        "num_batches": batch_size,
        "elements_per_batch": hidden_size,
        "row_dim": vlen,
        "use_stride_mode": use_stride_mode
    }


def reset_plena_config(verbose: bool = True) -> None:
    """
    Reset plena_settings.toml back to the default configuration.
    """
    base_dir = Path(__file__).parent.parent.parent / "src" / "definitions"
    plena_settings_path = base_dir / "plena_settings.toml"
    default_settings_path = base_dir / "plena_settings.default.toml"

    if not default_settings_path.exists():
        raise FileNotFoundError(f"Missing default config: {default_settings_path}")

    with open(default_settings_path, 'r') as f:
        content = f.read()

    with open(plena_settings_path, 'w') as f:
        f.write(content)

    if verbose:
        print("Reset plena_settings.toml to plena_settings.default.toml")

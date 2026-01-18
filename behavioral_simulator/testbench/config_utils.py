"""
Utility functions for managing hardware configuration across tests.
"""

import tomlkit
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

    Args:
        vlen: Vector length. If None, keeps current value.
        mlen: Matrix tile length. If None, keeps current value.
        blen: Batch tile length. If None, keeps current value.
        hlen: Systolic array height. If None, keeps current value.
        broadcast_amount: Broadcast lanes. Must satisfy broadcast_amount * hlen == mlen.
        matrix_sram_size: Matrix SRAM depth. If None, keeps current value.
        vector_sram_size: Vector SRAM depth. If None, keeps current value.
        hbm_m_prefetch_amount: Matrix prefetch amount (HBM_M_Prefetch_Amount).
            Must be a positive multiple of MLEN.
        verbose: If True, print the updated configuration.

    Example:
        # Update both vlen and mlen
        update_plena_config(vlen=128, mlen=128)

        # Update only vlen
        update_plena_config(vlen=64)

        # Update MLEN and matrix prefetch amount together
        update_plena_config(mlen=128, hbm_m_prefetch_amount=128)

        # Update MLEN with matching broadcast configuration
        update_plena_config(mlen=128, hlen=16, broadcast_amount=8)
    """
    plena_settings_path = Path(__file__).parent.parent.parent / "src" / "definitions" / "plena_settings.toml"

    with open(plena_settings_path, 'r') as f:
        config = tomlkit.load(f)

    def require_positive(name: str, value: Optional[int]) -> None:
        if value is not None and value <= 0:
            raise ValueError(f"{name} must be a positive integer, got {value}")

    require_positive("vlen", vlen)
    require_positive("mlen", mlen)
    require_positive("blen", blen)
    require_positive("hlen", hlen)
    require_positive("broadcast_amount", broadcast_amount)
    require_positive("matrix_sram_size", matrix_sram_size)
    require_positive("vector_sram_size", vector_sram_size)
    require_positive("hbm_m_prefetch_amount", hbm_m_prefetch_amount)

    current_mlen = int(config['CONFIG']['MLEN']['value'])
    next_mlen = mlen if mlen is not None else current_mlen
    current_hlen = int(config['CONFIG']['HLEN']['value'])
    next_hlen = hlen if hlen is not None else current_hlen
    current_broadcast_amount = int(config['CONFIG']['BROADCAST_AMOUNT']['value'])
    next_broadcast_amount = (
        broadcast_amount if broadcast_amount is not None else current_broadcast_amount
    )

    if next_broadcast_amount * next_hlen != next_mlen:
        raise ValueError(
            "BROADCAST_AMOUNT * HLEN must equal MLEN "
            f"(got BROADCAST_AMOUNT={next_broadcast_amount}, HLEN={next_hlen}, MLEN={next_mlen})"
        )

    current_hbm_m_prefetch_amount = int(config['CONFIG']['HBM_M_Prefetch_Amount']['value'])
    next_hbm_m_prefetch_amount = (
        hbm_m_prefetch_amount
        if hbm_m_prefetch_amount is not None
        else current_hbm_m_prefetch_amount
    )

    # HBM_M_Prefetch_Amount must be a multiple of MLEN
    if next_hbm_m_prefetch_amount % next_mlen != 0:
        raise ValueError(
            "HBM_M_Prefetch_Amount must be a multiple of MLEN "
            f"(got HBM_M_Prefetch_Amount={next_hbm_m_prefetch_amount}, MLEN={next_mlen})"
        )

    updated = []
    if vlen is not None:
        config['CONFIG']['VLEN']['value'] = vlen
        updated.append(f"VLEN={vlen}")
    if mlen is not None:
        config['CONFIG']['MLEN']['value'] = mlen
        updated.append(f"MLEN={mlen}")
    if blen is not None:
        config['CONFIG']['BLEN']['value'] = blen
        updated.append(f"BLEN={blen}")
    if hlen is not None:
        config['CONFIG']['HLEN']['value'] = hlen
        updated.append(f"HLEN={hlen}")
    if broadcast_amount is not None:
        config['CONFIG']['BROADCAST_AMOUNT']['value'] = broadcast_amount
        updated.append(f"BROADCAST_AMOUNT={broadcast_amount}")
    if matrix_sram_size is not None:
        config['CONFIG']['MATRIX_SRAM_SIZE']['value'] = matrix_sram_size
        updated.append(f"MATRIX_SRAM_SIZE={matrix_sram_size}")
    if vector_sram_size is not None:
        config['CONFIG']['VECTOR_SRAM_SIZE']['value'] = vector_sram_size
        updated.append(f"VECTOR_SRAM_SIZE={vector_sram_size}")
    if hbm_m_prefetch_amount is not None:
        config['CONFIG']['HBM_M_Prefetch_Amount']['value'] = hbm_m_prefetch_amount
        updated.append(f"HBM_M_Prefetch_Amount={hbm_m_prefetch_amount}")

    with open(plena_settings_path, 'w') as f:
        tomlkit.dump(config, f)

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

    Args:
        vlen: Vector length used in the test
        batch_size: Number of batches
        hidden_size: Hidden dimension size (elements per batch)
        result_vram_offset: Starting address in VRAM where results are stored
        use_stride_mode: If None, automatically determined based on vlen vs hidden_size.
                        If True/False, uses that value explicitly.

    Returns:
        Dictionary of comparison parameters for view_mem.py

    Note:
        Stride mode is used when vlen < hidden_size (multiple vectors per batch).
        Batch-wise mode is used when vlen >= hidden_size (one vector per batch).
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

    Args:
        verbose: If True, print the reset action.
    """
    base_dir = Path(__file__).parent.parent.parent / "src" / "definitions"
    plena_settings_path = base_dir / "plena_settings.toml"
    default_settings_path = base_dir / "plena_settings.default.toml"

    if not default_settings_path.exists():
        raise FileNotFoundError(f"Missing default config: {default_settings_path}")

    with open(default_settings_path, 'r') as f:
        config = tomlkit.load(f)

    with open(plena_settings_path, 'w') as f:
        tomlkit.dump(config, f)

    if verbose:
        print("Reset plena_settings.toml to plena_settings.default.toml")

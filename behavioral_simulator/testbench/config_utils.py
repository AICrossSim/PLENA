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
    verbose: bool = True
) -> None:
    """
    Update plena_settings.toml with test-specific hardware parameters.
    Uses simple string replacement to avoid tomlkit dependency.
    """
    plena_settings_path = Path(__file__).parent.parent.parent / "src" / "definitions" / "plena_settings.toml"

    with open(plena_settings_path, 'r') as f:
        content = f.read()

    updated = []

    if vlen is not None:
        # Match [CONFIG.VLEN] section and update value
        content = re.sub(
            r'(\[CONFIG\.VLEN\]\s*\nvalue\s*=\s*)\d+',
            f'\\g<1>{vlen}',
            content
        )
        updated.append(f"VLEN={vlen}")

    if mlen is not None:
        content = re.sub(
            r'(\[CONFIG\.MLEN\]\s*\nvalue\s*=\s*)\d+',
            f'\\g<1>{mlen}',
            content
        )
        updated.append(f"MLEN={mlen}")

    if blen is not None:
        content = re.sub(
            r'(\[CONFIG\.BLEN\]\s*\nvalue\s*=\s*)\d+',
            f'\\g<1>{blen}',
            content
        )
        updated.append(f"BLEN={blen}")

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

import numpy as np
import re
import os


def parse_golden_output(golden_file_path):
    """
    Parse the "Original Output" section from golden_result.txt.

    Args:
        golden_file_path: Path to the golden_result.txt file

    Returns:
        numpy array: Flattened 1D array of all values from Original Output
    """
    with open(golden_file_path, 'r') as f:
        content = f.read()

    # Find the "Original Output:" section
    match = re.search(r'Original Output:\s*\[(.*?)\]', content, re.DOTALL)
    if not match:
        raise ValueError("Could not find 'Original Output' section in golden file")

    # Extract the values section
    values_text = match.group(1)

    # Parse all floating point numbers (handles negative, positive, scientific notation)
    values = []
    for line in values_text.strip().split('\n'):
        line = line.strip()
        if not line:
            continue
        # Split by whitespace and parse each value
        for val_str in line.split():
            try:
                val = float(val_str)
                values.append(val)
            except ValueError:
                continue

    return np.array(values, dtype=np.float32)


def read_bin_file_as_array(bin_file,
                           exp_width,
                           man_width,
                           row_dim,
                           num_bytes_per_val=2,
                           start_row_idx=0,
                           num_rows=None):
    """
    Read binary file and convert to numpy array (similar to view_bin_file_by_row but returns array).
    Uses the same row-based indexing logic as view_bin_file_by_row.

    Args:
        bin_file: Path to binary file
        exp_width: Number of bits for exponent
        man_width: Number of bits for mantissa
        row_dim: Number of values per row (must match view_bin_file_by_row)
        num_bytes_per_val: Number of bytes per value (default 2 for BF16)
        start_row_idx: Starting row index
        num_rows: Number of rows to read (None = read all remaining rows)

    Returns:
        numpy array: Flattened 1D array of values, respecting row boundaries
    """
    sign_width = 1
    total_width = sign_width + exp_width + man_width
    if total_width > num_bytes_per_val * 8:
        raise ValueError("num_bytes_per_val is too small for given bit widths.")

    def raw_to_fp(bits_val):
        """Convert raw bits to floating point value."""
        sign = (bits_val >> (exp_width + man_width)) & 0x1
        exponent = (bits_val >> man_width) & ((1 << exp_width) - 1)
        mantissa = bits_val & ((1 << man_width) - 1)
        bias = (1 << (exp_width - 1)) - 1 if exp_width > 0 else 0

        if exp_width == 0:
            base = float(mantissa)
        else:
            if exponent == 0:
                if mantissa == 0:
                    return 0.0 if sign == 0 else -0.0
                base = mantissa / (2 ** man_width)
                exp_val = 1 - bias
                return ((-1) ** sign) * base * (2 ** exp_val)
            elif exponent == (1 << exp_width) - 1:
                if mantissa == 0:
                    return float('-inf') if sign else float('inf')
                else:
                    return float('nan')
            else:
                base = 1 + mantissa / (2 ** man_width)
                exp_val = exponent - bias
                return ((-1) ** sign) * base * (2 ** exp_val)
        return ((-1) ** sign) * base

    with open(bin_file, "rb") as f:
        data = f.read()

    num_vals = len(data) // num_bytes_per_val
    total_rows = (num_vals + row_dim - 1) // row_dim

    # Calculate which rows to read
    end_row_idx = total_rows if num_rows is None else start_row_idx + num_rows

    values = []
    # Iterate through rows, matching the logic of view_bin_file_by_row
    for row_idx in range(start_row_idx, end_row_idx):
        for col_idx in range(row_dim):
            val_idx = row_idx * row_dim + col_idx
            if val_idx >= num_vals:
                # Reached end of data, pad with None or break
                break
            chunk = data[val_idx * num_bytes_per_val : (val_idx + 1) * num_bytes_per_val]
            if not chunk or len(chunk) < num_bytes_per_val:
                break
            # Use little-endian byte order to match Rust's byte packing
            bits_val = int.from_bytes(chunk, byteorder='little')
            float_val = raw_to_fp(bits_val)
            values.append(float_val)

    return np.array(values, dtype=np.float32)


def reorder_stride_mode(data, num_batches=4, elements_per_batch=128, stride=64):
    """
    Reorder stride-mode data to batch-wise layout.

    Stride mode layout (how data is stored in VRAM):
        For elements_per_batch=128: 2 chunks per batch
        [Batch0[0:64], Batch1[0:64], Batch2[0:64], Batch3[0:64],
         Batch0[64:128], Batch1[64:128], Batch2[64:128], Batch3[64:128]]

        For elements_per_batch=256: 4 chunks per batch
        [Batch0[0:64], Batch1[0:64], Batch2[0:64], Batch3[0:64],
         Batch0[64:128], Batch1[64:128], Batch2[64:128], Batch3[64:128],
         Batch0[128:192], Batch1[128:192], Batch2[128:192], Batch3[128:192],
         Batch0[192:256], Batch1[192:256], Batch2[192:256], Batch3[192:256]]

    Batch-wise layout (how golden data is organized):
        [Batch0[0:elements_per_batch], Batch1[...], ...]

    Args:
        data: 1D numpy array in stride mode
        num_batches: Number of batches (default 4)
        elements_per_batch: Elements per batch (default 128)
        stride: Stride size in stride mode (default 64, typically mlen)

    Returns:
        Reordered 1D numpy array in batch-wise layout
    """
    chunk_size = stride  # Stride mode uses chunks of 'stride' elements (typically mlen=64)
    chunks_per_batch = elements_per_batch // stride
    total_chunks = len(data) // chunk_size
    expected_chunks = num_batches * chunks_per_batch

    if total_chunks != expected_chunks:
        print(f"Warning: Expected {expected_chunks} chunks, got {total_chunks}")

    # Reshape into chunks: [chunk0, chunk1, ..., chunk_n]
    chunks = data.reshape(total_chunks, chunk_size)

    # Reorder: group all chunks for each batch together
    # For 4 batches with 4 chunks each (256 elements):
    #   batch0: chunks 0, 4, 8, 12
    #   batch1: chunks 1, 5, 9, 13
    #   batch2: chunks 2, 6, 10, 14
    #   batch3: chunks 3, 7, 11, 15
    reordered_chunks = []
    for batch_idx in range(num_batches):
        for chunk_group in range(chunks_per_batch):
            chunk_idx = chunk_group * num_batches + batch_idx
            reordered_chunks.append(chunks[chunk_idx])

    return np.concatenate(reordered_chunks)


def compare_with_golden(bin_file,
                        golden_file,
                        exp_width=8,
                        man_width=7,
                        num_bytes_per_val=2,
                        row_dim=64,
                        start_row_idx=0,
                        num_batches=4,
                        num_rows=None,
                        tolerance=1,
                        use_stride_mode=True,
                        elements_per_batch=128):
    """
    Compare binary file output with golden reference from golden_result.txt.

    Args:
        bin_file: Path to binary file to compare
        golden_file: Path to golden_result.txt file
        exp_width: Exponent width for binary file parsing
        man_width: Mantissa width for binary file parsing
        num_bytes_per_val: Bytes per value in binary file
        row_dim: Row dimension (for determining which rows to compare)
        start_row_idx: Starting row index to compare
        num_rows: Number of rows to compare (None = compare all)
        tolerance: Tolerance for comparison (used for reporting)
        use_stride_mode: Whether to reorder data from stride mode to batch-wise layout

    Returns:
        dict: Dictionary containing comparison metrics:
            - 'mse': Mean Squared Error
            - 'mae': Mean Absolute Error
            - 'max_error': Maximum absolute error
            - 'relative_error': Mean relative error
            - 'match_rate': Percentage of values within tolerance
            - 'golden_shape': Shape of golden array
            - 'simulated_shape': Shape of simulated array
            - 'errors': Array of absolute errors
    """
    # Parse golden output
    golden_values = parse_golden_output(golden_file)
    # Read binary file (now properly handles row-based indexing)
    simulated_values = read_bin_file_as_array(
        bin_file, exp_width, man_width, row_dim, num_bytes_per_val, start_row_idx, num_rows
    )

    # Reorder stride-mode data to match batch-wise golden layout
    if use_stride_mode:
        print("Reordering stride-mode data to batch-wise layout...")
        simulated_values = reorder_stride_mode(simulated_values, num_batches, elements_per_batch)

    # Ensure dimensions match by truncating to the smaller size
    min_len = min(len(golden_values), len(simulated_values))
    golden_values = golden_values[:min_len]
    simulated_values = simulated_values[:min_len]

    # To print all values without truncation (even for high-dimensional arrays):
    import numpy as np
    np.set_printoptions(threshold=np.inf, linewidth=200, edgeitems=20, suppress=True)
    print("golden_values is:\n", golden_values)
    print("golden_values shape is:\n", golden_values.shape)
    print("simulated_values is:\n", simulated_values)
    print("simulated_values shape is:\n", simulated_values.shape)
    # breakpoint()

    if len(golden_values) == 0:
        raise ValueError("No values to compare")

    # Compute errors
    errors = np.abs(golden_values - simulated_values)

    # Compute metrics
    mse = np.mean((golden_values - simulated_values) ** 2)
    mae = np.mean(errors)
    max_error = np.max(errors)

    # Relative error (avoid division by zero)
    with np.errstate(divide='ignore', invalid='ignore'):
        relative_errors = np.where(
            np.abs(golden_values) > 1e-10,
            errors / np.abs(golden_values),
            errors
        )
    mean_relative_error = np.mean(relative_errors)

    # Match rate (within tolerance)
    within_tolerance = errors <= tolerance
    match_rate = np.sum(within_tolerance) / len(errors) * 100.0

    return {
        'mse': mse,
        'mae': mae,
        'max_error': max_error,
        'relative_error': mean_relative_error,
        'match_rate': match_rate,
        'golden_shape': golden_values.shape,
        'simulated_shape': simulated_values.shape,
        'errors': errors,
        'golden_values': golden_values,
        'simulated_values': simulated_values
    }


def print_comparison_results(results, verbose=False):
    """
    Print comparison results in a readable format.

    Args:
        results: Dictionary returned by compare_with_golden
        verbose: If True, print detailed error statistics
    """
    print("=" * 60)
    print("Comparison Results")
    print("=" * 60)
    print(f"Golden values shape:     {results['golden_shape']}")
    print(f"Simulated values shape:  {results['simulated_shape']}")
    print(f"Number of values:        {len(results['golden_values'])}")
    print()
    print("Error Metrics:")
    print(f"  Mean Squared Error (MSE):     {results['mse']:.6e}")
    print(f"  Mean Absolute Error (MAE):    {results['mae']:.6f}")
    print(f"  Maximum Absolute Error:      {results['max_error']:.6f}")
    print(f"  Mean Relative Error:          {results['relative_error']:.6f}")
    print()

    if verbose:
        errors = results['errors']
        print("Error Statistics:")
        print(f"  Min error:                  {np.min(errors):.6f}")
        print(f"  Max error:                  {np.max(errors):.6f}")
        print(f"  Median error:               {np.median(errors):.6f}")
        print(f"  Std deviation:             {np.std(errors):.6f}")
        print()

        # Find indices with largest errors
        top_5_indices = np.argsort(errors)[-5:][::-1]
        print("Top 5 Largest Errors:")
        for idx in top_5_indices:
            print(f"  Index {idx:4d}: Golden={results['golden_values'][idx]:8.4f}, "
                  f"Simulated={results['simulated_values'][idx]:8.4f}, "
                  f"Error={errors[idx]:.6f}")


if __name__ == "__main__":
    # Example usage
    script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    golden_file = os.path.join(script_dir, "behavioral_simulator", "testbench", "build", "golden_result.txt")
    vram_file = os.path.join(script_dir, "behavioral_simulator", "vram_dump.bin")

    if os.path.exists(golden_file) and os.path.exists(vram_file):
        results = compare_with_golden(
            vram_file,
            golden_file,
            exp_width=8,
            man_width=7,
            num_bytes_per_val=2,
            row_dim=64,
            start_row_idx=0,
            num_rows=4,
            use_stride_mode=True
        )
        print_comparison_results(results, verbose=True)
    else:
        print(f"Files not found:")
        print(f"  Golden: {golden_file}")
        print(f"  VRAM:   {vram_file}")
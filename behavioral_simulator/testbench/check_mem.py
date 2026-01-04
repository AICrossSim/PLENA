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


def reorder_stride_mode(data, num_batches=4, elements_per_batch=128):
    """
    Reorder stride-mode data to batch-wise layout.

    Stride mode layout (how data is stored in VRAM):
        [Batch0[0:64], Batch1[0:64], Batch2[0:64], Batch3[0:64],
         Batch0[64:128], Batch1[64:128], Batch2[64:128], Batch3[64:128]]

    Batch-wise layout (how golden data is organized):
        [Batch0[0:128], Batch1[0:128], Batch2[0:128], Batch3[0:128]]

    Args:
        data: 1D numpy array in stride mode
        num_batches: Number of batches (default 4)
        elements_per_batch: Elements per batch (default 128)

    Returns:
        Reordered 1D numpy array in batch-wise layout
    """
    chunk_size = elements_per_batch // 2  # 64 elements per chunk
    total_chunks = len(data) // chunk_size

    if total_chunks != num_batches * 2:
        print(f"Warning: Expected {num_batches * 2} chunks, got {total_chunks}")

    # Reshape into chunks: [chunk0, chunk1, ..., chunk7]
    chunks = data.reshape(total_chunks, chunk_size)

    # Reorder: [chunk0, chunk4, chunk1, chunk5, chunk2, chunk6, chunk3, chunk7]
    # This groups each batch's two halves together
    reordered_chunks = []
    for batch_idx in range(num_batches):
        reordered_chunks.append(chunks[batch_idx])                  # First 64 elements
        reordered_chunks.append(chunks[batch_idx + num_batches])    # Last 64 elements

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
    print("golden_values is:\n", golden_values)
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


def read_bin_file_as_int_array(bin_file,
                               row_dim,
                               int_width=32,
                               num_bytes_per_val=4,
                               start_row_idx=0,
                               num_rows=None,
                               signed=False):
    """
    Read binary file and convert to numpy array of integers.

    Args:
        bin_file: Path to binary file
        row_dim: Number of values per row
        int_width: Bit width of the integer (default 32)
        num_bytes_per_val: Number of bytes per value (default 4 for u32)
        start_row_idx: Starting row index
        num_rows: Number of rows to read (None = read all remaining rows)
        signed: If True, interpret as signed integer

    Returns:
        numpy array: Flattened 1D array of integer values
    """
    with open(bin_file, "rb") as f:
        data = f.read()

    num_vals = len(data) // num_bytes_per_val
    total_rows = (num_vals + row_dim - 1) // row_dim

    end_row_idx = total_rows if num_rows is None else start_row_idx + num_rows

    values = []
    for row_idx in range(start_row_idx, end_row_idx):
        for col_idx in range(row_dim):
            val_idx = row_idx * row_dim + col_idx
            if val_idx >= num_vals:
                break
            chunk = data[val_idx * num_bytes_per_val : (val_idx + 1) * num_bytes_per_val]
            if not chunk or len(chunk) < num_bytes_per_val:
                break
            int_val = int.from_bytes(chunk, byteorder='little', signed=signed)
            values.append(int_val)

    return np.array(values, dtype=np.int32 if signed else np.uint32)


def parse_golden_int_output(golden_file_path, section_name="Int SRAM Output"):
    """
    Parse integer values from golden_result.txt or a similar file.

    Args:
        golden_file_path: Path to the golden file
        section_name: Section name to look for (default "Int SRAM Output")
                      If "Original Output" is used, it will parse the Original Output section
                      which contains argmax results as integers (stored as floats)

    Returns:
        numpy array: Flattened 1D array of integer values
    """
    with open(golden_file_path, 'r') as f:
        content = f.read()

    match = re.search(rf'{section_name}:\s*\[(.*?)\]', content, re.DOTALL)
    if not match:
        match = re.search(rf'{section_name}:\s*(.*?)(?=\n\n|\Z)', content, re.DOTALL)
        if not match:
            if section_name == "Int SRAM Output":
                match = re.search(r'Original Output:\s*\[(.*?)\]', content, re.DOTALL)
                if not match:
                    return None
            else:
                return None

    values_text = match.group(1) if match.lastindex >= 1 else match.group(0)

    values = []
    for line in values_text.strip().split('\n'):
        line = line.strip()
        if not line:
            continue
        for val_str in line.split():
            try:
                val = int(float(val_str))
                values.append(val)
            except ValueError:
                continue

    return np.array(values, dtype=np.int32) if len(values) > 0 else None


def compare_int_with_golden(bin_file,
                            golden_file,
                            row_dim=64,
                            int_width=32,
                            num_bytes_per_val=4,
                            start_row_idx=0,
                            num_rows=None,
                            tolerance=0,
                            signed=False,
                            section_name="Int SRAM Output"):
    """
    Compare int SRAM binary file with golden reference.

    Args:
        bin_file: Path to binary file to compare
        golden_file: Path to golden file
        row_dim: Row dimension
        int_width: Bit width of integer
        num_bytes_per_val: Bytes per value in binary file
        start_row_idx: Starting row index to compare
        num_rows: Number of rows to compare (None = compare all)
        tolerance: Tolerance for comparison (0 = exact match)
        signed: Whether to interpret as signed integer
        section_name: Section name in golden file to parse

    Returns:
        dict: Dictionary containing comparison metrics
    """
    golden_values = parse_golden_int_output(golden_file, section_name)
    if golden_values is None:
        print(f"Warning: Could not find '{section_name}' section in golden file. Skipping comparison.")
        return None

    simulated_values = read_bin_file_as_int_array(
        bin_file, row_dim, int_width, num_bytes_per_val, start_row_idx, num_rows, signed
    )

    min_len = min(len(golden_values), len(simulated_values))
    golden_values = golden_values[:min_len]
    simulated_values = simulated_values[:min_len]

    if len(golden_values) == 0:
        raise ValueError("No values to compare")

    errors = np.abs(golden_values.astype(np.int64) - simulated_values.astype(np.int64))
    mse = np.mean(errors.astype(np.float64) ** 2)
    mae = np.mean(errors.astype(np.float64))
    max_error = np.max(errors)

    with np.errstate(divide='ignore', invalid='ignore'):
        relative_errors = np.where(
            np.abs(golden_values) > 0,
            errors.astype(np.float64) / np.abs(golden_values.astype(np.float64)),
            errors.astype(np.float64)
        )
    mean_relative_error = np.mean(relative_errors)

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


def print_int_comparison_results(results, verbose=False):
    """
    Print integer comparison results in a readable format.
    For int comparison, only shows match/mismatch status, not error values.

    Args:
        results: Dictionary returned by compare_int_with_golden
        verbose: If True, print mismatched indices
    """
    print("=" * 60)
    print("Int SRAM Comparison Results")
    print("=" * 60)
    print(f"Golden values shape:     {results['golden_shape']}")
    print(f"Simulated values shape:  {results['simulated_shape']}")
    print(f"Number of values:        {len(results['golden_values'])}")
    print()
    
    match_rate = results['match_rate']
    errors = results['errors']
    mismatched_count = np.sum(errors > 0)
    matched_count = len(errors) - mismatched_count
    
    print("Match Status:")
    print(f"  Matched:                   {matched_count}/{len(errors)} ({match_rate:.2f}%)")
    print(f"  Mismatched:                {mismatched_count}/{len(errors)} ({100-match_rate:.2f}%)")
    
    if match_rate == 100.0:
        print()
        print("✓ All values match!")
    else:
        print()
        print(f"✗ {mismatched_count} value(s) do not match")
        
        if verbose and mismatched_count > 0:
            print()
            print("Mismatched Indices:")
            mismatched_indices = np.where(errors > 0)[0]
            for idx in mismatched_indices[:20]:
                print(f"  Index {idx:4d}: Golden={results['golden_values'][idx]:8d}, "
                      f"Simulated={results['simulated_values'][idx]:8d}")
            if len(mismatched_indices) > 20:
                print(f"  ... and {len(mismatched_indices) - 20} more mismatches")
    print()


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
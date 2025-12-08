"""
Address alignment utilities.
"""


def align_addr_up(addr: int, multiple: int) -> int:
    """
    Round an address up to the next multiple of the given value.
    
    Args:
        addr: The input address to align
        multiple: The alignment multiple (e.g., 64 for 64-byte alignment)
    
    Returns:
        The address rounded up to the next multiple
    """
    if multiple <= 0:
        raise ValueError("multiple must be positive")
    
    # Round up: (addr + multiple - 1) // multiple * multiple
    return int(((addr + multiple - 1) // multiple) * multiple)


if __name__ == "__main__":
    # Test cases
    test_cases = [
        (32, 64, 64),
        (16, 64, 64),
        (64, 64, 64),
        (65, 64, 128),
        (100, 64, 128),
        (0, 64, 0),
        (1, 64, 64),
        (63, 64, 64),
        (128, 64, 128),
    ]
    
    print("Testing align_addr_up:")
    for addr, multiple, expected in test_cases:
        result = align_addr_up(addr, multiple)
        status = "✓" if result == expected else "✗"
        print(f"{status} align_addr_up({addr}, {multiple}) = {result} (expected {expected})")


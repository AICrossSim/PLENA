import torch


def device_str(device: torch.device) -> str:
    if isinstance(device, str):
        device_str = device
    else:
        device_str = str(device)
    return device_str


def dtype_str(dtype: torch.dtype) -> str:
    if isinstance(dtype, str):
        dtype_str = dtype
    else:
        dtype_str = str(dtype).removeprefix("torch.")
    return dtype_str


def shape_tuple(shape: torch.Size | tuple[int, ...]) -> tuple[int, ...]:
    if isinstance(shape, torch.Size):
        shape_tuple = tuple(shape)
    else:
        shape_tuple = shape
    return shape_tuple
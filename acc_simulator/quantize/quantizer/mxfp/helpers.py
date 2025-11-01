from torch import Tensor


def flatten_for_quantize(tensor: Tensor, block_dim: int) -> Tensor:
    """
    Permute the tensor to move the block dimension to the last position and flatten it (for quantization).
    """
    # Permute the tensor to move the block dimension to the last position and flatten it
    ori_shape = tuple(tensor.shape)
    ndim = len(ori_shape)
    block_dim = block_dim % ndim

    # Create permutation to move block_dim to last position
    permute = list(range(ndim))
    permute.append(permute.pop(block_dim))

    tensor = tensor.permute(permute)
    # Flatten all dimensions
    tensor = tensor.flatten()
    return tensor


def permute_for_dequantize(
    flatten_tensor: Tensor,
    ori_shape: tuple[int, ...],
    block_dim: int,
) -> Tensor:
    """
    Reshape the flattened tensor back to its original shape after dequantization.
    """
    # Permute the flatten tensor back to its original shape
    ndim = len(ori_shape)
    block_dim = block_dim % ndim

    # Create the shape after moving block_dim to last position
    permuted_shape = list(ori_shape)
    permuted_shape.append(permuted_shape.pop(block_dim))

    # Reshape from flattened form to intermediate permuted form
    tensor = flatten_tensor.reshape(permuted_shape)

    # Create inverse permutation to restore original dimension order
    inverse_permute = list(range(ndim))
    inverse_permute.insert(block_dim, inverse_permute.pop(-1))

    tensor = tensor.permute(inverse_permute)
    return tensor

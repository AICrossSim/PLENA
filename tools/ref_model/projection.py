import torch


def pretty_print_matrix(matrix, precision=4):
    """Nicely print a 2D PyTorch tensor."""
    rows = matrix.size(0)
    cols = matrix.size(1)
    for i in range(rows):
        row_str = ' '.join(f"{matrix[i, j].item():>{precision + 6}.{precision}f}" for j in range(cols))
        print(row_str)

def ref_projection(
    data_directory: str
):
    data = torch.load(data_directory)
    
    weight = data[0:8, :]
    activation = data[8:, :]
    print("----------- Weight Matrix -----------")
    pretty_print_matrix(weight, precision=4)
    print("----------- Activation Matrix -----------")
    pretty_print_matrix(activation, precision=4)
    output = torch.matmul(activation, weight.T)
    print("----------- Output Matrix -----------")
    pretty_print_matrix(output, precision=4)



if __name__ == "__main__":
    data_directory        = "../../test/weight/test_projection_data.pt"
    ref_projection(data_directory)

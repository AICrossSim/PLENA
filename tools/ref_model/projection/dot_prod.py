import torch
import numpy as np

def pretty_print_matrix(matrix, precision=4):
    """Nicely print a 2D PyTorch tensor."""
    rows = matrix.size(0)
    cols = matrix.size(1)
    for i in range(rows):
        row_str = ' '.join(f"{matrix[i, j].item():>{precision + 6}.{precision}f}" for j in range(cols))
        print(row_str)


data_a =  [
    [ 0.8435, -1.3156,  0.0346,  0.4956,  0.7142,  1.5411,  0.7825, -0.8609],
    [ 1.3445, -1.1543, -1.5221,  0.9577, -2.4076, -0.0330, -0.3837,  2.1279],
    [ 1.4366, -0.0015,  0.9206,  0.0776,  0.9865,  0.4197, -0.9261,  1.3938],
    [-2.6703,  0.8981, -0.4509, -1.4467, -2.3132,  1.8184,  1.4665,  0.3304],
]

weight = torch.tensor(data_a)

data_b = [
    [ 0.0528,  1.2122,  0.7130, -0.1187, -0.5170,  0.3029,  1.3407,  0.0218],
    [ 0.1754, -1.3636, -0.0411, -0.2942, -0.2843,  0.1709,  1.3538, -1.9442],
    [-0.2385,  0.4545,  0.1929, -0.5859, -1.0069,  0.5797, -0.6329,  0.3542],
    [-1.0020, -0.1936, -0.5148, -0.0965,  0.2638,  0.4340,  1.8284, -0.1923],
]

activation = torch.tensor(data_b)
output = torch.matmul(activation, weight.T)
pretty_print_matrix(output, precision=4)

test1 = torch.tensor([-0.5170,  0.3029,  1.3407,  0.0218])
test2 = torch.tensor([-2.4076, -0.0330, -0.3837,  2.1279])

print(f"result: {torch.dot(test1, test2)}")
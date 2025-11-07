import numpy as np
import matplotlib.pyplot as plt

# Parameters
x_b = 5   # divisor (fixed)
x = np.linspace(0, 20, 500)  # x_a values

# Function: P_divisibility(x) = -sin^2(pi * x / x_b)
P_div = -(np.sin(np.pi * x / x_b))**2

# Plot
plt.figure(figsize=(10,5))
plt.plot(x, P_div, label=fr"$P_{{div}}(x)$")
plt.axhline(0, color="black", linewidth=0.8, linestyle="--")
plt.axvline(0, color="black", linewidth=0.8, linestyle="--")

# Mark integer multiples of x_b
multiples = np.arange(0, 21, x_b)
plt.scatter(multiples, np.zeros_like(multiples), color="red", zorder=5, label="Multiples of $x_b$")

# plt.title("Divisibility Function")
plt.xlabel("$\\frac{x_a}{x_b}$")
plt.ylabel("$P_{div}(x)$")
plt.legend(loc="upper right")
plt.grid(True, linestyle="--", alpha=0.6)
# plt.show()
plt.savefig("divisibility_function.png", dpi=300)

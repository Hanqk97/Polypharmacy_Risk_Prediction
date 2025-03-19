import torch

# Check MPS availability
if torch.backends.mps.is_available():
    device = torch.device("mps")  # Apple Silicon GPU
    print("MPS is available. Using MPS device.")
else:
    device = torch.device("cpu")
    print("MPS not found. Using CPU.")

# Simple test
x = torch.randn(2, 3, device=device)
y = x * 2
print(y)

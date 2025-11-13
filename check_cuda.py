#!/usr/bin/env python3
import os
import sys
import ctypes

print("=== CUDA Diagnostics ===\n")

# Check environment variables
print("1. LD_LIBRARY_PATH:")
ld_path = os.environ.get('LD_LIBRARY_PATH', 'NOT SET')
print(f"   {ld_path}")

# Check libcuda
print("\n2. libcuda.so.1 Check:")
try:
    libcuda = ctypes.CDLL('libcuda.so.1')
    print("   ✓ libcuda.so.1 can be loaded")
except Exception as e:
    print(f"   ✗ libcuda.so.1 cannot be loaded: {e}")

# Check PyTorch
print("\n3. PyTorch Information:")
try:
    import torch
    print(f"   Python: {sys.executable}")
    print(f"   PyTorch Version: {torch.__version__}")
    print(f"   PyTorch Path: {torch.__file__}")
    print(f"   CUDA Version (compiled): {torch.version.cuda}")
    print(f"   CUDA Available: {torch.cuda.is_available()}")
    
    if not torch.cuda.is_available():
        print("\n4. Attempting to get detailed error information:")
        try:
            # Try initializing CUDA to get error details
            torch.cuda.init()
            print("   CUDA initialization successful")
        except Exception as e:
            print(f"   CUDA initialization failed: {e}")
        
        # Check PyTorch CUDA libraries
        torch_lib_path = os.path.join(os.path.dirname(torch.__file__), 'lib')
        if os.path.exists(torch_lib_path):
            print(f"\n5. PyTorch lib directory contents ({torch_lib_path}):")
            try:
                libs = [f for f in os.listdir(torch_lib_path) if 'cuda' in f.lower() or 'cudnn' in f.lower()]
                for lib in sorted(libs)[:10]:
                    print(f"   - {lib}")
            except Exception as e:
                print(f"   Cannot list: {e}")
        
        # Check if CUDA libraries can be found
        print("\n6. Attempting to find CUDA libraries:")
        import subprocess
        for path in ld_path.split(':') if ld_path != 'NOT SET' else []:
            if os.path.exists(path):
                cuda_libs = [f for f in os.listdir(path) if 'libcuda' in f.lower() or 'libcudart' in f.lower()]
                if cuda_libs:
                    print(f"   Found in {path}: {', '.join(cuda_libs[:5])}")
                    
except ImportError as e:
    print(f"   ✗ Cannot import torch: {e}")


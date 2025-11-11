#!/usr/bin/env python3
import os
import sys
import ctypes

print("=== CUDA 诊断信息 ===\n")

# 检查环境变量
print("1. LD_LIBRARY_PATH:")
ld_path = os.environ.get('LD_LIBRARY_PATH', 'NOT SET')
print(f"   {ld_path}")

# 检查 libcuda
print("\n2. libcuda.so.1 检查:")
try:
    libcuda = ctypes.CDLL('libcuda.so.1')
    print("   ✓ libcuda.so.1 可以加载")
except Exception as e:
    print(f"   ✗ libcuda.so.1 无法加载: {e}")

# 检查 PyTorch
print("\n3. PyTorch 信息:")
try:
    import torch
    print(f"   Python: {sys.executable}")
    print(f"   PyTorch 版本: {torch.__version__}")
    print(f"   PyTorch 路径: {torch.__file__}")
    print(f"   CUDA 版本 (编译): {torch.version.cuda}")
    print(f"   CUDA 可用: {torch.cuda.is_available()}")
    
    if not torch.cuda.is_available():
        print("\n4. 尝试获取详细错误信息:")
        try:
            # 尝试初始化 CUDA 以获取错误
            torch.cuda.init()
            print("   CUDA 初始化成功")
        except Exception as e:
            print(f"   CUDA 初始化失败: {e}")
        
        # 检查 PyTorch CUDA 库
        torch_lib_path = os.path.join(os.path.dirname(torch.__file__), 'lib')
        if os.path.exists(torch_lib_path):
            print(f"\n5. PyTorch lib 目录内容 ({torch_lib_path}):")
            try:
                libs = [f for f in os.listdir(torch_lib_path) if 'cuda' in f.lower() or 'cudnn' in f.lower()]
                for lib in sorted(libs)[:10]:
                    print(f"   - {lib}")
            except Exception as e:
                print(f"   无法列出: {e}")
        
        # 检查是否可以找到 CUDA 库
        print("\n6. 尝试查找 CUDA 库:")
        import subprocess
        for path in ld_path.split(':') if ld_path != 'NOT SET' else []:
            if os.path.exists(path):
                cuda_libs = [f for f in os.listdir(path) if 'libcuda' in f.lower() or 'libcudart' in f.lower()]
                if cuda_libs:
                    print(f"   在 {path} 中找到: {', '.join(cuda_libs[:5])}")
                    
except ImportError as e:
    print(f"   ✗ 无法导入 torch: {e}")


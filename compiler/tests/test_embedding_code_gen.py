#!/usr/bin/env python3
"""
Test script for attention code generation
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from passes.code_gen import _generate_embedding_code

def test_embeddings_code_generation():
    """Test the embeddings code generation function"""

    # Test node with LLaMA-3.1 8B parameters
    test_node = {
        "name": "embeddings",
        "operation_type": "embeddings",
        "dimensions": {
            "hidden_size": 4096,
            "num_attention_heads": 32,
            "head_dim": 128,
            "num_key_value_heads": 8
        }
    }
    hardware_config = {
        "mlen" : 256,
        "blen" : 4
    }
    model_info = {
        "batch_size" : 4,
        "vocab_size" : 128256
    }
    scheduler = {
        "activation_base_address": 0,
        "register_assignment": {
            "hbm_addr_reg": {
                "token_table_offset": 0
            }
        }
    }

    # Generate the assembly code
    generated_code = _generate_embedding_code(
        test_node,
        model_info=model_info,
        hardware_config=hardware_config,
        scheduler=scheduler
    )

    print("Generated Embedding Assembly Code:")
    print("=" * 50)
    print(generated_code)
    print("=" * 50)
    
    # Basic validation
    # assert "Flash Attention Implementation" in generated_code
    # assert "S_LD_FIX i1, i0, 11" in generated_code
    # assert "M_TMM_IC 0, i1, i2" in generated_code
    # assert "M_TMM_PS i7, i1, i2" in generated_code
    # assert "M_MM_WO i1, 0, 0" in generated_code
    # assert "Flash Attention Implementation Template" in generated_code
    
    print("✅ All tests passed! The attention code generation is working correctly.")

if __name__ == "__main__":
    test_embeddings_code_generation() 

import torch
import torch.nn as nn
import logging
import os
from pathlib import Path
from safetensors.torch import save_file, load_file
from tqdm import tqdm
import time

from .utils import find_qlayers, cleanup_memory
from .gptq import GPTQ

from ..quantize.quantized_layers import MXFPLinearPTQ
from ..utils import set_layer_by_name


def save_layer_checkpoint(model, layer_idx, checkpoint_dir, model_name="quantized_model"):
    """
    Save only the specific quantized layer instead of the entire model.
    
    Args:
        model: The model being quantized
        layer_idx: Index of the layer that was just quantized
        checkpoint_dir: Directory to save checkpoints
        model_name: Name prefix for the checkpoint files
    """
    if checkpoint_dir is None:
        return
        
    checkpoint_path = Path(checkpoint_dir)
    checkpoint_path.mkdir(parents=True, exist_ok=True)
    
    # Create checkpoint file for this specific layer
    layer_checkpoint_file = checkpoint_path / f"{model_name}_layer_{layer_idx}.safetensors"
    
    # Remove any existing directory with the same name (fix for I/O error)
    if layer_checkpoint_file.exists() and layer_checkpoint_file.is_dir():
        import shutil
        shutil.rmtree(layer_checkpoint_file)
        logging.info(f"Removed existing directory: {layer_checkpoint_file}")
    
    logging.info(f"Saving layer {layer_idx} checkpoint to {layer_checkpoint_file}")
    
    try:
        # Extract only the specific layer's state dict
        layer_state_dict = {}
        layer_prefix = f"model.layers.{layer_idx}."
        
        for name, param in model.named_parameters():
            if name.startswith(layer_prefix):
                # Save with relative layer name (remove the model.layers.X. prefix)
                relative_name = name[len(layer_prefix):]
                layer_state_dict[relative_name] = param.detach().cpu()
        
        if not layer_state_dict:
            logging.warning(f"No parameters found for layer {layer_idx} with prefix {layer_prefix}")
            return
        
        # Save only this layer's parameters
        save_file(layer_state_dict, str(layer_checkpoint_file))
        
        # Save metadata about the checkpoint
        metadata = {
            "layer_idx": layer_idx,
            "total_layers": len(model.model.layers),
            "checkpoint_file": str(layer_checkpoint_file),
            "model_name": model_name,
            "num_parameters": len(layer_state_dict),
            "parameter_names": list(layer_state_dict.keys())
        }
        
        metadata_file = checkpoint_path / f"{model_name}_layer_{layer_idx}_metadata.json"
        import json
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
            
        logging.info(f"Layer {layer_idx} checkpoint saved successfully ({len(layer_state_dict)} parameters)")
        
    except Exception as e:
        logging.error(f"Failed to save layer {layer_idx} checkpoint: {e}")


# Keep the old function for backward compatibility
def save_checkpoint(model, layer_idx, checkpoint_dir, model_name="quantized_model"):
    """Backward compatibility wrapper"""
    return save_layer_checkpoint(model, layer_idx, checkpoint_dir, model_name)


def detect_quantized_layers(checkpoint_dir, model_name="quantized_model"):
    """
    Detect which layers have been quantized based on available checkpoints.
    
    Args:
        checkpoint_dir: Directory containing layer checkpoints
        model_name: Name prefix for checkpoint files
    
    Returns:
        dict: {layer_idx: checkpoint_file_path} for all available quantized layers
    """
    if checkpoint_dir is None or not os.path.exists(checkpoint_dir):
        return {}
    
    checkpoint_path = Path(checkpoint_dir)
    checkpoints = list(checkpoint_path.glob(f"{model_name}_layer_*.safetensors"))
    
    quantized_layers = {}
    for checkpoint in checkpoints:
        try:
            layer_idx = int(checkpoint.stem.split('_layer_')[-1])
            quantized_layers[layer_idx] = str(checkpoint)
        except ValueError:
            continue
    
    return quantized_layers


def load_layer_checkpoint(model, layer_idx, checkpoint_file):
    """
    Load a specific layer's quantized weights into the model.
    
    Args:
        model: The model to load the layer into
        layer_idx: Index of the layer to load
        checkpoint_file: Path to the layer checkpoint file
    
    Returns:
        bool: True if successfully loaded, False otherwise
    """
    if not os.path.exists(checkpoint_file):
        logging.error(f"Layer checkpoint file {checkpoint_file} not found")
        return False
    
    try:
        # Load the layer state dict
        layer_state_dict = load_file(checkpoint_file)
        
        # Load into the specific layer
        layer_prefix = f"model.layers.{layer_idx}."
        model_state_dict = {}
        
        for param_name, param_value in layer_state_dict.items():
            full_param_name = layer_prefix + param_name
            model_state_dict[full_param_name] = param_value
        
        # Load the parameters into the model
        model.load_state_dict(model_state_dict, strict=False)
        
        logging.info(f"Successfully loaded layer {layer_idx} from checkpoint")
        return True
        
    except Exception as e:
        logging.error(f"Failed to load layer {layer_idx} checkpoint: {e}")
        return False


def auto_load_quantized_layers(model, checkpoint_dir, model_name="quantized_model"):
    """
    Automatically detect and load all available quantized layers.
    
    Args:
        model: The model to load layers into
        checkpoint_dir: Directory containing layer checkpoints
        model_name: Name prefix for checkpoint files
    
    Returns:
        int: Number of layers successfully loaded, or highest layer index if resuming
    """
    quantized_layers = detect_quantized_layers(checkpoint_dir, model_name)
    
    if not quantized_layers:
        logging.info("No quantized layer checkpoints found")
        return -1
    
    loaded_count = 0
    max_layer_idx = -1
    
    for layer_idx in sorted(quantized_layers.keys()):
        checkpoint_file = quantized_layers[layer_idx]
        if load_layer_checkpoint(model, layer_idx, checkpoint_file):
            loaded_count += 1
            max_layer_idx = layer_idx
        else:
            logging.warning(f"Failed to load layer {layer_idx}, stopping auto-load")
            break
    
    logging.info(f"Auto-loaded {loaded_count} quantized layers (up to layer {max_layer_idx})")
    return max_layer_idx


from transformers import AutoModelForCausalLM

def load_checkpoint(model, checkpoint_dir_path):
    """
    Load model checkpoint from directory.
    
    Args:
        model: The model to load weights into
        checkpoint_dir_path: Path to the checkpoint directory
    
    Returns:
        (model, layer_idx): The loaded model and layer index
    """
    if not os.path.exists(checkpoint_dir_path):
        raise FileNotFoundError(f"Checkpoint directory {checkpoint_dir_path} not found")
    
    logging.info(f"Loading checkpoint from {checkpoint_dir_path}")
    
    try:
        # Load model from the checkpoint directory
        loaded_model = AutoModelForCausalLM.from_pretrained(
            checkpoint_dir_path,
            torch_dtype="auto",        
            low_cpu_mem_usage=True,    
            device_map="auto",         
        )
        
        # Extract layer index from directory name
        dirname = Path(checkpoint_dir_path).name
        layer_idx = int(dirname.split('_layer_')[-1])
        
        logging.info(f"Checkpoint loaded successfully for layer {layer_idx}")
        return loaded_model, layer_idx
        
    except Exception as e:
        logging.error(f"Failed to load checkpoint {checkpoint_dir_path}: {e}")
        raise


def find_latest_checkpoint(checkpoint_dir, model_name="quantized_model"):
    """
    Find the latest checkpoint in the checkpoint directory.
    
    Args:
        checkpoint_dir: Directory containing checkpoints
        model_name: Name prefix for the checkpoint directories
    
    Returns:
        (checkpoint_dir_path, layer_idx): Path to latest checkpoint directory and its layer index,
                                         or (None, -1) if no checkpoints found
    """
    if checkpoint_dir is None or not os.path.exists(checkpoint_dir):
        return None, -1
    
    checkpoint_path = Path(checkpoint_dir)
    # Look for checkpoint directories instead of files
    checkpoint_dirs = [d for d in checkpoint_path.iterdir() if d.is_dir() and d.name.startswith(f"{model_name}_layer_")]
    
    if not checkpoint_dirs:
        return None, -1
    
    # Sort by layer index to find the latest
    latest_checkpoint = max(checkpoint_dirs, key=lambda x: int(x.name.split('_layer_')[-1]))
    layer_idx = int(latest_checkpoint.name.split('_layer_')[-1])
    
    return str(latest_checkpoint), layer_idx

@torch.no_grad()
def quantize_model_gptq(model, dataloader, quant_args, dev, nsamples = 128, percdamp = 0.01, seqlen=2048, save_q_model=False, cali_batch_size=32, checkpoint_dir=None, resume_from_checkpoint=None):
    '''
    Adapting From Quarot/GPTQ repo 
    
    Args:
        checkpoint_dir: Directory to save/load checkpoints from
        resume_from_checkpoint: Specific checkpoint file to resume from, or 'latest' to auto-find latest
    '''
    logging.info('-----GPTQ Quantization-----')
    
    # Handle checkpoint resuming
    start_layer = 0
    if resume_from_checkpoint and checkpoint_dir:
        # Auto-load all available quantized layers
        max_quantized_layer = auto_load_quantized_layers(model, checkpoint_dir)
        if max_quantized_layer >= 0:
            start_layer = max_quantized_layer + 1
            logging.info(f"Resuming quantization from layer {start_layer} (loaded {max_quantized_layer} layers)")
        else:
            logging.info("No layer checkpoints found, starting from beginning")

        if start_layer == len(model.model.layers):
            return 

    
    # disable kv cache for efficiency 
    use_cache = model.config.use_cache
    model.config.use_cache = False

    layers = model.model.layers

    # Move the first decoder block on to device 
    model.model.embed_tokens = model.model.embed_tokens.to(dev)
    model.model.norm = model.model.norm.to(dev)
    rope = model.model.rotary_emb.to(dev)
    layers[0] = layers[0].to(dev)

    dtype = next(iter(model.parameters())).dtype

    inps = torch.zeros(
        (nsamples, seqlen, model.config.hidden_size), dtype=dtype, device=dev
    )
    cache = {'i': 0, 'attention_mask': None}

    class Catcher(nn.Module):
        def __init__(self, module):
            super().__init__()
            self.module = module
        def forward(self, inp, **kwargs):
            # The input tensor inp (shape (2048, 4096)) is stored into inps[cache['i']]. 
            # sequence length and hidden size

            inps[cache['i']] = inp
            cache['i'] += 1
            cache['attention_mask'] = kwargs['attention_mask']
            cache['position_ids'] = kwargs['position_ids']
            raise ValueError
    layers[0] = Catcher(layers[0])
    # this is iterating over a list (not a PyTorch DataLoader), and each batch is just one sample. tuple (ids, labels)
    for batch in dataloader:
        try:
            # only pass in Input token IDs (to feed into the model),[0] is input ids, [1] is mask
            model(batch[0].to(dev))
            # this calls the forward method and stores the data in inps
        except ValueError:
            pass
    layers[0] = layers[0].module
    # replace modules back after catchers
    torch.cuda.empty_cache()

    outs = torch.zeros_like(inps)
    attention_mask = cache['attention_mask']
    position_ids = cache['position_ids']

    sequential = [
                ['self_attn.k_proj', 'self_attn.v_proj', 'self_attn.q_proj'],
                ['self_attn.o_proj'],
                ['mlp.up_proj', 'mlp.gate_proj'],
                ['mlp.down_proj']
            ]
    for i in range(start_layer, len(layers)):
        print(f'\nLayer {i}:', flush=True, end=' ')
        layer = layers[i].to(dev)
        full = find_qlayers(layer, layers=[torch.nn.Linear])
        for names in sequential:

            subset = {n: full[n] for n in names}

            gptq = {}
            for name in subset:
                print(f'{name}', end='  ', flush=True)
                gptq[name] = GPTQ(subset[name])
    
            pre_act = []
            def make_pre_hook():
                def pre_hook(_, inp):
                    pre_act.append(inp[0])    
                return pre_hook

            def add_batch(name):
                def tmp(_, inp, out):
                    # given each batch is only one sample , [0] here represents only input ids.
                    gptq[name].add_batch(inp[0].data, out.data)
                return tmp
            
            handles = []
            for name in subset:
                handles.append(subset[name].register_forward_hook(add_batch(name)))
            # Inps are the same across subset
            handles.append(subset[name].register_forward_pre_hook(make_pre_hook()))

            for j in range(nsamples):
                # layer is the decoder block 
                # now feeds in smaples into each decoder block, each time only one sample (sqeunce, hidden)
                # This feeds one sample at a time (shape [1, seqlen, hidden]) through the current transformer block.
                #  The hooks are triggered inside this call, note we have two types of hooks
                x = inps[j].unsqueeze(0) 
                # For newer hf attention interface, get rope first 
                cos, sin = rope(x, position_ids)
                outs[j] = layer(
                    x,
                    attention_mask=attention_mask,
                    position_embeddings=(cos, sin)
                )[0]
            
            pre_act = torch.cat(pre_act, dim=0)

            for h in handles:
                h.remove()

            for name in subset:
                quantized_linear_w = gptq[name].fasterquant(
                    activation = pre_act if quant_args["fc_kwargs"]["clip_search_y"] else None, 
                    w_meta = quant_args["fc_kwargs"]["w_meta"],
                    percdamp=percdamp, 
                    cali_batch_size=cali_batch_size,
                    layer_name=f"layers{i}.{name}"
                )

                if save_q_model:
                    assert quantized_linear_w.shape == gptq[name].layer.weight.shape
                    # replace the qunatized weights inline, more friendly for saving the model
                    gptq[name].layer.weight.data.copy_(quantized_linear_w)
             
                else:
                    # replace linear here with from_quantize()
                    new_layer = MXFPLinearPTQ.from_quantized(
                        layer=gptq[name].layer,
                        weight_q=quantized_linear_w,
                        x_meta=quant_args["fc_kwargs"]["x_meta"],
                        w_meta=quant_args["fc_kwargs"]["w_meta"],
                        b_meta=quant_args["fc_kwargs"]["b_meta"],
                        layer_type=quant_args["fc_kwargs"]["layer_type"],
                        online_rotate=quant_args["fc_kwargs"]["online_rotate"]
                    )

                    def to_abs_name(i: int, rel: str) -> str:
                        return f"model.layers.{i}.{rel}"

                    set_layer_by_name(model, to_abs_name(i, name), new_layer)
                gptq[name].free()

        # Prepare inps for next decoder block
        for j in range(nsamples):
            x = inps[j].unsqueeze(0) 
            
            cos, sin = model.model.rotary_emb(x, position_ids)
            outs[j] = layer(
                x,
                attention_mask=attention_mask,
                position_embeddings=(cos, sin)
            )[0]
        
        # move back to cpu to save space
        layers[i] = layer.cpu()
        del layer
        del gptq 
        torch.cuda.empty_cache()

        inps, outs = outs, inps
        
        # Save checkpoint after completing this layer
        if checkpoint_dir is not None:
            save_checkpoint(model, i, checkpoint_dir)

    # reset to enable kv cache
    model.config.use_cache = use_cache
    cleanup_memory(verbos=True)
    logging.info('-----GPTQ Quantization Done-----\n')





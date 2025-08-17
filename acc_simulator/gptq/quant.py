
import torch
import torch.nn as nn
import logging
import os
from pathlib import Path
from safetensors.torch import save_file, load_file

from .utils import find_qlayers, cleanup_memory
from .gptq import GPTQ

from ..quantize.quantized_layers import MXFPLinearPTQ
from ..utils import set_layer_by_name


def save_checkpoint(model, layer_idx, checkpoint_dir, model_name="quantized_model", checkpoint_layers=None):
    """
    Save model checkpoint after quantizing a specific layer and delete all previous checkpoints.
    
    Args:
        model: The model being quantized
        layer_idx: Index of the layer that was just quantized
        checkpoint_dir: Directory to save checkpoints
        model_name: Name prefix for the checkpoint files
        checkpoint_layers: Number of layers to process before saving a checkpoint (e.g., 5 = every 5 layers)
                          or "last" to only save the final layer
                          or None to save every layer (default)
    """
    if checkpoint_dir is None:
        return
    
    # Determine if we should save this layer
    should_save = False

    try:
        checkpoint_layers = int(checkpoint_layers)
    except:
        pass
    
    if checkpoint_layers is None:
        # Default behavior: save every layer
        should_save = True
    elif isinstance(checkpoint_layers, str) and checkpoint_layers == "last":
        # Only save the last layer
        total_layers = len(model.model.layers)
        should_save = (layer_idx == total_layers - 1)
    elif isinstance(checkpoint_layers, int):
        # Save every N layers + always save the final layer
        total_layers = len(model.model.layers)
        should_save = ((layer_idx + 1) % checkpoint_layers == 0) or (layer_idx == total_layers - 1)

    breakpoint()
    
    if not should_save:
        return
        
    checkpoint_path = Path(checkpoint_dir)
    checkpoint_path.mkdir(parents=True, exist_ok=True)
    
    # Create checkpoint filename with layer index
    checkpoint_file = checkpoint_path / f"{model_name}_layer_{layer_idx}.safetensors"
    
    logging.info(f"Saving checkpoint after layer {layer_idx} to {checkpoint_file}")
    
    # Save model state dict
    try:
        # Option 1: Direct save (faster, but may use more GPU memory)
        state_dict = model.state_dict()
        save_file(state_dict, str(checkpoint_file))
        
        # Also save metadata about the checkpoint
        metadata = {
            "layer_idx": layer_idx,
            "total_layers": len(model.model.layers),
            "checkpoint_file": str(checkpoint_file),
            "model_name": model_name
        }
        
        metadata_file = checkpoint_path / f"{model_name}_layer_{layer_idx}_metadata.json"
        import json
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
            
        logging.info(f"Checkpoint saved successfully for layer {layer_idx}")
        
        # Delete ALL previous checkpoints to save disk space
        delete_all_previous_checkpoints(checkpoint_dir, layer_idx, model_name)
        
    except Exception as e:
        logging.error(f"Failed to save checkpoint for layer {layer_idx}: {e}")


def delete_all_previous_checkpoints(checkpoint_dir, current_layer_idx, model_name="quantized_model"):
    """
    Delete ALL previous checkpoints to save disk space, keeping only the current one.
    
    Args:
        checkpoint_dir: Directory containing checkpoints
        current_layer_idx: Index of the current layer that was just saved
        model_name: Name prefix for the checkpoint files
    """
    if checkpoint_dir is None:
        return
    
    checkpoint_path = Path(checkpoint_dir)
    if not checkpoint_path.exists():
        return
    
    # Find all existing checkpoints
    checkpoints = list(checkpoint_path.glob(f"{model_name}_layer_*.safetensors"))
    
    if len(checkpoints) <= 1:
        return  # Only one checkpoint, nothing to delete
    
    # Delete all checkpoints except the current one
    for checkpoint in checkpoints:
        try:
            layer_idx = int(checkpoint.stem.split('_layer_')[-1])
            if layer_idx != current_layer_idx:
                # Delete this checkpoint
                os.remove(checkpoint)
                logging.info(f"Deleted previous checkpoint: {checkpoint}")
                
                # Also delete the metadata file
                metadata_file = checkpoint_path / f"{model_name}_layer_{layer_idx}_metadata.json"
                if metadata_file.exists():
                    os.remove(metadata_file)
                    logging.info(f"Deleted previous metadata: {metadata_file}")
                    
        except ValueError:
            # Skip files that don't match the expected pattern
            continue
        except Exception as e:
            logging.error(f"Failed to delete checkpoint {checkpoint}: {e}")


def load_checkpoint(model, checkpoint_file):
    """
    Load model checkpoint from file.
    
    Args:
        model: The model to load weights into
        checkpoint_file: Path to the checkpoint file
    
    Returns:
        layer_idx: The layer index this checkpoint corresponds to
    """
    if not os.path.exists(checkpoint_file):
        raise FileNotFoundError(f"Checkpoint file {checkpoint_file} not found")
    
    logging.info(f"Loading checkpoint from {checkpoint_file}")
    
    try:
        state_dict = load_file(checkpoint_file)
        model.load_state_dict(state_dict)
        
        # Extract layer index from filename
        filename = Path(checkpoint_file).stem
        layer_idx = int(filename.split('_layer_')[-1])
        
        logging.info(f"Checkpoint loaded successfully for layer {layer_idx}")
        return layer_idx
        
    except Exception as e:
        logging.error(f"Failed to load checkpoint {checkpoint_file}: {e}")
        raise


def find_latest_checkpoint(checkpoint_dir, model_name="quantized_model"):
    """
    Find the latest checkpoint in the checkpoint directory.
    
    Args:
        checkpoint_dir: Directory containing checkpoints
        model_name: Name prefix for the checkpoint files
    
    Returns:
        (checkpoint_file, layer_idx): Path to latest checkpoint and its layer index,
                                     or (None, -1) if no checkpoints found
    """
    if checkpoint_dir is None or not os.path.exists(checkpoint_dir):
        return None, -1
    
    checkpoint_path = Path(checkpoint_dir)
    checkpoints = list(checkpoint_path.glob(f"{model_name}_layer_*.safetensors"))
    
    if not checkpoints:
        return None, -1
    
    # Sort by layer index to find the latest
    latest_checkpoint = max(checkpoints, key=lambda x: int(x.stem.split('_layer_')[-1]))
    layer_idx = int(latest_checkpoint.stem.split('_layer_')[-1])
    
    return str(latest_checkpoint), layer_idx

@torch.no_grad()
def quantize_model_gptq(model, dataloader, quant_args, dev, nsamples = 128, percdamp = 0.01, seqlen=2048, save_q_model=False, cali_batch_size=32, checkpoint_dir=None, resume_from_checkpoint=None, checkpoint_layers=None):
    '''
    Adapting From Quarot/GPTQ repo 
    
    Args:
        checkpoint_dir: Directory to save/load checkpoints from
        resume_from_checkpoint: Specific checkpoint file to resume from, or 'latest' to auto-find latest
        checkpoint_layers: Controls checkpoint frequency to minimize disk usage:
                          - None: Save checkpoint after every layer (default)
                          - "last": Only save checkpoint after the final layer
                          - int: Save checkpoint every N layers (e.g., 5 = every 5 layers)
                          Note: When saving a new checkpoint, ALL previous checkpoints are deleted
    '''
    logging.info('-----GPTQ Quantization-----')
    
    # Handle checkpoint resuming
    start_layer = 0
    if resume_from_checkpoint:
        checkpoint_file, layer_idx = find_latest_checkpoint(checkpoint_dir)
        if checkpoint_file is not None:
            load_checkpoint(model, checkpoint_file)
            start_layer = layer_idx + 1
            logging.info(f"Resuming quantization from layer {start_layer}")
        else:
            logging.info("No checkpoint found, starting from beginning")

    
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
            save_checkpoint(model, i, checkpoint_dir, checkpoint_layers=checkpoint_layers)

    # reset to enable kv cache
    model.config.use_cache = use_cache
    cleanup_memory(verbos=True)
    logging.info('-----GPTQ Quantization Done-----\n')






import torch
import torch.nn as nn
import logging

from .utils import find_qlayers, cleanup_memory
from .gptq import GPTQ

from ..quantize.quantized_layers import MXFPLinearPTQ
from ..utils import set_layer_by_name


@torch.no_grad()
def quantize_model_gptq(model, dataloader, quant_args, dev, nsamples = 128, percdamp = 0.01, seqlen=2048):
    '''
    Adapting From Quarot/GPTQ repo 
    '''
    logging.info('-----GPTQ Quantization-----')
    
    # disable kv cache for efficiency 
    use_cache = model.config.use_cache
    model.config.use_cache = False

    layers = model.model.layers

    # Move the first decoder block on to device 
    model.model.embed_tokens = model.model.embed_tokens.to(dev)
    model.model.norm = model.model.norm.to(dev)
    rope = model.model.rotary_emb
    rope = rope.to(next(model.parameters()).device)
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
    for i in range(len(layers)):
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
                    percdamp=percdamp
                )

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

    # reset to enable kv cache
    model.config.use_cache = use_cache
    cleanup_memory(verbos=True)
    logging.info('-----GPTQ Quantization Done-----\n')





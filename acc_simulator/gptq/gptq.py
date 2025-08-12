import math
import tqdm
import torch

from .utils import cleanup_memory
from ..quantize.quantizer.mxint import MXIntMeta, mxint_quantizer_sim


class GPTQ:

    def __init__(self, layer):
        self.layer = layer
        self.dev = self.layer.weight.device
        W = layer.weight.data.clone()
        self.rows = W.shape[0]
        self.columns = W.shape[1]
        self.H = torch.zeros((self.columns, self.columns), device=self.dev)
        self.nsamples = 0

    def add_batch(self, inp, out):
        if len(inp.shape) == 2:
            inp = inp.unsqueeze(0)
        # the input are already unsqueezed at (0)
        # tmp here i assume takes the batch size, while we only have one sample per batch 
        tmp = inp.shape[0]
        if len(inp.shape) == 3:
            # Collapsed the batch and sequence into a flat list of tokens.
            # below keeps the last dimention fixed, and all preceding dimensions collapsed into on
            inp = inp.reshape((-1, inp.shape[-1]))
        inp = inp.t()
        # H hiddensize/hiddensize
        # It's doing weighted averaging of the Gram matrix XTX across multiple batches.
        # Each time you add a new batch of tmp samples (tokens), you need to scale the existing H to make room for the new contribution.
        self.H *= self.nsamples / (self.nsamples + tmp)
        self.nsamples += tmp
        # inp = inp.float()
        inp = math.sqrt(2 / self.nsamples) * inp.float()
        # self.H += 2 / self.nsamples * inp.matmul(inp.t())
        self.H += inp.matmul(inp.t())

    def fasterquant(
        self, activation, w_meta, percdamp=.01
    ): 
        W = self.layer.weight.data.clone()

        H = self.H
        del self.H
        dead = torch.diag(H) == 0
        H[dead, dead] = 1
        W[:, dead] = 0

        Losses = torch.zeros_like(W)
        Q = torch.zeros_like(W)

        damp = percdamp * torch.mean(torch.diag(H))
        diag = torch.arange(self.columns, device=self.dev)
        H[diag, diag] += damp
        H = torch.linalg.cholesky(H)
        H = torch.cholesky_inverse(H)
        H = torch.linalg.cholesky(H, upper=True)
        Hinv = H

        # set blocksize in gptq to be the same as the mx block from meta
        blocksize = w_meta.block_size
        for i1 in tqdm.tqdm(range(0, self.columns, blocksize), desc="Quantizing blocks", disable=True):
            i2 = min(i1 + blocksize, self.columns)

            W1 = W[:, i1:i2].clone()
            
            if activation != None:
                Act1 = activation[:, :, i1:i2].clone()
                Q1 = mxint_quantizer_sim(W1, act_tensor=Act1, block_dim=1, mxint_meta=w_meta, quantile_search=True)
            else:
                Q1 = mxint_quantizer_sim(W1, block_dim=1, mxint_meta=w_meta, quantile_search=True)
            
            Hinv1 = Hinv[i1:i2, i1:i2]
            Err1 = (W1 - Q1) / torch.diag(Hinv1).unsqueeze(0)
            Losses1 = ((W1 - Q1) ** 2) / (torch.diag(Hinv1) ** 2).unsqueeze(0)

            Q[:, i1:i2] = Q1
            Losses[:, i1:i2] = Losses1 / 2

            W[:, i2:] -= Err1.matmul(Hinv[i1:i2, i2:])


        assert Q.shape == W.shape, \
            f"Shape mismatch: {Q.shape} != {W.shape}"
        
        return Q
    
    def free(self):
        self.H = None
        self.Losses = None
        torch.cuda.empty_cache()
        cleanup_memory(verbos=False)
        


from typing import Any
import torch
from .operations import Operation_list


class Operation:
    def __init__(self, name: str):
        self.name = name

    def __str__(self):
        return f"{self.name}"

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        return Operation_list._operation_dict[self.name](*args, **kwds)

class CoarseGrainedQuantOperation(Operation):
    def __init__(self, name: str, quant_type: str, quant_func_dict: dict):
        super().__init__(name)
        self.quant_type = quant_type
        assert isinstance(quant_func_dict, dict), "quant_func_dict must be a dictionary, key is the argument name, value is the quantizer function"
        self.quant_func_dict = quant_func_dict
    
    def __str__(self):
        return f"{self.name} ({self.quant_type})"

    def __call__(self, **kwds: Any) -> Any:
        for arg_name, arg in kwds.items():
            if isinstance(arg, torch.Tensor):
                kwds[arg_name] = self.quant_func_dict[arg_name](arg)
        return Operation_list._operation_dict[self.name](**kwds)

class FineGrainedQuantOperation(Operation):
    def __init__(self, name: str):
        super().__init__(name)

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        '''
        need to write the hardware logic here
        '''
        raise NotImplementedError
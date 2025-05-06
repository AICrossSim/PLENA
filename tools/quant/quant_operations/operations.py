
'''
a decorator to add a base instruction to a list of instructions
'''

class Operation_list:
    _operation_dict: dict = {}


def register_operation(name: str):
    def decorator(func):
        Operation_list._operation_dict[name] = func
        return func
    return decorator

@register_operation(name="add")
def add(a, b):
    return a + b

@register_operation(name="mul")
def mul(a, b):
    return a * b

@register_operation(name="matmul")
def matmul(a, b):
    return a @ b




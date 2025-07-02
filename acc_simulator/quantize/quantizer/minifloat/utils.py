from logging import getLogger

from torch.autograd.function import InplaceFunction

logger = getLogger(__name__)


# Forced torch gradient overrider
class MyClamp(InplaceFunction):
    @staticmethod
    def forward(ctx, input, min, max):
        return input.clamp(min=min, max=max)

    @staticmethod
    def backward(ctx, grad_output):
        grad_input = grad_output.clone()
        return grad_input, None, None


class MyRound(InplaceFunction):
    @staticmethod
    def forward(ctx, input):
        ctx.input = input
        return input.round()

    @staticmethod
    def backward(ctx, grad_output):
        grad_input = grad_output.clone()
        return grad_input


class MyFloor(InplaceFunction):
    @staticmethod
    def forward(ctx, input):
        ctx.input = input
        return input.floor()

    @staticmethod
    def backward(ctx, grad_output):
        grad_input = grad_output.clone()
        return grad_input


my_clamp = MyClamp.apply
my_round = MyRound.apply
my_floor = MyFloor.apply

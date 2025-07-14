from dataclasses import dataclass

@dataclass
class MXFPMeta:
    block_size: int
    scale_exp_bits: int
    element_exp_bits: int
    element_frac_bits: int

    def __post_init__(self):
        legal_scale_exp_bits = (8,)
        # assert self.scale_exp_bits in legal_scale_exp_bits, (
        #     f"Invalid exponent bits: {self.scale_exp_bits}. "
        #     f"Legal values are: {legal_scale_exp_bits}."
        # )

        legal_element_exp_frac_bits = ((4, 3), (5, 2), (2, 3), (3, 2), (2, 1))
        el_exp_frac = (self.element_exp_bits, self.element_frac_bits)
        # assert el_exp_frac in legal_element_exp_frac_bits, (
        #     f"Invalid element exponent and fraction bits: {self.element_exp_bits}, {self.element_frac_bits}. "
        #     f"Legal values are: {legal_element_exp_frac_bits}."
        # )
        self.element_bits = self.element_exp_bits + self.element_frac_bits + 1

@dataclass
class MXFPTensorMeta:
    device: str
    dtype: str
    shape: tuple[int, ...]
    block_dim: int
    meta: MXFPMeta


OCP_MXFP8_E2M5 = MXFPMeta(
    block_size=16,
    scale_exp_bits=8,
    element_exp_bits=2,
    element_frac_bits=5,
)
OCP_MXFP8_E4M3 = MXFPMeta(
    block_size=16,
    scale_exp_bits=8,
    element_exp_bits=4,
    element_frac_bits=3,
)
OCP_MXFP8_E5M2 = MXFPMeta(
    block_size=16,
    scale_exp_bits=8,
    element_exp_bits=5,
    element_frac_bits=2,
)
OCP_MXFP6_E2M3 = MXFPMeta(
    block_size=16,
    scale_exp_bits=8,
    element_exp_bits=2,
    element_frac_bits=3,
)
OCP_MXFP6_E3M2 = MXFPMeta(
    block_size=16,
    scale_exp_bits=8,
    element_exp_bits=3,
    element_frac_bits=2,
)
OCP_MXFP4_E2M1 = MXFPMeta(
    block_size=16,
    scale_exp_bits=8,
    element_exp_bits=2,
    element_frac_bits=1,
)
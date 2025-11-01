#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct FpType {
    pub sign: bool,
    pub exponent: u8,
    pub mantissa: u8,
}

const fn mask(x: u8) -> u32 {
    ((1u64 << x) - 1) as _
}

impl FpType {
    pub const E8M0: Self = FpType {
        sign: false,
        exponent: 8,
        mantissa: 0,
    };

    pub const F16: Self = FpType {
        sign: true,
        exponent: 5,
        mantissa: 10,
    };

    pub const BF16: Self = FpType {
        sign: true,
        exponent: 8,
        mantissa: 7,
    };

    pub const F32: Self = FpType {
        sign: true,
        exponent: 8,
        mantissa: 23,
    };

    pub const fn size_in_bits(self) -> u8 {
        self.sign as u8 + self.exponent + self.mantissa
    }

    pub const fn cast(self, new_ty: FpType, bits: u32) -> u32 {
        let sign = if self.sign {
            (bits >> (self.exponent + self.mantissa)) & 1
        } else {
            0
        };

        // Sign bit not representable, round to smallest representable number, i.e. zero.
        if sign == 1 && !new_ty.sign {
            return 0;
        }

        let mantissa_bits = bits & mask(self.mantissa);
        let exponent_mask = mask(self.exponent);
        let exponent = (bits >> self.mantissa) & exponent_mask;

        let new_exponent_mask = mask(new_ty.exponent);

        let mut converted_exponent = match exponent {
            // Subnormal -> subnormal
            0 => 0,
            // Inf/NaN -> Inf/NaN
            _ if exponent == exponent_mask => new_exponent_mask,
            // Normal number bias conversion
            _ if self.exponent <= new_ty.exponent => {
                exponent + ((new_exponent_mask - exponent_mask) >> 1)
            }
            _ => {
                // In this case, the conversion is lossy, we need to check the bias diff first.
                let bias_diff = (exponent - new_exponent_mask) >> 1;
                if exponent <= bias_diff {
                    // Underflow
                    todo!();
                } else if exponent - bias_diff >= new_exponent_mask {
                    // Overflow
                    todo!();
                } else {
                    exponent - bias_diff
                }
            }
        };

        let mut converted_mantissa = if self.mantissa <= new_ty.mantissa {
            mantissa_bits << (new_ty.mantissa - self.mantissa)
        } else {
            // In this case, the conversion is lossy, we need to perform rounding.
            let discarded_bits = (mantissa_bits & mask(self.mantissa - new_ty.mantissa - 1)) != 0;
            let prelim_shift = mantissa_bits >> (self.mantissa - new_ty.mantissa - 1);
            let round_dir = match (prelim_shift & 3, discarded_bits) {
                // < 0.5, Round down
                (0b00 | 0b10, _) => 0,
                // > 0.5, Round up
                (0b01 | 0b11, true) => 1,
                // = 0.5, Round to even
                (0b01, false) => 0,
                (0b11, false) => 1,
                _ => unreachable!(),
            };
            let shift = (prelim_shift + round_dir) >> 1;
            if shift >> new_ty.mantissa != 0 {
                // Rounding overflow: increment exponent and zero mantissa (saturate to Inf on overflow)
                if converted_exponent < new_exponent_mask {
                    converted_exponent += 1;
                }
                // Saturate to Inf if exponent overflowed
                if converted_exponent >= new_exponent_mask {
                    converted_exponent = new_exponent_mask;
                }
                0
            } else {
                shift
            }
        };

        sign << (new_ty.exponent + new_ty.mantissa)
            | converted_exponent << new_ty.mantissa
            | converted_mantissa
    }

    /// Convert f32 to bits. The conversion is lossy and is by rounding.
    pub const fn bits_from_f32(self, float: f32) -> u32 {
        Self::F32.cast(self, float.to_bits())
    }

    /// Convert bits to f32. Only lower `bits()` bits are used.
    pub const fn convert_bits_to_f32(self, bits: u32) -> f32 {
        f32::from_bits(self.cast(Self::F32, bits))
    }
}

#[test]
fn test_f32() {
    let ty = FpType::F32;

    assert_eq!(ty.convert_bits_to_f32(0f32.to_bits()), 0f32);
    assert_eq!(ty.convert_bits_to_f32(1f32.to_bits()), 1f32);
    assert_eq!(
        ty.convert_bits_to_f32(f32::INFINITY.to_bits()),
        f32::INFINITY
    );
    assert_eq!(
        ty.convert_bits_to_f32(f32::NEG_INFINITY.to_bits()),
        f32::NEG_INFINITY
    );
}

#[test]
fn test_f16() {
    use half::f16;

    let ty = FpType::F16;

    assert_eq!(ty.convert_bits_to_f32(f16::ZERO.to_bits() as u32), 0f32);
    assert_eq!(ty.convert_bits_to_f32(f16::ONE.to_bits() as u32), 1f32);
    assert_eq!(
        ty.convert_bits_to_f32(f16::INFINITY.to_bits() as u32),
        f32::INFINITY
    );
    assert_eq!(
        ty.convert_bits_to_f32(f16::NEG_INFINITY.to_bits() as u32),
        f32::NEG_INFINITY
    );
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum DataType {
    Fp(FpType),
}

impl From<FpType> for DataType {
    fn from(value: FpType) -> Self {
        Self::Fp(value)
    }
}

impl DataType {
    pub fn size_in_bits(self) -> u8 {
        match self {
            DataType::Fp(fp_type) => fp_type.size_in_bits(),
        }
    }

    pub const fn bits_from_f32(self, float: f32) -> u32 {
        match self {
            DataType::Fp(fp_type) => fp_type.bits_from_f32(float),
        }
    }

    pub const fn convert_bits_to_f32(self, bits: u32) -> f32 {
        match self {
            DataType::Fp(fp_type) => fp_type.convert_bits_to_f32(bits),
        }
    }

    /// Convert bytes to vector of f32.
    pub fn convert_bytes_to_f32_vec(self, mut bytes: &[u8], out: &mut [f32]) {
        let bits = self.size_in_bits();
        let mut data = 0;
        let mut bits_left = 0;
        for out in out.iter_mut() {
            while bits_left < bits {
                data |= (bytes[0] as u32) << bits_left;
                bits_left += 8;
                bytes = &bytes[1..];
            }

            *out = self.convert_bits_to_f32(data);
            bits_left -= bits;
            data >>= bits;
        }
    }

    pub fn bytes_from_f32(self, input: &[f32], mut out: &mut [u8]) {
        let bits = self.size_in_bits();
        let mut data = 0;
        let mut bits_left = 0u8;

        for elem in input.iter().copied() {
            while bits_left >= 8 {
                out[0] = data as u8;
                out = &mut out[1..];
                data >>= 8;
                bits_left -= 8;
            }

            data |= self.bits_from_f32(elem) << bits_left;
            bits_left += bits;
        }

        while bits_left > 0 {
            out[0] = data as u8;
            out = &mut out[1..];
            data >>= 8;
            bits_left = bits_left.saturating_sub(8);
        }
    }

    pub fn size_in_bytes(&self) -> usize {
        let size = self.size_in_bits();
        assert!(size.is_multiple_of(8));
        size as usize
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum MxDataType {
    Plain(DataType),
    Mx {
        elem: DataType,
        scale: DataType,
        block: u32,
    },
}

impl MxDataType {
    pub fn element_type(self) -> DataType {
        match self {
            MxDataType::Plain(elem) => elem,
            MxDataType::Mx { elem, .. } => elem,
        }
    }
}

impl From<FpType> for MxDataType {
    fn from(value: FpType) -> Self {
        MxDataType::Plain(value.into())
    }
}

impl From<DataType> for MxDataType {
    fn from(value: DataType) -> Self {
        MxDataType::Plain(value)
    }
}

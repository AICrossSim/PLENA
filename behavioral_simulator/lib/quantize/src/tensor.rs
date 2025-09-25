use anyhow::Result;
use tch::Tensor;

use crate::dtype::MxDataType;

pub struct QuantTensor {
    tensor: Tensor,
    ty: MxDataType,
}

impl Clone for QuantTensor {
    fn clone(&self) -> Self {
        Self {
            tensor: self.tensor.copy(),
            ty: self.ty,
        }
    }
}

impl QuantTensor {
    /// Create a quantized tensor, assuming the tensor is already quantized.
    pub fn new_assuming_quantized(tensor: Tensor, ty: MxDataType) -> Result<Self> {
        anyhow::ensure!(tensor.dim() == 1);
        anyhow::ensure!(tensor.kind() == tch::Kind::Float);
        anyhow::ensure!(tensor.device() == tch::Device::Cpu);
        Ok(QuantTensor { tensor: tensor, ty })
    }

    /// Create a quantized tensor, assuming the tensor is already quantized.
    pub fn quantize(tensor: Tensor, ty: MxDataType) -> Self {
        // TODO: add actual quantization
        Self::new_assuming_quantized(tensor, ty).unwrap()
    }

    /// Create a zeroed quantized tensor.
    pub fn zeros(size: usize, ty: MxDataType) -> Self {
        Self::new_assuming_quantized(
            Tensor::zeros([size as i64], (tch::Kind::Float, tch::Device::Cpu)),
            ty,
        )
        .unwrap()
    }

    /// Return the underlying torch Tensor.
    pub fn as_tensor(&self) -> &Tensor {
        &self.tensor
    }

    /// Return the data type of the quantized tensor.
    pub fn data_type(&self) -> MxDataType {
        self.ty
    }

    /// Deserialize a quantized tensor from bytes.
    pub fn from_bytes(bytes: &[u8], scale_bytes: &[u8], len: usize, ty: MxDataType) -> Self {
        let elem_ty = ty.element_type();

        let mut vec = vec![0f32; len];
        elem_ty.convert_bytes_to_f32_vec(bytes, &mut vec);

        if let MxDataType::Mx {
            elem: _,
            scale,
            block,
        } = ty
        {
            let mut scale_vec = vec![0f32; len / block as usize];

            scale.convert_bytes_to_f32_vec(&scale_bytes, &mut scale_vec);

            for (elem, scale) in vec
                .chunks_mut(block as usize)
                .zip(scale_vec.iter().copied())
            {
                for elem in elem.iter_mut() {
                    *elem *= scale;
                }
            }
        }

        let tensor = tch::Tensor::from_slice(&vec);
        Self { tensor, ty }
    }

    /// Serialize the quantized tensor into bytes.
    pub fn into_bytes(&mut self) -> (Vec<u8>, Vec<u8>) {
        let len = self.tensor.size1().unwrap() as usize;
        let slice =
            unsafe { core::slice::from_raw_parts(self.tensor.data_ptr() as *const f32, len) };

        let elem_ty = self.ty.element_type();
        let mut out = vec![0; len * elem_ty.size_in_bits() as usize / 8];
        elem_ty.bytes_from_f32(slice, &mut out);

        if let MxDataType::Mx {
            elem: _,
            scale,
            block,
        } = self.ty
        {
            // TODO: properly do this
            let scale_vec = vec![1f32; len / block as usize];
            let mut scale_out = vec![0; (len / block as usize) * scale.size_in_bits() as usize / 8];

            scale.bytes_from_f32(&scale_vec, &mut scale_out);

            return (out, scale_out);
        }

        (out, Vec::new())
    }
}

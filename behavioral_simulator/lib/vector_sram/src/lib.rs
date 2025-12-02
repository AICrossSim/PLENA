use quantize::{MxDataType, QuantTensor};
use tokio::sync::Mutex;
use tokio::sync::oneshot::Receiver;
use tch::{IndexOp, Tensor};

/// Vector SRAM that stores data in binary format with row-based storage.
///
/// The SRAM is organized as rows, where each row has a width of `vlen * element_size_in_bytes`.
/// During read/write operations, data is clipped to VLEN-sized vectors and converted
/// between storage precision and access precision.
pub struct VectorSram {
    /// Vector length (VLEN) - determines the size of each vector operation
    vlen: u32,
    /// Number of rows in the SRAM
    depth: usize,
    /// Storage precision - how data is stored internally
    storage_precision: MxDataType,
    /// Access precision - how data is read/written (defaults to storage_precision if None)
    access_precision: Option<MxDataType>,
    /// Raw binary storage: each row is stored as bytes
    /// Row width = vlen * element_size_in_bytes(storage_precision)
    rows: Vec<Mutex<RowData>>,
}

/// Represents a row of data, either ready or pending from a delayed write
enum RowData {
    Ready(Vec<u8>),
    Pending(Receiver<QuantTensor>),
}

impl VectorSram {
    /// Create a new Vector SRAM with given vector length, depth, and storage precision.
    ///
    /// # Arguments
    /// * `vlen` - Vector length (VLEN)
    /// * `depth` - Number of rows in the SRAM
    /// * `storage_precision` - Precision used for internal storage
    /// * `access_precision` - Optional precision for read/write operations (defaults to storage_precision)
    pub fn new(
        vlen: u32,
        depth: usize,
        storage_precision: MxDataType,
        access_precision: Option<MxDataType>,
    ) -> Self {
        let element_ty = storage_precision.element_type();
        let element_size = element_ty.size_in_bits() as usize / 8;
        let row_width = vlen as usize * element_size;

        // Handle Mx format: need to account for scale bytes
        let row_width = match storage_precision {
            MxDataType::Plain(_) => row_width,
            MxDataType::Mx { block, scale, .. } => {
                let num_blocks = (vlen as usize + block as usize - 1) / block as usize;
                let scale_bytes = scale.size_in_bits() as usize / 8;
                row_width + num_blocks * scale_bytes
            }
        };

        let rows = (0..depth)
            .map(|_| {
                Mutex::new(RowData::Ready(vec![0u8; row_width]))
            })
            .collect();

        Self {
            vlen,
            depth,
            storage_precision,
            access_precision,
            rows,
        }
    }

    /// Get the vector length (VLEN)
    pub fn tile_size(&self) -> u32 {
        self.vlen
    }

    /// Get the storage precision type
    pub fn ty(&self) -> MxDataType {
        self.access_precision.unwrap_or(self.storage_precision)
    }

    /// Get the size of the SRAM in bytes
    pub fn size_in_bytes(&self) -> usize {
        let element_ty = self.storage_precision.element_type();
        let element_size = element_ty.size_in_bits() as usize / 8;
        let base_row_width = self.vlen as usize * element_size;

        let row_width = match self.storage_precision {
            MxDataType::Plain(_) => base_row_width,
            MxDataType::Mx { block, scale, .. } => {
                let num_blocks = (self.vlen as usize + block as usize - 1) / block as usize;
                let scale_bytes = scale.size_in_bits() as usize / 8;
                base_row_width + num_blocks * scale_bytes
            }
        };

        row_width * self.depth
    }

    /// Read a vector from the SRAM at the given address.
    ///
    /// The address must be a multiple of vlen (in element units).
    /// Data is read from storage precision and converted to access precision.
    pub async fn read(&self, addr: u32) -> QuantTensor {
        let row_idx = self.addr_to_row_idx(addr);
        assert!(row_idx < self.depth, "Address out of bounds");

        let mut guard = self.rows[row_idx].lock().await;
        
        // Handle pending writes
        if let RowData::Pending(ref mut receiver) = *guard {
            let tensor = receiver.await.unwrap();
            let row_bytes = self.quant_tensor_to_bytes(&tensor, self.storage_precision);
            *guard = RowData::Ready(row_bytes);
        }

        // Read the row data
        let row_bytes = match &*guard {
            RowData::Ready(bytes) => bytes.clone(),
            RowData::Pending(_) => unreachable!(),
        };

        // Convert from storage precision to access precision
        let access_precision = self.access_precision.unwrap_or(self.storage_precision);
        let tensor = self.bytes_to_quant_tensor(&row_bytes, self.storage_precision, self.vlen);
        
        // Convert to access precision if different
        if access_precision != self.storage_precision {
            let tensor_f32 = tensor.as_tensor();
            QuantTensor::quantize(tensor_f32.shallow_clone(), access_precision)
        } else {
            tensor
        }
    }

    /// Write a vector to the SRAM at the given address.
    ///
    /// The address must be a multiple of vlen (in element units).
    /// Data is converted from access precision to storage precision before writing.
    pub async fn write(&self, addr: u32, tensor: QuantTensor) {
        let row_idx = self.addr_to_row_idx(addr);
        assert!(row_idx < self.depth, "Address out of bounds");

        // Convert to storage precision if needed
        let storage_tensor = if tensor.data_type() != self.storage_precision {
            let tensor_f32 = tensor.as_tensor();
            QuantTensor::quantize(tensor_f32.shallow_clone(), self.storage_precision)
        } else {
            tensor
        };

        // Clip to VLEN
        let clipped = self.clip_to_vlen(&storage_tensor);
        
        // Convert to bytes
        let row_bytes = self.quant_tensor_to_bytes(&clipped, self.storage_precision);

        *self.rows[row_idx].lock().await = RowData::Ready(row_bytes);
    }

    /// Write a vector with delayed delivery (from a channel).
    pub async fn write_delayed(&self, addr: u32, tensor: Receiver<QuantTensor>) {
        let row_idx = self.addr_to_row_idx(addr);
        assert!(row_idx < self.depth, "Address out of bounds");

        *self.rows[row_idx].lock().await = RowData::Pending(tensor);
    }

    /// Continuous write delayed - writes multiple rows from a single tensor.
    pub async fn continous_write_delayed(
        &self,
        addr: u32,
        write_amount: u32,
        tensor: Receiver<QuantTensor>,
    ) {
        let start_row_idx = self.addr_to_row_idx(addr);
        
        // Await the tensor from the channel
        let tensor = tensor.await.unwrap();
        let tensor_data = tensor.as_tensor();
        let total_elements = tensor_data.size1().unwrap() as i64;

        // Convert to storage precision if needed
        let storage_tensor = if tensor.data_type() != self.storage_precision {
            QuantTensor::quantize(tensor_data.shallow_clone(), self.storage_precision)
        } else {
            tensor
        };

        let chunk_size = self.vlen as i64;
        let num_chunks = write_amount.min(((total_elements + chunk_size - 1) / chunk_size) as u32);

        for i in 0..num_chunks {
            let row_idx = start_row_idx + i as usize;
            if row_idx >= self.depth {
                break;
            }

            let start = i as i64 * chunk_size;
            let end = (start + chunk_size).min(total_elements);
            let chunk = storage_tensor
                .as_tensor()
                .narrow(0, start, end - start)
                .shallow_clone();

            // Pad to VLEN if needed
            let padded = if (end - start) < chunk_size {
                let mut padded_tensor = Tensor::zeros(
                    [chunk_size],
                    (tch::Kind::Float, tch::Device::Cpu),
                );
                padded_tensor
                    .i(0..(end - start))
                    .copy_(&chunk);
                padded_tensor
            } else {
                chunk
            };

            let chunk_qt = QuantTensor::quantize(padded, self.storage_precision);
            let row_bytes = self.quant_tensor_to_bytes(&chunk_qt, self.storage_precision);
            *self.rows[row_idx].lock().await = RowData::Ready(row_bytes);
        }
    }

    /// Load data from bytes into the SRAM.
    ///
    /// This is used for preloading the SRAM with test data.
    pub async fn load_from_bytes(&self, bytes: &[u8]) {
        let element_ty = self.storage_precision.element_type();
        let element_bits = element_ty.size_in_bits();
        let bytes_per_element = (element_bits / 8) as usize;

        // Calculate row width
        let base_row_width = self.vlen as usize * bytes_per_element;
        let _row_width = match self.storage_precision {
            MxDataType::Plain(_) => base_row_width,
            MxDataType::Mx { block, scale, .. } => {
                let num_blocks = (self.vlen as usize + block as usize - 1) / block as usize;
                let scale_bytes = scale.size_in_bits() as usize / 8;
                base_row_width + num_blocks * scale_bytes
            }
        };

        let total_elements = bytes.len() / bytes_per_element;
        let num_rows = (total_elements + self.vlen as usize - 1) / self.vlen as usize;

        for row_idx in 0..num_rows.min(self.depth) {
            let start_element = row_idx * self.vlen as usize;
            let end_element = (start_element + self.vlen as usize).min(total_elements);
            let elements_in_row = end_element - start_element;

            let start_byte = start_element * bytes_per_element;
            let end_byte = end_element * bytes_per_element;

            // Convert bytes to f32 values
            let mut vec = vec![0f32; elements_in_row];
            element_ty.convert_bytes_to_f32_vec(&bytes[start_byte..end_byte], &mut vec);

            // Pad with zeros if needed
            if elements_in_row < self.vlen as usize {
                vec.resize(self.vlen as usize, 0.0f32);
            }

            // Create QuantTensor and convert to bytes
            let tensor = Tensor::from_slice(&vec);
            let quant_tensor = QuantTensor::quantize(tensor, self.storage_precision);
            let row_bytes = self.quant_tensor_to_bytes(&quant_tensor, self.storage_precision);
            *self.rows[row_idx].lock().await = RowData::Ready(row_bytes);
        }
    }

    /// Dump the entire SRAM content as bytes.
    ///
    /// This returns the raw binary representation of all stored data.
    pub async fn as_bytes(&self) -> Vec<u8> {
        let mut result = Vec::new();

        for row_mutex in &self.rows {
            let mut guard = row_mutex.lock().await;
            
            // Handle pending writes
            if let RowData::Pending(ref mut receiver) = *guard {
                let tensor = receiver.await.unwrap();
                let row_bytes = self.quant_tensor_to_bytes(&tensor, self.storage_precision);
                *guard = RowData::Ready(row_bytes);
            }

            // Read the row data
            let row_bytes = match &*guard {
                RowData::Ready(bytes) => bytes.clone(),
                RowData::Pending(_) => unreachable!(),
            };

            result.extend_from_slice(&row_bytes);
        }

        result
    }

    // Helper methods

    /// Convert address (in element units) to row index
    fn addr_to_row_idx(&self, addr: u32) -> usize {
        assert!(addr % self.vlen == 0, "Address must be multiple of vlen");
        (addr / self.vlen) as usize
    }

    /// Clip a tensor to VLEN size
    fn clip_to_vlen(&self, tensor: &QuantTensor) -> QuantTensor {
        let tensor_data = tensor.as_tensor();
        let len = tensor_data.size1().unwrap() as i64;
        
        if len <= self.vlen as i64 {
            tensor.clone()
        } else {
            let clipped = tensor_data.narrow(0, 0, self.vlen as i64);
            QuantTensor::quantize(clipped, tensor.data_type())
        }
    }

    /// Convert QuantTensor to bytes according to the given precision
    fn quant_tensor_to_bytes(&self, tensor: &QuantTensor, precision: MxDataType) -> Vec<u8> {
        let tensor_data = tensor.as_tensor();
        let len = tensor_data.size1().unwrap() as usize;
        let f32_slice = unsafe {
            core::slice::from_raw_parts(tensor_data.data_ptr() as *const f32, len)
        };

        match precision {
            MxDataType::Plain(elem_ty) => {
                let total_bits = len * elem_ty.size_in_bits() as usize;
                let bytes_needed = (total_bits + 7) / 8;
                let mut bytes = vec![0u8; bytes_needed];
                elem_ty.bytes_from_f32(f32_slice, &mut bytes);
                bytes
            }
            MxDataType::Mx { elem, scale, block } => {
                // Serialize elements
                let total_bits = len * elem.size_in_bits() as usize;
                let elem_bytes_needed = (total_bits + 7) / 8;
                let mut elem_bytes = vec![0u8; elem_bytes_needed];
                elem.bytes_from_f32(f32_slice, &mut elem_bytes);

                // Serialize scales (one per block)
                let num_blocks = (len + block as usize - 1) / block as usize;
                // For now, use scale of 1.0 for each block
                // TODO: implement proper scale calculation
                let scale_vec = vec![1.0f32; num_blocks];
                let scale_bytes_needed = num_blocks * (scale.size_in_bits() as usize / 8);
                let mut scale_bytes = vec![0u8; scale_bytes_needed];
                scale.bytes_from_f32(&scale_vec, &mut scale_bytes);

                // Combine: elements first, then scales
                let mut result = elem_bytes;
                result.extend_from_slice(&scale_bytes);
                result
            }
        }
    }

    /// Convert bytes to QuantTensor according to the given precision
    fn bytes_to_quant_tensor(
        &self,
        bytes: &[u8],
        precision: MxDataType,
        expected_len: u32,
    ) -> QuantTensor {
        match precision {
            MxDataType::Plain(elem_ty) => {
                let bytes_per_element = elem_ty.size_in_bits() as usize / 8;
                let num_elements = bytes.len() / bytes_per_element;
                let actual_len = num_elements.min(expected_len as usize);

                let mut vec = vec![0f32; actual_len];
                elem_ty.convert_bytes_to_f32_vec(&bytes[..actual_len * bytes_per_element], &mut vec);

                // Pad to expected_len if needed
                if actual_len < expected_len as usize {
                    vec.resize(expected_len as usize, 0.0f32);
                }

                let tensor = Tensor::from_slice(&vec);
                QuantTensor::quantize(tensor, precision)
            }
            MxDataType::Mx { elem, scale, block } => {
                // Parse elements and scales
                let elem_bytes_per_element = elem.size_in_bits() as usize / 8;
                let num_blocks = (expected_len as usize + block as usize - 1) / block as usize;
                let scale_bytes_per_scale = scale.size_in_bits() as usize / 8;
                
                let elem_bytes_len = expected_len as usize * elem_bytes_per_element;
                let scale_bytes_len = num_blocks * scale_bytes_per_scale;
                let total_expected = elem_bytes_len + scale_bytes_len;

                let (elem_bytes, scale_bytes) = if bytes.len() >= total_expected {
                    bytes.split_at(elem_bytes_len)
                } else {
                    // Handle incomplete data
                    let elem_len = bytes.len().min(elem_bytes_len);
                    (&bytes[..elem_len], &bytes[elem_len..])
                };

                // Convert elements
                let mut vec = vec![0f32; expected_len as usize];
                if !elem_bytes.is_empty() {
                    let actual_elem_len = (elem_bytes.len() / elem_bytes_per_element).min(expected_len as usize);
                    elem.convert_bytes_to_f32_vec(
                        &elem_bytes[..actual_elem_len * elem_bytes_per_element],
                        &mut vec[..actual_elem_len],
                    );
                }

                // Apply scales if available
                if !scale_bytes.is_empty() && scale_bytes.len() >= scale_bytes_per_scale {
                    let mut scale_vec = vec![0f32; num_blocks];
                    scale.convert_bytes_to_f32_vec(scale_bytes, &mut scale_vec);

                    for (chunk, scale_val) in vec.chunks_mut(block as usize).zip(scale_vec.iter().copied()) {
                        for elem in chunk.iter_mut() {
                            *elem *= scale_val;
                        }
                    }
                }

                let tensor = Tensor::from_slice(&vec);
                QuantTensor::quantize(tensor, precision)
            }
        }
    }
}


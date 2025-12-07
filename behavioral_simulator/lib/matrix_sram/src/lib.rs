use quantize::{MxDataType, QuantTensor};
use tokio::sync::Mutex;
use tokio::sync::oneshot::Receiver;
use std::sync::Arc;
use sram3d::MultiLayerInterposerSram;
use sram3d::model::{InterposerConfig, SingleSRAMConfig};
use runtime::{Duration, Executor};
use memory::MemoryModel;

/// Configuration for Matrix SRAM
#[derive(Debug, Clone)]
pub struct MatrixSramConfig {
    /// Enable 3D SRAM (if available)
    pub sram3d_enabled: bool,
    /// Normal SRAM read latency in cycles (default: 1)
    pub normal_read_latency_cycles: u32,
    /// Normal SRAM write latency in cycles (default: 1)
    pub normal_write_latency_cycles: u32,
    /// 3D SRAM configuration (only used if sram3d_enabled is true)
    pub sram3d_config: Option<InterposerConfig>,
}

impl Default for MatrixSramConfig {
    fn default() -> Self {
        Self {
            sram3d_enabled: false,
            normal_read_latency_cycles: 1,
            normal_write_latency_cycles: 1,
            sram3d_config: None,
        }
    }
}

/// Storage backend for Matrix SRAM
enum StorageBackend {
    /// Normal SRAM with tile-based storage
    Normal {
        tiles: Vec<Mutex<TileData>>,
    },
    /// 3D SRAM backend
    Sram3d {
        /// Tile-based storage for data
        tiles: Vec<Mutex<TileData>>,
        /// 3D SRAM instance for latency modeling
        sram3d: Arc<MultiLayerInterposerSram>,
        /// Base byte address for this SRAM in 3D SRAM address space
        base_addr: u64,
    },
}

/// Represents a tile of data, either ready or pending from a delayed write
enum TileData {
    Ready(QuantTensor),
    Pending(Receiver<QuantTensor>),
}

/// Matrix SRAM that stores data in tile-based format.
///
/// The SRAM stores matrix tiles where each tile is of size `tile_size * tile_size`.
/// Supports both normal SRAM and 3D SRAM backends with configurable latency.
pub struct MatrixSram {
    /// Tile size (e.g., MLEN) - determines the dimensions of each matrix tile
    tile_size: u32,
    /// Number of tiles in the SRAM
    depth: usize,
    /// Data type for storage
    ty: MxDataType,
    /// Storage backend (normal or 3D SRAM)
    storage: StorageBackend,
    /// Configuration
    config: MatrixSramConfig,
}

impl MatrixSram {
    /// Create a new Matrix SRAM with given tile size, depth, and data type.
    ///
    /// # Arguments
    /// * `tile_size` - Tile size (e.g., MLEN) - dimensions of each matrix tile
    /// * `depth` - Number of tiles in the SRAM
    /// * `ty` - Matrix data type
    pub fn new(tile_size: u32, depth: usize, ty: MxDataType) -> Self {
        Self::new_with_config(tile_size, depth, ty, MatrixSramConfig::default())
    }

    /// Create a new Matrix SRAM with given tile size, depth, data type, and SRAM type string.
    ///
    /// # Arguments
    /// * `tile_size` - Tile size (e.g., MLEN) - dimensions of each matrix tile
    /// * `depth` - Number of tiles in the SRAM
    /// * `ty` - Matrix data type
    /// * `sram_type` - SRAM type string: "SRAM" for normal SRAM, "3D_SRAM" for 3D SRAM
    pub fn new_with_type(tile_size: u32, depth: usize, ty: MxDataType, sram_type: &str) -> Self {
        let mut config = MatrixSramConfig::default();
        
        // Check if 3D SRAM is requested (case-insensitive comparison)
        let sram_type_upper = sram_type.trim().to_uppercase();
        if sram_type_upper == "3D_SRAM" || sram_type_upper == "3DSRAM" {
            config.sram3d_enabled = true;
        }
        // If sram_type is "SRAM" or anything else, use default (normal SRAM)
        
        Self::new_with_config(tile_size, depth, ty, config)
    }

    /// Create a new Matrix SRAM with configuration.
    ///
    /// # Arguments
    /// * `tile_size` - Tile size (e.g., MLEN) - dimensions of each matrix tile
    /// * `depth` - Number of tiles in the SRAM
    /// * `ty` - Matrix data type
    /// * `config` - Configuration including 3D SRAM enable and latency settings
    pub fn new_with_config(
        tile_size: u32,
        depth: usize,
        ty: MxDataType,
        config: MatrixSramConfig,
    ) -> Self {
        let tiles: Vec<Mutex<TileData>> = (0..depth)
            .map(|_| {
                Mutex::new(TileData::Ready(QuantTensor::zeros(
                    (tile_size * tile_size) as usize,
                    ty.clone(),
                )))
            })
            .collect();

        let storage = if config.sram3d_enabled {
            // Calculate total capacity needed
            let element_ty = ty.element_type();
            let element_size = element_ty.size_in_bits() as usize / 8;
            let tile_size_elements = (tile_size * tile_size) as usize;
            let tile_size_bytes = tile_size_elements * element_size;
            let total_capacity = tile_size_bytes * depth;
            
            // Round up to 64-byte cache lines
            let capacity_bytes = ((total_capacity + 63) / 64) * 64;

            // Use provided config or default
            let sram3d_config = config.sram3d_config.clone().unwrap_or_else(|| {
                InterposerConfig {
                    layers: vec![SingleSRAMConfig::new(
                        capacity_bytes.max(64) as u64,
                        256, // bytes per cycle bandwidth
                    )],
                    srams_per_layer: 64,
                    cycle_time: Duration::from_picos(1000), // 1 ns cycle
                    base_latency_cycles: 5,
                }
            });

            let sram3d = Arc::new(MultiLayerInterposerSram::new(sram3d_config));
            StorageBackend::Sram3d {
                tiles,
                sram3d,
                base_addr: 0,
            }
        } else {
            StorageBackend::Normal { tiles }
        };

        Self {
            tile_size,
            depth,
            ty,
            storage,
            config,
        }
    }

    /// Simulate latency for normal SRAM operations
    async fn simulate_latency(&self, cycles: u32, _is_read: bool) {
        // Use runtime executor for cycle-accurate latency simulation
        // Note: This assumes the runtime executor is available in the simulation context
        let executor = Executor::current();
        let cycle_time = Duration::from_picos(1000); // 1 ns per cycle
        let latency = cycle_time * cycles as u64;
        executor.resolve_at(executor.now() + latency).await;
    }

    /// Convert address (in element units) to tile index
    fn addr_to_tile_idx(&self, addr: u32) -> usize {
        assert!(addr.is_multiple_of(self.tile_size * self.tile_size), 
                "Address must be multiple of tile_size * tile_size");
        (addr / (self.tile_size * self.tile_size)) as usize
    }

    /// Get the tile size
    pub fn tile_size(&self) -> u32 {
        self.tile_size
    }

    /// Get the data type
    pub fn ty(&self) -> &MxDataType {
        &self.ty
    }

    /// Get the size of the SRAM in bytes
    pub fn size_in_bytes(&self) -> usize {
        let element_ty = self.ty.element_type();
        let element_size = element_ty.size_in_bits() as usize / 8;
        let tile_size_elements = (self.tile_size * self.tile_size) as usize;
        tile_size_elements * element_size * self.depth
    }

    /// Read a tile from the SRAM at the given address.
    ///
    /// The address must be a multiple of tile_size * tile_size (in element units).
    pub async fn read(&self, addr: u32) -> QuantTensor {
        let tile_idx = self.addr_to_tile_idx(addr);
        assert!(tile_idx < self.depth, "Address out of bounds");

        // Simulate latency based on backend
        match &self.storage {
            StorageBackend::Normal { .. } => {
                self.simulate_latency(self.config.normal_read_latency_cycles, true).await;
            }
            StorageBackend::Sram3d { sram3d, base_addr, .. } => {
                // Calculate byte address for this tile
                let element_ty = self.ty.element_type();
                let element_size = element_ty.size_in_bits() as usize / 8;
                let tile_size_bytes = (self.tile_size * self.tile_size) as usize * element_size;
                let byte_addr = base_addr + (tile_idx * tile_size_bytes) as u64;
                // Align to 64-byte cache line
                let cache_line_addr = (byte_addr / 64) * 64;
                
                // Use 3D SRAM latency model
                let _ = sram3d.read(cache_line_addr).await;
            }
        }

        // Read actual data from tile storage
        let tile = match &self.storage {
            StorageBackend::Normal { tiles } => {
                let mut guard = tiles[tile_idx].lock().await;
                
                // Handle pending writes
                if let TileData::Pending(ref mut receiver) = *guard {
                    let tensor = receiver.await.unwrap();
                    *guard = TileData::Ready(tensor.clone());
                    tensor
                } else {
                    match &*guard {
                        TileData::Ready(tensor) => tensor.clone(),
                        TileData::Pending(_) => unreachable!(),
                    }
                }
            }
            StorageBackend::Sram3d { tiles, .. } => {
                let mut guard = tiles[tile_idx].lock().await;
                
                // Handle pending writes
                if let TileData::Pending(ref mut receiver) = *guard {
                    let tensor = receiver.await.unwrap();
                    *guard = TileData::Ready(tensor.clone());
                    tensor
                } else {
                    match &*guard {
                        TileData::Ready(tensor) => tensor.clone(),
                        TileData::Pending(_) => unreachable!(),
                    }
                }
            }
        };

        tile
    }

    /// Write a tile to the SRAM at the given address.
    ///
    /// The address must be a multiple of tile_size * tile_size (in element units).
    pub async fn write(&self, addr: u32, tensor: QuantTensor) {
        let tile_idx = self.addr_to_tile_idx(addr);
        assert!(tile_idx < self.depth, "Address out of bounds");
        assert!(tensor.data_type() == self.ty, "Tensor data type mismatch");

        // Simulate latency based on backend
        match &self.storage {
            StorageBackend::Normal { .. } => {
                self.simulate_latency(self.config.normal_write_latency_cycles, false).await;
            }
            StorageBackend::Sram3d { sram3d, base_addr, .. } => {
                // Calculate byte address for this tile
                let element_ty = self.ty.element_type();
                let element_size = element_ty.size_in_bits() as usize / 8;
                let tile_size_bytes = (self.tile_size * self.tile_size) as usize * element_size;
                let byte_addr = base_addr + (tile_idx * tile_size_bytes) as u64;
                let cache_line_addr = (byte_addr / 64) * 64;
                
                // Convert tensor to bytes for 3D SRAM write
                let tensor_data = tensor.as_tensor();
                let len = tensor_data.size1().unwrap() as usize;
                let f32_slice = unsafe {
                    core::slice::from_raw_parts(tensor_data.data_ptr() as *const f32, len)
                };
                
                let total_bits = len * element_ty.size_in_bits() as usize;
                let bytes_needed = (total_bits + 7) / 8;
                let mut tile_bytes = vec![0u8; bytes_needed];
                element_ty.bytes_from_f32(f32_slice, &mut tile_bytes);
                
                // Write to 3D SRAM (pad to 64-byte cache line)
                let mut cache_line = [0u8; 64];
                let copy_len = tile_bytes.len().min(64);
                cache_line[..copy_len].copy_from_slice(&tile_bytes[..copy_len]);
                sram3d.write(cache_line_addr, cache_line).await;
            }
        }

        // Write to tile storage
        match &self.storage {
            StorageBackend::Normal { tiles } => {
                *tiles[tile_idx].lock().await = TileData::Ready(tensor);
            }
            StorageBackend::Sram3d { tiles, .. } => {
                *tiles[tile_idx].lock().await = TileData::Ready(tensor);
            }
        }
    }

    /// Write a tile with delayed delivery (from a channel).
    /// 
    /// The address is in tile units (not element units), so it's divided by tile_size.
    pub async fn write_delayed(&self, addr: u32, tensor: Receiver<QuantTensor>) {
        // Note: original code used assert_multiple_of(self.tile_size), which divides by tile_size
        // This suggests addr is in tile units, not element units
        let tile_idx = (addr / self.tile_size) as usize;
        assert!(tile_idx < self.depth, "Address out of bounds");

        match &self.storage {
            StorageBackend::Normal { tiles } => {
                *tiles[tile_idx].lock().await = TileData::Pending(tensor);
            }
            StorageBackend::Sram3d { tiles, .. } => {
                *tiles[tile_idx].lock().await = TileData::Pending(tensor);
            }
        }
    }

    /// Continuous write delayed - writes multiple tiles from a single tensor.
    pub async fn continous_write_delayed(
        &self,
        addr: u32,
        write_amount: u32,
        tensor: Receiver<QuantTensor>,
    ) {
        let start_tile_idx = self.addr_to_tile_idx(addr);
        
        // Await the tensor from the channel
        let tensor = tensor.await.unwrap();
        let tensor_data = tensor.as_tensor();
        let dims = tensor_data.size();
        let chunk_size = (self.tile_size * self.tile_size) as i64;
        let total = dims[0];

        // Split the tensor into chunks of tile_size * tile_size and store each in tiles
        for i in 0..write_amount.min(
            (total as u32 + self.tile_size * self.tile_size - 1)
                / (self.tile_size * self.tile_size),
        ) {
            let tile_idx = start_tile_idx + i as usize;
            if tile_idx >= self.depth {
                break;
            }

            let start = (i as i64) * chunk_size;
            let end = ((i as i64 + 1) * chunk_size).min(total);
            let chunk = tensor_data
                .narrow(0, start, end - start)
                .shallow_clone();
            let chunk_qt = QuantTensor::quantize(chunk, self.ty.clone());

            // Simulate latency for each write
            match &self.storage {
                StorageBackend::Normal { .. } => {
                    self.simulate_latency(self.config.normal_write_latency_cycles, false).await;
                }
                StorageBackend::Sram3d { sram3d, base_addr, .. } => {
                    let element_ty = self.ty.element_type();
                    let element_size = element_ty.size_in_bits() as usize / 8;
                    let tile_size_bytes = (self.tile_size * self.tile_size) as usize * element_size;
                    let byte_addr = base_addr + (tile_idx * tile_size_bytes) as u64;
                    let cache_line_addr = (byte_addr / 64) * 64;
                    
                    // Convert chunk to bytes
                    let chunk_data = chunk_qt.as_tensor();
                    let len = chunk_data.size1().unwrap() as usize;
                    let f32_slice = unsafe {
                        core::slice::from_raw_parts(chunk_data.data_ptr() as *const f32, len)
                    };
                    
                    let total_bits = len * element_ty.size_in_bits() as usize;
                    let bytes_needed = (total_bits + 7) / 8;
                    let mut tile_bytes = vec![0u8; bytes_needed];
                    element_ty.bytes_from_f32(f32_slice, &mut tile_bytes);
                    
                    let mut cache_line = [0u8; 64];
                    let copy_len = tile_bytes.len().min(64);
                    cache_line[..copy_len].copy_from_slice(&tile_bytes[..copy_len]);
                    sram3d.write(cache_line_addr, cache_line).await;
                }
            }

            // Write to storage
            match &self.storage {
                StorageBackend::Normal { tiles } => {
                    *tiles[tile_idx].lock().await = TileData::Ready(chunk_qt);
                }
                StorageBackend::Sram3d { tiles, .. } => {
                    *tiles[tile_idx].lock().await = TileData::Ready(chunk_qt);
                }
            }
        }
    }

    /// Dump the entire SRAM content as bytes.
    ///
    /// This returns the raw binary representation of all stored data.
    pub async fn as_bytes(&self) -> Vec<u8> {
        let element_ty = self.ty.element_type();
        let mut result = Vec::new();

        match &self.storage {
            StorageBackend::Normal { tiles } => {
                for tile_mutex in tiles {
                    let mut guard = tile_mutex.lock().await;
                    if let TileData::Pending(ref mut fut) = *guard {
                        let tensor = fut.await.unwrap();
                        *guard = TileData::Ready(tensor.clone());
                    }
                    let tensor = match &*guard {
                        TileData::Ready(tensor) => tensor,
                        TileData::Pending(_) => unreachable!(),
                    };
                    let tensor_data = tensor.as_tensor();
                    let len = tensor_data.size1().unwrap() as usize;
                    let f32_slice = unsafe {
                        core::slice::from_raw_parts(tensor_data.data_ptr() as *const f32, len)
                    };
                    // Calculate bytes needed for THIS tile's actual size
                    let total_bits = len * element_ty.size_in_bits() as usize;
                    let bytes_needed = (total_bits + 7) / 8;
                    let mut tile_bytes = vec![0u8; bytes_needed];
                    element_ty.bytes_from_f32(f32_slice, &mut tile_bytes);
                    result.extend_from_slice(&tile_bytes);
                }
            }
            StorageBackend::Sram3d { tiles, .. } => {
                for tile_mutex in tiles {
                    let mut guard = tile_mutex.lock().await;
                    if let TileData::Pending(ref mut fut) = *guard {
                        let tensor = fut.await.unwrap();
                        *guard = TileData::Ready(tensor.clone());
                    }
                    let tensor = match &*guard {
                        TileData::Ready(tensor) => tensor,
                        TileData::Pending(_) => unreachable!(),
                    };
                    let tensor_data = tensor.as_tensor();
                    let len = tensor_data.size1().unwrap() as usize;
                    let f32_slice = unsafe {
                        core::slice::from_raw_parts(tensor_data.data_ptr() as *const f32, len)
                    };
                    // Calculate bytes needed for THIS tile's actual size
                    let total_bits = len * element_ty.size_in_bits() as usize;
                    let bytes_needed = (total_bits + 7) / 8;
                    let mut tile_bytes = vec![0u8; bytes_needed];
                    element_ty.bytes_from_f32(f32_slice, &mut tile_bytes);
                    result.extend_from_slice(&tile_bytes);
                }
            }
        }

        result
    }
}


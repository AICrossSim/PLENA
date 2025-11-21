use std::sync::Mutex;

use async_trait::async_trait;
use memory::MemoryModel;
use runtime::{Duration, Executor, Instant};
use tokio::sync::Mutex as AsyncMutex;

/// Size of a cache line / transfer unit in bytes.
const LINE_SIZE: u64 = 64;

/// Configuration for a single interposer layer.
#[derive(Debug, Clone)]
pub struct LayerConfig {
    /// Byte addressable capacity provided by this layer.
    pub capacity_bytes: u64,
    /// Per-SRAM bandwidth expressed in bytes per cycle.
    pub sram_bandwidth_bytes_per_cycle: u32,
}

impl LayerConfig {
    pub const fn new(capacity_bytes: u64, sram_bandwidth_bytes_per_cycle: u32) -> Self {
        Self {
            capacity_bytes,
            sram_bandwidth_bytes_per_cycle,
        }
    }
}

/// Configuration for the multi-layer interposer SRAM.
#[derive(Debug, Clone)]
pub struct InterposerConfig {
    /// Description for every stacked interposer.
    pub layers: Vec<LayerConfig>,
    /// Number of SRAM tiles per interposer (default 64).
    pub srams_per_layer: usize,
    /// Duration of a single cycle in the timing model.
    pub cycle_time: Duration,
    /// Base latency component in cycles (latency = base + layer_id).
    pub base_latency_cycles: u32,
}

impl Default for InterposerConfig {
    fn default() -> Self {
        let per_layer_capacity = 1u64 << 30; // 1 GiB per interposer.
        Self {
            layers: vec![
                LayerConfig::new(per_layer_capacity, 256),
                LayerConfig::new(per_layer_capacity, 256),
                LayerConfig::new(per_layer_capacity, 256),
                LayerConfig::new(per_layer_capacity, 256),
            ],
            srams_per_layer: 64,
            cycle_time: Duration::from_picos(1000), // 1 ns cycle.
            base_latency_cycles: 5,
        }
    }
}

struct Tile {
    data: Mutex<Vec<[u8; LINE_SIZE as usize]>>,
    next_issue: AsyncMutex<Instant>,
}

impl Tile {
    fn new(blocks: usize) -> Self {
        Self {
            data: Mutex::new(vec![[0; LINE_SIZE as usize]; blocks]),
            next_issue: AsyncMutex::new(Instant::INIT),
        }
    }

    fn read_block(&self, idx: usize) -> [u8; 64] {
        self.data.lock().unwrap()[idx]
    }

    fn write_block(&self, idx: usize, bytes: [u8; 64]) {
        self.data.lock().unwrap()[idx] = bytes;
    }
}

/// A configurable, multi-layer interposer SRAM timing + storage model.
pub struct MultiLayerInterposerSram {
    config: InterposerConfig,
    tiles: Vec<Vec<Tile>>,
    layer_size: Vec<u64>,
    issue_duration: Vec<Duration>,
    layer_latency: Vec<Duration>,
    total_capacity: u64,
}

impl MultiLayerInterposerSram {
    pub fn new(config: InterposerConfig) -> Self {
        assert!(!config.layers.is_empty(), "Need at least one interposer layer");
        assert!(config.srams_per_layer > 0, "Need at least one SRAM per layer");
        for layer in &config.layers {
            assert!(
                layer.capacity_bytes.is_multiple_of(LINE_SIZE),
                "Layer capacity must align to 64-byte lines"
            );
            assert!(
                layer.sram_bandwidth_bytes_per_cycle > 0,
                "Tile bandwidth must be non-zero"
            );
        }

        let total_capacity = config.layers.iter().map(|l| l.capacity_bytes).sum();
        let mut tiles = Vec::with_capacity(config.layers.len());
        let mut layer_size = Vec::with_capacity(config.layers.len());
        let mut issue_duration = Vec::with_capacity(config.layers.len());
        let mut layer_latency = Vec::with_capacity(config.layers.len());

        for (layer_id, layer) in config.layers.iter().enumerate() {
            let tile_capacity = layer.capacity_bytes / config.srams_per_layer as u64;
            assert!(
                tile_capacity.is_multiple_of(LINE_SIZE),
                "Tile capacity must be aligned to 64 bytes"
            );
            let blocks_per_tile = (tile_capacity / LINE_SIZE) as usize;
            let mut per_layer_tiles = Vec::with_capacity(config.srams_per_layer);
            for _ in 0..config.srams_per_layer {
                per_layer_tiles.push(Tile::new(blocks_per_tile));
            }
            tiles.push(per_layer_tiles);
            layer_size.push(layer.capacity_bytes);

            let cycles_per_issue =
                (LINE_SIZE + layer.sram_bandwidth_bytes_per_cycle as u64 - 1)
                    / layer.sram_bandwidth_bytes_per_cycle as u64;
            issue_duration.push(config.cycle_time * cycles_per_issue);

            let latency_cycles = config.base_latency_cycles as u64 + layer_id as u64;
            layer_latency.push(config.cycle_time * latency_cycles);
        }

        Self {
            config,
            tiles,
            layer_size,
            issue_duration,
            layer_latency,
            total_capacity,
        }
    }

    fn locate(&self, addr: u64) -> (usize, usize, usize) {
        assert!(
            addr + LINE_SIZE <= self.total_capacity,
            "Address {addr:#x} exceeds SRAM capacity {:#x}",
            self.total_capacity
        );

        let mut remaining = addr;
        let mut layer_idx = 0;
        for (idx, size) in self.layer_size.iter().enumerate() {
            if remaining < *size {
                layer_idx = idx;
                break;
            }
            remaining -= *size;
        }

        let tile_capacity = self.layer_size[layer_idx] / self.config.srams_per_layer as u64;
        let tile_idx = (remaining / tile_capacity) as usize;
        let offset_in_tile = remaining % tile_capacity;
        assert!(
            offset_in_tile + LINE_SIZE <= tile_capacity,
            "Access spans across tiles"
        );
        let block_idx = (offset_in_tile / LINE_SIZE) as usize;
        (layer_idx, tile_idx, block_idx)
    }

    async fn service_request(&self, layer_idx: usize, tile_idx: usize) {
        let tile = &self.tiles[layer_idx][tile_idx];
        let mut next_issue = tile.next_issue.lock().await;
        let executor = Executor::current();
        let now = executor.now();
        let issue_time = if *next_issue > now {
            *next_issue
        } else {
            now
        };
        let completion = issue_time + self.layer_latency[layer_idx];
        *next_issue = issue_time + self.issue_duration[layer_idx];
        drop(next_issue);

        if issue_time > now {
            executor.resolve_at(issue_time).await;
        }
        executor.resolve_at(completion).await;
    }
}

#[async_trait]
impl MemoryModel for MultiLayerInterposerSram {
    async fn read(&self, addr: u64) -> [u8; 64] {
        let (layer_idx, tile_idx, block_idx) = self.locate(addr);
        self.service_request(layer_idx, tile_idx).await;
        self.tiles[layer_idx][tile_idx].read_block(block_idx)
    }

    async fn write(&self, addr: u64, bytes: [u8; 64]) {
        let (layer_idx, tile_idx, block_idx) = self.locate(addr);
        self.service_request(layer_idx, tile_idx).await;
        self.tiles[layer_idx][tile_idx].write_block(block_idx, bytes);
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use runtime::{Duration, Executor, Instant};

    #[test]
    fn basic_round_trip() {
        let rt = tokio::runtime::Runtime::new().unwrap();
        rt.block_on(async {
            let cfg = InterposerConfig {
                layers: vec![LayerConfig::new(256 * 1024, 64)],
                srams_per_layer: 4,
                cycle_time: Duration::from_nanos(1),
                base_latency_cycles: 5,
            };
            let executor = Executor::new();
            executor.spawn(async move {
                let model = MultiLayerInterposerSram::new(cfg);
                let pattern = [0xAA; 64];
                model.write(0, pattern).await;
                let read_back = model.read(0).await;
                assert_eq!(read_back, pattern);
            });
            let timeout = Instant::INIT + Duration::from_micros(10);
            executor.enter(timeout).await;
        });
    }
}


use anyhow::Result;

use crate::Ramulator;
use crate::config::Config;

impl Ramulator {
    pub fn hbm2_preset(num_channels: usize) -> Result<Self> {
        let config = Config {
            dram: serde_json::json!({
                "impl": "HBM2",
                "org": {
                    "preset": "HBM2_8Gb",
                    "channel": num_channels,
                },
                "timing": {
                    "preset": "HBM2_2Gbps",
                },
            }),
            controller: serde_json::json!({
                "impl": "Generic",
                "Scheduler": {
                    "impl": "FRFCFS",
                },
                "RefreshManager": {
                    "impl": "AllBank",
                },
                "RowPolicy": {
                    "impl": "OpenRowPolicy",
                },
            }),
            addr_mapper: serde_json::json!({
                "impl": "MOP4CLXOR",
            }),
        };
        Self::new(config)
    }
}

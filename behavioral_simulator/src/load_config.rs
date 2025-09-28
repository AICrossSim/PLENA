// load_config.rs
use serde::{Deserialize, Serialize};
use std::fs;
use std::time::Duration;
use once_cell::sync::Lazy;

// Import the types from your main module
use quantize::{DataType, FpType, MxDataType};

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct AcceleratorConfig {
    pub period_nanos: u64,
    pub vector_basic_cycles: u32,
    pub vector_reduct_cycles: u32,
    pub tile_size: u32,
    pub batch_size: u32,
    pub hbm_size: usize,
    pub matrix_sram_size: usize,
    pub vector_sram_size: usize,
    pub matrix_sram_type: MxDataTypeConfig,
    pub vector_sram_type: MxDataTypeConfig,
    pub matrix_weight_type: MxDataTypeConfig,
    pub matrix_kv_type: MxDataTypeConfig,
    pub vector_activation_type: MxDataTypeConfig,
    pub vector_kv_type: MxDataTypeConfig,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct FpTypeConfig {
    pub sign: bool,
    pub exponent: u8,
    pub mantissa: u8,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
#[serde(tag = "type")]
pub enum DataTypeConfig {
    Fp(FpTypeConfig),
}

#[derive(Debug, Serialize, Deserialize, Clone)]
#[serde(tag = "format")]
pub enum MxDataTypeConfig {
    Plain { data_type: DataTypeConfig },
    Mx {
        elem: DataTypeConfig,
        scale: DataTypeConfig,
        block: u32,
    },
}

impl Default for AcceleratorConfig {
    fn default() -> Self {
        AcceleratorConfig {
            period_nanos: 1,
            vector_basic_cycles: 1,
            vector_reduct_cycles: 4,
            tile_size: 128,
            batch_size: 4,
            hbm_size: 1024 * 1024 * 1024,
            matrix_sram_size: 1024,
            vector_sram_size: 1024,
            matrix_sram_type: MxDataTypeConfig::Plain {
                data_type: DataTypeConfig::Fp(FpTypeConfig {
                    sign: true,
                    exponent: 8,
                    mantissa: 7,
                }),
            },
            vector_sram_type: MxDataTypeConfig::Plain {
                data_type: DataTypeConfig::Fp(FpTypeConfig {
                    sign: true,
                    exponent: 8,
                    mantissa: 7,
                }),
            },
            matrix_weight_type: MxDataTypeConfig::Plain {
                data_type: DataTypeConfig::Fp(FpTypeConfig {
                    sign: true,
                    exponent: 8,
                    mantissa: 7,
                }),
            },
            matrix_kv_type: MxDataTypeConfig::Plain {
                data_type: DataTypeConfig::Fp(FpTypeConfig {
                    sign: true,
                    exponent: 8,
                    mantissa: 7,
                }),
            },
            vector_activation_type: MxDataTypeConfig::Mx {
                elem: DataTypeConfig::Fp(FpTypeConfig {
                    sign: true,
                    exponent: 3,
                    mantissa: 4,
                }),
                scale: DataTypeConfig::Fp(FpTypeConfig {
                    sign: true,
                    exponent: 8,
                    mantissa: 0,
                }),
                block: 4,
            },
            vector_kv_type: MxDataTypeConfig::Mx {
                elem: DataTypeConfig::Fp(FpTypeConfig {
                    sign: true,
                    exponent: 7,
                    mantissa: 8,
                }),
                scale: DataTypeConfig::Fp(FpTypeConfig {
                    sign: true,
                    exponent: 8,
                    mantissa: 0,
                }),
                block: 4,
            },
        }
    }
}

// Conversion functions from config types to your actual types
impl From<FpTypeConfig> for FpType {
    fn from(config: FpTypeConfig) -> Self {
        FpType {
            sign: config.sign,
            exponent: config.exponent,
            mantissa: config.mantissa,
        }
    }
}

impl From<DataTypeConfig> for DataType {
    fn from(config: DataTypeConfig) -> Self {
        match config {
            DataTypeConfig::Fp(fp_config) => DataType::Fp(fp_config.into()),
        }
    }
}

impl From<MxDataTypeConfig> for MxDataType {
    fn from(config: MxDataTypeConfig) -> Self {
        match config {
            MxDataTypeConfig::Plain { data_type } => MxDataType::Plain(data_type.into()),
            MxDataTypeConfig::Mx { elem, scale, block } => MxDataType::Mx {
                elem: elem.into(),
                scale: scale.into(),
                block,
            },
        }
    }
}

// Global configuration loaded at runtime
pub static CONFIG: Lazy<AcceleratorConfig> = Lazy::new(|| {
    load_config().unwrap_or_else(|e| {
        eprintln!("Failed to load config: {}. Using defaults.", e);
        AcceleratorConfig::default()
    })
});

// Configuration loading functions
pub fn load_config() -> Result<AcceleratorConfig, Box<dyn std::error::Error>> {
    // Try multiple sources in order of preference
    
    // 1. Try environment variable for config file path
    if let Ok(config_path) = std::env::var("CONFIG_FILE_PATH") {
        if let Ok(config) = load_config_from_file(&config_path) {
            println!("Loaded config from: {}", config_path);
            return Ok(config);
        }
    }
    
    // 2. Try standard config file locations
    let config_paths = [
        "./plena_settings.toml"
    ];
    
    for path in &config_paths {
        if let Ok(config) = load_config_from_file(path) {
            println!("Loaded config from: {}", path);
            return Ok(config);
        }
    }
    
    Err("No configuration file found".into())
}

pub fn load_config_from_file(path: &str) -> Result<AcceleratorConfig, Box<dyn std::error::Error>> {
    let content = fs::read_to_string(path)?;
    let config: AcceleratorConfig = toml::from_str(&content)?;
    Ok(config)
}

// Convenience functions to access configuration values with the same names as your constants
pub fn period() -> Duration {
    Duration::from_nanos(CONFIG.period_nanos)
}

pub fn vector_basic_cycles() -> u32 {
    CONFIG.vector_basic_cycles
}

pub fn vector_reduct_cycles() -> u32 {
    CONFIG.vector_reduct_cycles
}

pub fn tile_size() -> u32 {
    CONFIG.tile_size
}

pub fn batch_size() -> u32 {
    CONFIG.batch_size
}

pub fn hbm_size() -> usize {
    CONFIG.hbm_size
}

pub fn matrix_sram_size() -> usize {
    CONFIG.matrix_sram_size
}

pub fn vector_sram_size() -> usize {
    CONFIG.vector_sram_size
}

pub fn matrix_sram_type() -> MxDataType {
    CONFIG.matrix_sram_type.clone().into()
}

pub fn vector_sram_type() -> MxDataType {
    CONFIG.vector_sram_type.clone().into()
}

pub fn matrix_weight_type() -> MxDataType {
    CONFIG.matrix_weight_type.clone().into()
}

pub fn matrix_kv_type() -> MxDataType {
    CONFIG.matrix_kv_type.clone().into()
}

pub fn vector_activation_type() -> MxDataType {
    CONFIG.vector_activation_type.clone().into()
}

pub fn vector_kv_type() -> MxDataType {
    CONFIG.vector_kv_type.clone().into()
}

// Utility function to generate example config file
pub fn generate_example_config() -> Result<(), Box<dyn std::error::Error>> {
    let config = AcceleratorConfig::default();
    let toml_content = toml::to_string_pretty(&config)?;
    fs::write("plena_settings.toml", toml_content)?;
    println!("Example plena_settings.toml generated successfully!");
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_default_config() {
        let config = AcceleratorConfig::default();
        assert_eq!(config.period_nanos, 1);
        assert_eq!(config.vector_basic_cycles, 1);
        assert_eq!(config.tile_size, 128);
    }
    
    #[test]
    fn test_config_conversion() {
        let config = AcceleratorConfig::default();
        let mx_type: MxDataType = config.matrix_sram_type.into();
        
        // Test that conversion works
        match mx_type {
            MxDataType::Plain(DataType::Fp(fp_type)) => {
                assert!(fp_type.sign);
                assert_eq!(fp_type.exponent, 8);
                assert_eq!(fp_type.mantissa, 7);
            }
            _ => panic!("Unexpected type conversion"),
        }
    }
    #[test]
    fn test_toml_loading() {
        let test_file = "./src/test_config.toml";
        
        let absolute_path = std::fs::canonicalize(test_file).unwrap_or_else(|_| {
            std::env::current_dir().unwrap().join(test_file)
        });
        println!("Test file path: {:?}", absolute_path);
        
        // Test the specific file directly instead of using load_config()
        let config = load_config_from_file(test_file).expect("Failed to load test config");
        
        assert_eq!(config.period_nanos, 15);
        assert_eq!(config.vector_basic_cycles, 7);
        assert_eq!(config.tile_size, 1024);
    }
}
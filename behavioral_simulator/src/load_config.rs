// load_config.rs
use serde::{Deserialize, Serialize};
use std::{fs, sync::LazyLock};
use std::time::Duration;

// Import the types from your main module
use quantize::{DataType, FpType, MxDataType};

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct ConfigValue {
    pub value: u32,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct ConfigValueUsize {
    pub value: usize,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct LatencyValue {
    pub dc_lib_en: u32,
    pub dc_lib_dis: u32,
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
pub struct MxDataTypeConfig {
    pub format: String,
    #[serde(flatten)]
    pub data: MxDataTypeData,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
#[serde(untagged)]
pub enum MxDataTypeData {
    Plain {
        #[serde(rename = "DATA_TYPE")]
        data_type: DataTypeConfig,
    },
    Mx {
        block: u32,
        #[serde(rename = "ELEM")]
        elem: DataTypeConfig,
        #[serde(rename = "SCALE")]
        scale: DataTypeConfig,
    },
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct AcceleratorConfig {
    #[serde(rename = "CONFIG")]
    pub config: ConfigSection,
    #[serde(rename = "PRECISION")]
    pub precision: PrecisionSection,
    #[serde(rename = "LATENCY")]
    pub latency: LatencySection,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct ConfigSection {
    #[serde(rename = "BLEN")]
    pub blen: ConfigValue,
    #[serde(rename = "MLEN")]
    pub mlen: ConfigValue,
    #[serde(rename = "VLEN")]
    pub vlen: ConfigValue,
    #[serde(rename = "HBM_SIZE")]
    pub hbm_size: ConfigValueUsize,
    #[serde(rename = "MATRIX_SRAM_SIZE")]
    pub matrix_sram_size: ConfigValueUsize,
    #[serde(rename = "VECTOR_SRAM_SIZE")]
    pub vector_sram_size: ConfigValueUsize,
    #[serde(rename = "HBM_M_Prefetch_Amount")]
    pub hbm_m_prefetch_amount: ConfigValue,
    #[serde(rename = "HBM_V_Prefetch_Amount")]
    pub hbm_v_prefetch_amount: ConfigValue,
    #[serde(rename = "HBM_V_Writeback_Amount")]
    pub hbm_v_writeback_amount: ConfigValue,
    #[serde(rename = "DC_EN")]
    pub dc_en: ConfigValue,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct PrecisionSection {
    #[serde(rename = "MATRIX_SRAM_TYPE")]
    pub matrix_sram_type: MxDataTypeConfig,
    #[serde(rename = "VECTOR_SRAM_TYPE")]
    pub vector_sram_type: MxDataTypeConfig,
    #[serde(rename = "HBM_M_WEIGHT_TYPE")]
    pub hbm_m_weight_type: MxDataTypeConfig,
    #[serde(rename = "HBM_M_KV_TYPE")]
    pub hbm_m_kv_type: MxDataTypeConfig,
    #[serde(rename = "HBM_V_ACT_TYPE")]
    pub hbm_v_act_type: MxDataTypeConfig,
    #[serde(rename = "HBM_V_KV_TYPE")]
    pub hbm_v_kv_type: MxDataTypeConfig,
    #[serde(rename = "SCALAR_FP")]
    pub scalar_fp: DataTypeConfig,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct LatencySection {
    #[serde(rename = "SYSTOLIC_PROCESSING_OVERHEAD")]
    pub systolic_processing_overhead: LatencyValue,
    #[serde(rename = "VECTOR_ADD_CYCLES")]
    pub vector_add_cycles: LatencyValue,
    #[serde(rename = "VECTOR_MUL_CYCLES")]
    pub vector_mul_cycles: LatencyValue,
    #[serde(rename = "VECTOR_EXP_CYCLES")]
    pub vector_exp_cycles: LatencyValue,
    #[serde(rename = "VECTOR_PREFIX_SCAN_CYCLES")]
    pub vector_prefix_scan_cycles: LatencyValue,
    #[serde(rename = "VECTOR_SHIFT_CYCLES")]
    pub vector_shift_cycles: LatencyValue,
    #[serde(rename = "VECTOR_RECI_CYCLES")]
    pub vector_reci_cycles: LatencyValue,
    #[serde(rename = "VECTOR_MAX_CYCLES")]
    pub vector_max_cycles: LatencyValue,
    #[serde(rename = "VECTOR_SUM_CYCLES")]
    pub vector_sum_cycles: LatencyValue,
    #[serde(rename = "SCALAR_FP_LONGEST_OPERATE_CYCLES")]
    pub scalar_fp_longest_operate_cycles: LatencyValue,
    #[serde(rename = "SCALAR_FP_BASIC_CYCLES")]
    pub scalar_fp_basic_cycles: LatencyValue,
    #[serde(rename = "SCALAR_FP_EXP_CYCLES")]
    pub scalar_fp_exp_cycles: LatencyValue,
    #[serde(rename = "SCALAR_FP_SQRT_CYCLES")]
    pub scalar_fp_sqrt_cycles: LatencyValue,
    #[serde(rename = "SCALAR_FP_RECI_CYCLES")]
    pub scalar_fp_reci_cycles: LatencyValue,
    #[serde(rename = "SCALAR_INT_BASIC_CYCLES")]
    pub scalar_int_basic_cycles: LatencyValue,
}

impl Default for AcceleratorConfig {
    fn default() -> Self {
        AcceleratorConfig {
            config: ConfigSection {
                blen: ConfigValue { value: 32 },
                mlen: ConfigValue { value: 32 },
                vlen: ConfigValue { value: 32 },
                hbm_size: ConfigValueUsize { value: 1073741824 },
                matrix_sram_size: ConfigValueUsize { value: 1024 },
                vector_sram_size: ConfigValueUsize { value: 1024 },
                hbm_m_prefetch_amount: ConfigValue { value: 16 },
                hbm_v_prefetch_amount: ConfigValue { value: 16 },
                hbm_v_writeback_amount: ConfigValue { value: 16 },
                dc_en: ConfigValue { value: 1 },
            },
            precision: PrecisionSection {
                matrix_sram_type: MxDataTypeConfig {
                    format: "Plain".to_string(),
                    data: MxDataTypeData::Plain {
                        data_type: DataTypeConfig::Fp(FpTypeConfig {
                            sign: true,
                            exponent: 8,
                            mantissa: 7,
                        }),
                    },
                },
                vector_sram_type: MxDataTypeConfig {
                    format: "Plain".to_string(),
                    data: MxDataTypeData::Plain {
                        data_type: DataTypeConfig::Fp(FpTypeConfig {
                            sign: true,
                            exponent: 8,
                            mantissa: 7,
                        }),
                    },
                },
                hbm_m_weight_type: MxDataTypeConfig {
                    format: "Mx".to_string(),
                    data: MxDataTypeData::Mx {
                        block: 8,
                        elem: DataTypeConfig::Fp(FpTypeConfig {
                            sign: true,
                            exponent: 4,
                            mantissa: 3,
                        }),
                        scale: DataTypeConfig::Fp(FpTypeConfig {
                            sign: true,
                            exponent: 8,
                            mantissa: 0,
                        }),
                    },
                },
                hbm_m_kv_type: MxDataTypeConfig {
                    format: "Mx".to_string(),
                    data: MxDataTypeData::Mx {
                        block: 8,
                        elem: DataTypeConfig::Fp(FpTypeConfig {
                            sign: true,
                            exponent: 4,
                            mantissa: 3,
                        }),
                        scale: DataTypeConfig::Fp(FpTypeConfig {
                            sign: true,
                            exponent: 8,
                            mantissa: 0,
                        }),
                    },
                },
                hbm_v_act_type: MxDataTypeConfig {
                    format: "Mx".to_string(),
                    data: MxDataTypeData::Mx {
                        block: 8,
                        elem: DataTypeConfig::Fp(FpTypeConfig {
                            sign: true,
                            exponent: 4,
                            mantissa: 3,
                        }),
                        scale: DataTypeConfig::Fp(FpTypeConfig {
                            sign: true,
                            exponent: 8,
                            mantissa: 0,
                        }),
                    },
                },
                hbm_v_kv_type: MxDataTypeConfig {
                    format: "Mx".to_string(),
                    data: MxDataTypeData::Mx {
                        block: 8,
                        elem: DataTypeConfig::Fp(FpTypeConfig {
                            sign: true,
                            exponent: 4,
                            mantissa: 3,
                        }),
                        scale: DataTypeConfig::Fp(FpTypeConfig {
                            sign: true,
                            exponent: 8,
                            mantissa: 0,
                        }),
                    },
                },
                scalar_fp: DataTypeConfig::Fp(FpTypeConfig {
                    sign: true,
                    exponent: 8,
                    mantissa: 7,
                }),
            },
            latency: LatencySection {
                systolic_processing_overhead: LatencyValue { dc_lib_en: 0, dc_lib_dis: 0 },
                vector_add_cycles: LatencyValue { dc_lib_en: 2, dc_lib_dis: 7 },
                vector_mul_cycles: LatencyValue { dc_lib_en: 1, dc_lib_dis: 5 },
                vector_exp_cycles: LatencyValue { dc_lib_en: 1, dc_lib_dis: 6 },
                vector_prefix_scan_cycles: LatencyValue { dc_lib_en: 9, dc_lib_dis: 9 },
                vector_shift_cycles: LatencyValue { dc_lib_en: 1, dc_lib_dis: 1 },
                vector_reci_cycles: LatencyValue { dc_lib_en: 2, dc_lib_dis: 7 },
                vector_max_cycles: LatencyValue { dc_lib_en: 4, dc_lib_dis: 4 },
                vector_sum_cycles: LatencyValue { dc_lib_en: 8, dc_lib_dis: 20 },
                scalar_fp_longest_operate_cycles: LatencyValue { dc_lib_en: 4, dc_lib_dis: 4 },
                scalar_fp_basic_cycles: LatencyValue { dc_lib_en: 1, dc_lib_dis: 1 },
                scalar_fp_exp_cycles: LatencyValue { dc_lib_en: 1, dc_lib_dis: 2 },
                scalar_fp_sqrt_cycles: LatencyValue { dc_lib_en: 1, dc_lib_dis: 2 },
                scalar_fp_reci_cycles: LatencyValue { dc_lib_en: 1, dc_lib_dis: 2 },
                scalar_int_basic_cycles: LatencyValue { dc_lib_en: 1, dc_lib_dis: 1 },
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
        match config.data {
            MxDataTypeData::Plain { data_type } => MxDataType::Plain(data_type.into()),
            MxDataTypeData::Mx { elem, scale, block } => MxDataType::Mx {
                elem: elem.into(),
                scale: scale.into(),
                block,
            },
        }
    }
}

// Global configuration loaded at runtime
pub static CONFIG: LazyLock<AcceleratorConfig> = LazyLock::new(|| {
    load_config().unwrap_or_else(|e| {
        eprintln!("Failed to load config: {}. Using defaults.", e);
        AcceleratorConfig::default()
    })
});

// Configuration loading functions
pub fn load_config() -> Result<AcceleratorConfig, Box<dyn std::error::Error>> {

    let config_paths = [
        "../src/definitions/plena_settings.toml"
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

// Helper function to check if DC library is enabled from config
pub fn is_dc_lib_enabled() -> bool {
    CONFIG.config.dc_en.value != 0
}

// Helper function to select DC library enabled or disabled values
pub fn get_dc_lib_value(latency_val: &LatencyValue) -> u32 {
    if is_dc_lib_enabled() {
        latency_val.dc_lib_en
    } else {
        latency_val.dc_lib_dis
    }
}

// Configuration accessor functions (automatically uses DC_EN setting from config)

pub fn hbm_size() -> usize {
    CONFIG.config.hbm_size.value
}

pub fn matrix_sram_size() -> usize {
    CONFIG.config.matrix_sram_size.value
}

pub fn vector_sram_size() -> usize {
    CONFIG.config.vector_sram_size.value
}

pub fn matrix_sram_type() -> MxDataType {
    CONFIG.precision.matrix_sram_type.clone().into()
}

pub fn vector_sram_type() -> MxDataType {
    CONFIG.precision.vector_sram_type.clone().into()
}

pub fn matrix_weight_type() -> MxDataType {
    CONFIG.precision.hbm_m_weight_type.clone().into()
}

pub fn matrix_kv_type() -> MxDataType {
    CONFIG.precision.hbm_m_kv_type.clone().into()
}

pub fn vector_activation_type() -> MxDataType {
    CONFIG.precision.hbm_v_act_type.clone().into()
}

pub fn vector_kv_type() -> MxDataType {
    CONFIG.precision.hbm_v_kv_type.clone().into()
}

// Additional accessor functions for new parameters
pub fn mlen() -> u32 {
    CONFIG.config.mlen.value
}

pub fn vlen() -> u32 {
    CONFIG.config.vlen.value
}

pub fn blen() -> u32 {
    CONFIG.config.blen.value
}

pub fn dc_en() -> u32 {
    CONFIG.config.dc_en.value
}

// Latency accessor functions (automatically uses DC_EN setting from config)
pub fn systolic_processing_overhead() -> u32 {
    get_dc_lib_value(&CONFIG.latency.systolic_processing_overhead)
}

// pub fn vector_ps_cycles() -> u32 {
//     get_dc_lib_value(&CONFIG.latency.vector_ps_cycles)
// }

// pub fn vector_shift_cycles() -> u32 {
//     get_dc_lib_value(&CONFIG.latency.vector_shift_cycles)
// }

pub fn vector_max_cycles() -> u32 {
    get_dc_lib_value(&CONFIG.latency.vector_max_cycles)
}

pub fn vector_sum_cycles() -> u32 {
    get_dc_lib_value(&CONFIG.latency.vector_sum_cycles)
}

pub fn vector_add_cycles() -> u32 {
    get_dc_lib_value(&CONFIG.latency.vector_add_cycles)
}

pub fn vector_mul_cycles() -> u32 {
    get_dc_lib_value(&CONFIG.latency.vector_mul_cycles)
}

pub fn vector_exp_cycles() -> u32 {
    get_dc_lib_value(&CONFIG.latency.vector_exp_cycles)
}

pub fn vector_reci_cycles() -> u32 {
    get_dc_lib_value(&CONFIG.latency.vector_reci_cycles)
}

pub fn scalar_fp_longest_operate_cycles() -> u32 {
    get_dc_lib_value(&CONFIG.latency.scalar_fp_longest_operate_cycles)
}

pub fn scalar_fp_basic_cycles() -> u32 {
    get_dc_lib_value(&CONFIG.latency.scalar_fp_basic_cycles)
}

pub fn scalar_fp_exp_cycles() -> u32 {
    get_dc_lib_value(&CONFIG.latency.scalar_fp_exp_cycles)
}

pub fn scalar_fp_sqrt_cycles() -> u32 {
    get_dc_lib_value(&CONFIG.latency.scalar_fp_sqrt_cycles)
}

pub fn scalar_fp_reci_cycles() -> u32 {
    get_dc_lib_value(&CONFIG.latency.scalar_fp_reci_cycles)
}

pub fn scalar_int_basic_cycles() -> u32 {
    get_dc_lib_value(&CONFIG.latency.scalar_int_basic_cycles)
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
        assert_eq!(config.config.blen.value, 32);
        assert_eq!(config.config.mlen.value, 32);
        assert_eq!(config.config.vlen.value, 32);
        assert_eq!(config.config.dc_en.value, 1);
    }
    
    #[test]
    fn test_dc_lib_selection() {
        let config = AcceleratorConfig::default();
        // Test with DC_EN = 1 (enabled)
        assert_eq!(get_dc_lib_value(&config.latency.vector_add_cycles), 2);
        
        // Test is_dc_lib_enabled function
        assert!(is_dc_lib_enabled());
    }
    
    #[test]
    fn test_accessor_functions() {
        assert_eq!(mlen(), 32);
        assert_eq!(vlen(), 32);
        assert_eq!(blen(), 32);
        assert_eq!(dc_en(), 1);
        assert_eq!(vector_add_cycles(), 2); // Should use dc_lib_en since DC_EN = 1
    }
}
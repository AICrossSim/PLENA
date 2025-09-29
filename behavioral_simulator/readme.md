# Behavioural Level Simulator
This simulator is mainly built by **Dr. Gary Guo**

## Feature


## HBM

The simulator integrates **Ramulator 2** for HBM modelling.

**MX Data Type Address Pattern**
- **Element**:  
  `element_addr[Onchip] + hbm_offset`
- **Scale**:  
  `Scale_offset + (element_addr[Onchip] >> element_2_scale_ratio)`
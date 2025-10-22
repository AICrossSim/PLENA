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



## Matrix Machine

**MM_WO**
Write a (BLEN, BLEN) acc matrix (m_accum) to the Vector SRAM. This involves loading a (BLEN, VLEN) matrix from the HBM and use mask to write to the Vector SRAM.


## Notes
- Currently the MLEN and VLEN are assumed to be the same for this simulator.




## Support Experiments
- Linear Projection Testing (linear)
- RMSNorm Testing (rms)

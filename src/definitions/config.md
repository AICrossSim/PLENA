# Accelerator's Design Space and Tuning Method
## Tuning Method

You can customise build parameters using the `make set` command:

```bash
make set CONFIG="VLEN=4 MLEN=123" MODE=ASIC
```

### Arguments

- **MODE**  
  Specifies the target environment. Available options:
  - `ASIC` : Only includes the core configurations.
  - `SIMULATION` : Includes additional configurations for simulation environments, such as fake HBM memory and other simulation-specific settings.

- **CONFIG**  
  A string of one or more key-value pairs to override default parameters. Use this to tune individual or multiple settings at once. 

### Example Usage

To set `VLEN` to 4 and `MLEN` to 123 for the ASIC mode:

```bash
make set CONFIG="VLEN=4 MLEN=123" MODE=ASIC
```

To set `HIGH_MXFP_MANT_WIDTH` to 8 for the ASIC mode:
```bash
 make set PRECISION="HIGH_MXFP_MANT_WIDTH=8"
```

This approach enables flexible, fine-grained control over build configurations for different deployment targets.

## Design Space

### Configuration Parameters


### Precision Parameters
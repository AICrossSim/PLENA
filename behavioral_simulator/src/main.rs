mod load_config;
mod op; // Add this line to include the config module

use std::future::Future;
use std::mem::ManuallyDrop;
use std::path::PathBuf;
use std::pin::Pin;
use std::sync::Arc;
use std::sync::LazyLock;

use clap::Parser;
use futures::StreamExt;
use futures::stream::FuturesUnordered;
use half::f16;
use memory::MemoryModel;
use quantize::{MxDataType, QuantTensor};
use runtime::{Duration, Executor, Instant};
use tch::{IndexOp, Tensor};

use tokio::sync::Mutex;
use tokio::sync::oneshot::{self, Receiver};

// Import the configuration functions
use load_config::*;

// Replace the const declarations with function calls to the config
// These functions will be called at runtime to get the configured values

const PERIOD: Duration = Duration::from_nanos(1);
static SYSTOLIC_PROCESSING_OVERHEAD: LazyLock<u32> =
    LazyLock::new(|| systolic_processing_overhead());
static VECTOR_ADD_CYCLES: LazyLock<u32> = LazyLock::new(|| vector_add_cycles());
static VECTOR_MUL_CYCLES: LazyLock<u32> = LazyLock::new(|| vector_mul_cycles());
static VECTOR_EXP_CYCLES: LazyLock<u32> = LazyLock::new(|| vector_exp_cycles());
static VECTOR_RECI_CYCLES: LazyLock<u32> = LazyLock::new(|| vector_reci_cycles());
static VECTOR_MAX_CYCLES: LazyLock<u32> = LazyLock::new(|| vector_max_cycles());
static VECTOR_SUM_CYCLES: LazyLock<u32> = LazyLock::new(|| vector_sum_cycles());
static SCALAR_FP_BASIC_CYCLES: LazyLock<u32> = LazyLock::new(|| scalar_fp_basic_cycles());
static SCALAR_FP_EXP_CYCLES: LazyLock<u32> = LazyLock::new(|| scalar_fp_exp_cycles());
static SCALAR_FP_SQRT_CYCLES: LazyLock<u32> = LazyLock::new(|| scalar_fp_sqrt_cycles());
static SCALAR_FP_RECI_CYCLES: LazyLock<u32> = LazyLock::new(|| scalar_fp_reci_cycles());
static SCALAR_INT_BASIC_CYCLES: LazyLock<u32> = LazyLock::new(|| scalar_int_basic_cycles());

static MLEN: LazyLock<u32> = LazyLock::new(|| mlen());
static VLEN: LazyLock<u32> = LazyLock::new(|| vlen());
static BLEN: LazyLock<u32> = LazyLock::new(|| blen());
static HBM_SIZE: LazyLock<usize> = LazyLock::new(|| hbm_size());
static MATRIX_SRAM_SIZE: LazyLock<usize> = LazyLock::new(|| matrix_sram_size());
static VECTOR_SRAM_SIZE: LazyLock<usize> = LazyLock::new(|| vector_sram_size());
static MATRIX_SRAM_TYPE: LazyLock<MxDataType> = LazyLock::new(|| matrix_sram_type());
static VECTOR_SRAM_TYPE: LazyLock<MxDataType> = LazyLock::new(|| vector_sram_type());
static MATRIX_WEIGHT_TYPE: LazyLock<MxDataType> = LazyLock::new(|| matrix_weight_type());
static MATRIX_KV_TYPE: LazyLock<MxDataType> = LazyLock::new(|| matrix_kv_type());
static VECTOR_ACTIVATION_TYPE: LazyLock<MxDataType> = LazyLock::new(|| vector_activation_type());
static VECTOR_KV_TYPE: LazyLock<MxDataType> = LazyLock::new(|| vector_kv_type());

/// Address handling utilities.
///
/// Many operations on matrix and vector SRAM operate on entire tiles so it needs to be multiple, but some aren't, so we use
/// element indexing. This utility provides some helper functions for address handling.
trait AddrUtils: Sized {
    fn assert_multiple_of(self, mul: Self) -> Self;

    fn multiple_and_offset(self, mul: Self) -> (Self, Self);
}

impl AddrUtils for u32 {
    fn assert_multiple_of(self, mul: u32) -> u32 {
        assert!(self.is_multiple_of(mul));
        self / mul
    }

    fn multiple_and_offset(self, mul: u32) -> (u32, u32) {
        let d = self / mul;
        let r = self % mul;
        (d * mul, r)
    }
}

macro_rules! cycle {
    ($cycle: expr) => {
        runtime::Executor::current()
            .resolve_at(PERIOD * ($cycle as u32))
            .await;
    };
}

/// Behaviour modelling of matrix SRAM.
///
/// The timing aspect is to be considered by the matrix machine itself.
struct MatrixSram {
    tile_size: u32,
    tiles: Vec<Mutex<Result<QuantTensor, Receiver<QuantTensor>>>>,
    ty: MxDataType,
}

impl MatrixSram {
    /// Creata a matrix SRAM with given tile size and depth.
    fn new(tile_size: u32, depth: usize, ty: MxDataType) -> Self {
        let tiles = (0..depth)
            .map(|_| Mutex::new(Ok(QuantTensor::zeros((tile_size * tile_size) as usize, ty))))
            .collect();
        Self {
            tile_size,
            tiles,
            ty,
        }
    }

    fn size_in_bytes(&self) -> usize {
        (self.tile_size * self.tile_size) as usize * self.tiles.len()
    }

    async fn read(&self, addr: u32) -> QuantTensor {
        let addr_in_tiles = addr.assert_multiple_of(self.tile_size * self.tile_size);

        let mut guard = self.tiles[addr_in_tiles as usize].lock().await;
        if let Err(ref mut fut) = *guard {
            *guard = Ok(fut.await.unwrap());
        }

        guard.as_ref().map_err(|_| ()).unwrap().clone()
    }

    async fn write(&self, addr: u32, tensor: QuantTensor) {
        let addr_in_tiles = addr.assert_multiple_of(self.tile_size * self.tile_size);

        assert!(tensor.data_type() == self.ty);
        *self.tiles[addr_in_tiles as usize].lock().await = Ok(tensor);
    }

    async fn write_delayed(&self, addr: u32, tensor: Receiver<QuantTensor>) {
        let addr_in_tiles = addr.assert_multiple_of(self.tile_size * self.tile_size);

        *self.tiles[addr_in_tiles as usize].lock().await = Err(tensor);
    }
}

/// Behaviour modelling of vector SRAM.
///
/// The timing aspect is to be considered by the matrix and vector machines themselves.
struct VectorSram {
    tile_size: u32,
    tiles: Vec<Mutex<Result<QuantTensor, Receiver<QuantTensor>>>>,
    ty: MxDataType,
}

impl VectorSram {
    /// Creata a matrix SRAM with given tile size and depth.
    fn new(tile_size: u32, depth: usize, ty: MxDataType) -> Self {
        let tiles = (0..depth)
            .map(|_| Mutex::new(Ok(QuantTensor::zeros(tile_size as usize, ty))))
            .collect();
        Self {
            tile_size,
            tiles,
            ty,
        }
    }

    fn size_in_bytes(&self) -> usize {
        self.tile_size as usize * self.tiles.len()
    }

    async fn read(&self, addr: u32) -> QuantTensor {
        let addr_in_tiles = addr.assert_multiple_of(self.tile_size);

        let mut guard = self.tiles[addr_in_tiles as usize].lock().await;
        if let Err(ref mut fut) = *guard {
            *guard = Ok(fut.await.unwrap());
        }

        guard.as_ref().map_err(|_| ()).unwrap().clone()
    }

    async fn write(&self, addr: u32, tensor: QuantTensor) {
        let addr_in_tiles = addr.assert_multiple_of(self.tile_size);

        assert_eq!(tensor.data_type(), self.ty);
        *self.tiles[addr_in_tiles as usize].lock().await = Ok(tensor);
    }

    async fn write_delayed(&self, addr: u32, tensor: Receiver<QuantTensor>) {
        let addr_in_tiles = addr.assert_multiple_of(self.tile_size);

        *self.tiles[addr_in_tiles as usize].lock().await = Err(tensor);
    }
}

struct MatrixMachine {
    mram: Arc<MatrixSram>,
    vram: Arc<VectorSram>,
    m_accum: Tensor,
    v_accum: Tensor,
    tile_size: u32,
    blen: u32,
}

impl MatrixMachine {
    async fn mm(&mut self, v_addr: u32, m_addr: u32) {
        let (mat_base, mat_offset) = m_addr.multiple_and_offset(self.tile_size * self.tile_size);
        let mat_offset = mat_offset.assert_multiple_of(self.tile_size);
        assert!(mat_offset.is_multiple_of(self.blen));

        let full_mat = self.mram.read(mat_base).await;
        let mat = full_mat
            .as_tensor()
            .i((mat_offset as i64..(mat_offset + self.blen) as i64, ..));

        let mut tensors = Vec::with_capacity(self.blen as usize);
        cycle!(*SYSTOLIC_PROCESSING_OVERHEAD + self.tile_size);
        for i in 0..self.blen {
            tensors.push(
                self.vram
                    .read(v_addr + i * self.tile_size)
                    .await
                    .as_tensor()
                    .shallow_clone(),
            );
        }
        let vec = tch::Tensor::stack(&tensors, -1);

        self.m_accum += mat.matmul(&vec);
    }

    async fn tmm(&mut self, v_addr: u32, m_addr: u32) {
        let (mat_base, mat_offset) = m_addr.multiple_and_offset(self.tile_size * self.tile_size);
        let mat_offset = mat_offset.assert_multiple_of(self.tile_size);
        assert!(mat_offset.is_multiple_of(self.blen));
        let full_mat = self.mram.read(mat_base).await;
        let mat = full_mat
            .as_tensor()
            .transpose(-1, -2)
            .i((mat_offset as i64..(mat_offset + self.blen) as i64, ..));
        let mut tensors = Vec::with_capacity(self.blen as usize);
        cycle!(*SYSTOLIC_PROCESSING_OVERHEAD + self.tile_size);
        for i in 0..self.blen {
            tensors.push(
                self.vram
                    .read(v_addr + i * self.tile_size)
                    .await
                    .as_tensor()
                    .shallow_clone(),
            );
        }
        let vec = tch::Tensor::stack(&tensors, -1);

        self.m_accum += mat.matmul(&vec);
    }

    async fn mm_wo(&mut self, v_addr: u32) {
        let (vec_base, vec_offset) = v_addr.multiple_and_offset(self.tile_size);
        assert!(vec_offset.is_multiple_of(self.blen));
        cycle!(1);
        for i in 0..self.blen {
            let tensor = self.m_accum.i((i as i64, ..)).unsqueeze(0);
            let old = self.vram.read(vec_base + i * self.tile_size).await;
            let new = old.as_tensor().copy();
            new.i(vec_offset as i64..(vec_offset + self.blen) as i64)
                .copy_(&tensor);
            self.vram
                .write(
                    vec_base + i * self.tile_size,
                    QuantTensor::quantize(new, old.data_type()),
                )
                .await;
        }

        self.m_accum = Tensor::zeros(
            [self.blen as i64, self.blen as i64],
            (tch::Kind::Float, tch::Device::Cpu),
        );
    }

    async fn mv(&mut self, v_addr: u32, m_addr: u32) {
        let mat = self.mram.read(m_addr).await;
        let vec = self.vram.read(v_addr).await;
        cycle!(self.tile_size);
        self.v_accum += mat.as_tensor().matmul(vec.as_tensor());
    }

    async fn tmv(&mut self, v_addr: u32, m_addr: u32) {
        let mat = self.mram.read(m_addr).await;
        let vec = self.vram.read(v_addr).await;
        cycle!(self.tile_size);
        self.v_accum += mat.as_tensor().transpose(-1, -2).matmul(vec.as_tensor());
    }

    async fn mv_wo(&mut self, v_addr: u32) {
        let quant = QuantTensor::quantize(self.v_accum.shallow_clone(), self.vram.ty);
        self.vram.write(v_addr, quant).await;
        cycle!(1);
        self.v_accum = Tensor::zeros(
            [self.tile_size as i64],
            (tch::Kind::Float, tch::Device::Cpu),
        );
    }
}

struct VectorMachine {
    vram: Arc<VectorSram>,
}

impl VectorMachine {
    async fn add_scalar(&mut self, vd: u32, vs1: u32, f: f32) {
        let a = self.vram.read(vs1).await;
        let c = QuantTensor::quantize(a.as_tensor() + (f as f64), a.data_type());
        cycle!(*VECTOR_ADD_CYCLES);
        self.vram.write(vd, c).await;
    }

    async fn mul_scalar(&mut self, vd: u32, vs1: u32, f: f32) {
        let a = self.vram.read(vs1).await;
        let c = QuantTensor::quantize(a.as_tensor() * (f as f64), a.data_type());
        cycle!(*VECTOR_MUL_CYCLES);
        self.vram.write(vd, c).await;
    }

    async fn add(&mut self, vd: u32, vs1: u32, vs2: u32) {
        let (a, b) = tokio::join!(self.vram.read(vs1), self.vram.read(vs2));
        let c = QuantTensor::quantize(a.as_tensor() + b.as_tensor(), a.data_type());
        cycle!(*VECTOR_ADD_CYCLES);
        self.vram.write(vd, c).await;
    }

    async fn sub(&mut self, vd: u32, vs1: u32, vs2: u32) {
        let (a, b) = tokio::join!(self.vram.read(vs1), self.vram.read(vs2));
        let c = QuantTensor::quantize(a.as_tensor() - b.as_tensor(), a.data_type());
        cycle!(*VECTOR_ADD_CYCLES);
        self.vram.write(vd, c).await;
    }

    async fn mul(&mut self, vd: u32, vs1: u32, vs2: u32) {
        let (a, b) = tokio::join!(self.vram.read(vs1), self.vram.read(vs2));
        let c = QuantTensor::quantize(a.as_tensor() * b.as_tensor(), a.data_type());
        cycle!(*VECTOR_MUL_CYCLES);
        self.vram.write(vd, c).await;
    }

    async fn exp(&mut self, vd: u32, vs1: u32) {
        let a = self.vram.read(vs1).await;
        let c = QuantTensor::quantize(a.as_tensor().exp(), a.data_type());
        cycle!(*VECTOR_EXP_CYCLES);
        self.vram.write(vd, c).await;
    }

    async fn reciprocal(&mut self, vd: u32, vs1: u32) {
        let a = self.vram.read(vs1).await;
        let c = QuantTensor::quantize(a.as_tensor().reciprocal(), a.data_type());
        cycle!(*VECTOR_RECI_CYCLES);
        self.vram.write(vd, c).await;
    }

    // async fn broadcast(&mut self, vd: u32, f: f32) {
    //     let c = QuantTensor::quantize(
    //         Tensor::full(
    //             [self.vram.tile_size as i64],
    //             f as f64,
    //             (tch::Kind::Float, tch::Device::Cpu),
    //         ),
    //         self.vram.ty,
    //     );
    //     cycle!(*VECTOR_BASIC_CYCLES);
    //     self.vram.write(vd, c).await;
    // }

    async fn reduce_sum(&mut self, vs1: u32, f: f32) -> f32 {
        let a = self.vram.read(vs1).await;
        cycle!(*VECTOR_SUM_CYCLES);
        let val: f32 = a.as_tensor().sum(tch::Kind::Float).i(0).try_into().unwrap();
        f + val
    }

    async fn reduce_max(&mut self, vs1: u32, f: f32) -> f32 {
        let a = self.vram.read(vs1).await;
        cycle!(*VECTOR_MAX_CYCLES);
        let val: f32 = a.as_tensor().max().i(0).try_into().unwrap();
        f32::max(val, f)
    }
}

struct Accelerator {
    m_machine: MatrixMachine,
    v_machine: VectorMachine,
    hbm: Arc<dyn MemoryModel>,
    tile_size: u32,
    reg_file: AcceeleratorRegFile,
    int_sram: Vec<u32>,
    fp_sram: Vec<f16>,
}

struct AcceeleratorRegFile {
    gp_reg: [u32; 16],
    fp_reg: [f16; 8],
    hbm_addr_reg: [u64; 8],
    scale: u32,
}

impl Accelerator {
    /// Transfer a vector from HBM to host.
    ///
    /// `len` is size in bytes.
    fn transfer_from_hbm(
        &mut self,
        index: u64,
        // For MXFP/MXINT, load from this index.
        scale_index: u64,
        len: usize,
        hbm_type: MxDataType,
        sram_type: MxDataType,
    ) -> Receiver<QuantTensor> {
        let (sender, receiver) = oneshot::channel();

        // Launch the data transfer in parallel.
        let hbm_clone = self.hbm.clone();
        Executor::current().spawn(async move {
            let element_ty = hbm_type.element_type();
            let element_bits = element_ty.size_in_bits();
            assert!(element_bits.is_power_of_two());

            let len_in_bits = element_bits as u32 * len as u32;
            assert!(len_in_bits.is_multiple_of(8 * 64));
            let len_in_bytes = len_in_bits / 8;

            let (scale_len_in_bytes, block) = if let MxDataType::Mx {
                elem: _,
                scale,
                block,
            } = hbm_type
            {
                let scale_bits = scale.size_in_bits();
                assert!(scale_bits.is_power_of_two());
                let scale_len_in_bits = scale_bits as u32 * len as u32;
                assert!(scale_len_in_bits.is_multiple_of(8 * 64));
                (scale_len_in_bits / 8, block as usize)
            } else {
                (0, usize::MAX)
            };

            let mut bytes = vec![0; len_in_bytes as usize];
            let mut scale_bytes = vec![0; scale_len_in_bytes as usize];
            let hbm_clone = &hbm_clone;
            let futures = FuturesUnordered::<Pin<Box<dyn Future<Output = _> + Send>>>::new();

            for (i, x) in bytes.chunks_mut(64).enumerate() {
                futures.push(Box::pin(async move {
                    let chunk = hbm_clone.read(index + i as u64 * 64).await;
                    x.copy_from_slice(&chunk[..x.len()]);
                }));
            }

            for (i, x) in scale_bytes.chunks_mut(64).enumerate() {
                futures.push(Box::pin(async move {
                    let chunk = hbm_clone.read(scale_index + i as u64 * 64).await;
                    x.copy_from_slice(&chunk[..x.len()]);
                }));
            }

            futures.collect::<()>().await;
            // eprintln!("HBM Loaded Value: {:08X?}", &bytes);

            let mut vec = vec![0f32; len];
            element_ty.convert_bytes_to_f32_vec(&bytes, &mut vec);
            // println!("{:?}", vec);

            let mut scale_vec = vec![0f32; len / block as usize];
            if let MxDataType::Mx {
                elem: _,
                scale,
                block,
            } = hbm_type
            {
                scale.convert_bytes_to_f32_vec(&scale_bytes, &mut scale_vec);

            for (i, (elem_block, scale_val)) in vec
                .chunks_mut(block as usize)
                .zip(scale_vec.iter().copied())
                .enumerate()
                {
                    for elem in elem_block.iter_mut() {
                        *elem *= scale_val;
                    }
                }
            }

            let tensor = tch::Tensor::from_slice(&vec);
            let _ = sender.send(QuantTensor::quantize(tensor, sram_type));
        });

        receiver
    }

    async fn do_ops(&mut self, ops: &[op::Opcode]) {
        for op in ops {
            match *op {
                op::Opcode::Invalid => todo!(),

                op::Opcode::M_MM { rs1, rs2 } => {
                    self.m_machine
                        .mm(
                            self.reg_file.gp_reg[rs1 as usize],
                            self.reg_file.gp_reg[rs2 as usize],
                        )
                        .await;
                }
                op::Opcode::M_MM_WO { rd, imm } => {
                    self.m_machine
                        .mm_wo(self.reg_file.gp_reg[rd as usize] + imm as u32)
                        .await;
                }
                op::Opcode::M_TMM { rs1, rs2 } => {
                    self.m_machine
                        .tmm(
                            self.reg_file.gp_reg[rs1 as usize],
                            self.reg_file.gp_reg[rs2 as usize],
                        )
                        .await;
                }
                op::Opcode::M_MV { rs1, rs2 } => {
                    self.m_machine
                        .mv(
                            self.reg_file.gp_reg[rs1 as usize],
                            self.reg_file.gp_reg[rs2 as usize],
                        )
                        .await;
                }
                op::Opcode::M_MV_WO { rd, imm } => {
                    self.m_machine
                        .mv_wo(self.reg_file.gp_reg[rd as usize] + imm as u32)
                        .await;
                }
                op::Opcode::M_TMV { rs1, rs2 } => {
                    self.m_machine
                        .tmv(
                            self.reg_file.gp_reg[rs1 as usize],
                            self.reg_file.gp_reg[rs2 as usize],
                        )
                        .await;
                }

                op::Opcode::V_ADD_VV { rd, rs1, rs2 } => {
                    self.v_machine
                        .add(
                            self.reg_file.gp_reg[rd as usize],
                            self.reg_file.gp_reg[rs1 as usize],
                            self.reg_file.gp_reg[rs2 as usize],
                        )
                        .await;
                }
                op::Opcode::V_ADD_VF { rd, rs1, rs2 } => {
                    self.v_machine
                        .add_scalar(
                            self.reg_file.gp_reg[rd as usize],
                            self.reg_file.gp_reg[rs1 as usize],
                            self.reg_file.fp_reg[rs2 as usize].into(),
                        )
                        .await;
                }
                op::Opcode::V_SUB_VV { rd, rs1, rs2 } => {
                    self.v_machine
                        .sub(
                            self.reg_file.gp_reg[rd as usize],
                            self.reg_file.gp_reg[rs1 as usize],
                            self.reg_file.gp_reg[rs2 as usize],
                        )
                        .await;
                }
                op::Opcode::V_SUB_VF { rd, rs1, rs2 } => {
                    self.v_machine
                        .add_scalar(
                            self.reg_file.gp_reg[rd as usize],
                            self.reg_file.gp_reg[rs1 as usize],
                            (-self.reg_file.fp_reg[rs2 as usize]).into(),
                        )
                        .await;
                }
                op::Opcode::V_MUL_VV { rd, rs1, rs2 } => {
                    self.v_machine
                        .mul(
                            self.reg_file.gp_reg[rd as usize],
                            self.reg_file.gp_reg[rs1 as usize],
                            self.reg_file.gp_reg[rs2 as usize],
                        )
                        .await;
                }
                op::Opcode::V_MUL_VF { rd, rs1, rs2 } => {
                    self.v_machine
                        .mul_scalar(
                            self.reg_file.gp_reg[rd as usize],
                            self.reg_file.gp_reg[rs1 as usize],
                            self.reg_file.fp_reg[rs2 as usize].into(),
                        )
                        .await;
                }
                op::Opcode::V_EXP_V { rd, rs1 } => {
                    self.v_machine
                        .exp(
                            self.reg_file.gp_reg[rd as usize],
                            self.reg_file.gp_reg[rs1 as usize],
                        )
                        .await;
                }
                op::Opcode::V_RECI_V { rd, rs1 } => {
                    self.v_machine
                        .reciprocal(
                            self.reg_file.gp_reg[rd as usize],
                            self.reg_file.gp_reg[rs1 as usize],
                        )
                        .await;
                }

                // Write to fp0 is a no-op.
                op::Opcode::V_RED_SUM { rd: 0, .. } | op::Opcode::V_RED_MAX { rd: 0, .. } => (),

                op::Opcode::V_RED_SUM { rd, rs1 } => {
                    let result = self
                        .v_machine
                        .reduce_sum(
                            self.reg_file.gp_reg[rs1 as usize],
                            self.reg_file.fp_reg[rd as usize].into(),
                        )
                        .await;
                    self.reg_file.fp_reg[rd as usize] = f16::from_f32(result);
                }
                op::Opcode::V_RED_MAX { rd, rs1 } => {
                    let result = self
                        .v_machine
                        .reduce_max(
                            self.reg_file.gp_reg[rs1 as usize],
                            self.reg_file.fp_reg[rd as usize].into(),
                        )
                        .await;
                    self.reg_file.fp_reg[rd as usize] = f16::from_f32(result);
                }

                // Write to fp0 is a no-op.
                op::Opcode::S_ADD_FP { rd: 0, .. }
                | op::Opcode::S_SUB_FP { rd: 0, .. }
                | op::Opcode::S_MAX_FP { rd: 0, .. }
                | op::Opcode::S_MUL_FP { rd: 0, .. }
                | op::Opcode::S_EXP_FP { rd: 0, .. }
                | op::Opcode::S_RECI_FP { rd: 0, .. }
                | op::Opcode::S_SQRT_FP { rd: 0, .. } => {}

                op::Opcode::S_ADD_FP { rd, rs1, rs2 } => {
                    self.reg_file.fp_reg[rd as usize] =
                        self.reg_file.fp_reg[rs1 as usize] + self.reg_file.fp_reg[rs2 as usize];
                    cycle!(*SCALAR_FP_BASIC_CYCLES);
                }
                op::Opcode::S_SUB_FP { rd, rs1, rs2 } => {
                    self.reg_file.fp_reg[rd as usize] =
                        self.reg_file.fp_reg[rs1 as usize] - self.reg_file.fp_reg[rs2 as usize];
                    cycle!(*SCALAR_FP_BASIC_CYCLES);
                }
                op::Opcode::S_MAX_FP { rd, rs1, rs2 } => {
                    self.reg_file.fp_reg[rd as usize] = f16::max(
                        self.reg_file.fp_reg[rs1 as usize],
                        self.reg_file.fp_reg[rs2 as usize],
                    );
                    cycle!(*SCALAR_FP_BASIC_CYCLES);
                }
                op::Opcode::S_MUL_FP { rd, rs1, rs2 } => {
                    self.reg_file.fp_reg[rd as usize] =
                        self.reg_file.fp_reg[rs1 as usize] * self.reg_file.fp_reg[rs2 as usize];
                    cycle!(*SCALAR_FP_BASIC_CYCLES);
                }
                op::Opcode::S_EXP_FP { rd, rs1 } => {
                    self.reg_file.fp_reg[rd as usize] =
                        f16::from_f32(f32::exp(self.reg_file.fp_reg[rs1 as usize].into()));
                    cycle!(*SCALAR_FP_EXP_CYCLES);
                }
                op::Opcode::S_RECI_FP { rd, rs1 } => {
                    self.reg_file.fp_reg[rd as usize] =
                        f16::ONE / self.reg_file.fp_reg[rs1 as usize];
                    cycle!(*SCALAR_FP_RECI_CYCLES);
                }
                op::Opcode::S_SQRT_FP { rd, rs1 } => {
                    self.reg_file.fp_reg[rd as usize] =
                        f16::from_f32(f32::from(self.reg_file.fp_reg[rs1 as usize]).sqrt());
                    cycle!(*SCALAR_FP_SQRT_CYCLES);
                }
                op::Opcode::S_LD_FP { rd, rs1, imm } => {
                    self.reg_file.fp_reg[rd as usize] =
                        self.fp_sram[(self.reg_file.gp_reg[rs1 as usize] + imm) as usize];
                    cycle!(1);
                }
                op::Opcode::S_ST_FP { rd, rs1, imm } => {
                    self.fp_sram[(self.reg_file.gp_reg[rs1 as usize] + imm) as usize] =
                        self.reg_file.fp_reg[rd as usize];
                    cycle!(1);
                }
                op::Opcode::S_MAP_V_FP { rd, rs1, imm } => todo!(),

                op::Opcode::S_ADD_INT { rd, rs1, rs2 } => {
                    self.reg_file.gp_reg[rd as usize] = self.reg_file.gp_reg[rs1 as usize]
                        .wrapping_add(self.reg_file.gp_reg[rs2 as usize]);
                    cycle!(*SCALAR_INT_BASIC_CYCLES);
                }
                op::Opcode::S_ADDI_INT { rd, rs1, imm } => {
                    self.reg_file.gp_reg[rd as usize] =
                        self.reg_file.gp_reg[rs1 as usize].wrapping_add(imm as u32);
                    cycle!(*SCALAR_INT_BASIC_CYCLES);
                }
                op::Opcode::S_SUB_INT { rd, rs1, rs2 } => {
                    self.reg_file.gp_reg[rd as usize] = self.reg_file.gp_reg[rs1 as usize]
                        .wrapping_sub(self.reg_file.gp_reg[rs2 as usize]);
                    cycle!(*SCALAR_INT_BASIC_CYCLES);
                }
                op::Opcode::S_MUL_INT { rd, rs1, rs2 } => {
                    self.reg_file.gp_reg[rd as usize] = self.reg_file.gp_reg[rs1 as usize]
                        .wrapping_mul(self.reg_file.gp_reg[rs2 as usize]);
                    cycle!(*SCALAR_INT_BASIC_CYCLES);
                }
                op::Opcode::S_LUI_INT { rd, imm } => {
                    self.reg_file.gp_reg[rd as usize] = (imm as u32) << 12;
                    cycle!(*SCALAR_INT_BASIC_CYCLES);
                }
                op::Opcode::S_LD_INT { rd, rs1, imm } => {
                    self.reg_file.gp_reg[rd as usize] =
                        self.int_sram[(self.reg_file.gp_reg[rs1 as usize] + imm) as usize];
                    cycle!(*SCALAR_INT_BASIC_CYCLES);
                }
                op::Opcode::S_ST_INT { rd, rs1, imm } => {
                    self.int_sram[(self.reg_file.gp_reg[rs1 as usize] + imm) as usize] =
                        self.reg_file.gp_reg[rd as usize];
                    cycle!(*SCALAR_INT_BASIC_CYCLES);
                }
                op::Opcode::H_PREFETCH_M {
                    rd,
                    rs1,
                    rs2,
                    rstride,
                    precision,
                } => {
                    // TODO: rstride support to be added
                    let offset = self.reg_file.gp_reg[rs1 as usize];
                    let addr = self.reg_file.hbm_addr_reg[rs2 as usize];
                    let dtype = match precision {
                        op::MatrixPrecision::Weights => *MATRIX_WEIGHT_TYPE,
                        op::MatrixPrecision::KeyValue => *MATRIX_KV_TYPE,
                    };

                    let scale = match dtype {
                        MxDataType::Plain(_) => 0,
                        MxDataType::Mx { elem, scale, block } => {
                            offset
                                / (elem.size_in_bits() as u32 * block / scale.size_in_bits() as u32)
                        } // Element addr shifted by (element to scale ratio)
                    };
                    println!(
                        "prefetch_m: dtype_size = {:?}",
                        dtype.element_type().size_in_bits()
                    );

                    let xfer = self.transfer_from_hbm(
                        addr + offset as u64,
                        addr + self.reg_file.scale as u64 + scale as u64,
                        (*MLEN * *MLEN) as usize,
                        dtype,
                        self.m_machine.mram.ty,
                    );
                    self.m_machine
                        .mram
                        .write_delayed(self.reg_file.gp_reg[rd as usize], xfer)
                        .await;
                }
                op::Opcode::H_PREFETCH_V {
                    rd,
                    rs1,
                    rs2,
                    rstride,
                    precision,
                } => {
                    // TODO: rstride support to be added
                    let offset = self.reg_file.gp_reg[rs1 as usize];
                    let addr = self.reg_file.hbm_addr_reg[rs2 as usize];

                    let dtype = match precision {
                        op::VectorPrecision::Activation => *VECTOR_ACTIVATION_TYPE,
                        op::VectorPrecision::KeyValue => *VECTOR_KV_TYPE,
                    };

                    let scale = match dtype {
                        MxDataType::Plain(_) => 0,
                        MxDataType::Mx { elem, scale, block } => {
                            offset
                                / (elem.size_in_bits() as u32 * block / scale.size_in_bits() as u32)
                        }
                    };
                    println!(
                        "prefetch_v: dtype_size = {:?}",
                        dtype.element_type().size_in_bits()
                    );
                    let xfer = self.transfer_from_hbm(
                        addr + offset as u64,
                        addr + self.reg_file.scale as u64 + scale as u64,
                        *VLEN as usize,
                        dtype,
                        self.v_machine.vram.ty,
                    );
                
                    let dest = self.reg_file.gp_reg[rd as usize];
                    self.v_machine.vram.write_delayed(dest, xfer).await;
                }
                op::Opcode::H_STORE_V {
                    rd,
                    rs1,
                    rs2,
                    rstride,
                    precision: _,
                } => todo!(),
                op::Opcode::C_SET_ADDR_REG { rd, rs1, rs2 } => {
                    let imm = ((self.reg_file.gp_reg[rs1 as usize] as u64) << 32)
                        | (self.reg_file.gp_reg[rs2 as usize] as u64);
                    self.reg_file.hbm_addr_reg[rd as usize] = imm;
                    cycle!(1);
                }
                op::Opcode::C_SET_SCALE_REG { rd } => {
                    self.reg_file.scale = self.reg_file.gp_reg[rd as usize];
                    cycle!(1);
                }
                op::Opcode::C_BREAK => todo!(),
            }
        }
    }
}

#[derive(Parser)]
struct Opts {
    #[arg(long)]
    /// Path to file storing opcodes.
    opcode: PathBuf,

    #[arg(long)]
    /// Path to file storing HBM contents.
    hbm: PathBuf,
}

async fn start() {
    let opts = Opts::parse();

    let mram = Arc::new(MatrixSram::new(*MLEN, *MATRIX_SRAM_SIZE, *MATRIX_SRAM_TYPE)); // Matrix SRAM
    let vram = Arc::new(VectorSram::new(*VLEN, *VECTOR_SRAM_SIZE, *VECTOR_SRAM_TYPE)); // Vector SRAM
    let machine = MatrixMachine {
        mram,
        vram: vram.clone(),
        tile_size: *MLEN,
        blen: *BLEN,
        m_accum: Tensor::zeros(
            [*BLEN as i64, *BLEN as i64],
            (tch::Kind::Float, tch::Device::Cpu),
        ),
        v_accum: Tensor::zeros([*MLEN as i64], (tch::Kind::Float, tch::Device::Cpu)),
    };
    let v_machine = VectorMachine { vram }; // Share same dim with VSRAM

    let hbm = Arc::new(memory::WithTiming::new(
        ManuallyDrop::new(ramulator::Ramulator::hbm2_preset(8).unwrap()),
        memory::MemoryBacked::with_capacity(*HBM_SIZE),
    ));

    let mut accelerator = Accelerator {
        m_machine: machine,
        v_machine,
        hbm: hbm.clone(),
        tile_size: *MLEN,
        reg_file: AcceeleratorRegFile {
            gp_reg: [0; 16],
            fp_reg: [f16::ZERO; 8],
            hbm_addr_reg: [0; 8],
            scale: 0,
        },
        int_sram: vec![0; 1024],
        fp_sram: vec![f16::ZERO; 1024],
    };

    use std::fs;
    let op_file = fs::read_to_string(opts.opcode).unwrap();
    eprintln!("Loaded opcode file: {:?}", op_file);

    let op: Vec<u32> = op_file
        .split_whitespace() // split by spaces/newlines
        .map(|tok| u32::from_str_radix(tok.trim_start_matches("0x"), 16).unwrap())
        .collect();

    for (i, word) in op.iter().enumerate() {
        let decoded = op::Opcode::decode(*word);
        println!("{i:04}: 0x{word:08X} -> {:?}", decoded);
    }

    // Memory Initialization
    // - HBM Preload
    
    let hbm_data = std::fs::read(opts.hbm).unwrap();

    hbm.data().with_data(|f| {
        f[..hbm_data.len()].copy_from_slice(&hbm_data);
    });
    // - FP_SRAM Preload
    accelerator.fp_sram[0] = f16::from_bits(0x3F00); // Preloading a constant at the 0 index

    // - Execute Instructions
    accelerator
        .do_ops(&dbg!(
            op.into_iter().map(op::Opcode::decode).collect::<Vec<_>>()
        ))
        .await;

    println!("gp1 = {:x}", accelerator.reg_file.gp_reg[1]);
    println!("scale = {}", accelerator.reg_file.scale);
    println!(
        "{}",
        accelerator.v_machine.vram.read(0x0000).await.as_tensor()
    );
}

#[tokio::main]
async fn main() {
    let executor = Executor::new();
    executor.spawn(start());
    executor.enter(Instant::ETERNITY).await;
    eprintln!("Simulation completed. Last instance {:?}", executor.now());
}

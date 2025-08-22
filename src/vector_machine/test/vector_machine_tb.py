#!/usr/bin/env python3
from pathlib import Path
import sys
# Use 4 levels up, not 5
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "tools"))

import logging
import pytest
import cocotb
from cocotb.triggers import RisingEdge
from cocotb.clock import Clock
from cfl_cocotb import veri_runner
from cfl_cocotb.runner import SRC_PATH
from cfl_cocotb.fp_generation import FpGenerator

logger = logging.getLogger("testbench")
logger.setLevel(logging.INFO)

def pack_v(bus_elems, elem_width):
    """Pack list of element words [0..VLEN-1] into single int bus (lane 0 at LSB)."""
    v = 0
    mask = (1 << elem_width) - 1
    for i, w in enumerate(bus_elems):
        v |= (int(w) & mask) << (i * elem_width)
    return v

def unpack_v(bus, lanes, elem_w):
    mask = (1 << elem_w) - 1
    return [ (bus >> (i * elem_w)) & mask for i in range(lanes) ]

def pretty_list(xs):
    return "[" + ", ".join(f"{x:.6g}" if isinstance(x, float) else str(x) for x in xs) + "]"

#@cocotb.test()
async def prefix_scan_vm_test(dut):
    cocotb.log.info("========== Vector Machine Prefix-Scan Test ==========")

    # Match precision.svh and configuration.svh
    EXP, MANT, VLEN = 7, 8, 8
    ELEM_W = 1 + EXP + MANT
    gen = FpGenerator(EXP, MANT)
    cocotb.log.info(f"Config (from definitions): EXP={EXP}, MANT={MANT}, VLEN={VLEN}, ELEM_W={ELEM_W} bits")

    # Clock and active-high reset
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    dut.rst.value = 1
    for _ in range(3):
        await RisingEdge(dut.clk)
    dut.rst.value = 0
    for _ in range(3):
        await RisingEdge(dut.clk)
    cocotb.log.info("Reset deasserted")

    # Controls
    if hasattr(dut, "broadcast_fp2"):    dut.broadcast_fp2.value = 0
    if hasattr(dut, "reduct_v_control"): dut.reduct_v_control.value = 0  # STALL_V_REDUCT
    if hasattr(dut, "element_v_control"): dut.element_v_control.value = 8  # PREFIX_SCAN_V_ELEMENT

    # Build input vector [1..VLEN] using EXP=7/MANT=8 encoding
    values = [float(i + 1) for i in range(VLEN)]
    fp_vals, enc = gen.generate_specified_value_fp_input(values)
    v_a_bus = pack_v(enc[:VLEN], ELEM_W)

    cocotb.log.info("<------- Input Vector (A) --------->")
    cocotb.log.info(f"Input values: {pretty_list(values)}")
    for i in range(VLEN):
        cocotb.log.info(f"  A[{i}] = {fp_vals[i]:.6g}  enc=0x{enc[i]:0{(ELEM_W+3)//4}X}")
    cocotb.log.info(f"Packed A bus: 0x{v_a_bus:0{(VLEN*ELEM_W+3)//4}X}")

    # Drive inputs (A only) and keep v_out_ready asserted
    if hasattr(dut, "v_b_in"):      dut.v_b_in.value = 0
    if hasattr(dut, "v_b_valid"):   dut.v_b_valid.value = 0
    if hasattr(dut, "s_in"):        dut.s_in.value = 0
    if hasattr(dut, "s_in_valid"):  dut.s_in_valid.value = 0
    if hasattr(dut, "result_waddr"):        dut.result_waddr.value = 0
    if hasattr(dut, "result_waddr_update"): dut.result_waddr_update.value = 0
    if hasattr(dut, "v_out_ready"): dut.v_out_ready.value = 1

    dut.v_a_in.value = v_a_bus
    if hasattr(dut, "v_a_ready"):
        while int(dut.v_a_ready.value) == 0:
            await RisingEdge(dut.clk)

    if hasattr(dut, "v_a_valid"):
        dut.v_a_valid.value = 1
        await RisingEdge(dut.clk)
        dut.v_a_valid.value = 0
        cocotb.log.info("A valid pulsed for 1 cycle")
    else:
        await RisingEdge(dut.clk)

    cocotb.log.info("Inputs driven, waiting for element-wise result...")

    # Wait for element_v_out_valid; then +2 cycles to sample v_out (due to p1 stage)
    elem_cycle = None
    MAX_CYCLES = 300
    for cycle in range(1, MAX_CYCLES + 1):
        await RisingEdge(dut.clk)
        if hasattr(dut, "element_v_out_valid") and int(dut.element_v_out_valid.value) == 1:
            elem_cycle = cycle
            cocotb.log.info(f"Element valid at cycle {cycle}")
            break
        if cycle % 10 == 0:
            try:
                ev = int(dut.element_v_out_valid.value)
                cocotb.log.info(f"Cycle {cycle:02d}: element_v_out_valid={ev}")
            except Exception:
                pass

    assert elem_cycle is not None, "Timeout waiting for element_v_out_valid"

    # Optional: log p1_result_v_out if visible
    if hasattr(dut, "p1_result_v_out"):
        try:
            p1_val = int(dut.p1_result_v_out.value)
            cocotb.log.info(f"p1_result_v_out at cycle {elem_cycle}: 0x{p1_val:0{(VLEN*ELEM_W+3)//4}X}")
        except Exception:
            pass

    await RisingEdge(dut.clk)  # +1
    await RisingEdge(dut.clk)  # +2 (v_out updated from p1)
    assert hasattr(dut, "v_out"), "DUT has no v_out"
    got_vec = int(dut.v_out.value)
    cocotb.log.info(f"v_out captured at cycle {elem_cycle+2}: 0x{got_vec:0{(VLEN*ELEM_W+3)//4}X}")

    # Decode using EXP=7/MANT=8/ VL=8
    out_fp = gen.translate_packed_array_fp(VLEN, EXP, MANT, got_vec)

    # Expected prefix-scan
    exp_scan, acc = [], 0.0
    for x in values:
        acc += x
        exp_scan.append(acc)

    cocotb.log.info("<------- Prefix Scan Results --------->")
    cocotb.log.info(f"Hardware Result:  {pretty_list(out_fp)}")
    cocotb.log.info(f"Expected Result:  {pretty_list(exp_scan)}")

    tol = 0.5
    all_ok = True
    for i, (g, e) in enumerate(zip(out_fp, exp_scan)):
        err = abs(g - e)
        if err > tol:
            cocotb.log.error(f"✗ Mismatch at index {i}: expected {e}, got {g}, err {err}")
            all_ok = False
        else:
            cocotb.log.info(f"✓ Index {i}: {g:.6g} ≈ {e:.6g}")
    assert all_ok, "Prefix-scan verification failed"

    # Keep sim alive a bit for waveform
    for _ in range(5):
        await RisingEdge(dut.clk)
    cocotb.log.info("✓ Test complete")

@cocotb.test()
async def shift_vm_test(dut):
    cocotb.log.info("========== Vector Machine Shift Test ==========")

    # Match precision.svh and configuration.svh
    EXP, MANT, VLEN = 7, 8, 8
    ELEM_W = 1 + EXP + MANT
    gen = FpGenerator(EXP, MANT)

    # Clock and reset
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    dut.rst.value = 1
    for _ in range(3):
        await RisingEdge(dut.clk)
    dut.rst.value = 0
    for _ in range(3):
        await RisingEdge(dut.clk)

    # Defaults
    dut.v_out_ready.value = 1
    dut.broadcast_fp2.value = 0
    dut.reduct_v_control.value = 0  # STALL_V_REDUCT

    # Config (match your precision/VLEN)
    EXP, MANT, VLEN = 7, 8, 8
    ELEM_W = 1 + EXP + MANT

    # Program writeback addr (optional)
    dut.result_waddr.value = 0
    dut.result_waddr_update.value = 1
    await RisingEdge(dut.clk)
    dut.result_waddr_update.value = 0

    # Prepare vector A [1..VLEN]
    vals = list(range(1, VLEN + 1))
    v_a_bus = pack_v(vals, ELEM_W)

    # Shift immediate (lanes)
    shift_amount = 2
    dut.s_wtarget.value = shift_amount

    # Issue SHIFT op (set to your enum value for SHIFT_V_LANES_ELEMENT)
    SHIFT_OP = 9  # TODO: adjust to your enum encoding
    dut.element_v_control.value = SHIFT_OP

    # Drive A for one cycle
    dut.v_a_in.value = v_a_bus
    dut.v_a_valid.value = 1
    await RisingEdge(dut.clk)
    dut.v_a_valid.value = 0

    # Deassert op back to STALL
    dut.element_v_control.value = 0

    # Wait up to N cycles for non-zero v_out
    got_packed = 0
    seen_nonzero = False
    when = -1
    MAX_WAIT = 32
    for t in range(MAX_WAIT):
        await RisingEdge(dut.clk)
        got = int(dut.v_out.value)
        if got != 0 and not seen_nonzero:
            got_packed = got
            seen_nonzero = True
            when = t  # cycles after deasserting v_a_valid
            # keep running a couple more cycles to mimic your waveform observation
    # If nothing seen, sample last value anyway
    if not seen_nonzero:
        got_packed = int(dut.v_out.value)

    # Expected shifted lanes
    expected = ([0] * shift_amount) + vals[:VLEN - shift_amount]
    actual = unpack_v(got_packed, VLEN, ELEM_W)

    cocotb.log.info(f"Observed v_out after {when if seen_nonzero else MAX_WAIT} cycles")
    cocotb.log.info(f"v_out (packed)=0x{got_packed:0{(VLEN*ELEM_W+3)//4}X}")
    cocotb.log.info(f"expected lanes: {expected}")
    cocotb.log.info(f"actual   lanes: {actual}")

    assert actual == expected, "Shift output mismatch"

@pytest.mark.dev
def test_vector_machine():
    veri_runner(
        group="vector_machine",
        module="vector_machine",
        additional_include_paths=[
            str(SRC_PATH / "basic_components" / "buffer"),
            str(SRC_PATH / "basic_components" / "common"),
            str(SRC_PATH / "basic_components" / "fp_operation"),
            str(SRC_PATH / "basic_components" / "hadamard_transform"),
            str(SRC_PATH / "basic_components" / "synopsis_ip_inst"),
            str(SRC_PATH / "basic_components" / "conversion"),
            str(SRC_PATH / "basic_components" / "fixed_operation"),
            str(SRC_PATH / "basic_components" / "int_operation"),
            str(SRC_PATH / "basic_components" / "synopsis"),
        ],
        definitions_path=[str(SRC_PATH / "definitions")],
        trace=True,
    )

if __name__ == "__main__":
    test_vector_machine()
// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Tracing implementation internals
#include "verilated_vcd_c.h"
#include "Vtop__Syms.h"


VL_ATTR_COLD void Vtop___024root__trace_init_sub__TOP__0(Vtop___024root* vlSelf, VerilatedVcd* tracep) {
    (void)vlSelf;  // Prevent unused variable warning
    Vtop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root__trace_init_sub__TOP__0\n"); );
    auto &vlSelfRef = std::ref(*vlSelf).get();
    // Init
    const int c = vlSymsp->__Vm_baseCode;
    // Body
    tracep->declBit(c+1,0,"clk",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+2,0,"rst",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->pushPrefix("x_data", VerilatedTracePrefixType::ARRAY_UNPACKED);
    for (int i = 0; i < 4; ++i) {
        tracep->declBus(c+3+i*1,0,"",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, true,(i+0), 7,0);
    }
    tracep->popPrefix();
    tracep->declBit(c+7,0,"x_valid",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+8,0,"x_ready",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->pushPrefix("y_data", VerilatedTracePrefixType::ARRAY_UNPACKED);
    for (int i = 0; i < 4; ++i) {
        tracep->declBus(c+9+i*1,0,"",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, true,(i+0), 7,0);
    }
    tracep->popPrefix();
    tracep->declBit(c+13,0,"y_valid",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+14,0,"y_ready",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->pushPrefix("out_data", VerilatedTracePrefixType::ARRAY_UNPACKED);
    for (int i = 0; i < 4; ++i) {
        tracep->declBus(c+15+i*1,0,"",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, true,(i+0), 15,0);
    }
    tracep->popPrefix();
    tracep->declBit(c+19,0,"out_valid",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+20,0,"out_ready",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->pushPrefix("simple_matmul", VerilatedTracePrefixType::SCOPE_MODULE);
    tracep->declBus(c+598,0,"N",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+598,0,"M",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+598,0,"K",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+599,0,"X_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+600,0,"X_FRAC_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+599,0,"Y_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+600,0,"Y_FRAC_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+600,0,"OUTPUT_ROUNDING",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+601,0,"OUT_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+598,0,"OUT_FRAC_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBit(c+21,0,"clk",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+22,0,"rst",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->pushPrefix("x_data", VerilatedTracePrefixType::ARRAY_UNPACKED);
    for (int i = 0; i < 4; ++i) {
        tracep->declBus(c+23+i*1,0,"",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, true,(i+0), 7,0);
    }
    tracep->popPrefix();
    tracep->declBit(c+27,0,"x_valid",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+28,0,"x_ready",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->pushPrefix("y_data", VerilatedTracePrefixType::ARRAY_UNPACKED);
    for (int i = 0; i < 4; ++i) {
        tracep->declBus(c+29+i*1,0,"",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, true,(i+0), 7,0);
    }
    tracep->popPrefix();
    tracep->declBit(c+33,0,"y_valid",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+34,0,"y_ready",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->pushPrefix("out_data", VerilatedTracePrefixType::ARRAY_UNPACKED);
    for (int i = 0; i < 4; ++i) {
        tracep->declBus(c+35+i*1,0,"",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, true,(i+0), 15,0);
    }
    tracep->popPrefix();
    tracep->declBit(c+39,0,"out_valid",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+40,0,"out_ready",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBus(c+602,0,"ACC_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+598,0,"ACC_FRAC_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->pushPrefix("y_data_transpose", VerilatedTracePrefixType::ARRAY_UNPACKED);
    for (int i = 0; i < 4; ++i) {
        tracep->declBus(c+41+i*1,0,"",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, true,(i+0), 7,0);
    }
    tracep->popPrefix();
    tracep->declBit(c+45,0,"dot_product_ready",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+46,0,"inputs_valid",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+47,0,"inputs_ready",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBus(c+48,0,"dot_product_valid",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1, 3,0);
    tracep->declBus(c+49,0,"sync_ready",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1, 3,0);
    tracep->pushPrefix("dot_product_data_out", VerilatedTracePrefixType::ARRAY_UNPACKED);
    for (int i = 0; i < 4; ++i) {
        tracep->declBus(c+50+i*1,0,"",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, true,(i+0), 16,0);
    }
    tracep->popPrefix();
    tracep->pushPrefix("rounded_dot_product", VerilatedTracePrefixType::ARRAY_UNPACKED);
    for (int i = 0; i < 4; ++i) {
        tracep->declBus(c+54+i*1,0,"",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, true,(i+0), 15,0);
    }
    tracep->popPrefix();
    tracep->pushPrefix("multi_row[0]", VerilatedTracePrefixType::SCOPE_MODULE);
    tracep->pushPrefix("multi_col[0]", VerilatedTracePrefixType::SCOPE_MODULE);
    tracep->pushPrefix("dot_product_inst", VerilatedTracePrefixType::SCOPE_MODULE);
    tracep->declBus(c+599,0,"IN_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+598,0,"IN_SIZE",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+599,0,"WEIGHT_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+602,0,"OUT_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBit(c+58,0,"clk",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+59,0,"rst",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->pushPrefix("data_in", VerilatedTracePrefixType::ARRAY_UNPACKED);
    for (int i = 0; i < 2; ++i) {
        tracep->declBus(c+60+i*1,0,"",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, true,(i+0), 7,0);
    }
    tracep->popPrefix();
    tracep->declBit(c+62,0,"data_in_valid",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+63,0,"data_in_ready",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->pushPrefix("weight", VerilatedTracePrefixType::ARRAY_UNPACKED);
    for (int i = 0; i < 2; ++i) {
        tracep->declBus(c+64+i*1,0,"",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, true,(i+0), 7,0);
    }
    tracep->popPrefix();
    tracep->declBit(c+66,0,"weight_valid",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+67,0,"weight_ready",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBus(c+68,0,"data_out",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 16,0);
    tracep->declBit(c+69,0,"data_out_valid",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+70,0,"data_out_ready",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBus(c+601,0,"PRODUCT_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->pushPrefix("pv", VerilatedTracePrefixType::ARRAY_UNPACKED);
    for (int i = 0; i < 2; ++i) {
        tracep->declBus(c+71+i*1,0,"",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, true,(i+0), 15,0);
    }
    tracep->popPrefix();
    tracep->declBit(c+73,0,"pv_valid",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+74,0,"pv_ready",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBus(c+75,0,"sum",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1, 16,0);
    tracep->declBit(c+76,0,"sum_valid",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+77,0,"sum_ready",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->pushPrefix("fixed_adder_tree_inst", VerilatedTracePrefixType::SCOPE_MODULE);
    tracep->declBus(c+598,0,"IN_SIZE",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+601,0,"IN_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+602,0,"OUT_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBit(c+78,0,"clk",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+79,0,"rst",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->pushPrefix("data_in", VerilatedTracePrefixType::ARRAY_UNPACKED);
    for (int i = 0; i < 2; ++i) {
        tracep->declBus(c+80+i*1,0,"",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, true,(i+0), 15,0);
    }
    tracep->popPrefix();
    tracep->declBit(c+82,0,"data_in_valid",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+83,0,"data_in_ready",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBus(c+84,0,"data_out",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 16,0);
    tracep->declBit(c+85,0,"data_out_valid",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+86,0,"data_out_ready",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBus(c+600,0,"LEVELS",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->pushPrefix("gen_adder_tree", VerilatedTracePrefixType::SCOPE_MODULE);
    tracep->pushPrefix("data", VerilatedTracePrefixType::ARRAY_UNPACKED);
    for (int i = 0; i < 2; ++i) {
        tracep->declQuad(c+87+i*2,0,"",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, true,(i+0), 33,0);
    }
    tracep->popPrefix();
    tracep->pushPrefix("sum", VerilatedTracePrefixType::ARRAY_UNPACKED);
    for (int i = 0; i < 1; ++i) {
        tracep->declQuad(c+91+i*2,0,"",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, true,(i+0), 33,0);
    }
    tracep->popPrefix();
    tracep->pushPrefix("valid", VerilatedTracePrefixType::ARRAY_UNPACKED);
    for (int i = 0; i < 2; ++i) {
        tracep->declBit(c+93+i*1,0,"",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, true,(i+0));
    }
    tracep->popPrefix();
    tracep->pushPrefix("ready", VerilatedTracePrefixType::ARRAY_UNPACKED);
    for (int i = 0; i < 2; ++i) {
        tracep->declBit(c+95+i*1,0,"",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, true,(i+0));
    }
    tracep->popPrefix();
    tracep->pushPrefix("level[0]", VerilatedTracePrefixType::SCOPE_MODULE);
    tracep->declBus(c+598,0,"LEVEL_IN_SIZE",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+600,0,"LEVEL_OUT_SIZE",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+601,0,"LEVEL_IN_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+602,0,"LEVEL_OUT_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->pushPrefix("layer", VerilatedTracePrefixType::SCOPE_MODULE);
    tracep->declBus(c+598,0,"IN_SIZE",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+601,0,"IN_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+600,0,"SIGNED",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+602,0,"OUT_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+600,0,"OUT_SIZE",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+97,0,"data_in",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+98,0,"data_out",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 16,0);
    tracep->pushPrefix("data_in_unflat", VerilatedTracePrefixType::ARRAY_UNPACKED);
    for (int i = 0; i < 2; ++i) {
        tracep->declBus(c+99+i*1,0,"",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, true,(i+0), 15,0);
    }
    tracep->popPrefix();
    tracep->pushPrefix("data_out_unflat", VerilatedTracePrefixType::ARRAY_UNPACKED);
    for (int i = 0; i < 1; ++i) {
        tracep->declBus(c+101+i*1,0,"",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, true,(i+0), 16,0);
    }
    tracep->popPrefix();
    tracep->popPrefix();
    tracep->pushPrefix("register_slice", VerilatedTracePrefixType::SCOPE_MODULE);
    tracep->declBus(c+602,0,"DATA_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBit(c+102,0,"clk",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+103,0,"rst",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBus(c+104,0,"data_in",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 16,0);
    tracep->declBit(c+105,0,"data_in_valid",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+106,0,"data_in_ready",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBus(c+107,0,"data_out",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 16,0);
    tracep->declBit(c+108,0,"data_out_valid",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+109,0,"data_out_ready",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBus(c+110,0,"data_buffer_out",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1, 16,0);
    tracep->declBit(c+111,0,"data_buffer_wren",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+112,0,"data_out_wren",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+113,0,"use_buffered_data",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBus(c+114,0,"selected_data",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1, 16,0);
    tracep->declBit(c+115,0,"insert",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+116,0,"remove",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+117,0,"load",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+118,0,"flow",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+119,0,"fill",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+120,0,"flush",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+121,0,"unload",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBus(c+122,0,"state",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::INT, false,-1, 31,0);
    tracep->declBus(c+123,0,"state_next",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::INT, false,-1, 31,0);
    tracep->popPrefix();
    tracep->popPrefix();
    tracep->popPrefix();
    tracep->popPrefix();
    tracep->pushPrefix("fixed_vector_mult_inst", VerilatedTracePrefixType::SCOPE_MODULE);
    tracep->declBus(c+599,0,"IN_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+599,0,"WEIGHT_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+601,0,"OUT_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+598,0,"IN_SIZE",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBit(c+124,0,"clk",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+125,0,"rst",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->pushPrefix("data_in", VerilatedTracePrefixType::ARRAY_UNPACKED);
    for (int i = 0; i < 2; ++i) {
        tracep->declBus(c+126+i*1,0,"",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, true,(i+0), 7,0);
    }
    tracep->popPrefix();
    tracep->declBit(c+128,0,"data_in_valid",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+129,0,"data_in_ready",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->pushPrefix("weight", VerilatedTracePrefixType::ARRAY_UNPACKED);
    for (int i = 0; i < 2; ++i) {
        tracep->declBus(c+130+i*1,0,"",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, true,(i+0), 7,0);
    }
    tracep->popPrefix();
    tracep->declBit(c+132,0,"weight_valid",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+133,0,"weight_ready",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->pushPrefix("data_out", VerilatedTracePrefixType::ARRAY_UNPACKED);
    for (int i = 0; i < 2; ++i) {
        tracep->declBus(c+134+i*1,0,"",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, true,(i+0), 15,0);
    }
    tracep->popPrefix();
    tracep->declBit(c+136,0,"data_out_valid",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+137,0,"data_out_ready",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBus(c+601,0,"PRODUCT_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->pushPrefix("product_vector", VerilatedTracePrefixType::ARRAY_UNPACKED);
    for (int i = 0; i < 2; ++i) {
        tracep->declBus(c+138+i*1,0,"",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, true,(i+0), 15,0);
    }
    tracep->popPrefix();
    tracep->declBit(c+140,0,"product_data_in_valid",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+141,0,"product_data_in_ready",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+142,0,"product_data_out_valid",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+143,0,"product_data_out_ready",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBus(c+144,0,"product_data_in",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+145,0,"product_data_out",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->pushPrefix("join_inst", VerilatedTracePrefixType::SCOPE_MODULE);
    tracep->declBus(c+146,0,"data_in_valid",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 1,0);
    tracep->declBus(c+147,0,"data_in_ready",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 1,0);
    tracep->declBit(c+148,0,"data_out_valid",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+149,0,"data_out_ready",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->popPrefix();
    tracep->pushPrefix("parallel_mult[0]", VerilatedTracePrefixType::SCOPE_MODULE);
    tracep->pushPrefix("fixed_mult_inst", VerilatedTracePrefixType::SCOPE_MODULE);
    tracep->declBus(c+599,0,"IN_A_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+599,0,"IN_B_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+150,0,"data_a",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 7,0);
    tracep->declBus(c+151,0,"data_b",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 7,0);
    tracep->declBus(c+152,0,"product",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 15,0);
    tracep->popPrefix();
    tracep->popPrefix();
    tracep->pushPrefix("parallel_mult[1]", VerilatedTracePrefixType::SCOPE_MODULE);
    tracep->pushPrefix("fixed_mult_inst", VerilatedTracePrefixType::SCOPE_MODULE);
    tracep->declBus(c+599,0,"IN_A_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+599,0,"IN_B_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+153,0,"data_a",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 7,0);
    tracep->declBus(c+154,0,"data_b",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 7,0);
    tracep->declBus(c+155,0,"product",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 15,0);
    tracep->popPrefix();
    tracep->popPrefix();
    tracep->pushPrefix("register_slice", VerilatedTracePrefixType::SCOPE_MODULE);
    tracep->declBus(c+603,0,"DATA_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBit(c+156,0,"clk",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+157,0,"rst",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBus(c+158,0,"data_in",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBit(c+159,0,"data_in_valid",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+160,0,"data_in_ready",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBus(c+161,0,"data_out",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBit(c+162,0,"data_out_valid",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+163,0,"data_out_ready",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBus(c+164,0,"data_buffer_out",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBit(c+165,0,"data_buffer_wren",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+166,0,"data_out_wren",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+167,0,"use_buffered_data",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBus(c+168,0,"selected_data",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBit(c+169,0,"insert",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+170,0,"remove",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+171,0,"load",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+172,0,"flow",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+173,0,"fill",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+174,0,"flush",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+175,0,"unload",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBus(c+176,0,"state",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::INT, false,-1, 31,0);
    tracep->declBus(c+177,0,"state_next",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::INT, false,-1, 31,0);
    tracep->popPrefix();
    tracep->popPrefix();
    tracep->popPrefix();
    tracep->pushPrefix("rounding", VerilatedTracePrefixType::SCOPE_MODULE);
    tracep->pushPrefix("round_inst", VerilatedTracePrefixType::SCOPE_MODULE);
    tracep->declBus(c+602,0,"IN_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+598,0,"IN_FRAC_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+601,0,"OUT_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+598,0,"OUT_FRAC_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+178,0,"data_in",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 16,0);
    tracep->declBus(c+179,0,"data_out",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 15,0);
    tracep->declBus(c+604,0,"IN_INT_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+605,0,"OUT_INT_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+180,0,"MAX_POS",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1, 16,0);
    tracep->declBus(c+181,0,"MAX_NEG",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1, 16,0);
    tracep->declBus(c+182,0,"lsb_below",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1, 2,0);
    tracep->declBus(c+183,0,"input_data",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1, 15,0);
    tracep->declBit(c+184,0,"carry_in",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+185,0,"input_sign",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declQuad(c+186,0,"rounded_out_data",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1, 33,0);
    tracep->declQuad(c+188,0,"comp_rouded_out",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1, 33,0);
    tracep->popPrefix();
    tracep->popPrefix();
    tracep->popPrefix();
    tracep->pushPrefix("multi_col[1]", VerilatedTracePrefixType::SCOPE_MODULE);
    tracep->pushPrefix("dot_product_inst", VerilatedTracePrefixType::SCOPE_MODULE);
    tracep->declBus(c+599,0,"IN_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+598,0,"IN_SIZE",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+599,0,"WEIGHT_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+602,0,"OUT_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBit(c+190,0,"clk",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+191,0,"rst",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->pushPrefix("data_in", VerilatedTracePrefixType::ARRAY_UNPACKED);
    for (int i = 0; i < 2; ++i) {
        tracep->declBus(c+192+i*1,0,"",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, true,(i+0), 7,0);
    }
    tracep->popPrefix();
    tracep->declBit(c+194,0,"data_in_valid",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+195,0,"data_in_ready",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->pushPrefix("weight", VerilatedTracePrefixType::ARRAY_UNPACKED);
    for (int i = 0; i < 2; ++i) {
        tracep->declBus(c+196+i*1,0,"",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, true,(i+0), 7,0);
    }
    tracep->popPrefix();
    tracep->declBit(c+198,0,"weight_valid",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+199,0,"weight_ready",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBus(c+200,0,"data_out",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 16,0);
    tracep->declBit(c+201,0,"data_out_valid",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+202,0,"data_out_ready",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBus(c+601,0,"PRODUCT_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->pushPrefix("pv", VerilatedTracePrefixType::ARRAY_UNPACKED);
    for (int i = 0; i < 2; ++i) {
        tracep->declBus(c+203+i*1,0,"",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, true,(i+0), 15,0);
    }
    tracep->popPrefix();
    tracep->declBit(c+205,0,"pv_valid",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+206,0,"pv_ready",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBus(c+207,0,"sum",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1, 16,0);
    tracep->declBit(c+208,0,"sum_valid",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+209,0,"sum_ready",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->pushPrefix("fixed_adder_tree_inst", VerilatedTracePrefixType::SCOPE_MODULE);
    tracep->declBus(c+598,0,"IN_SIZE",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+601,0,"IN_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+602,0,"OUT_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBit(c+210,0,"clk",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+211,0,"rst",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->pushPrefix("data_in", VerilatedTracePrefixType::ARRAY_UNPACKED);
    for (int i = 0; i < 2; ++i) {
        tracep->declBus(c+212+i*1,0,"",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, true,(i+0), 15,0);
    }
    tracep->popPrefix();
    tracep->declBit(c+214,0,"data_in_valid",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+215,0,"data_in_ready",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBus(c+216,0,"data_out",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 16,0);
    tracep->declBit(c+217,0,"data_out_valid",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+218,0,"data_out_ready",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBus(c+600,0,"LEVELS",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->pushPrefix("gen_adder_tree", VerilatedTracePrefixType::SCOPE_MODULE);
    tracep->pushPrefix("data", VerilatedTracePrefixType::ARRAY_UNPACKED);
    for (int i = 0; i < 2; ++i) {
        tracep->declQuad(c+219+i*2,0,"",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, true,(i+0), 33,0);
    }
    tracep->popPrefix();
    tracep->pushPrefix("sum", VerilatedTracePrefixType::ARRAY_UNPACKED);
    for (int i = 0; i < 1; ++i) {
        tracep->declQuad(c+223+i*2,0,"",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, true,(i+0), 33,0);
    }
    tracep->popPrefix();
    tracep->pushPrefix("valid", VerilatedTracePrefixType::ARRAY_UNPACKED);
    for (int i = 0; i < 2; ++i) {
        tracep->declBit(c+225+i*1,0,"",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, true,(i+0));
    }
    tracep->popPrefix();
    tracep->pushPrefix("ready", VerilatedTracePrefixType::ARRAY_UNPACKED);
    for (int i = 0; i < 2; ++i) {
        tracep->declBit(c+227+i*1,0,"",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, true,(i+0));
    }
    tracep->popPrefix();
    tracep->pushPrefix("level[0]", VerilatedTracePrefixType::SCOPE_MODULE);
    tracep->declBus(c+598,0,"LEVEL_IN_SIZE",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+600,0,"LEVEL_OUT_SIZE",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+601,0,"LEVEL_IN_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+602,0,"LEVEL_OUT_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->pushPrefix("layer", VerilatedTracePrefixType::SCOPE_MODULE);
    tracep->declBus(c+598,0,"IN_SIZE",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+601,0,"IN_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+600,0,"SIGNED",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+602,0,"OUT_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+600,0,"OUT_SIZE",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+229,0,"data_in",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+230,0,"data_out",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 16,0);
    tracep->pushPrefix("data_in_unflat", VerilatedTracePrefixType::ARRAY_UNPACKED);
    for (int i = 0; i < 2; ++i) {
        tracep->declBus(c+231+i*1,0,"",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, true,(i+0), 15,0);
    }
    tracep->popPrefix();
    tracep->pushPrefix("data_out_unflat", VerilatedTracePrefixType::ARRAY_UNPACKED);
    for (int i = 0; i < 1; ++i) {
        tracep->declBus(c+233+i*1,0,"",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, true,(i+0), 16,0);
    }
    tracep->popPrefix();
    tracep->popPrefix();
    tracep->pushPrefix("register_slice", VerilatedTracePrefixType::SCOPE_MODULE);
    tracep->declBus(c+602,0,"DATA_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBit(c+234,0,"clk",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+235,0,"rst",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBus(c+236,0,"data_in",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 16,0);
    tracep->declBit(c+237,0,"data_in_valid",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+238,0,"data_in_ready",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBus(c+239,0,"data_out",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 16,0);
    tracep->declBit(c+240,0,"data_out_valid",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+241,0,"data_out_ready",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBus(c+242,0,"data_buffer_out",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1, 16,0);
    tracep->declBit(c+243,0,"data_buffer_wren",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+244,0,"data_out_wren",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+245,0,"use_buffered_data",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBus(c+246,0,"selected_data",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1, 16,0);
    tracep->declBit(c+247,0,"insert",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+248,0,"remove",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+249,0,"load",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+250,0,"flow",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+251,0,"fill",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+252,0,"flush",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+253,0,"unload",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBus(c+254,0,"state",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::INT, false,-1, 31,0);
    tracep->declBus(c+255,0,"state_next",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::INT, false,-1, 31,0);
    tracep->popPrefix();
    tracep->popPrefix();
    tracep->popPrefix();
    tracep->popPrefix();
    tracep->pushPrefix("fixed_vector_mult_inst", VerilatedTracePrefixType::SCOPE_MODULE);
    tracep->declBus(c+599,0,"IN_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+599,0,"WEIGHT_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+601,0,"OUT_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+598,0,"IN_SIZE",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBit(c+256,0,"clk",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+257,0,"rst",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->pushPrefix("data_in", VerilatedTracePrefixType::ARRAY_UNPACKED);
    for (int i = 0; i < 2; ++i) {
        tracep->declBus(c+258+i*1,0,"",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, true,(i+0), 7,0);
    }
    tracep->popPrefix();
    tracep->declBit(c+260,0,"data_in_valid",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+261,0,"data_in_ready",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->pushPrefix("weight", VerilatedTracePrefixType::ARRAY_UNPACKED);
    for (int i = 0; i < 2; ++i) {
        tracep->declBus(c+262+i*1,0,"",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, true,(i+0), 7,0);
    }
    tracep->popPrefix();
    tracep->declBit(c+264,0,"weight_valid",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+265,0,"weight_ready",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->pushPrefix("data_out", VerilatedTracePrefixType::ARRAY_UNPACKED);
    for (int i = 0; i < 2; ++i) {
        tracep->declBus(c+266+i*1,0,"",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, true,(i+0), 15,0);
    }
    tracep->popPrefix();
    tracep->declBit(c+268,0,"data_out_valid",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+269,0,"data_out_ready",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBus(c+601,0,"PRODUCT_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->pushPrefix("product_vector", VerilatedTracePrefixType::ARRAY_UNPACKED);
    for (int i = 0; i < 2; ++i) {
        tracep->declBus(c+270+i*1,0,"",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, true,(i+0), 15,0);
    }
    tracep->popPrefix();
    tracep->declBit(c+272,0,"product_data_in_valid",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+273,0,"product_data_in_ready",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+274,0,"product_data_out_valid",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+275,0,"product_data_out_ready",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBus(c+276,0,"product_data_in",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+277,0,"product_data_out",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->pushPrefix("join_inst", VerilatedTracePrefixType::SCOPE_MODULE);
    tracep->declBus(c+278,0,"data_in_valid",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 1,0);
    tracep->declBus(c+279,0,"data_in_ready",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 1,0);
    tracep->declBit(c+280,0,"data_out_valid",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+281,0,"data_out_ready",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->popPrefix();
    tracep->pushPrefix("parallel_mult[0]", VerilatedTracePrefixType::SCOPE_MODULE);
    tracep->pushPrefix("fixed_mult_inst", VerilatedTracePrefixType::SCOPE_MODULE);
    tracep->declBus(c+599,0,"IN_A_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+599,0,"IN_B_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+282,0,"data_a",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 7,0);
    tracep->declBus(c+283,0,"data_b",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 7,0);
    tracep->declBus(c+284,0,"product",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 15,0);
    tracep->popPrefix();
    tracep->popPrefix();
    tracep->pushPrefix("parallel_mult[1]", VerilatedTracePrefixType::SCOPE_MODULE);
    tracep->pushPrefix("fixed_mult_inst", VerilatedTracePrefixType::SCOPE_MODULE);
    tracep->declBus(c+599,0,"IN_A_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+599,0,"IN_B_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+285,0,"data_a",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 7,0);
    tracep->declBus(c+286,0,"data_b",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 7,0);
    tracep->declBus(c+287,0,"product",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 15,0);
    tracep->popPrefix();
    tracep->popPrefix();
    tracep->pushPrefix("register_slice", VerilatedTracePrefixType::SCOPE_MODULE);
    tracep->declBus(c+603,0,"DATA_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBit(c+288,0,"clk",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+289,0,"rst",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBus(c+290,0,"data_in",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBit(c+291,0,"data_in_valid",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+292,0,"data_in_ready",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBus(c+293,0,"data_out",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBit(c+294,0,"data_out_valid",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+295,0,"data_out_ready",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBus(c+296,0,"data_buffer_out",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBit(c+297,0,"data_buffer_wren",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+298,0,"data_out_wren",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+299,0,"use_buffered_data",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBus(c+300,0,"selected_data",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBit(c+301,0,"insert",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+302,0,"remove",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+303,0,"load",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+304,0,"flow",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+305,0,"fill",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+306,0,"flush",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+307,0,"unload",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBus(c+308,0,"state",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::INT, false,-1, 31,0);
    tracep->declBus(c+309,0,"state_next",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::INT, false,-1, 31,0);
    tracep->popPrefix();
    tracep->popPrefix();
    tracep->popPrefix();
    tracep->pushPrefix("rounding", VerilatedTracePrefixType::SCOPE_MODULE);
    tracep->pushPrefix("round_inst", VerilatedTracePrefixType::SCOPE_MODULE);
    tracep->declBus(c+602,0,"IN_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+598,0,"IN_FRAC_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+601,0,"OUT_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+598,0,"OUT_FRAC_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+310,0,"data_in",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 16,0);
    tracep->declBus(c+311,0,"data_out",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 15,0);
    tracep->declBus(c+604,0,"IN_INT_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+605,0,"OUT_INT_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+312,0,"MAX_POS",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1, 16,0);
    tracep->declBus(c+313,0,"MAX_NEG",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1, 16,0);
    tracep->declBus(c+314,0,"lsb_below",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1, 2,0);
    tracep->declBus(c+315,0,"input_data",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1, 15,0);
    tracep->declBit(c+316,0,"carry_in",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+317,0,"input_sign",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declQuad(c+318,0,"rounded_out_data",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1, 33,0);
    tracep->declQuad(c+320,0,"comp_rouded_out",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1, 33,0);
    tracep->popPrefix();
    tracep->popPrefix();
    tracep->popPrefix();
    tracep->popPrefix();
    tracep->pushPrefix("multi_row[1]", VerilatedTracePrefixType::SCOPE_MODULE);
    tracep->pushPrefix("multi_col[0]", VerilatedTracePrefixType::SCOPE_MODULE);
    tracep->pushPrefix("dot_product_inst", VerilatedTracePrefixType::SCOPE_MODULE);
    tracep->declBus(c+599,0,"IN_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+598,0,"IN_SIZE",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+599,0,"WEIGHT_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+602,0,"OUT_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBit(c+322,0,"clk",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+323,0,"rst",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->pushPrefix("data_in", VerilatedTracePrefixType::ARRAY_UNPACKED);
    for (int i = 0; i < 2; ++i) {
        tracep->declBus(c+324+i*1,0,"",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, true,(i+0), 7,0);
    }
    tracep->popPrefix();
    tracep->declBit(c+326,0,"data_in_valid",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+327,0,"data_in_ready",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->pushPrefix("weight", VerilatedTracePrefixType::ARRAY_UNPACKED);
    for (int i = 0; i < 2; ++i) {
        tracep->declBus(c+328+i*1,0,"",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, true,(i+0), 7,0);
    }
    tracep->popPrefix();
    tracep->declBit(c+330,0,"weight_valid",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+331,0,"weight_ready",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBus(c+332,0,"data_out",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 16,0);
    tracep->declBit(c+333,0,"data_out_valid",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+334,0,"data_out_ready",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBus(c+601,0,"PRODUCT_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->pushPrefix("pv", VerilatedTracePrefixType::ARRAY_UNPACKED);
    for (int i = 0; i < 2; ++i) {
        tracep->declBus(c+335+i*1,0,"",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, true,(i+0), 15,0);
    }
    tracep->popPrefix();
    tracep->declBit(c+337,0,"pv_valid",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+338,0,"pv_ready",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBus(c+339,0,"sum",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1, 16,0);
    tracep->declBit(c+340,0,"sum_valid",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+341,0,"sum_ready",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->pushPrefix("fixed_adder_tree_inst", VerilatedTracePrefixType::SCOPE_MODULE);
    tracep->declBus(c+598,0,"IN_SIZE",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+601,0,"IN_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+602,0,"OUT_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBit(c+342,0,"clk",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+343,0,"rst",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->pushPrefix("data_in", VerilatedTracePrefixType::ARRAY_UNPACKED);
    for (int i = 0; i < 2; ++i) {
        tracep->declBus(c+344+i*1,0,"",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, true,(i+0), 15,0);
    }
    tracep->popPrefix();
    tracep->declBit(c+346,0,"data_in_valid",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+347,0,"data_in_ready",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBus(c+348,0,"data_out",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 16,0);
    tracep->declBit(c+349,0,"data_out_valid",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+350,0,"data_out_ready",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBus(c+600,0,"LEVELS",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->pushPrefix("gen_adder_tree", VerilatedTracePrefixType::SCOPE_MODULE);
    tracep->pushPrefix("data", VerilatedTracePrefixType::ARRAY_UNPACKED);
    for (int i = 0; i < 2; ++i) {
        tracep->declQuad(c+351+i*2,0,"",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, true,(i+0), 33,0);
    }
    tracep->popPrefix();
    tracep->pushPrefix("sum", VerilatedTracePrefixType::ARRAY_UNPACKED);
    for (int i = 0; i < 1; ++i) {
        tracep->declQuad(c+355+i*2,0,"",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, true,(i+0), 33,0);
    }
    tracep->popPrefix();
    tracep->pushPrefix("valid", VerilatedTracePrefixType::ARRAY_UNPACKED);
    for (int i = 0; i < 2; ++i) {
        tracep->declBit(c+357+i*1,0,"",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, true,(i+0));
    }
    tracep->popPrefix();
    tracep->pushPrefix("ready", VerilatedTracePrefixType::ARRAY_UNPACKED);
    for (int i = 0; i < 2; ++i) {
        tracep->declBit(c+359+i*1,0,"",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, true,(i+0));
    }
    tracep->popPrefix();
    tracep->pushPrefix("level[0]", VerilatedTracePrefixType::SCOPE_MODULE);
    tracep->declBus(c+598,0,"LEVEL_IN_SIZE",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+600,0,"LEVEL_OUT_SIZE",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+601,0,"LEVEL_IN_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+602,0,"LEVEL_OUT_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->pushPrefix("layer", VerilatedTracePrefixType::SCOPE_MODULE);
    tracep->declBus(c+598,0,"IN_SIZE",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+601,0,"IN_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+600,0,"SIGNED",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+602,0,"OUT_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+600,0,"OUT_SIZE",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+361,0,"data_in",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+362,0,"data_out",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 16,0);
    tracep->pushPrefix("data_in_unflat", VerilatedTracePrefixType::ARRAY_UNPACKED);
    for (int i = 0; i < 2; ++i) {
        tracep->declBus(c+363+i*1,0,"",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, true,(i+0), 15,0);
    }
    tracep->popPrefix();
    tracep->pushPrefix("data_out_unflat", VerilatedTracePrefixType::ARRAY_UNPACKED);
    for (int i = 0; i < 1; ++i) {
        tracep->declBus(c+365+i*1,0,"",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, true,(i+0), 16,0);
    }
    tracep->popPrefix();
    tracep->popPrefix();
    tracep->pushPrefix("register_slice", VerilatedTracePrefixType::SCOPE_MODULE);
    tracep->declBus(c+602,0,"DATA_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBit(c+366,0,"clk",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+367,0,"rst",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBus(c+368,0,"data_in",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 16,0);
    tracep->declBit(c+369,0,"data_in_valid",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+370,0,"data_in_ready",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBus(c+371,0,"data_out",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 16,0);
    tracep->declBit(c+372,0,"data_out_valid",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+373,0,"data_out_ready",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBus(c+374,0,"data_buffer_out",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1, 16,0);
    tracep->declBit(c+375,0,"data_buffer_wren",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+376,0,"data_out_wren",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+377,0,"use_buffered_data",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBus(c+378,0,"selected_data",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1, 16,0);
    tracep->declBit(c+379,0,"insert",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+380,0,"remove",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+381,0,"load",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+382,0,"flow",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+383,0,"fill",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+384,0,"flush",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+385,0,"unload",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBus(c+386,0,"state",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::INT, false,-1, 31,0);
    tracep->declBus(c+387,0,"state_next",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::INT, false,-1, 31,0);
    tracep->popPrefix();
    tracep->popPrefix();
    tracep->popPrefix();
    tracep->popPrefix();
    tracep->pushPrefix("fixed_vector_mult_inst", VerilatedTracePrefixType::SCOPE_MODULE);
    tracep->declBus(c+599,0,"IN_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+599,0,"WEIGHT_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+601,0,"OUT_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+598,0,"IN_SIZE",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBit(c+388,0,"clk",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+389,0,"rst",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->pushPrefix("data_in", VerilatedTracePrefixType::ARRAY_UNPACKED);
    for (int i = 0; i < 2; ++i) {
        tracep->declBus(c+390+i*1,0,"",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, true,(i+0), 7,0);
    }
    tracep->popPrefix();
    tracep->declBit(c+392,0,"data_in_valid",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+393,0,"data_in_ready",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->pushPrefix("weight", VerilatedTracePrefixType::ARRAY_UNPACKED);
    for (int i = 0; i < 2; ++i) {
        tracep->declBus(c+394+i*1,0,"",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, true,(i+0), 7,0);
    }
    tracep->popPrefix();
    tracep->declBit(c+396,0,"weight_valid",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+397,0,"weight_ready",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->pushPrefix("data_out", VerilatedTracePrefixType::ARRAY_UNPACKED);
    for (int i = 0; i < 2; ++i) {
        tracep->declBus(c+398+i*1,0,"",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, true,(i+0), 15,0);
    }
    tracep->popPrefix();
    tracep->declBit(c+400,0,"data_out_valid",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+401,0,"data_out_ready",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBus(c+601,0,"PRODUCT_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->pushPrefix("product_vector", VerilatedTracePrefixType::ARRAY_UNPACKED);
    for (int i = 0; i < 2; ++i) {
        tracep->declBus(c+402+i*1,0,"",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, true,(i+0), 15,0);
    }
    tracep->popPrefix();
    tracep->declBit(c+404,0,"product_data_in_valid",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+405,0,"product_data_in_ready",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+406,0,"product_data_out_valid",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+407,0,"product_data_out_ready",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBus(c+408,0,"product_data_in",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+409,0,"product_data_out",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->pushPrefix("join_inst", VerilatedTracePrefixType::SCOPE_MODULE);
    tracep->declBus(c+410,0,"data_in_valid",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 1,0);
    tracep->declBus(c+411,0,"data_in_ready",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 1,0);
    tracep->declBit(c+412,0,"data_out_valid",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+413,0,"data_out_ready",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->popPrefix();
    tracep->pushPrefix("parallel_mult[0]", VerilatedTracePrefixType::SCOPE_MODULE);
    tracep->pushPrefix("fixed_mult_inst", VerilatedTracePrefixType::SCOPE_MODULE);
    tracep->declBus(c+599,0,"IN_A_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+599,0,"IN_B_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+414,0,"data_a",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 7,0);
    tracep->declBus(c+415,0,"data_b",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 7,0);
    tracep->declBus(c+416,0,"product",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 15,0);
    tracep->popPrefix();
    tracep->popPrefix();
    tracep->pushPrefix("parallel_mult[1]", VerilatedTracePrefixType::SCOPE_MODULE);
    tracep->pushPrefix("fixed_mult_inst", VerilatedTracePrefixType::SCOPE_MODULE);
    tracep->declBus(c+599,0,"IN_A_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+599,0,"IN_B_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+417,0,"data_a",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 7,0);
    tracep->declBus(c+418,0,"data_b",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 7,0);
    tracep->declBus(c+419,0,"product",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 15,0);
    tracep->popPrefix();
    tracep->popPrefix();
    tracep->pushPrefix("register_slice", VerilatedTracePrefixType::SCOPE_MODULE);
    tracep->declBus(c+603,0,"DATA_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBit(c+420,0,"clk",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+421,0,"rst",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBus(c+422,0,"data_in",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBit(c+423,0,"data_in_valid",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+424,0,"data_in_ready",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBus(c+425,0,"data_out",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBit(c+426,0,"data_out_valid",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+427,0,"data_out_ready",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBus(c+428,0,"data_buffer_out",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBit(c+429,0,"data_buffer_wren",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+430,0,"data_out_wren",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+431,0,"use_buffered_data",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBus(c+432,0,"selected_data",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBit(c+433,0,"insert",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+434,0,"remove",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+435,0,"load",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+436,0,"flow",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+437,0,"fill",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+438,0,"flush",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+439,0,"unload",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBus(c+440,0,"state",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::INT, false,-1, 31,0);
    tracep->declBus(c+441,0,"state_next",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::INT, false,-1, 31,0);
    tracep->popPrefix();
    tracep->popPrefix();
    tracep->popPrefix();
    tracep->pushPrefix("rounding", VerilatedTracePrefixType::SCOPE_MODULE);
    tracep->pushPrefix("round_inst", VerilatedTracePrefixType::SCOPE_MODULE);
    tracep->declBus(c+602,0,"IN_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+598,0,"IN_FRAC_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+601,0,"OUT_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+598,0,"OUT_FRAC_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+442,0,"data_in",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 16,0);
    tracep->declBus(c+443,0,"data_out",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 15,0);
    tracep->declBus(c+604,0,"IN_INT_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+605,0,"OUT_INT_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+444,0,"MAX_POS",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1, 16,0);
    tracep->declBus(c+445,0,"MAX_NEG",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1, 16,0);
    tracep->declBus(c+446,0,"lsb_below",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1, 2,0);
    tracep->declBus(c+447,0,"input_data",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1, 15,0);
    tracep->declBit(c+448,0,"carry_in",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+449,0,"input_sign",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declQuad(c+450,0,"rounded_out_data",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1, 33,0);
    tracep->declQuad(c+452,0,"comp_rouded_out",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1, 33,0);
    tracep->popPrefix();
    tracep->popPrefix();
    tracep->popPrefix();
    tracep->pushPrefix("multi_col[1]", VerilatedTracePrefixType::SCOPE_MODULE);
    tracep->pushPrefix("dot_product_inst", VerilatedTracePrefixType::SCOPE_MODULE);
    tracep->declBus(c+599,0,"IN_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+598,0,"IN_SIZE",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+599,0,"WEIGHT_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+602,0,"OUT_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBit(c+454,0,"clk",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+455,0,"rst",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->pushPrefix("data_in", VerilatedTracePrefixType::ARRAY_UNPACKED);
    for (int i = 0; i < 2; ++i) {
        tracep->declBus(c+456+i*1,0,"",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, true,(i+0), 7,0);
    }
    tracep->popPrefix();
    tracep->declBit(c+458,0,"data_in_valid",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+459,0,"data_in_ready",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->pushPrefix("weight", VerilatedTracePrefixType::ARRAY_UNPACKED);
    for (int i = 0; i < 2; ++i) {
        tracep->declBus(c+460+i*1,0,"",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, true,(i+0), 7,0);
    }
    tracep->popPrefix();
    tracep->declBit(c+462,0,"weight_valid",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+463,0,"weight_ready",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBus(c+464,0,"data_out",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 16,0);
    tracep->declBit(c+465,0,"data_out_valid",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+466,0,"data_out_ready",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBus(c+601,0,"PRODUCT_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->pushPrefix("pv", VerilatedTracePrefixType::ARRAY_UNPACKED);
    for (int i = 0; i < 2; ++i) {
        tracep->declBus(c+467+i*1,0,"",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, true,(i+0), 15,0);
    }
    tracep->popPrefix();
    tracep->declBit(c+469,0,"pv_valid",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+470,0,"pv_ready",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBus(c+471,0,"sum",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1, 16,0);
    tracep->declBit(c+472,0,"sum_valid",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+473,0,"sum_ready",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->pushPrefix("fixed_adder_tree_inst", VerilatedTracePrefixType::SCOPE_MODULE);
    tracep->declBus(c+598,0,"IN_SIZE",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+601,0,"IN_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+602,0,"OUT_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBit(c+474,0,"clk",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+475,0,"rst",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->pushPrefix("data_in", VerilatedTracePrefixType::ARRAY_UNPACKED);
    for (int i = 0; i < 2; ++i) {
        tracep->declBus(c+476+i*1,0,"",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, true,(i+0), 15,0);
    }
    tracep->popPrefix();
    tracep->declBit(c+478,0,"data_in_valid",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+479,0,"data_in_ready",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBus(c+480,0,"data_out",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 16,0);
    tracep->declBit(c+481,0,"data_out_valid",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+482,0,"data_out_ready",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBus(c+600,0,"LEVELS",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->pushPrefix("gen_adder_tree", VerilatedTracePrefixType::SCOPE_MODULE);
    tracep->pushPrefix("data", VerilatedTracePrefixType::ARRAY_UNPACKED);
    for (int i = 0; i < 2; ++i) {
        tracep->declQuad(c+483+i*2,0,"",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, true,(i+0), 33,0);
    }
    tracep->popPrefix();
    tracep->pushPrefix("sum", VerilatedTracePrefixType::ARRAY_UNPACKED);
    for (int i = 0; i < 1; ++i) {
        tracep->declQuad(c+487+i*2,0,"",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, true,(i+0), 33,0);
    }
    tracep->popPrefix();
    tracep->pushPrefix("valid", VerilatedTracePrefixType::ARRAY_UNPACKED);
    for (int i = 0; i < 2; ++i) {
        tracep->declBit(c+489+i*1,0,"",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, true,(i+0));
    }
    tracep->popPrefix();
    tracep->pushPrefix("ready", VerilatedTracePrefixType::ARRAY_UNPACKED);
    for (int i = 0; i < 2; ++i) {
        tracep->declBit(c+491+i*1,0,"",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, true,(i+0));
    }
    tracep->popPrefix();
    tracep->pushPrefix("level[0]", VerilatedTracePrefixType::SCOPE_MODULE);
    tracep->declBus(c+598,0,"LEVEL_IN_SIZE",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+600,0,"LEVEL_OUT_SIZE",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+601,0,"LEVEL_IN_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+602,0,"LEVEL_OUT_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->pushPrefix("layer", VerilatedTracePrefixType::SCOPE_MODULE);
    tracep->declBus(c+598,0,"IN_SIZE",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+601,0,"IN_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+600,0,"SIGNED",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+602,0,"OUT_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+600,0,"OUT_SIZE",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+493,0,"data_in",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+494,0,"data_out",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 16,0);
    tracep->pushPrefix("data_in_unflat", VerilatedTracePrefixType::ARRAY_UNPACKED);
    for (int i = 0; i < 2; ++i) {
        tracep->declBus(c+495+i*1,0,"",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, true,(i+0), 15,0);
    }
    tracep->popPrefix();
    tracep->pushPrefix("data_out_unflat", VerilatedTracePrefixType::ARRAY_UNPACKED);
    for (int i = 0; i < 1; ++i) {
        tracep->declBus(c+497+i*1,0,"",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, true,(i+0), 16,0);
    }
    tracep->popPrefix();
    tracep->popPrefix();
    tracep->pushPrefix("register_slice", VerilatedTracePrefixType::SCOPE_MODULE);
    tracep->declBus(c+602,0,"DATA_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBit(c+498,0,"clk",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+499,0,"rst",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBus(c+500,0,"data_in",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 16,0);
    tracep->declBit(c+501,0,"data_in_valid",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+502,0,"data_in_ready",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBus(c+503,0,"data_out",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 16,0);
    tracep->declBit(c+504,0,"data_out_valid",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+505,0,"data_out_ready",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBus(c+506,0,"data_buffer_out",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1, 16,0);
    tracep->declBit(c+507,0,"data_buffer_wren",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+508,0,"data_out_wren",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+509,0,"use_buffered_data",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBus(c+510,0,"selected_data",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1, 16,0);
    tracep->declBit(c+511,0,"insert",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+512,0,"remove",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+513,0,"load",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+514,0,"flow",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+515,0,"fill",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+516,0,"flush",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+517,0,"unload",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBus(c+518,0,"state",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::INT, false,-1, 31,0);
    tracep->declBus(c+519,0,"state_next",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::INT, false,-1, 31,0);
    tracep->popPrefix();
    tracep->popPrefix();
    tracep->popPrefix();
    tracep->popPrefix();
    tracep->pushPrefix("fixed_vector_mult_inst", VerilatedTracePrefixType::SCOPE_MODULE);
    tracep->declBus(c+599,0,"IN_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+599,0,"WEIGHT_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+601,0,"OUT_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+598,0,"IN_SIZE",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBit(c+520,0,"clk",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+521,0,"rst",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->pushPrefix("data_in", VerilatedTracePrefixType::ARRAY_UNPACKED);
    for (int i = 0; i < 2; ++i) {
        tracep->declBus(c+522+i*1,0,"",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, true,(i+0), 7,0);
    }
    tracep->popPrefix();
    tracep->declBit(c+524,0,"data_in_valid",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+525,0,"data_in_ready",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->pushPrefix("weight", VerilatedTracePrefixType::ARRAY_UNPACKED);
    for (int i = 0; i < 2; ++i) {
        tracep->declBus(c+526+i*1,0,"",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, true,(i+0), 7,0);
    }
    tracep->popPrefix();
    tracep->declBit(c+528,0,"weight_valid",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+529,0,"weight_ready",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->pushPrefix("data_out", VerilatedTracePrefixType::ARRAY_UNPACKED);
    for (int i = 0; i < 2; ++i) {
        tracep->declBus(c+530+i*1,0,"",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, true,(i+0), 15,0);
    }
    tracep->popPrefix();
    tracep->declBit(c+532,0,"data_out_valid",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+533,0,"data_out_ready",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBus(c+601,0,"PRODUCT_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->pushPrefix("product_vector", VerilatedTracePrefixType::ARRAY_UNPACKED);
    for (int i = 0; i < 2; ++i) {
        tracep->declBus(c+534+i*1,0,"",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, true,(i+0), 15,0);
    }
    tracep->popPrefix();
    tracep->declBit(c+536,0,"product_data_in_valid",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+537,0,"product_data_in_ready",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+538,0,"product_data_out_valid",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+539,0,"product_data_out_ready",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBus(c+540,0,"product_data_in",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+541,0,"product_data_out",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->pushPrefix("join_inst", VerilatedTracePrefixType::SCOPE_MODULE);
    tracep->declBus(c+542,0,"data_in_valid",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 1,0);
    tracep->declBus(c+543,0,"data_in_ready",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 1,0);
    tracep->declBit(c+544,0,"data_out_valid",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+545,0,"data_out_ready",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->popPrefix();
    tracep->pushPrefix("parallel_mult[0]", VerilatedTracePrefixType::SCOPE_MODULE);
    tracep->pushPrefix("fixed_mult_inst", VerilatedTracePrefixType::SCOPE_MODULE);
    tracep->declBus(c+599,0,"IN_A_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+599,0,"IN_B_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+546,0,"data_a",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 7,0);
    tracep->declBus(c+547,0,"data_b",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 7,0);
    tracep->declBus(c+548,0,"product",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 15,0);
    tracep->popPrefix();
    tracep->popPrefix();
    tracep->pushPrefix("parallel_mult[1]", VerilatedTracePrefixType::SCOPE_MODULE);
    tracep->pushPrefix("fixed_mult_inst", VerilatedTracePrefixType::SCOPE_MODULE);
    tracep->declBus(c+599,0,"IN_A_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+599,0,"IN_B_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+549,0,"data_a",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 7,0);
    tracep->declBus(c+550,0,"data_b",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 7,0);
    tracep->declBus(c+551,0,"product",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 15,0);
    tracep->popPrefix();
    tracep->popPrefix();
    tracep->pushPrefix("register_slice", VerilatedTracePrefixType::SCOPE_MODULE);
    tracep->declBus(c+603,0,"DATA_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBit(c+552,0,"clk",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+553,0,"rst",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBus(c+554,0,"data_in",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBit(c+555,0,"data_in_valid",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+556,0,"data_in_ready",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBus(c+557,0,"data_out",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBit(c+558,0,"data_out_valid",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+559,0,"data_out_ready",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBus(c+560,0,"data_buffer_out",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBit(c+561,0,"data_buffer_wren",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+562,0,"data_out_wren",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+563,0,"use_buffered_data",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBus(c+564,0,"selected_data",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBit(c+565,0,"insert",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+566,0,"remove",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+567,0,"load",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+568,0,"flow",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+569,0,"fill",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+570,0,"flush",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+571,0,"unload",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBus(c+572,0,"state",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::INT, false,-1, 31,0);
    tracep->declBus(c+573,0,"state_next",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::INT, false,-1, 31,0);
    tracep->popPrefix();
    tracep->popPrefix();
    tracep->popPrefix();
    tracep->pushPrefix("rounding", VerilatedTracePrefixType::SCOPE_MODULE);
    tracep->pushPrefix("round_inst", VerilatedTracePrefixType::SCOPE_MODULE);
    tracep->declBus(c+602,0,"IN_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+598,0,"IN_FRAC_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+601,0,"OUT_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+598,0,"OUT_FRAC_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+574,0,"data_in",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 16,0);
    tracep->declBus(c+575,0,"data_out",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 15,0);
    tracep->declBus(c+604,0,"IN_INT_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+605,0,"OUT_INT_WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+576,0,"MAX_POS",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1, 16,0);
    tracep->declBus(c+577,0,"MAX_NEG",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1, 16,0);
    tracep->declBus(c+578,0,"lsb_below",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1, 2,0);
    tracep->declBus(c+579,0,"input_data",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1, 15,0);
    tracep->declBit(c+580,0,"carry_in",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+581,0,"input_sign",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declQuad(c+582,0,"rounded_out_data",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1, 33,0);
    tracep->declQuad(c+584,0,"comp_rouded_out",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, false,-1, 33,0);
    tracep->popPrefix();
    tracep->popPrefix();
    tracep->popPrefix();
    tracep->popPrefix();
    tracep->pushPrefix("sync_handshake", VerilatedTracePrefixType::SCOPE_MODULE);
    tracep->declBus(c+586,0,"data_in_valid",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 1,0);
    tracep->declBus(c+587,0,"data_in_ready",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 1,0);
    tracep->declBit(c+588,0,"data_out_valid",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+589,0,"data_out_ready",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->popPrefix();
    tracep->pushPrefix("y_transpose", VerilatedTracePrefixType::SCOPE_MODULE);
    tracep->declBus(c+599,0,"WIDTH",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+598,0,"DIM0",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+598,0,"DIM1",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::PARAMETER, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->pushPrefix("in_data", VerilatedTracePrefixType::ARRAY_UNPACKED);
    for (int i = 0; i < 4; ++i) {
        tracep->declBus(c+590+i*1,0,"",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, true,(i+0), 7,0);
    }
    tracep->popPrefix();
    tracep->pushPrefix("out_data", VerilatedTracePrefixType::ARRAY_UNPACKED);
    for (int i = 0; i < 4; ++i) {
        tracep->declBus(c+594+i*1,0,"",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, true,(i+0), 7,0);
    }
    tracep->popPrefix();
    tracep->popPrefix();
    tracep->popPrefix();
}

VL_ATTR_COLD void Vtop___024root__trace_init_top(Vtop___024root* vlSelf, VerilatedVcd* tracep) {
    (void)vlSelf;  // Prevent unused variable warning
    Vtop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root__trace_init_top\n"); );
    auto &vlSelfRef = std::ref(*vlSelf).get();
    // Body
    Vtop___024root__trace_init_sub__TOP__0(vlSelf, tracep);
}

VL_ATTR_COLD void Vtop___024root__trace_const_0(void* voidSelf, VerilatedVcd::Buffer* bufp);
VL_ATTR_COLD void Vtop___024root__trace_full_0(void* voidSelf, VerilatedVcd::Buffer* bufp);
void Vtop___024root__trace_chg_0(void* voidSelf, VerilatedVcd::Buffer* bufp);
void Vtop___024root__trace_cleanup(void* voidSelf, VerilatedVcd* /*unused*/);

VL_ATTR_COLD void Vtop___024root__trace_register(Vtop___024root* vlSelf, VerilatedVcd* tracep) {
    (void)vlSelf;  // Prevent unused variable warning
    Vtop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root__trace_register\n"); );
    auto &vlSelfRef = std::ref(*vlSelf).get();
    // Body
    tracep->addConstCb(&Vtop___024root__trace_const_0, 0U, vlSelf);
    tracep->addFullCb(&Vtop___024root__trace_full_0, 0U, vlSelf);
    tracep->addChgCb(&Vtop___024root__trace_chg_0, 0U, vlSelf);
    tracep->addCleanupCb(&Vtop___024root__trace_cleanup, vlSelf);
}

VL_ATTR_COLD void Vtop___024root__trace_const_0_sub_0(Vtop___024root* vlSelf, VerilatedVcd::Buffer* bufp);

VL_ATTR_COLD void Vtop___024root__trace_const_0(void* voidSelf, VerilatedVcd::Buffer* bufp) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root__trace_const_0\n"); );
    // Init
    Vtop___024root* const __restrict vlSelf VL_ATTR_UNUSED = static_cast<Vtop___024root*>(voidSelf);
    Vtop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    // Body
    Vtop___024root__trace_const_0_sub_0((&vlSymsp->TOP), bufp);
}

VL_ATTR_COLD void Vtop___024root__trace_const_0_sub_0(Vtop___024root* vlSelf, VerilatedVcd::Buffer* bufp) {
    (void)vlSelf;  // Prevent unused variable warning
    Vtop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root__trace_const_0_sub_0\n"); );
    auto &vlSelfRef = std::ref(*vlSelf).get();
    // Init
    uint32_t* const oldp VL_ATTR_UNUSED = bufp->oldp(vlSymsp->__Vm_baseCode);
    // Body
    bufp->fullIData(oldp+598,(2U),32);
    bufp->fullIData(oldp+599,(8U),32);
    bufp->fullIData(oldp+600,(1U),32);
    bufp->fullIData(oldp+601,(0x10U),32);
    bufp->fullIData(oldp+602,(0x11U),32);
    bufp->fullIData(oldp+603,(0x20U),32);
    bufp->fullIData(oldp+604,(0xfU),32);
    bufp->fullIData(oldp+605,(0xeU),32);
}

VL_ATTR_COLD void Vtop___024root__trace_full_0_sub_0(Vtop___024root* vlSelf, VerilatedVcd::Buffer* bufp);

VL_ATTR_COLD void Vtop___024root__trace_full_0(void* voidSelf, VerilatedVcd::Buffer* bufp) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root__trace_full_0\n"); );
    // Init
    Vtop___024root* const __restrict vlSelf VL_ATTR_UNUSED = static_cast<Vtop___024root*>(voidSelf);
    Vtop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    // Body
    Vtop___024root__trace_full_0_sub_0((&vlSymsp->TOP), bufp);
}

VL_ATTR_COLD void Vtop___024root__trace_full_0_sub_0(Vtop___024root* vlSelf, VerilatedVcd::Buffer* bufp) {
    (void)vlSelf;  // Prevent unused variable warning
    Vtop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root__trace_full_0_sub_0\n"); );
    auto &vlSelfRef = std::ref(*vlSelf).get();
    // Init
    uint32_t* const oldp VL_ATTR_UNUSED = bufp->oldp(vlSymsp->__Vm_baseCode);
    // Body
    bufp->fullBit(oldp+1,(vlSelfRef.clk));
    bufp->fullBit(oldp+2,(vlSelfRef.rst));
    bufp->fullCData(oldp+3,(vlSelfRef.x_data[0]),8);
    bufp->fullCData(oldp+4,(vlSelfRef.x_data[1]),8);
    bufp->fullCData(oldp+5,(vlSelfRef.x_data[2]),8);
    bufp->fullCData(oldp+6,(vlSelfRef.x_data[3]),8);
    bufp->fullBit(oldp+7,(vlSelfRef.x_valid));
    bufp->fullBit(oldp+8,(vlSelfRef.x_ready));
    bufp->fullCData(oldp+9,(vlSelfRef.y_data[0]),8);
    bufp->fullCData(oldp+10,(vlSelfRef.y_data[1]),8);
    bufp->fullCData(oldp+11,(vlSelfRef.y_data[2]),8);
    bufp->fullCData(oldp+12,(vlSelfRef.y_data[3]),8);
    bufp->fullBit(oldp+13,(vlSelfRef.y_valid));
    bufp->fullBit(oldp+14,(vlSelfRef.y_ready));
    bufp->fullSData(oldp+15,(vlSelfRef.out_data[0]),16);
    bufp->fullSData(oldp+16,(vlSelfRef.out_data[1]),16);
    bufp->fullSData(oldp+17,(vlSelfRef.out_data[2]),16);
    bufp->fullSData(oldp+18,(vlSelfRef.out_data[3]),16);
    bufp->fullBit(oldp+19,(vlSelfRef.out_valid));
    bufp->fullBit(oldp+20,(vlSelfRef.out_ready));
    bufp->fullBit(oldp+21,(vlSelfRef.simple_matmul__DOT__clk));
    bufp->fullBit(oldp+22,(vlSelfRef.simple_matmul__DOT__rst));
    bufp->fullCData(oldp+23,(vlSelfRef.simple_matmul__DOT__x_data[0]),8);
    bufp->fullCData(oldp+24,(vlSelfRef.simple_matmul__DOT__x_data[1]),8);
    bufp->fullCData(oldp+25,(vlSelfRef.simple_matmul__DOT__x_data[2]),8);
    bufp->fullCData(oldp+26,(vlSelfRef.simple_matmul__DOT__x_data[3]),8);
    bufp->fullBit(oldp+27,(vlSelfRef.simple_matmul__DOT__x_valid));
    bufp->fullBit(oldp+28,(vlSelfRef.simple_matmul__DOT__x_ready));
    bufp->fullCData(oldp+29,(vlSelfRef.simple_matmul__DOT__y_data[0]),8);
    bufp->fullCData(oldp+30,(vlSelfRef.simple_matmul__DOT__y_data[1]),8);
    bufp->fullCData(oldp+31,(vlSelfRef.simple_matmul__DOT__y_data[2]),8);
    bufp->fullCData(oldp+32,(vlSelfRef.simple_matmul__DOT__y_data[3]),8);
    bufp->fullBit(oldp+33,(vlSelfRef.simple_matmul__DOT__y_valid));
    bufp->fullBit(oldp+34,(vlSelfRef.simple_matmul__DOT__y_ready));
    bufp->fullSData(oldp+35,(vlSelfRef.simple_matmul__DOT__out_data[0]),16);
    bufp->fullSData(oldp+36,(vlSelfRef.simple_matmul__DOT__out_data[1]),16);
    bufp->fullSData(oldp+37,(vlSelfRef.simple_matmul__DOT__out_data[2]),16);
    bufp->fullSData(oldp+38,(vlSelfRef.simple_matmul__DOT__out_data[3]),16);
    bufp->fullBit(oldp+39,(vlSelfRef.simple_matmul__DOT__out_valid));
    bufp->fullBit(oldp+40,(vlSelfRef.simple_matmul__DOT__out_ready));
    bufp->fullCData(oldp+41,(vlSelfRef.simple_matmul__DOT__y_data_transpose[0]),8);
    bufp->fullCData(oldp+42,(vlSelfRef.simple_matmul__DOT__y_data_transpose[1]),8);
    bufp->fullCData(oldp+43,(vlSelfRef.simple_matmul__DOT__y_data_transpose[2]),8);
    bufp->fullCData(oldp+44,(vlSelfRef.simple_matmul__DOT__y_data_transpose[3]),8);
    bufp->fullBit(oldp+45,(vlSelfRef.simple_matmul__DOT__dot_product_ready));
    bufp->fullBit(oldp+46,(vlSelfRef.simple_matmul__DOT__inputs_valid));
    bufp->fullBit(oldp+47,(vlSelfRef.simple_matmul__DOT__inputs_ready));
    bufp->fullCData(oldp+48,(vlSelfRef.simple_matmul__DOT__dot_product_valid),4);
    bufp->fullCData(oldp+49,(vlSelfRef.simple_matmul__DOT__sync_ready),4);
    bufp->fullIData(oldp+50,(vlSelfRef.simple_matmul__DOT__dot_product_data_out[0]),17);
    bufp->fullIData(oldp+51,(vlSelfRef.simple_matmul__DOT__dot_product_data_out[1]),17);
    bufp->fullIData(oldp+52,(vlSelfRef.simple_matmul__DOT__dot_product_data_out[2]),17);
    bufp->fullIData(oldp+53,(vlSelfRef.simple_matmul__DOT__dot_product_data_out[3]),17);
    bufp->fullSData(oldp+54,(vlSelfRef.simple_matmul__DOT__rounded_dot_product[0]),16);
    bufp->fullSData(oldp+55,(vlSelfRef.simple_matmul__DOT__rounded_dot_product[1]),16);
    bufp->fullSData(oldp+56,(vlSelfRef.simple_matmul__DOT__rounded_dot_product[2]),16);
    bufp->fullSData(oldp+57,(vlSelfRef.simple_matmul__DOT__rounded_dot_product[3]),16);
    bufp->fullBit(oldp+58,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__clk));
    bufp->fullBit(oldp+59,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__rst));
    bufp->fullCData(oldp+60,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__data_in[0]),8);
    bufp->fullCData(oldp+61,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__data_in[1]),8);
    bufp->fullBit(oldp+62,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__data_in_valid));
    bufp->fullBit(oldp+63,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__data_in_ready));
    bufp->fullCData(oldp+64,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__weight[0]),8);
    bufp->fullCData(oldp+65,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__weight[1]),8);
    bufp->fullBit(oldp+66,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__weight_valid));
    bufp->fullBit(oldp+67,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__weight_ready));
    bufp->fullIData(oldp+68,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__data_out),17);
    bufp->fullBit(oldp+69,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__data_out_valid));
    bufp->fullBit(oldp+70,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__data_out_ready));
    bufp->fullSData(oldp+71,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__pv[0]),16);
    bufp->fullSData(oldp+72,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__pv[1]),16);
    bufp->fullBit(oldp+73,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__pv_valid));
    bufp->fullBit(oldp+74,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__pv_ready));
    bufp->fullIData(oldp+75,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__sum),17);
    bufp->fullBit(oldp+76,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__sum_valid));
    bufp->fullBit(oldp+77,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__sum_ready));
    bufp->fullBit(oldp+78,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__clk));
    bufp->fullBit(oldp+79,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__rst));
    bufp->fullSData(oldp+80,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__data_in[0]),16);
    bufp->fullSData(oldp+81,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__data_in[1]),16);
    bufp->fullBit(oldp+82,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__data_in_valid));
    bufp->fullBit(oldp+83,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__data_in_ready));
    bufp->fullIData(oldp+84,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__data_out),17);
    bufp->fullBit(oldp+85,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__data_out_valid));
    bufp->fullBit(oldp+86,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__data_out_ready));
    bufp->fullQData(oldp+87,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__data[0]),34);
    bufp->fullQData(oldp+89,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__data[1]),34);
    bufp->fullQData(oldp+91,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__sum[0]),34);
    bufp->fullBit(oldp+93,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__valid[0]));
    bufp->fullBit(oldp+94,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__valid[1]));
    bufp->fullBit(oldp+95,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__ready[0]));
    bufp->fullBit(oldp+96,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__ready[1]));
    bufp->fullIData(oldp+97,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__layer__DOT__data_in),32);
    bufp->fullIData(oldp+98,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__layer__DOT__data_out),17);
    bufp->fullSData(oldp+99,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__layer__DOT__data_in_unflat[0]),16);
    bufp->fullSData(oldp+100,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__layer__DOT__data_in_unflat[1]),16);
    bufp->fullIData(oldp+101,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__layer__DOT__data_out_unflat[0]),17);
    bufp->fullBit(oldp+102,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__clk));
    bufp->fullBit(oldp+103,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__rst));
    bufp->fullIData(oldp+104,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__data_in),17);
    bufp->fullBit(oldp+105,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__data_in_valid));
    bufp->fullBit(oldp+106,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__data_in_ready));
    bufp->fullIData(oldp+107,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__data_out),17);
    bufp->fullBit(oldp+108,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__data_out_valid));
    bufp->fullBit(oldp+109,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__data_out_ready));
    bufp->fullIData(oldp+110,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__data_buffer_out),17);
    bufp->fullBit(oldp+111,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__data_buffer_wren));
    bufp->fullBit(oldp+112,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__data_out_wren));
    bufp->fullBit(oldp+113,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__use_buffered_data));
    bufp->fullIData(oldp+114,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__selected_data),17);
    bufp->fullBit(oldp+115,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__insert));
    bufp->fullBit(oldp+116,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__remove));
    bufp->fullBit(oldp+117,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__load));
    bufp->fullBit(oldp+118,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__flow));
    bufp->fullBit(oldp+119,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__fill));
    bufp->fullBit(oldp+120,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__flush));
    bufp->fullBit(oldp+121,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__unload));
    bufp->fullIData(oldp+122,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__state),32);
    bufp->fullIData(oldp+123,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__state_next),32);
    bufp->fullBit(oldp+124,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__clk));
    bufp->fullBit(oldp+125,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__rst));
    bufp->fullCData(oldp+126,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__data_in[0]),8);
    bufp->fullCData(oldp+127,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__data_in[1]),8);
    bufp->fullBit(oldp+128,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__data_in_valid));
    bufp->fullBit(oldp+129,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__data_in_ready));
    bufp->fullCData(oldp+130,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__weight[0]),8);
    bufp->fullCData(oldp+131,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__weight[1]),8);
    bufp->fullBit(oldp+132,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__weight_valid));
    bufp->fullBit(oldp+133,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__weight_ready));
    bufp->fullSData(oldp+134,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__data_out[0]),16);
    bufp->fullSData(oldp+135,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__data_out[1]),16);
    bufp->fullBit(oldp+136,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__data_out_valid));
    bufp->fullBit(oldp+137,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__data_out_ready));
    bufp->fullSData(oldp+138,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__product_vector[0]),16);
    bufp->fullSData(oldp+139,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__product_vector[1]),16);
    bufp->fullBit(oldp+140,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__product_data_in_valid));
    bufp->fullBit(oldp+141,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__product_data_in_ready));
    bufp->fullBit(oldp+142,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__product_data_out_valid));
    bufp->fullBit(oldp+143,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__product_data_out_ready));
    bufp->fullIData(oldp+144,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__product_data_in),32);
    bufp->fullIData(oldp+145,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__product_data_out),32);
    bufp->fullCData(oldp+146,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__join_inst__DOT__data_in_valid),2);
    bufp->fullCData(oldp+147,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__join_inst__DOT__data_in_ready),2);
    bufp->fullBit(oldp+148,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__join_inst__DOT__data_out_valid));
    bufp->fullBit(oldp+149,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__join_inst__DOT__data_out_ready));
    bufp->fullCData(oldp+150,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__parallel_mult__BRA__0__KET____DOT__fixed_mult_inst__DOT__data_a),8);
    bufp->fullCData(oldp+151,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__parallel_mult__BRA__0__KET____DOT__fixed_mult_inst__DOT__data_b),8);
    bufp->fullSData(oldp+152,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__parallel_mult__BRA__0__KET____DOT__fixed_mult_inst__DOT__product),16);
    bufp->fullCData(oldp+153,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__parallel_mult__BRA__1__KET____DOT__fixed_mult_inst__DOT__data_a),8);
    bufp->fullCData(oldp+154,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__parallel_mult__BRA__1__KET____DOT__fixed_mult_inst__DOT__data_b),8);
    bufp->fullSData(oldp+155,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__parallel_mult__BRA__1__KET____DOT__fixed_mult_inst__DOT__product),16);
    bufp->fullBit(oldp+156,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__clk));
    bufp->fullBit(oldp+157,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__rst));
    bufp->fullIData(oldp+158,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__data_in),32);
    bufp->fullBit(oldp+159,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__data_in_valid));
    bufp->fullBit(oldp+160,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__data_in_ready));
    bufp->fullIData(oldp+161,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__data_out),32);
    bufp->fullBit(oldp+162,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__data_out_valid));
    bufp->fullBit(oldp+163,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__data_out_ready));
    bufp->fullIData(oldp+164,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__data_buffer_out),32);
    bufp->fullBit(oldp+165,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__data_buffer_wren));
    bufp->fullBit(oldp+166,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__data_out_wren));
    bufp->fullBit(oldp+167,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__use_buffered_data));
    bufp->fullIData(oldp+168,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__selected_data),32);
    bufp->fullBit(oldp+169,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__insert));
    bufp->fullBit(oldp+170,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__remove));
    bufp->fullBit(oldp+171,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__load));
    bufp->fullBit(oldp+172,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__flow));
    bufp->fullBit(oldp+173,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__fill));
    bufp->fullBit(oldp+174,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__flush));
    bufp->fullBit(oldp+175,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__unload));
    bufp->fullIData(oldp+176,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__state),32);
    bufp->fullIData(oldp+177,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__state_next),32);
    bufp->fullIData(oldp+178,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__rounding__DOT__round_inst__DOT__data_in),17);
    bufp->fullSData(oldp+179,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__rounding__DOT__round_inst__DOT__data_out),16);
    bufp->fullIData(oldp+180,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__rounding__DOT__round_inst__DOT__MAX_POS),17);
    bufp->fullIData(oldp+181,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__rounding__DOT__round_inst__DOT__MAX_NEG),17);
    bufp->fullCData(oldp+182,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__rounding__DOT__round_inst__DOT__lsb_below),3);
    bufp->fullSData(oldp+183,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__rounding__DOT__round_inst__DOT__input_data),16);
    bufp->fullBit(oldp+184,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__rounding__DOT__round_inst__DOT__carry_in));
    bufp->fullBit(oldp+185,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__rounding__DOT__round_inst__DOT__input_sign));
    bufp->fullQData(oldp+186,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__rounding__DOT__round_inst__DOT__rounded_out_data),34);
    bufp->fullQData(oldp+188,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__rounding__DOT__round_inst__DOT__comp_rouded_out),34);
    bufp->fullBit(oldp+190,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__clk));
    bufp->fullBit(oldp+191,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__rst));
    bufp->fullCData(oldp+192,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__data_in[0]),8);
    bufp->fullCData(oldp+193,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__data_in[1]),8);
    bufp->fullBit(oldp+194,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__data_in_valid));
    bufp->fullBit(oldp+195,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__data_in_ready));
    bufp->fullCData(oldp+196,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__weight[0]),8);
    bufp->fullCData(oldp+197,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__weight[1]),8);
    bufp->fullBit(oldp+198,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__weight_valid));
    bufp->fullBit(oldp+199,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__weight_ready));
    bufp->fullIData(oldp+200,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__data_out),17);
    bufp->fullBit(oldp+201,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__data_out_valid));
    bufp->fullBit(oldp+202,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__data_out_ready));
    bufp->fullSData(oldp+203,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__pv[0]),16);
    bufp->fullSData(oldp+204,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__pv[1]),16);
    bufp->fullBit(oldp+205,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__pv_valid));
    bufp->fullBit(oldp+206,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__pv_ready));
    bufp->fullIData(oldp+207,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__sum),17);
    bufp->fullBit(oldp+208,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__sum_valid));
    bufp->fullBit(oldp+209,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__sum_ready));
    bufp->fullBit(oldp+210,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__clk));
    bufp->fullBit(oldp+211,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__rst));
    bufp->fullSData(oldp+212,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__data_in[0]),16);
    bufp->fullSData(oldp+213,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__data_in[1]),16);
    bufp->fullBit(oldp+214,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__data_in_valid));
    bufp->fullBit(oldp+215,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__data_in_ready));
    bufp->fullIData(oldp+216,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__data_out),17);
    bufp->fullBit(oldp+217,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__data_out_valid));
    bufp->fullBit(oldp+218,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__data_out_ready));
    bufp->fullQData(oldp+219,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__data[0]),34);
    bufp->fullQData(oldp+221,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__data[1]),34);
    bufp->fullQData(oldp+223,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__sum[0]),34);
    bufp->fullBit(oldp+225,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__valid[0]));
    bufp->fullBit(oldp+226,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__valid[1]));
    bufp->fullBit(oldp+227,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__ready[0]));
    bufp->fullBit(oldp+228,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__ready[1]));
    bufp->fullIData(oldp+229,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__layer__DOT__data_in),32);
    bufp->fullIData(oldp+230,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__layer__DOT__data_out),17);
    bufp->fullSData(oldp+231,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__layer__DOT__data_in_unflat[0]),16);
    bufp->fullSData(oldp+232,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__layer__DOT__data_in_unflat[1]),16);
    bufp->fullIData(oldp+233,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__layer__DOT__data_out_unflat[0]),17);
    bufp->fullBit(oldp+234,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__clk));
    bufp->fullBit(oldp+235,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__rst));
    bufp->fullIData(oldp+236,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__data_in),17);
    bufp->fullBit(oldp+237,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__data_in_valid));
    bufp->fullBit(oldp+238,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__data_in_ready));
    bufp->fullIData(oldp+239,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__data_out),17);
    bufp->fullBit(oldp+240,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__data_out_valid));
    bufp->fullBit(oldp+241,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__data_out_ready));
    bufp->fullIData(oldp+242,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__data_buffer_out),17);
    bufp->fullBit(oldp+243,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__data_buffer_wren));
    bufp->fullBit(oldp+244,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__data_out_wren));
    bufp->fullBit(oldp+245,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__use_buffered_data));
    bufp->fullIData(oldp+246,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__selected_data),17);
    bufp->fullBit(oldp+247,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__insert));
    bufp->fullBit(oldp+248,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__remove));
    bufp->fullBit(oldp+249,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__load));
    bufp->fullBit(oldp+250,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__flow));
    bufp->fullBit(oldp+251,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__fill));
    bufp->fullBit(oldp+252,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__flush));
    bufp->fullBit(oldp+253,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__unload));
    bufp->fullIData(oldp+254,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__state),32);
    bufp->fullIData(oldp+255,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__state_next),32);
    bufp->fullBit(oldp+256,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__clk));
    bufp->fullBit(oldp+257,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__rst));
    bufp->fullCData(oldp+258,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__data_in[0]),8);
    bufp->fullCData(oldp+259,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__data_in[1]),8);
    bufp->fullBit(oldp+260,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__data_in_valid));
    bufp->fullBit(oldp+261,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__data_in_ready));
    bufp->fullCData(oldp+262,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__weight[0]),8);
    bufp->fullCData(oldp+263,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__weight[1]),8);
    bufp->fullBit(oldp+264,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__weight_valid));
    bufp->fullBit(oldp+265,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__weight_ready));
    bufp->fullSData(oldp+266,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__data_out[0]),16);
    bufp->fullSData(oldp+267,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__data_out[1]),16);
    bufp->fullBit(oldp+268,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__data_out_valid));
    bufp->fullBit(oldp+269,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__data_out_ready));
    bufp->fullSData(oldp+270,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__product_vector[0]),16);
    bufp->fullSData(oldp+271,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__product_vector[1]),16);
    bufp->fullBit(oldp+272,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__product_data_in_valid));
    bufp->fullBit(oldp+273,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__product_data_in_ready));
    bufp->fullBit(oldp+274,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__product_data_out_valid));
    bufp->fullBit(oldp+275,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__product_data_out_ready));
    bufp->fullIData(oldp+276,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__product_data_in),32);
    bufp->fullIData(oldp+277,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__product_data_out),32);
    bufp->fullCData(oldp+278,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__join_inst__DOT__data_in_valid),2);
    bufp->fullCData(oldp+279,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__join_inst__DOT__data_in_ready),2);
    bufp->fullBit(oldp+280,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__join_inst__DOT__data_out_valid));
    bufp->fullBit(oldp+281,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__join_inst__DOT__data_out_ready));
    bufp->fullCData(oldp+282,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__parallel_mult__BRA__0__KET____DOT__fixed_mult_inst__DOT__data_a),8);
    bufp->fullCData(oldp+283,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__parallel_mult__BRA__0__KET____DOT__fixed_mult_inst__DOT__data_b),8);
    bufp->fullSData(oldp+284,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__parallel_mult__BRA__0__KET____DOT__fixed_mult_inst__DOT__product),16);
    bufp->fullCData(oldp+285,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__parallel_mult__BRA__1__KET____DOT__fixed_mult_inst__DOT__data_a),8);
    bufp->fullCData(oldp+286,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__parallel_mult__BRA__1__KET____DOT__fixed_mult_inst__DOT__data_b),8);
    bufp->fullSData(oldp+287,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__parallel_mult__BRA__1__KET____DOT__fixed_mult_inst__DOT__product),16);
    bufp->fullBit(oldp+288,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__clk));
    bufp->fullBit(oldp+289,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__rst));
    bufp->fullIData(oldp+290,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__data_in),32);
    bufp->fullBit(oldp+291,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__data_in_valid));
    bufp->fullBit(oldp+292,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__data_in_ready));
    bufp->fullIData(oldp+293,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__data_out),32);
    bufp->fullBit(oldp+294,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__data_out_valid));
    bufp->fullBit(oldp+295,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__data_out_ready));
    bufp->fullIData(oldp+296,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__data_buffer_out),32);
    bufp->fullBit(oldp+297,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__data_buffer_wren));
    bufp->fullBit(oldp+298,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__data_out_wren));
    bufp->fullBit(oldp+299,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__use_buffered_data));
    bufp->fullIData(oldp+300,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__selected_data),32);
    bufp->fullBit(oldp+301,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__insert));
    bufp->fullBit(oldp+302,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__remove));
    bufp->fullBit(oldp+303,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__load));
    bufp->fullBit(oldp+304,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__flow));
    bufp->fullBit(oldp+305,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__fill));
    bufp->fullBit(oldp+306,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__flush));
    bufp->fullBit(oldp+307,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__unload));
    bufp->fullIData(oldp+308,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__state),32);
    bufp->fullIData(oldp+309,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__state_next),32);
    bufp->fullIData(oldp+310,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__rounding__DOT__round_inst__DOT__data_in),17);
    bufp->fullSData(oldp+311,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__rounding__DOT__round_inst__DOT__data_out),16);
    bufp->fullIData(oldp+312,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__rounding__DOT__round_inst__DOT__MAX_POS),17);
    bufp->fullIData(oldp+313,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__rounding__DOT__round_inst__DOT__MAX_NEG),17);
    bufp->fullCData(oldp+314,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__rounding__DOT__round_inst__DOT__lsb_below),3);
    bufp->fullSData(oldp+315,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__rounding__DOT__round_inst__DOT__input_data),16);
    bufp->fullBit(oldp+316,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__rounding__DOT__round_inst__DOT__carry_in));
    bufp->fullBit(oldp+317,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__rounding__DOT__round_inst__DOT__input_sign));
    bufp->fullQData(oldp+318,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__rounding__DOT__round_inst__DOT__rounded_out_data),34);
    bufp->fullQData(oldp+320,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__rounding__DOT__round_inst__DOT__comp_rouded_out),34);
    bufp->fullBit(oldp+322,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__clk));
    bufp->fullBit(oldp+323,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__rst));
    bufp->fullCData(oldp+324,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__data_in[0]),8);
    bufp->fullCData(oldp+325,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__data_in[1]),8);
    bufp->fullBit(oldp+326,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__data_in_valid));
    bufp->fullBit(oldp+327,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__data_in_ready));
    bufp->fullCData(oldp+328,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__weight[0]),8);
    bufp->fullCData(oldp+329,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__weight[1]),8);
    bufp->fullBit(oldp+330,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__weight_valid));
    bufp->fullBit(oldp+331,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__weight_ready));
    bufp->fullIData(oldp+332,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__data_out),17);
    bufp->fullBit(oldp+333,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__data_out_valid));
    bufp->fullBit(oldp+334,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__data_out_ready));
    bufp->fullSData(oldp+335,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__pv[0]),16);
    bufp->fullSData(oldp+336,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__pv[1]),16);
    bufp->fullBit(oldp+337,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__pv_valid));
    bufp->fullBit(oldp+338,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__pv_ready));
    bufp->fullIData(oldp+339,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__sum),17);
    bufp->fullBit(oldp+340,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__sum_valid));
    bufp->fullBit(oldp+341,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__sum_ready));
    bufp->fullBit(oldp+342,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__clk));
    bufp->fullBit(oldp+343,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__rst));
    bufp->fullSData(oldp+344,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__data_in[0]),16);
    bufp->fullSData(oldp+345,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__data_in[1]),16);
    bufp->fullBit(oldp+346,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__data_in_valid));
    bufp->fullBit(oldp+347,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__data_in_ready));
    bufp->fullIData(oldp+348,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__data_out),17);
    bufp->fullBit(oldp+349,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__data_out_valid));
    bufp->fullBit(oldp+350,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__data_out_ready));
    bufp->fullQData(oldp+351,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__data[0]),34);
    bufp->fullQData(oldp+353,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__data[1]),34);
    bufp->fullQData(oldp+355,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__sum[0]),34);
    bufp->fullBit(oldp+357,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__valid[0]));
    bufp->fullBit(oldp+358,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__valid[1]));
    bufp->fullBit(oldp+359,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__ready[0]));
    bufp->fullBit(oldp+360,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__ready[1]));
    bufp->fullIData(oldp+361,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__layer__DOT__data_in),32);
    bufp->fullIData(oldp+362,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__layer__DOT__data_out),17);
    bufp->fullSData(oldp+363,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__layer__DOT__data_in_unflat[0]),16);
    bufp->fullSData(oldp+364,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__layer__DOT__data_in_unflat[1]),16);
    bufp->fullIData(oldp+365,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__layer__DOT__data_out_unflat[0]),17);
    bufp->fullBit(oldp+366,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__clk));
    bufp->fullBit(oldp+367,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__rst));
    bufp->fullIData(oldp+368,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__data_in),17);
    bufp->fullBit(oldp+369,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__data_in_valid));
    bufp->fullBit(oldp+370,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__data_in_ready));
    bufp->fullIData(oldp+371,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__data_out),17);
    bufp->fullBit(oldp+372,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__data_out_valid));
    bufp->fullBit(oldp+373,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__data_out_ready));
    bufp->fullIData(oldp+374,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__data_buffer_out),17);
    bufp->fullBit(oldp+375,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__data_buffer_wren));
    bufp->fullBit(oldp+376,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__data_out_wren));
    bufp->fullBit(oldp+377,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__use_buffered_data));
    bufp->fullIData(oldp+378,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__selected_data),17);
    bufp->fullBit(oldp+379,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__insert));
    bufp->fullBit(oldp+380,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__remove));
    bufp->fullBit(oldp+381,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__load));
    bufp->fullBit(oldp+382,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__flow));
    bufp->fullBit(oldp+383,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__fill));
    bufp->fullBit(oldp+384,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__flush));
    bufp->fullBit(oldp+385,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__unload));
    bufp->fullIData(oldp+386,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__state),32);
    bufp->fullIData(oldp+387,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__state_next),32);
    bufp->fullBit(oldp+388,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__clk));
    bufp->fullBit(oldp+389,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__rst));
    bufp->fullCData(oldp+390,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__data_in[0]),8);
    bufp->fullCData(oldp+391,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__data_in[1]),8);
    bufp->fullBit(oldp+392,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__data_in_valid));
    bufp->fullBit(oldp+393,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__data_in_ready));
    bufp->fullCData(oldp+394,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__weight[0]),8);
    bufp->fullCData(oldp+395,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__weight[1]),8);
    bufp->fullBit(oldp+396,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__weight_valid));
    bufp->fullBit(oldp+397,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__weight_ready));
    bufp->fullSData(oldp+398,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__data_out[0]),16);
    bufp->fullSData(oldp+399,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__data_out[1]),16);
    bufp->fullBit(oldp+400,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__data_out_valid));
    bufp->fullBit(oldp+401,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__data_out_ready));
    bufp->fullSData(oldp+402,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__product_vector[0]),16);
    bufp->fullSData(oldp+403,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__product_vector[1]),16);
    bufp->fullBit(oldp+404,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__product_data_in_valid));
    bufp->fullBit(oldp+405,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__product_data_in_ready));
    bufp->fullBit(oldp+406,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__product_data_out_valid));
    bufp->fullBit(oldp+407,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__product_data_out_ready));
    bufp->fullIData(oldp+408,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__product_data_in),32);
    bufp->fullIData(oldp+409,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__product_data_out),32);
    bufp->fullCData(oldp+410,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__join_inst__DOT__data_in_valid),2);
    bufp->fullCData(oldp+411,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__join_inst__DOT__data_in_ready),2);
    bufp->fullBit(oldp+412,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__join_inst__DOT__data_out_valid));
    bufp->fullBit(oldp+413,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__join_inst__DOT__data_out_ready));
    bufp->fullCData(oldp+414,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__parallel_mult__BRA__0__KET____DOT__fixed_mult_inst__DOT__data_a),8);
    bufp->fullCData(oldp+415,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__parallel_mult__BRA__0__KET____DOT__fixed_mult_inst__DOT__data_b),8);
    bufp->fullSData(oldp+416,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__parallel_mult__BRA__0__KET____DOT__fixed_mult_inst__DOT__product),16);
    bufp->fullCData(oldp+417,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__parallel_mult__BRA__1__KET____DOT__fixed_mult_inst__DOT__data_a),8);
    bufp->fullCData(oldp+418,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__parallel_mult__BRA__1__KET____DOT__fixed_mult_inst__DOT__data_b),8);
    bufp->fullSData(oldp+419,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__parallel_mult__BRA__1__KET____DOT__fixed_mult_inst__DOT__product),16);
    bufp->fullBit(oldp+420,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__clk));
    bufp->fullBit(oldp+421,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__rst));
    bufp->fullIData(oldp+422,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__data_in),32);
    bufp->fullBit(oldp+423,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__data_in_valid));
    bufp->fullBit(oldp+424,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__data_in_ready));
    bufp->fullIData(oldp+425,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__data_out),32);
    bufp->fullBit(oldp+426,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__data_out_valid));
    bufp->fullBit(oldp+427,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__data_out_ready));
    bufp->fullIData(oldp+428,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__data_buffer_out),32);
    bufp->fullBit(oldp+429,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__data_buffer_wren));
    bufp->fullBit(oldp+430,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__data_out_wren));
    bufp->fullBit(oldp+431,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__use_buffered_data));
    bufp->fullIData(oldp+432,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__selected_data),32);
    bufp->fullBit(oldp+433,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__insert));
    bufp->fullBit(oldp+434,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__remove));
    bufp->fullBit(oldp+435,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__load));
    bufp->fullBit(oldp+436,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__flow));
    bufp->fullBit(oldp+437,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__fill));
    bufp->fullBit(oldp+438,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__flush));
    bufp->fullBit(oldp+439,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__unload));
    bufp->fullIData(oldp+440,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__state),32);
    bufp->fullIData(oldp+441,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__state_next),32);
    bufp->fullIData(oldp+442,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__rounding__DOT__round_inst__DOT__data_in),17);
    bufp->fullSData(oldp+443,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__rounding__DOT__round_inst__DOT__data_out),16);
    bufp->fullIData(oldp+444,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__rounding__DOT__round_inst__DOT__MAX_POS),17);
    bufp->fullIData(oldp+445,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__rounding__DOT__round_inst__DOT__MAX_NEG),17);
    bufp->fullCData(oldp+446,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__rounding__DOT__round_inst__DOT__lsb_below),3);
    bufp->fullSData(oldp+447,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__rounding__DOT__round_inst__DOT__input_data),16);
    bufp->fullBit(oldp+448,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__rounding__DOT__round_inst__DOT__carry_in));
    bufp->fullBit(oldp+449,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__rounding__DOT__round_inst__DOT__input_sign));
    bufp->fullQData(oldp+450,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__rounding__DOT__round_inst__DOT__rounded_out_data),34);
    bufp->fullQData(oldp+452,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__rounding__DOT__round_inst__DOT__comp_rouded_out),34);
    bufp->fullBit(oldp+454,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__clk));
    bufp->fullBit(oldp+455,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__rst));
    bufp->fullCData(oldp+456,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__data_in[0]),8);
    bufp->fullCData(oldp+457,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__data_in[1]),8);
    bufp->fullBit(oldp+458,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__data_in_valid));
    bufp->fullBit(oldp+459,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__data_in_ready));
    bufp->fullCData(oldp+460,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__weight[0]),8);
    bufp->fullCData(oldp+461,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__weight[1]),8);
    bufp->fullBit(oldp+462,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__weight_valid));
    bufp->fullBit(oldp+463,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__weight_ready));
    bufp->fullIData(oldp+464,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__data_out),17);
    bufp->fullBit(oldp+465,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__data_out_valid));
    bufp->fullBit(oldp+466,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__data_out_ready));
    bufp->fullSData(oldp+467,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__pv[0]),16);
    bufp->fullSData(oldp+468,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__pv[1]),16);
    bufp->fullBit(oldp+469,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__pv_valid));
    bufp->fullBit(oldp+470,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__pv_ready));
    bufp->fullIData(oldp+471,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__sum),17);
    bufp->fullBit(oldp+472,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__sum_valid));
    bufp->fullBit(oldp+473,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__sum_ready));
    bufp->fullBit(oldp+474,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__clk));
    bufp->fullBit(oldp+475,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__rst));
    bufp->fullSData(oldp+476,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__data_in[0]),16);
    bufp->fullSData(oldp+477,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__data_in[1]),16);
    bufp->fullBit(oldp+478,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__data_in_valid));
    bufp->fullBit(oldp+479,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__data_in_ready));
    bufp->fullIData(oldp+480,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__data_out),17);
    bufp->fullBit(oldp+481,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__data_out_valid));
    bufp->fullBit(oldp+482,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__data_out_ready));
    bufp->fullQData(oldp+483,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__data[0]),34);
    bufp->fullQData(oldp+485,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__data[1]),34);
    bufp->fullQData(oldp+487,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__sum[0]),34);
    bufp->fullBit(oldp+489,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__valid[0]));
    bufp->fullBit(oldp+490,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__valid[1]));
    bufp->fullBit(oldp+491,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__ready[0]));
    bufp->fullBit(oldp+492,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__ready[1]));
    bufp->fullIData(oldp+493,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__layer__DOT__data_in),32);
    bufp->fullIData(oldp+494,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__layer__DOT__data_out),17);
    bufp->fullSData(oldp+495,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__layer__DOT__data_in_unflat[0]),16);
    bufp->fullSData(oldp+496,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__layer__DOT__data_in_unflat[1]),16);
    bufp->fullIData(oldp+497,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__layer__DOT__data_out_unflat[0]),17);
    bufp->fullBit(oldp+498,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__clk));
    bufp->fullBit(oldp+499,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__rst));
    bufp->fullIData(oldp+500,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__data_in),17);
    bufp->fullBit(oldp+501,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__data_in_valid));
    bufp->fullBit(oldp+502,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__data_in_ready));
    bufp->fullIData(oldp+503,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__data_out),17);
    bufp->fullBit(oldp+504,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__data_out_valid));
    bufp->fullBit(oldp+505,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__data_out_ready));
    bufp->fullIData(oldp+506,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__data_buffer_out),17);
    bufp->fullBit(oldp+507,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__data_buffer_wren));
    bufp->fullBit(oldp+508,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__data_out_wren));
    bufp->fullBit(oldp+509,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__use_buffered_data));
    bufp->fullIData(oldp+510,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__selected_data),17);
    bufp->fullBit(oldp+511,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__insert));
    bufp->fullBit(oldp+512,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__remove));
    bufp->fullBit(oldp+513,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__load));
    bufp->fullBit(oldp+514,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__flow));
    bufp->fullBit(oldp+515,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__fill));
    bufp->fullBit(oldp+516,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__flush));
    bufp->fullBit(oldp+517,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__unload));
    bufp->fullIData(oldp+518,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__state),32);
    bufp->fullIData(oldp+519,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__state_next),32);
    bufp->fullBit(oldp+520,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__clk));
    bufp->fullBit(oldp+521,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__rst));
    bufp->fullCData(oldp+522,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__data_in[0]),8);
    bufp->fullCData(oldp+523,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__data_in[1]),8);
    bufp->fullBit(oldp+524,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__data_in_valid));
    bufp->fullBit(oldp+525,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__data_in_ready));
    bufp->fullCData(oldp+526,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__weight[0]),8);
    bufp->fullCData(oldp+527,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__weight[1]),8);
    bufp->fullBit(oldp+528,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__weight_valid));
    bufp->fullBit(oldp+529,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__weight_ready));
    bufp->fullSData(oldp+530,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__data_out[0]),16);
    bufp->fullSData(oldp+531,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__data_out[1]),16);
    bufp->fullBit(oldp+532,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__data_out_valid));
    bufp->fullBit(oldp+533,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__data_out_ready));
    bufp->fullSData(oldp+534,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__product_vector[0]),16);
    bufp->fullSData(oldp+535,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__product_vector[1]),16);
    bufp->fullBit(oldp+536,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__product_data_in_valid));
    bufp->fullBit(oldp+537,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__product_data_in_ready));
    bufp->fullBit(oldp+538,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__product_data_out_valid));
    bufp->fullBit(oldp+539,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__product_data_out_ready));
    bufp->fullIData(oldp+540,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__product_data_in),32);
    bufp->fullIData(oldp+541,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__product_data_out),32);
    bufp->fullCData(oldp+542,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__join_inst__DOT__data_in_valid),2);
    bufp->fullCData(oldp+543,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__join_inst__DOT__data_in_ready),2);
    bufp->fullBit(oldp+544,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__join_inst__DOT__data_out_valid));
    bufp->fullBit(oldp+545,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__join_inst__DOT__data_out_ready));
    bufp->fullCData(oldp+546,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__parallel_mult__BRA__0__KET____DOT__fixed_mult_inst__DOT__data_a),8);
    bufp->fullCData(oldp+547,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__parallel_mult__BRA__0__KET____DOT__fixed_mult_inst__DOT__data_b),8);
    bufp->fullSData(oldp+548,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__parallel_mult__BRA__0__KET____DOT__fixed_mult_inst__DOT__product),16);
    bufp->fullCData(oldp+549,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__parallel_mult__BRA__1__KET____DOT__fixed_mult_inst__DOT__data_a),8);
    bufp->fullCData(oldp+550,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__parallel_mult__BRA__1__KET____DOT__fixed_mult_inst__DOT__data_b),8);
    bufp->fullSData(oldp+551,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__parallel_mult__BRA__1__KET____DOT__fixed_mult_inst__DOT__product),16);
    bufp->fullBit(oldp+552,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__clk));
    bufp->fullBit(oldp+553,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__rst));
    bufp->fullIData(oldp+554,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__data_in),32);
    bufp->fullBit(oldp+555,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__data_in_valid));
    bufp->fullBit(oldp+556,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__data_in_ready));
    bufp->fullIData(oldp+557,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__data_out),32);
    bufp->fullBit(oldp+558,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__data_out_valid));
    bufp->fullBit(oldp+559,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__data_out_ready));
    bufp->fullIData(oldp+560,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__data_buffer_out),32);
    bufp->fullBit(oldp+561,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__data_buffer_wren));
    bufp->fullBit(oldp+562,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__data_out_wren));
    bufp->fullBit(oldp+563,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__use_buffered_data));
    bufp->fullIData(oldp+564,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__selected_data),32);
    bufp->fullBit(oldp+565,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__insert));
    bufp->fullBit(oldp+566,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__remove));
    bufp->fullBit(oldp+567,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__load));
    bufp->fullBit(oldp+568,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__flow));
    bufp->fullBit(oldp+569,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__fill));
    bufp->fullBit(oldp+570,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__flush));
    bufp->fullBit(oldp+571,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__unload));
    bufp->fullIData(oldp+572,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__state),32);
    bufp->fullIData(oldp+573,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__state_next),32);
    bufp->fullIData(oldp+574,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__rounding__DOT__round_inst__DOT__data_in),17);
    bufp->fullSData(oldp+575,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__rounding__DOT__round_inst__DOT__data_out),16);
    bufp->fullIData(oldp+576,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__rounding__DOT__round_inst__DOT__MAX_POS),17);
    bufp->fullIData(oldp+577,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__rounding__DOT__round_inst__DOT__MAX_NEG),17);
    bufp->fullCData(oldp+578,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__rounding__DOT__round_inst__DOT__lsb_below),3);
    bufp->fullSData(oldp+579,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__rounding__DOT__round_inst__DOT__input_data),16);
    bufp->fullBit(oldp+580,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__rounding__DOT__round_inst__DOT__carry_in));
    bufp->fullBit(oldp+581,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__rounding__DOT__round_inst__DOT__input_sign));
    bufp->fullQData(oldp+582,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__rounding__DOT__round_inst__DOT__rounded_out_data),34);
    bufp->fullQData(oldp+584,(vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__rounding__DOT__round_inst__DOT__comp_rouded_out),34);
    bufp->fullCData(oldp+586,(vlSelfRef.simple_matmul__DOT__sync_handshake__DOT__data_in_valid),2);
    bufp->fullCData(oldp+587,(vlSelfRef.simple_matmul__DOT__sync_handshake__DOT__data_in_ready),2);
    bufp->fullBit(oldp+588,(vlSelfRef.simple_matmul__DOT__sync_handshake__DOT__data_out_valid));
    bufp->fullBit(oldp+589,(vlSelfRef.simple_matmul__DOT__sync_handshake__DOT__data_out_ready));
    bufp->fullCData(oldp+590,(vlSelfRef.simple_matmul__DOT__y_transpose__DOT__in_data[0]),8);
    bufp->fullCData(oldp+591,(vlSelfRef.simple_matmul__DOT__y_transpose__DOT__in_data[1]),8);
    bufp->fullCData(oldp+592,(vlSelfRef.simple_matmul__DOT__y_transpose__DOT__in_data[2]),8);
    bufp->fullCData(oldp+593,(vlSelfRef.simple_matmul__DOT__y_transpose__DOT__in_data[3]),8);
    bufp->fullCData(oldp+594,(vlSelfRef.simple_matmul__DOT__y_transpose__DOT__out_data[0]),8);
    bufp->fullCData(oldp+595,(vlSelfRef.simple_matmul__DOT__y_transpose__DOT__out_data[1]),8);
    bufp->fullCData(oldp+596,(vlSelfRef.simple_matmul__DOT__y_transpose__DOT__out_data[2]),8);
    bufp->fullCData(oldp+597,(vlSelfRef.simple_matmul__DOT__y_transpose__DOT__out_data[3]),8);
}

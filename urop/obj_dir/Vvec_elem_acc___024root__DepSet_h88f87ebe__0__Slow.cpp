// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vvec_elem_acc.h for the primary calling header

#include "verilated.h"

#include "Vvec_elem_acc___024root.h"

VL_ATTR_COLD void Vvec_elem_acc___024root___settle__TOP__0(Vvec_elem_acc___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vvec_elem_acc__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vvec_elem_acc___024root___settle__TOP__0\n"); );
    // Body
    vlSelf->V_out[0U] = vlSelf->vec_elem_acc__DOT__mem
        [0U];
    vlSelf->V_out[1U] = vlSelf->vec_elem_acc__DOT__mem
        [1U];
    vlSelf->V_out[2U] = vlSelf->vec_elem_acc__DOT__mem
        [2U];
    vlSelf->V_out[3U] = vlSelf->vec_elem_acc__DOT__mem
        [3U];
    vlSelf->V_out[4U] = vlSelf->vec_elem_acc__DOT__mem
        [4U];
    vlSelf->V_out[5U] = vlSelf->vec_elem_acc__DOT__mem
        [5U];
    vlSelf->V_out[6U] = vlSelf->vec_elem_acc__DOT__mem
        [6U];
    vlSelf->V_out[7U] = vlSelf->vec_elem_acc__DOT__mem
        [7U];
}

VL_ATTR_COLD void Vvec_elem_acc___024root___eval_initial(Vvec_elem_acc___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vvec_elem_acc__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vvec_elem_acc___024root___eval_initial\n"); );
    // Body
    vlSelf->__Vclklast__TOP__clk = vlSelf->clk;
}

VL_ATTR_COLD void Vvec_elem_acc___024root___eval_settle(Vvec_elem_acc___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vvec_elem_acc__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vvec_elem_acc___024root___eval_settle\n"); );
    // Body
    Vvec_elem_acc___024root___settle__TOP__0(vlSelf);
}

VL_ATTR_COLD void Vvec_elem_acc___024root___final(Vvec_elem_acc___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vvec_elem_acc__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vvec_elem_acc___024root___final\n"); );
}

VL_ATTR_COLD void Vvec_elem_acc___024root___ctor_var_reset(Vvec_elem_acc___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vvec_elem_acc__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vvec_elem_acc___024root___ctor_var_reset\n"); );
    // Body
    vlSelf->clk = VL_RAND_RESET_I(1);
    for (int __Vi0=0; __Vi0<8; ++__Vi0) {
        vlSelf->V_in[__Vi0] = VL_RAND_RESET_I(32);
    }
    for (int __Vi0=0; __Vi0<8; ++__Vi0) {
        vlSelf->V_out[__Vi0] = VL_RAND_RESET_I(32);
    }
    vlSelf->index = VL_RAND_RESET_I(6);
    vlSelf->write_en = VL_RAND_RESET_I(1);
    vlSelf->write_data = VL_RAND_RESET_I(32);
    vlSelf->read_en = VL_RAND_RESET_I(1);
    vlSelf->v_in_ready = VL_RAND_RESET_I(1);
    vlSelf->read_data = VL_RAND_RESET_I(32);
    for (int __Vi0=0; __Vi0<8; ++__Vi0) {
        vlSelf->vec_elem_acc__DOT__mem[__Vi0] = VL_RAND_RESET_I(32);
    }
}

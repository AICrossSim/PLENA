// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vvec_elem_acc.h for the primary calling header

#include "verilated.h"

#include "Vvec_elem_acc___024root.h"

VL_INLINE_OPT void Vvec_elem_acc___024root___sequent__TOP__0(Vvec_elem_acc___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vvec_elem_acc__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vvec_elem_acc___024root___sequent__TOP__0\n"); );
    // Init
    IData/*31:0*/ __Vdlyvval__vec_elem_acc__DOT__mem__v0;
    CData/*0:0*/ __Vdlyvset__vec_elem_acc__DOT__mem__v0;
    IData/*31:0*/ __Vdlyvval__vec_elem_acc__DOT__mem__v1;
    IData/*31:0*/ __Vdlyvval__vec_elem_acc__DOT__mem__v2;
    IData/*31:0*/ __Vdlyvval__vec_elem_acc__DOT__mem__v3;
    IData/*31:0*/ __Vdlyvval__vec_elem_acc__DOT__mem__v4;
    IData/*31:0*/ __Vdlyvval__vec_elem_acc__DOT__mem__v5;
    IData/*31:0*/ __Vdlyvval__vec_elem_acc__DOT__mem__v6;
    IData/*31:0*/ __Vdlyvval__vec_elem_acc__DOT__mem__v7;
    CData/*2:0*/ __Vdlyvdim0__vec_elem_acc__DOT__mem__v8;
    IData/*31:0*/ __Vdlyvval__vec_elem_acc__DOT__mem__v8;
    CData/*0:0*/ __Vdlyvset__vec_elem_acc__DOT__mem__v8;
    // Body
    __Vdlyvset__vec_elem_acc__DOT__mem__v0 = 0U;
    __Vdlyvset__vec_elem_acc__DOT__mem__v8 = 0U;
    if (vlSelf->read_en) {
        vlSelf->read_data = vlSelf->vec_elem_acc__DOT__mem
            [(7U & (IData)(vlSelf->index))];
    }
    if (vlSelf->v_in_ready) {
        __Vdlyvval__vec_elem_acc__DOT__mem__v0 = vlSelf->V_in
            [0U];
        __Vdlyvset__vec_elem_acc__DOT__mem__v0 = 1U;
        __Vdlyvval__vec_elem_acc__DOT__mem__v1 = vlSelf->V_in
            [1U];
        __Vdlyvval__vec_elem_acc__DOT__mem__v2 = vlSelf->V_in
            [2U];
        __Vdlyvval__vec_elem_acc__DOT__mem__v3 = vlSelf->V_in
            [3U];
        __Vdlyvval__vec_elem_acc__DOT__mem__v4 = vlSelf->V_in
            [4U];
        __Vdlyvval__vec_elem_acc__DOT__mem__v5 = vlSelf->V_in
            [5U];
        __Vdlyvval__vec_elem_acc__DOT__mem__v6 = vlSelf->V_in
            [6U];
        __Vdlyvval__vec_elem_acc__DOT__mem__v7 = vlSelf->V_in
            [7U];
    } else if (vlSelf->write_en) {
        __Vdlyvval__vec_elem_acc__DOT__mem__v8 = vlSelf->write_data;
        __Vdlyvset__vec_elem_acc__DOT__mem__v8 = 1U;
        __Vdlyvdim0__vec_elem_acc__DOT__mem__v8 = (7U 
                                                   & (IData)(vlSelf->index));
    }
    if (__Vdlyvset__vec_elem_acc__DOT__mem__v0) {
        vlSelf->vec_elem_acc__DOT__mem[0U] = __Vdlyvval__vec_elem_acc__DOT__mem__v0;
        vlSelf->vec_elem_acc__DOT__mem[1U] = __Vdlyvval__vec_elem_acc__DOT__mem__v1;
        vlSelf->vec_elem_acc__DOT__mem[2U] = __Vdlyvval__vec_elem_acc__DOT__mem__v2;
        vlSelf->vec_elem_acc__DOT__mem[3U] = __Vdlyvval__vec_elem_acc__DOT__mem__v3;
        vlSelf->vec_elem_acc__DOT__mem[4U] = __Vdlyvval__vec_elem_acc__DOT__mem__v4;
        vlSelf->vec_elem_acc__DOT__mem[5U] = __Vdlyvval__vec_elem_acc__DOT__mem__v5;
        vlSelf->vec_elem_acc__DOT__mem[6U] = __Vdlyvval__vec_elem_acc__DOT__mem__v6;
        vlSelf->vec_elem_acc__DOT__mem[7U] = __Vdlyvval__vec_elem_acc__DOT__mem__v7;
    }
    if (__Vdlyvset__vec_elem_acc__DOT__mem__v8) {
        vlSelf->vec_elem_acc__DOT__mem[__Vdlyvdim0__vec_elem_acc__DOT__mem__v8] 
            = __Vdlyvval__vec_elem_acc__DOT__mem__v8;
    }
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

void Vvec_elem_acc___024root___eval(Vvec_elem_acc___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vvec_elem_acc__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vvec_elem_acc___024root___eval\n"); );
    // Body
    if (((IData)(vlSelf->clk) & (~ (IData)(vlSelf->__Vclklast__TOP__clk)))) {
        Vvec_elem_acc___024root___sequent__TOP__0(vlSelf);
    }
    // Final
    vlSelf->__Vclklast__TOP__clk = vlSelf->clk;
}

#ifdef VL_DEBUG
void Vvec_elem_acc___024root___eval_debug_assertions(Vvec_elem_acc___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vvec_elem_acc__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vvec_elem_acc___024root___eval_debug_assertions\n"); );
    // Body
    if (VL_UNLIKELY((vlSelf->clk & 0xfeU))) {
        Verilated::overWidthError("clk");}
    if (VL_UNLIKELY((vlSelf->index & 0xc0U))) {
        Verilated::overWidthError("index");}
    if (VL_UNLIKELY((vlSelf->write_en & 0xfeU))) {
        Verilated::overWidthError("write_en");}
    if (VL_UNLIKELY((vlSelf->read_en & 0xfeU))) {
        Verilated::overWidthError("read_en");}
    if (VL_UNLIKELY((vlSelf->v_in_ready & 0xfeU))) {
        Verilated::overWidthError("v_in_ready");}
}
#endif  // VL_DEBUG

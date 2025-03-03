// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vtop.h for the primary calling header

#include "Vtop__pch.h"
#include "Vtop___024root.h"

VL_ATTR_COLD void Vtop___024root___eval_static(Vtop___024root* vlSelf) {
    (void)vlSelf;  // Prevent unused variable warning
    Vtop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root___eval_static\n"); );
    auto &vlSelfRef = std::ref(*vlSelf).get();
}

VL_ATTR_COLD void Vtop___024root___eval_initial__TOP(Vtop___024root* vlSelf);

VL_ATTR_COLD void Vtop___024root___eval_initial(Vtop___024root* vlSelf) {
    (void)vlSelf;  // Prevent unused variable warning
    Vtop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root___eval_initial\n"); );
    auto &vlSelfRef = std::ref(*vlSelf).get();
    // Body
    Vtop___024root___eval_initial__TOP(vlSelf);
    vlSelfRef.__Vtrigprevexpr___TOP__clk__0 = vlSelfRef.clk;
}

VL_ATTR_COLD void Vtop___024root___eval_initial__TOP(Vtop___024root* vlSelf) {
    (void)vlSelf;  // Prevent unused variable warning
    Vtop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root___eval_initial__TOP\n"); );
    auto &vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__rounding__DOT__round_inst__DOT__MAX_POS = 0x7fffU;
    vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__rounding__DOT__round_inst__DOT__MAX_NEG = 0x8000U;
    vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__rounding__DOT__round_inst__DOT__MAX_POS = 0x7fffU;
    vlSelfRef.simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__rounding__DOT__round_inst__DOT__MAX_NEG = 0x8000U;
    vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__rounding__DOT__round_inst__DOT__MAX_POS = 0x7fffU;
    vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__rounding__DOT__round_inst__DOT__MAX_NEG = 0x8000U;
    vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__rounding__DOT__round_inst__DOT__MAX_POS = 0x7fffU;
    vlSelfRef.simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__rounding__DOT__round_inst__DOT__MAX_NEG = 0x8000U;
}

VL_ATTR_COLD void Vtop___024root___eval_final(Vtop___024root* vlSelf) {
    (void)vlSelf;  // Prevent unused variable warning
    Vtop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root___eval_final\n"); );
    auto &vlSelfRef = std::ref(*vlSelf).get();
}

#ifdef VL_DEBUG
VL_ATTR_COLD void Vtop___024root___dump_triggers__stl(Vtop___024root* vlSelf);
#endif  // VL_DEBUG
VL_ATTR_COLD bool Vtop___024root___eval_phase__stl(Vtop___024root* vlSelf);

VL_ATTR_COLD void Vtop___024root___eval_settle(Vtop___024root* vlSelf) {
    (void)vlSelf;  // Prevent unused variable warning
    Vtop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root___eval_settle\n"); );
    auto &vlSelfRef = std::ref(*vlSelf).get();
    // Init
    IData/*31:0*/ __VstlIterCount;
    CData/*0:0*/ __VstlContinue;
    // Body
    __VstlIterCount = 0U;
    vlSelfRef.__VstlFirstIteration = 1U;
    __VstlContinue = 1U;
    while (__VstlContinue) {
        if (VL_UNLIKELY((0x64U < __VstlIterCount))) {
#ifdef VL_DEBUG
            Vtop___024root___dump_triggers__stl(vlSelf);
#endif
            VL_FATAL_MT("/home/hw1020/Documents/ARIA/Coprocessor_for_Llama/src/matrix_machine/rtl/mv_unit/rtl/simple_matmul.sv", 17, "", "Settle region did not converge.");
        }
        __VstlIterCount = ((IData)(1U) + __VstlIterCount);
        __VstlContinue = 0U;
        if (Vtop___024root___eval_phase__stl(vlSelf)) {
            __VstlContinue = 1U;
        }
        vlSelfRef.__VstlFirstIteration = 0U;
    }
}

#ifdef VL_DEBUG
VL_ATTR_COLD void Vtop___024root___dump_triggers__stl(Vtop___024root* vlSelf) {
    (void)vlSelf;  // Prevent unused variable warning
    Vtop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root___dump_triggers__stl\n"); );
    auto &vlSelfRef = std::ref(*vlSelf).get();
    // Body
    if ((1U & (~ vlSelfRef.__VstlTriggered.any()))) {
        VL_DBG_MSGF("         No triggers active\n");
    }
    if ((1ULL & vlSelfRef.__VstlTriggered.word(0U))) {
        VL_DBG_MSGF("         'stl' region trigger index 0 is active: Internal 'stl' trigger - first iteration\n");
    }
}
#endif  // VL_DEBUG

void Vtop___024root___ico_sequent__TOP__0(Vtop___024root* vlSelf);

VL_ATTR_COLD void Vtop___024root___eval_stl(Vtop___024root* vlSelf) {
    (void)vlSelf;  // Prevent unused variable warning
    Vtop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root___eval_stl\n"); );
    auto &vlSelfRef = std::ref(*vlSelf).get();
    // Body
    if ((1ULL & vlSelfRef.__VstlTriggered.word(0U))) {
        Vtop___024root___ico_sequent__TOP__0(vlSelf);
    }
}

VL_ATTR_COLD void Vtop___024root___eval_triggers__stl(Vtop___024root* vlSelf);

VL_ATTR_COLD bool Vtop___024root___eval_phase__stl(Vtop___024root* vlSelf) {
    (void)vlSelf;  // Prevent unused variable warning
    Vtop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root___eval_phase__stl\n"); );
    auto &vlSelfRef = std::ref(*vlSelf).get();
    // Init
    CData/*0:0*/ __VstlExecute;
    // Body
    Vtop___024root___eval_triggers__stl(vlSelf);
    __VstlExecute = vlSelfRef.__VstlTriggered.any();
    if (__VstlExecute) {
        Vtop___024root___eval_stl(vlSelf);
    }
    return (__VstlExecute);
}

#ifdef VL_DEBUG
VL_ATTR_COLD void Vtop___024root___dump_triggers__ico(Vtop___024root* vlSelf) {
    (void)vlSelf;  // Prevent unused variable warning
    Vtop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root___dump_triggers__ico\n"); );
    auto &vlSelfRef = std::ref(*vlSelf).get();
    // Body
    if ((1U & (~ vlSelfRef.__VicoTriggered.any()))) {
        VL_DBG_MSGF("         No triggers active\n");
    }
    if ((1ULL & vlSelfRef.__VicoTriggered.word(0U))) {
        VL_DBG_MSGF("         'ico' region trigger index 0 is active: Internal 'ico' trigger - first iteration\n");
    }
}
#endif  // VL_DEBUG

#ifdef VL_DEBUG
VL_ATTR_COLD void Vtop___024root___dump_triggers__act(Vtop___024root* vlSelf) {
    (void)vlSelf;  // Prevent unused variable warning
    Vtop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root___dump_triggers__act\n"); );
    auto &vlSelfRef = std::ref(*vlSelf).get();
    // Body
    if ((1U & (~ vlSelfRef.__VactTriggered.any()))) {
        VL_DBG_MSGF("         No triggers active\n");
    }
    if ((1ULL & vlSelfRef.__VactTriggered.word(0U))) {
        VL_DBG_MSGF("         'act' region trigger index 0 is active: @(posedge clk)\n");
    }
}
#endif  // VL_DEBUG

#ifdef VL_DEBUG
VL_ATTR_COLD void Vtop___024root___dump_triggers__nba(Vtop___024root* vlSelf) {
    (void)vlSelf;  // Prevent unused variable warning
    Vtop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root___dump_triggers__nba\n"); );
    auto &vlSelfRef = std::ref(*vlSelf).get();
    // Body
    if ((1U & (~ vlSelfRef.__VnbaTriggered.any()))) {
        VL_DBG_MSGF("         No triggers active\n");
    }
    if ((1ULL & vlSelfRef.__VnbaTriggered.word(0U))) {
        VL_DBG_MSGF("         'nba' region trigger index 0 is active: @(posedge clk)\n");
    }
}
#endif  // VL_DEBUG

VL_ATTR_COLD void Vtop___024root___ctor_var_reset(Vtop___024root* vlSelf) {
    (void)vlSelf;  // Prevent unused variable warning
    Vtop__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtop___024root___ctor_var_reset\n"); );
    auto &vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelf->clk = VL_RAND_RESET_I(1);
    vlSelf->rst = VL_RAND_RESET_I(1);
    for (int __Vi0 = 0; __Vi0 < 4; ++__Vi0) {
        vlSelf->x_data[__Vi0] = VL_RAND_RESET_I(8);
    }
    vlSelf->x_valid = VL_RAND_RESET_I(1);
    vlSelf->x_ready = VL_RAND_RESET_I(1);
    for (int __Vi0 = 0; __Vi0 < 4; ++__Vi0) {
        vlSelf->y_data[__Vi0] = VL_RAND_RESET_I(8);
    }
    vlSelf->y_valid = VL_RAND_RESET_I(1);
    vlSelf->y_ready = VL_RAND_RESET_I(1);
    for (int __Vi0 = 0; __Vi0 < 4; ++__Vi0) {
        vlSelf->out_data[__Vi0] = VL_RAND_RESET_I(16);
    }
    vlSelf->out_valid = VL_RAND_RESET_I(1);
    vlSelf->out_ready = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__clk = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__rst = VL_RAND_RESET_I(1);
    for (int __Vi0 = 0; __Vi0 < 4; ++__Vi0) {
        vlSelf->simple_matmul__DOT__x_data[__Vi0] = VL_RAND_RESET_I(8);
    }
    vlSelf->simple_matmul__DOT__x_valid = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__x_ready = VL_RAND_RESET_I(1);
    for (int __Vi0 = 0; __Vi0 < 4; ++__Vi0) {
        vlSelf->simple_matmul__DOT__y_data[__Vi0] = VL_RAND_RESET_I(8);
    }
    vlSelf->simple_matmul__DOT__y_valid = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__y_ready = VL_RAND_RESET_I(1);
    for (int __Vi0 = 0; __Vi0 < 4; ++__Vi0) {
        vlSelf->simple_matmul__DOT__out_data[__Vi0] = VL_RAND_RESET_I(16);
    }
    vlSelf->simple_matmul__DOT__out_valid = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__out_ready = VL_RAND_RESET_I(1);
    for (int __Vi0 = 0; __Vi0 < 4; ++__Vi0) {
        vlSelf->simple_matmul__DOT__y_data_transpose[__Vi0] = VL_RAND_RESET_I(8);
    }
    vlSelf->simple_matmul__DOT__dot_product_ready = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__inputs_valid = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__inputs_ready = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__dot_product_valid = VL_RAND_RESET_I(4);
    vlSelf->simple_matmul__DOT__sync_ready = VL_RAND_RESET_I(4);
    for (int __Vi0 = 0; __Vi0 < 4; ++__Vi0) {
        vlSelf->simple_matmul__DOT__dot_product_data_out[__Vi0] = VL_RAND_RESET_I(17);
    }
    for (int __Vi0 = 0; __Vi0 < 4; ++__Vi0) {
        vlSelf->simple_matmul__DOT__rounded_dot_product[__Vi0] = VL_RAND_RESET_I(16);
    }
    for (int __Vi0 = 0; __Vi0 < 2; ++__Vi0) {
        vlSelf->simple_matmul__DOT____Vcellinp__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__weight[__Vi0] = VL_RAND_RESET_I(8);
    }
    for (int __Vi0 = 0; __Vi0 < 2; ++__Vi0) {
        vlSelf->simple_matmul__DOT____Vcellinp__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__data_in[__Vi0] = VL_RAND_RESET_I(8);
    }
    for (int __Vi0 = 0; __Vi0 < 2; ++__Vi0) {
        vlSelf->simple_matmul__DOT____Vcellinp__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__weight[__Vi0] = VL_RAND_RESET_I(8);
    }
    for (int __Vi0 = 0; __Vi0 < 2; ++__Vi0) {
        vlSelf->simple_matmul__DOT____Vcellinp__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__data_in[__Vi0] = VL_RAND_RESET_I(8);
    }
    for (int __Vi0 = 0; __Vi0 < 2; ++__Vi0) {
        vlSelf->simple_matmul__DOT____Vcellinp__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__weight[__Vi0] = VL_RAND_RESET_I(8);
    }
    for (int __Vi0 = 0; __Vi0 < 2; ++__Vi0) {
        vlSelf->simple_matmul__DOT____Vcellinp__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__data_in[__Vi0] = VL_RAND_RESET_I(8);
    }
    for (int __Vi0 = 0; __Vi0 < 2; ++__Vi0) {
        vlSelf->simple_matmul__DOT____Vcellinp__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__weight[__Vi0] = VL_RAND_RESET_I(8);
    }
    for (int __Vi0 = 0; __Vi0 < 2; ++__Vi0) {
        vlSelf->simple_matmul__DOT____Vcellinp__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__data_in[__Vi0] = VL_RAND_RESET_I(8);
    }
    vlSelf->simple_matmul__DOT__sync_handshake__DOT__data_in_valid = VL_RAND_RESET_I(2);
    vlSelf->simple_matmul__DOT__sync_handshake__DOT__data_in_ready = VL_RAND_RESET_I(2);
    vlSelf->simple_matmul__DOT__sync_handshake__DOT__data_out_valid = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__sync_handshake__DOT__data_out_ready = VL_RAND_RESET_I(1);
    for (int __Vi0 = 0; __Vi0 < 4; ++__Vi0) {
        vlSelf->simple_matmul__DOT__y_transpose__DOT__in_data[__Vi0] = VL_RAND_RESET_I(8);
    }
    for (int __Vi0 = 0; __Vi0 < 4; ++__Vi0) {
        vlSelf->simple_matmul__DOT__y_transpose__DOT__out_data[__Vi0] = VL_RAND_RESET_I(8);
    }
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__clk = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__rst = VL_RAND_RESET_I(1);
    for (int __Vi0 = 0; __Vi0 < 2; ++__Vi0) {
        vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__data_in[__Vi0] = VL_RAND_RESET_I(8);
    }
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__data_in_valid = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__data_in_ready = VL_RAND_RESET_I(1);
    for (int __Vi0 = 0; __Vi0 < 2; ++__Vi0) {
        vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__weight[__Vi0] = VL_RAND_RESET_I(8);
    }
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__weight_valid = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__weight_ready = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__data_out = VL_RAND_RESET_I(17);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__data_out_valid = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__data_out_ready = VL_RAND_RESET_I(1);
    for (int __Vi0 = 0; __Vi0 < 2; ++__Vi0) {
        vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__pv[__Vi0] = VL_RAND_RESET_I(16);
    }
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__pv_valid = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__pv_ready = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__sum = VL_RAND_RESET_I(17);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__sum_valid = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__sum_ready = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__clk = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__rst = VL_RAND_RESET_I(1);
    for (int __Vi0 = 0; __Vi0 < 2; ++__Vi0) {
        vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__data_in[__Vi0] = VL_RAND_RESET_I(8);
    }
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__data_in_valid = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__data_in_ready = VL_RAND_RESET_I(1);
    for (int __Vi0 = 0; __Vi0 < 2; ++__Vi0) {
        vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__weight[__Vi0] = VL_RAND_RESET_I(8);
    }
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__weight_valid = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__weight_ready = VL_RAND_RESET_I(1);
    for (int __Vi0 = 0; __Vi0 < 2; ++__Vi0) {
        vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__data_out[__Vi0] = VL_RAND_RESET_I(16);
    }
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__data_out_valid = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__data_out_ready = VL_RAND_RESET_I(1);
    for (int __Vi0 = 0; __Vi0 < 2; ++__Vi0) {
        vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__product_vector[__Vi0] = VL_RAND_RESET_I(16);
    }
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__product_data_in_valid = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__product_data_in_ready = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__product_data_out_valid = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__product_data_out_ready = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__product_data_in = VL_RAND_RESET_I(32);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__product_data_out = VL_RAND_RESET_I(32);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__join_inst__DOT__data_in_valid = VL_RAND_RESET_I(2);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__join_inst__DOT__data_in_ready = VL_RAND_RESET_I(2);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__join_inst__DOT__data_out_valid = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__join_inst__DOT__data_out_ready = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__clk = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__rst = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__data_in = VL_RAND_RESET_I(32);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__data_in_valid = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__data_in_ready = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__data_out = VL_RAND_RESET_I(32);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__data_out_valid = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__data_out_ready = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__data_buffer_out = VL_RAND_RESET_I(32);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__data_buffer_wren = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__data_out_wren = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__use_buffered_data = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__selected_data = VL_RAND_RESET_I(32);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__insert = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__remove = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__load = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__flow = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__fill = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__flush = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__unload = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__state = 0;
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__state_next = 0;
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__parallel_mult__BRA__0__KET____DOT__fixed_mult_inst__DOT__data_a = VL_RAND_RESET_I(8);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__parallel_mult__BRA__0__KET____DOT__fixed_mult_inst__DOT__data_b = VL_RAND_RESET_I(8);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__parallel_mult__BRA__0__KET____DOT__fixed_mult_inst__DOT__product = VL_RAND_RESET_I(16);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__parallel_mult__BRA__1__KET____DOT__fixed_mult_inst__DOT__data_a = VL_RAND_RESET_I(8);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__parallel_mult__BRA__1__KET____DOT__fixed_mult_inst__DOT__data_b = VL_RAND_RESET_I(8);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__parallel_mult__BRA__1__KET____DOT__fixed_mult_inst__DOT__product = VL_RAND_RESET_I(16);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__clk = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__rst = VL_RAND_RESET_I(1);
    for (int __Vi0 = 0; __Vi0 < 2; ++__Vi0) {
        vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__data_in[__Vi0] = VL_RAND_RESET_I(16);
    }
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__data_in_valid = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__data_in_ready = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__data_out = VL_RAND_RESET_I(17);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__data_out_valid = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__data_out_ready = VL_RAND_RESET_I(1);
    for (int __Vi0 = 0; __Vi0 < 2; ++__Vi0) {
        vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__data[__Vi0] = VL_RAND_RESET_Q(34);
    }
    for (int __Vi0 = 0; __Vi0 < 1; ++__Vi0) {
        vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__sum[__Vi0] = VL_RAND_RESET_Q(34);
    }
    for (int __Vi0 = 0; __Vi0 < 2; ++__Vi0) {
        vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__valid[__Vi0] = VL_RAND_RESET_I(1);
    }
    for (int __Vi0 = 0; __Vi0 < 2; ++__Vi0) {
        vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__ready[__Vi0] = VL_RAND_RESET_I(1);
    }
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__layer__DOT__data_in = VL_RAND_RESET_I(32);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__layer__DOT__data_out = VL_RAND_RESET_I(17);
    for (int __Vi0 = 0; __Vi0 < 2; ++__Vi0) {
        vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__layer__DOT__data_in_unflat[__Vi0] = VL_RAND_RESET_I(16);
    }
    for (int __Vi0 = 0; __Vi0 < 1; ++__Vi0) {
        vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__layer__DOT__data_out_unflat[__Vi0] = VL_RAND_RESET_I(17);
    }
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__clk = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__rst = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__data_in = VL_RAND_RESET_I(17);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__data_in_valid = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__data_in_ready = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__data_out = VL_RAND_RESET_I(17);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__data_out_valid = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__data_out_ready = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__data_buffer_out = VL_RAND_RESET_I(17);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__data_buffer_wren = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__data_out_wren = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__use_buffered_data = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__selected_data = VL_RAND_RESET_I(17);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__insert = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__remove = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__load = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__flow = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__fill = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__flush = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__unload = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__state = 0;
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__state_next = 0;
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__rounding__DOT__round_inst__DOT__data_in = VL_RAND_RESET_I(17);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__rounding__DOT__round_inst__DOT__data_out = VL_RAND_RESET_I(16);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__rounding__DOT__round_inst__DOT__MAX_POS = VL_RAND_RESET_I(17);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__rounding__DOT__round_inst__DOT__MAX_NEG = VL_RAND_RESET_I(17);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__rounding__DOT__round_inst__DOT__lsb_below = VL_RAND_RESET_I(3);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__rounding__DOT__round_inst__DOT__input_data = VL_RAND_RESET_I(16);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__rounding__DOT__round_inst__DOT__carry_in = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__rounding__DOT__round_inst__DOT__input_sign = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__rounding__DOT__round_inst__DOT__rounded_out_data = VL_RAND_RESET_Q(34);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__0__KET____DOT__rounding__DOT__round_inst__DOT__comp_rouded_out = VL_RAND_RESET_Q(34);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__clk = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__rst = VL_RAND_RESET_I(1);
    for (int __Vi0 = 0; __Vi0 < 2; ++__Vi0) {
        vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__data_in[__Vi0] = VL_RAND_RESET_I(8);
    }
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__data_in_valid = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__data_in_ready = VL_RAND_RESET_I(1);
    for (int __Vi0 = 0; __Vi0 < 2; ++__Vi0) {
        vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__weight[__Vi0] = VL_RAND_RESET_I(8);
    }
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__weight_valid = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__weight_ready = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__data_out = VL_RAND_RESET_I(17);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__data_out_valid = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__data_out_ready = VL_RAND_RESET_I(1);
    for (int __Vi0 = 0; __Vi0 < 2; ++__Vi0) {
        vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__pv[__Vi0] = VL_RAND_RESET_I(16);
    }
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__pv_valid = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__pv_ready = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__sum = VL_RAND_RESET_I(17);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__sum_valid = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__sum_ready = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__clk = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__rst = VL_RAND_RESET_I(1);
    for (int __Vi0 = 0; __Vi0 < 2; ++__Vi0) {
        vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__data_in[__Vi0] = VL_RAND_RESET_I(8);
    }
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__data_in_valid = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__data_in_ready = VL_RAND_RESET_I(1);
    for (int __Vi0 = 0; __Vi0 < 2; ++__Vi0) {
        vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__weight[__Vi0] = VL_RAND_RESET_I(8);
    }
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__weight_valid = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__weight_ready = VL_RAND_RESET_I(1);
    for (int __Vi0 = 0; __Vi0 < 2; ++__Vi0) {
        vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__data_out[__Vi0] = VL_RAND_RESET_I(16);
    }
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__data_out_valid = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__data_out_ready = VL_RAND_RESET_I(1);
    for (int __Vi0 = 0; __Vi0 < 2; ++__Vi0) {
        vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__product_vector[__Vi0] = VL_RAND_RESET_I(16);
    }
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__product_data_in_valid = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__product_data_in_ready = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__product_data_out_valid = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__product_data_out_ready = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__product_data_in = VL_RAND_RESET_I(32);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__product_data_out = VL_RAND_RESET_I(32);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__join_inst__DOT__data_in_valid = VL_RAND_RESET_I(2);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__join_inst__DOT__data_in_ready = VL_RAND_RESET_I(2);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__join_inst__DOT__data_out_valid = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__join_inst__DOT__data_out_ready = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__clk = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__rst = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__data_in = VL_RAND_RESET_I(32);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__data_in_valid = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__data_in_ready = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__data_out = VL_RAND_RESET_I(32);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__data_out_valid = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__data_out_ready = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__data_buffer_out = VL_RAND_RESET_I(32);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__data_buffer_wren = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__data_out_wren = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__use_buffered_data = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__selected_data = VL_RAND_RESET_I(32);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__insert = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__remove = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__load = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__flow = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__fill = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__flush = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__unload = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__state = 0;
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__state_next = 0;
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__parallel_mult__BRA__0__KET____DOT__fixed_mult_inst__DOT__data_a = VL_RAND_RESET_I(8);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__parallel_mult__BRA__0__KET____DOT__fixed_mult_inst__DOT__data_b = VL_RAND_RESET_I(8);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__parallel_mult__BRA__0__KET____DOT__fixed_mult_inst__DOT__product = VL_RAND_RESET_I(16);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__parallel_mult__BRA__1__KET____DOT__fixed_mult_inst__DOT__data_a = VL_RAND_RESET_I(8);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__parallel_mult__BRA__1__KET____DOT__fixed_mult_inst__DOT__data_b = VL_RAND_RESET_I(8);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__parallel_mult__BRA__1__KET____DOT__fixed_mult_inst__DOT__product = VL_RAND_RESET_I(16);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__clk = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__rst = VL_RAND_RESET_I(1);
    for (int __Vi0 = 0; __Vi0 < 2; ++__Vi0) {
        vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__data_in[__Vi0] = VL_RAND_RESET_I(16);
    }
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__data_in_valid = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__data_in_ready = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__data_out = VL_RAND_RESET_I(17);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__data_out_valid = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__data_out_ready = VL_RAND_RESET_I(1);
    for (int __Vi0 = 0; __Vi0 < 2; ++__Vi0) {
        vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__data[__Vi0] = VL_RAND_RESET_Q(34);
    }
    for (int __Vi0 = 0; __Vi0 < 1; ++__Vi0) {
        vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__sum[__Vi0] = VL_RAND_RESET_Q(34);
    }
    for (int __Vi0 = 0; __Vi0 < 2; ++__Vi0) {
        vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__valid[__Vi0] = VL_RAND_RESET_I(1);
    }
    for (int __Vi0 = 0; __Vi0 < 2; ++__Vi0) {
        vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__ready[__Vi0] = VL_RAND_RESET_I(1);
    }
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__layer__DOT__data_in = VL_RAND_RESET_I(32);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__layer__DOT__data_out = VL_RAND_RESET_I(17);
    for (int __Vi0 = 0; __Vi0 < 2; ++__Vi0) {
        vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__layer__DOT__data_in_unflat[__Vi0] = VL_RAND_RESET_I(16);
    }
    for (int __Vi0 = 0; __Vi0 < 1; ++__Vi0) {
        vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__layer__DOT__data_out_unflat[__Vi0] = VL_RAND_RESET_I(17);
    }
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__clk = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__rst = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__data_in = VL_RAND_RESET_I(17);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__data_in_valid = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__data_in_ready = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__data_out = VL_RAND_RESET_I(17);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__data_out_valid = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__data_out_ready = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__data_buffer_out = VL_RAND_RESET_I(17);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__data_buffer_wren = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__data_out_wren = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__use_buffered_data = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__selected_data = VL_RAND_RESET_I(17);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__insert = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__remove = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__load = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__flow = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__fill = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__flush = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__unload = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__state = 0;
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__state_next = 0;
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__rounding__DOT__round_inst__DOT__data_in = VL_RAND_RESET_I(17);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__rounding__DOT__round_inst__DOT__data_out = VL_RAND_RESET_I(16);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__rounding__DOT__round_inst__DOT__MAX_POS = VL_RAND_RESET_I(17);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__rounding__DOT__round_inst__DOT__MAX_NEG = VL_RAND_RESET_I(17);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__rounding__DOT__round_inst__DOT__lsb_below = VL_RAND_RESET_I(3);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__rounding__DOT__round_inst__DOT__input_data = VL_RAND_RESET_I(16);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__rounding__DOT__round_inst__DOT__carry_in = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__rounding__DOT__round_inst__DOT__input_sign = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__rounding__DOT__round_inst__DOT__rounded_out_data = VL_RAND_RESET_Q(34);
    vlSelf->simple_matmul__DOT__multi_row__BRA__0__KET____DOT__multi_col__BRA__1__KET____DOT__rounding__DOT__round_inst__DOT__comp_rouded_out = VL_RAND_RESET_Q(34);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__clk = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__rst = VL_RAND_RESET_I(1);
    for (int __Vi0 = 0; __Vi0 < 2; ++__Vi0) {
        vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__data_in[__Vi0] = VL_RAND_RESET_I(8);
    }
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__data_in_valid = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__data_in_ready = VL_RAND_RESET_I(1);
    for (int __Vi0 = 0; __Vi0 < 2; ++__Vi0) {
        vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__weight[__Vi0] = VL_RAND_RESET_I(8);
    }
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__weight_valid = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__weight_ready = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__data_out = VL_RAND_RESET_I(17);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__data_out_valid = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__data_out_ready = VL_RAND_RESET_I(1);
    for (int __Vi0 = 0; __Vi0 < 2; ++__Vi0) {
        vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__pv[__Vi0] = VL_RAND_RESET_I(16);
    }
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__pv_valid = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__pv_ready = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__sum = VL_RAND_RESET_I(17);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__sum_valid = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__sum_ready = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__clk = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__rst = VL_RAND_RESET_I(1);
    for (int __Vi0 = 0; __Vi0 < 2; ++__Vi0) {
        vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__data_in[__Vi0] = VL_RAND_RESET_I(8);
    }
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__data_in_valid = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__data_in_ready = VL_RAND_RESET_I(1);
    for (int __Vi0 = 0; __Vi0 < 2; ++__Vi0) {
        vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__weight[__Vi0] = VL_RAND_RESET_I(8);
    }
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__weight_valid = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__weight_ready = VL_RAND_RESET_I(1);
    for (int __Vi0 = 0; __Vi0 < 2; ++__Vi0) {
        vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__data_out[__Vi0] = VL_RAND_RESET_I(16);
    }
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__data_out_valid = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__data_out_ready = VL_RAND_RESET_I(1);
    for (int __Vi0 = 0; __Vi0 < 2; ++__Vi0) {
        vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__product_vector[__Vi0] = VL_RAND_RESET_I(16);
    }
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__product_data_in_valid = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__product_data_in_ready = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__product_data_out_valid = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__product_data_out_ready = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__product_data_in = VL_RAND_RESET_I(32);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__product_data_out = VL_RAND_RESET_I(32);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__join_inst__DOT__data_in_valid = VL_RAND_RESET_I(2);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__join_inst__DOT__data_in_ready = VL_RAND_RESET_I(2);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__join_inst__DOT__data_out_valid = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__join_inst__DOT__data_out_ready = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__clk = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__rst = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__data_in = VL_RAND_RESET_I(32);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__data_in_valid = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__data_in_ready = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__data_out = VL_RAND_RESET_I(32);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__data_out_valid = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__data_out_ready = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__data_buffer_out = VL_RAND_RESET_I(32);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__data_buffer_wren = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__data_out_wren = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__use_buffered_data = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__selected_data = VL_RAND_RESET_I(32);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__insert = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__remove = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__load = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__flow = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__fill = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__flush = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__unload = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__state = 0;
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__state_next = 0;
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__parallel_mult__BRA__0__KET____DOT__fixed_mult_inst__DOT__data_a = VL_RAND_RESET_I(8);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__parallel_mult__BRA__0__KET____DOT__fixed_mult_inst__DOT__data_b = VL_RAND_RESET_I(8);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__parallel_mult__BRA__0__KET____DOT__fixed_mult_inst__DOT__product = VL_RAND_RESET_I(16);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__parallel_mult__BRA__1__KET____DOT__fixed_mult_inst__DOT__data_a = VL_RAND_RESET_I(8);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__parallel_mult__BRA__1__KET____DOT__fixed_mult_inst__DOT__data_b = VL_RAND_RESET_I(8);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__parallel_mult__BRA__1__KET____DOT__fixed_mult_inst__DOT__product = VL_RAND_RESET_I(16);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__clk = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__rst = VL_RAND_RESET_I(1);
    for (int __Vi0 = 0; __Vi0 < 2; ++__Vi0) {
        vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__data_in[__Vi0] = VL_RAND_RESET_I(16);
    }
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__data_in_valid = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__data_in_ready = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__data_out = VL_RAND_RESET_I(17);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__data_out_valid = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__data_out_ready = VL_RAND_RESET_I(1);
    for (int __Vi0 = 0; __Vi0 < 2; ++__Vi0) {
        vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__data[__Vi0] = VL_RAND_RESET_Q(34);
    }
    for (int __Vi0 = 0; __Vi0 < 1; ++__Vi0) {
        vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__sum[__Vi0] = VL_RAND_RESET_Q(34);
    }
    for (int __Vi0 = 0; __Vi0 < 2; ++__Vi0) {
        vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__valid[__Vi0] = VL_RAND_RESET_I(1);
    }
    for (int __Vi0 = 0; __Vi0 < 2; ++__Vi0) {
        vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__ready[__Vi0] = VL_RAND_RESET_I(1);
    }
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__layer__DOT__data_in = VL_RAND_RESET_I(32);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__layer__DOT__data_out = VL_RAND_RESET_I(17);
    for (int __Vi0 = 0; __Vi0 < 2; ++__Vi0) {
        vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__layer__DOT__data_in_unflat[__Vi0] = VL_RAND_RESET_I(16);
    }
    for (int __Vi0 = 0; __Vi0 < 1; ++__Vi0) {
        vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__layer__DOT__data_out_unflat[__Vi0] = VL_RAND_RESET_I(17);
    }
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__clk = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__rst = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__data_in = VL_RAND_RESET_I(17);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__data_in_valid = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__data_in_ready = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__data_out = VL_RAND_RESET_I(17);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__data_out_valid = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__data_out_ready = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__data_buffer_out = VL_RAND_RESET_I(17);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__data_buffer_wren = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__data_out_wren = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__use_buffered_data = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__selected_data = VL_RAND_RESET_I(17);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__insert = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__remove = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__load = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__flow = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__fill = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__flush = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__unload = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__state = 0;
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__state_next = 0;
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__rounding__DOT__round_inst__DOT__data_in = VL_RAND_RESET_I(17);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__rounding__DOT__round_inst__DOT__data_out = VL_RAND_RESET_I(16);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__rounding__DOT__round_inst__DOT__MAX_POS = VL_RAND_RESET_I(17);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__rounding__DOT__round_inst__DOT__MAX_NEG = VL_RAND_RESET_I(17);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__rounding__DOT__round_inst__DOT__lsb_below = VL_RAND_RESET_I(3);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__rounding__DOT__round_inst__DOT__input_data = VL_RAND_RESET_I(16);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__rounding__DOT__round_inst__DOT__carry_in = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__rounding__DOT__round_inst__DOT__input_sign = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__rounding__DOT__round_inst__DOT__rounded_out_data = VL_RAND_RESET_Q(34);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__0__KET____DOT__rounding__DOT__round_inst__DOT__comp_rouded_out = VL_RAND_RESET_Q(34);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__clk = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__rst = VL_RAND_RESET_I(1);
    for (int __Vi0 = 0; __Vi0 < 2; ++__Vi0) {
        vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__data_in[__Vi0] = VL_RAND_RESET_I(8);
    }
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__data_in_valid = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__data_in_ready = VL_RAND_RESET_I(1);
    for (int __Vi0 = 0; __Vi0 < 2; ++__Vi0) {
        vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__weight[__Vi0] = VL_RAND_RESET_I(8);
    }
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__weight_valid = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__weight_ready = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__data_out = VL_RAND_RESET_I(17);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__data_out_valid = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__data_out_ready = VL_RAND_RESET_I(1);
    for (int __Vi0 = 0; __Vi0 < 2; ++__Vi0) {
        vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__pv[__Vi0] = VL_RAND_RESET_I(16);
    }
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__pv_valid = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__pv_ready = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__sum = VL_RAND_RESET_I(17);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__sum_valid = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__sum_ready = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__clk = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__rst = VL_RAND_RESET_I(1);
    for (int __Vi0 = 0; __Vi0 < 2; ++__Vi0) {
        vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__data_in[__Vi0] = VL_RAND_RESET_I(8);
    }
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__data_in_valid = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__data_in_ready = VL_RAND_RESET_I(1);
    for (int __Vi0 = 0; __Vi0 < 2; ++__Vi0) {
        vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__weight[__Vi0] = VL_RAND_RESET_I(8);
    }
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__weight_valid = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__weight_ready = VL_RAND_RESET_I(1);
    for (int __Vi0 = 0; __Vi0 < 2; ++__Vi0) {
        vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__data_out[__Vi0] = VL_RAND_RESET_I(16);
    }
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__data_out_valid = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__data_out_ready = VL_RAND_RESET_I(1);
    for (int __Vi0 = 0; __Vi0 < 2; ++__Vi0) {
        vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__product_vector[__Vi0] = VL_RAND_RESET_I(16);
    }
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__product_data_in_valid = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__product_data_in_ready = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__product_data_out_valid = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__product_data_out_ready = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__product_data_in = VL_RAND_RESET_I(32);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__product_data_out = VL_RAND_RESET_I(32);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__join_inst__DOT__data_in_valid = VL_RAND_RESET_I(2);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__join_inst__DOT__data_in_ready = VL_RAND_RESET_I(2);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__join_inst__DOT__data_out_valid = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__join_inst__DOT__data_out_ready = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__clk = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__rst = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__data_in = VL_RAND_RESET_I(32);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__data_in_valid = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__data_in_ready = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__data_out = VL_RAND_RESET_I(32);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__data_out_valid = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__data_out_ready = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__data_buffer_out = VL_RAND_RESET_I(32);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__data_buffer_wren = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__data_out_wren = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__use_buffered_data = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__selected_data = VL_RAND_RESET_I(32);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__insert = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__remove = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__load = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__flow = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__fill = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__flush = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__unload = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__state = 0;
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__register_slice__DOT__state_next = 0;
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__parallel_mult__BRA__0__KET____DOT__fixed_mult_inst__DOT__data_a = VL_RAND_RESET_I(8);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__parallel_mult__BRA__0__KET____DOT__fixed_mult_inst__DOT__data_b = VL_RAND_RESET_I(8);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__parallel_mult__BRA__0__KET____DOT__fixed_mult_inst__DOT__product = VL_RAND_RESET_I(16);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__parallel_mult__BRA__1__KET____DOT__fixed_mult_inst__DOT__data_a = VL_RAND_RESET_I(8);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__parallel_mult__BRA__1__KET____DOT__fixed_mult_inst__DOT__data_b = VL_RAND_RESET_I(8);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_vector_mult_inst__DOT__parallel_mult__BRA__1__KET____DOT__fixed_mult_inst__DOT__product = VL_RAND_RESET_I(16);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__clk = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__rst = VL_RAND_RESET_I(1);
    for (int __Vi0 = 0; __Vi0 < 2; ++__Vi0) {
        vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__data_in[__Vi0] = VL_RAND_RESET_I(16);
    }
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__data_in_valid = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__data_in_ready = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__data_out = VL_RAND_RESET_I(17);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__data_out_valid = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__data_out_ready = VL_RAND_RESET_I(1);
    for (int __Vi0 = 0; __Vi0 < 2; ++__Vi0) {
        vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__data[__Vi0] = VL_RAND_RESET_Q(34);
    }
    for (int __Vi0 = 0; __Vi0 < 1; ++__Vi0) {
        vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__sum[__Vi0] = VL_RAND_RESET_Q(34);
    }
    for (int __Vi0 = 0; __Vi0 < 2; ++__Vi0) {
        vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__valid[__Vi0] = VL_RAND_RESET_I(1);
    }
    for (int __Vi0 = 0; __Vi0 < 2; ++__Vi0) {
        vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__ready[__Vi0] = VL_RAND_RESET_I(1);
    }
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__layer__DOT__data_in = VL_RAND_RESET_I(32);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__layer__DOT__data_out = VL_RAND_RESET_I(17);
    for (int __Vi0 = 0; __Vi0 < 2; ++__Vi0) {
        vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__layer__DOT__data_in_unflat[__Vi0] = VL_RAND_RESET_I(16);
    }
    for (int __Vi0 = 0; __Vi0 < 1; ++__Vi0) {
        vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__layer__DOT__data_out_unflat[__Vi0] = VL_RAND_RESET_I(17);
    }
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__clk = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__rst = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__data_in = VL_RAND_RESET_I(17);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__data_in_valid = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__data_in_ready = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__data_out = VL_RAND_RESET_I(17);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__data_out_valid = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__data_out_ready = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__data_buffer_out = VL_RAND_RESET_I(17);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__data_buffer_wren = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__data_out_wren = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__use_buffered_data = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__selected_data = VL_RAND_RESET_I(17);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__insert = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__remove = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__load = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__flow = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__fill = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__flush = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__unload = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__state = 0;
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__dot_product_inst__DOT__fixed_adder_tree_inst__DOT__gen_adder_tree__DOT__level__BRA__0__KET____DOT__register_slice__DOT__state_next = 0;
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__rounding__DOT__round_inst__DOT__data_in = VL_RAND_RESET_I(17);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__rounding__DOT__round_inst__DOT__data_out = VL_RAND_RESET_I(16);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__rounding__DOT__round_inst__DOT__MAX_POS = VL_RAND_RESET_I(17);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__rounding__DOT__round_inst__DOT__MAX_NEG = VL_RAND_RESET_I(17);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__rounding__DOT__round_inst__DOT__lsb_below = VL_RAND_RESET_I(3);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__rounding__DOT__round_inst__DOT__input_data = VL_RAND_RESET_I(16);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__rounding__DOT__round_inst__DOT__carry_in = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__rounding__DOT__round_inst__DOT__input_sign = VL_RAND_RESET_I(1);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__rounding__DOT__round_inst__DOT__rounded_out_data = VL_RAND_RESET_Q(34);
    vlSelf->simple_matmul__DOT__multi_row__BRA__1__KET____DOT__multi_col__BRA__1__KET____DOT__rounding__DOT__round_inst__DOT__comp_rouded_out = VL_RAND_RESET_Q(34);
    vlSelf->__Vtrigprevexpr___TOP__clk__0 = VL_RAND_RESET_I(1);
}

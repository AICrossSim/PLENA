// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design internal header
// See Vvec_elem_acc.h for the primary calling header

#ifndef VERILATED_VVEC_ELEM_ACC___024ROOT_H_
#define VERILATED_VVEC_ELEM_ACC___024ROOT_H_  // guard

#include "verilated.h"

class Vvec_elem_acc__Syms;

class Vvec_elem_acc___024root final : public VerilatedModule {
  public:

    // DESIGN SPECIFIC STATE
    VL_IN8(clk,0,0);
    VL_IN8(index,5,0);
    VL_IN8(write_en,0,0);
    VL_IN8(read_en,0,0);
    VL_IN8(v_in_ready,0,0);
    CData/*0:0*/ __Vclklast__TOP__clk;
    VL_IN(write_data,31,0);
    VL_OUT(read_data,31,0);
    VL_IN(V_in[8],31,0);
    VL_OUT(V_out[8],31,0);
    VlUnpacked<IData/*31:0*/, 8> vec_elem_acc__DOT__mem;

    // INTERNAL VARIABLES
    Vvec_elem_acc__Syms* const vlSymsp;

    // CONSTRUCTORS
    Vvec_elem_acc___024root(Vvec_elem_acc__Syms* symsp, const char* name);
    ~Vvec_elem_acc___024root();
    VL_UNCOPYABLE(Vvec_elem_acc___024root);

    // INTERNAL METHODS
    void __Vconfigure(bool first);
} VL_ATTR_ALIGNED(VL_CACHE_LINE_BYTES);


#endif  // guard

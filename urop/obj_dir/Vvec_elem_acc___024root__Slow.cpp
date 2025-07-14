// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vvec_elem_acc.h for the primary calling header

#include "verilated.h"

#include "Vvec_elem_acc__Syms.h"
#include "Vvec_elem_acc___024root.h"

void Vvec_elem_acc___024root___ctor_var_reset(Vvec_elem_acc___024root* vlSelf);

Vvec_elem_acc___024root::Vvec_elem_acc___024root(Vvec_elem_acc__Syms* symsp, const char* name)
    : VerilatedModule{name}
    , vlSymsp{symsp}
 {
    // Reset structure values
    Vvec_elem_acc___024root___ctor_var_reset(this);
}

void Vvec_elem_acc___024root::__Vconfigure(bool first) {
    if (false && first) {}  // Prevent unused
}

Vvec_elem_acc___024root::~Vvec_elem_acc___024root() {
}

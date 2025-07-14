// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Symbol table internal header
//
// Internal details; most calling programs do not need this header,
// unless using verilator public meta comments.

#ifndef VERILATED_VVEC_ELEM_ACC__SYMS_H_
#define VERILATED_VVEC_ELEM_ACC__SYMS_H_  // guard

#include "verilated.h"

// INCLUDE MODEL CLASS

#include "Vvec_elem_acc.h"

// INCLUDE MODULE CLASSES
#include "Vvec_elem_acc___024root.h"

// SYMS CLASS (contains all model state)
class Vvec_elem_acc__Syms final : public VerilatedSyms {
  public:
    // INTERNAL STATE
    Vvec_elem_acc* const __Vm_modelp;
    bool __Vm_didInit = false;

    // MODULE INSTANCE STATE
    Vvec_elem_acc___024root        TOP;

    // CONSTRUCTORS
    Vvec_elem_acc__Syms(VerilatedContext* contextp, const char* namep, Vvec_elem_acc* modelp);
    ~Vvec_elem_acc__Syms();

    // METHODS
    const char* name() { return TOP.name(); }
} VL_ATTR_ALIGNED(VL_CACHE_LINE_BYTES);

#endif  // guard

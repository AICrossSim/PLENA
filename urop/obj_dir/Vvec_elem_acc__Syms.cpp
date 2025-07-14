// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Symbol table implementation internals

#include "Vvec_elem_acc__Syms.h"
#include "Vvec_elem_acc.h"
#include "Vvec_elem_acc___024root.h"

// FUNCTIONS
Vvec_elem_acc__Syms::~Vvec_elem_acc__Syms()
{
}

Vvec_elem_acc__Syms::Vvec_elem_acc__Syms(VerilatedContext* contextp, const char* namep, Vvec_elem_acc* modelp)
    : VerilatedSyms{contextp}
    // Setup internal state of the Syms class
    , __Vm_modelp{modelp}
    // Setup module instances
    , TOP{this, namep}
{
    // Configure time unit / time precision
    _vm_contextp__->timeunit(-12);
    _vm_contextp__->timeprecision(-12);
    // Setup each module's pointers to their submodules
    // Setup each module's pointer back to symbol table (for public functions)
    TOP.__Vconfigure(true);
}

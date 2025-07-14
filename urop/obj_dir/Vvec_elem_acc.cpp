// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Model implementation (design independent parts)

#include "Vvec_elem_acc.h"
#include "Vvec_elem_acc__Syms.h"

//============================================================
// Constructors

Vvec_elem_acc::Vvec_elem_acc(VerilatedContext* _vcontextp__, const char* _vcname__)
    : VerilatedModel{*_vcontextp__}
    , vlSymsp{new Vvec_elem_acc__Syms(contextp(), _vcname__, this)}
    , clk{vlSymsp->TOP.clk}
    , index{vlSymsp->TOP.index}
    , write_en{vlSymsp->TOP.write_en}
    , read_en{vlSymsp->TOP.read_en}
    , v_in_ready{vlSymsp->TOP.v_in_ready}
    , write_data{vlSymsp->TOP.write_data}
    , read_data{vlSymsp->TOP.read_data}
    , V_in{vlSymsp->TOP.V_in}
    , V_out{vlSymsp->TOP.V_out}
    , rootp{&(vlSymsp->TOP)}
{
    // Register model with the context
    contextp()->addModel(this);
}

Vvec_elem_acc::Vvec_elem_acc(const char* _vcname__)
    : Vvec_elem_acc(Verilated::threadContextp(), _vcname__)
{
}

//============================================================
// Destructor

Vvec_elem_acc::~Vvec_elem_acc() {
    delete vlSymsp;
}

//============================================================
// Evaluation loop

void Vvec_elem_acc___024root___eval_initial(Vvec_elem_acc___024root* vlSelf);
void Vvec_elem_acc___024root___eval_settle(Vvec_elem_acc___024root* vlSelf);
void Vvec_elem_acc___024root___eval(Vvec_elem_acc___024root* vlSelf);
#ifdef VL_DEBUG
void Vvec_elem_acc___024root___eval_debug_assertions(Vvec_elem_acc___024root* vlSelf);
#endif  // VL_DEBUG
void Vvec_elem_acc___024root___final(Vvec_elem_acc___024root* vlSelf);

static void _eval_initial_loop(Vvec_elem_acc__Syms* __restrict vlSymsp) {
    vlSymsp->__Vm_didInit = true;
    Vvec_elem_acc___024root___eval_initial(&(vlSymsp->TOP));
    // Evaluate till stable
    do {
        VL_DEBUG_IF(VL_DBG_MSGF("+ Initial loop\n"););
        Vvec_elem_acc___024root___eval_settle(&(vlSymsp->TOP));
        Vvec_elem_acc___024root___eval(&(vlSymsp->TOP));
    } while (0);
}

void Vvec_elem_acc::eval_step() {
    VL_DEBUG_IF(VL_DBG_MSGF("+++++TOP Evaluate Vvec_elem_acc::eval_step\n"); );
#ifdef VL_DEBUG
    // Debug assertions
    Vvec_elem_acc___024root___eval_debug_assertions(&(vlSymsp->TOP));
#endif  // VL_DEBUG
    // Initialize
    if (VL_UNLIKELY(!vlSymsp->__Vm_didInit)) _eval_initial_loop(vlSymsp);
    // Evaluate till stable
    do {
        VL_DEBUG_IF(VL_DBG_MSGF("+ Clock loop\n"););
        Vvec_elem_acc___024root___eval(&(vlSymsp->TOP));
    } while (0);
    // Evaluate cleanup
}

//============================================================
// Utilities

const char* Vvec_elem_acc::name() const {
    return vlSymsp->name();
}

//============================================================
// Invoke final blocks

VL_ATTR_COLD void Vvec_elem_acc::final() {
    Vvec_elem_acc___024root___final(&(vlSymsp->TOP));
}

//============================================================
// Implementations of abstract methods from VerilatedModel

const char* Vvec_elem_acc::hierName() const { return vlSymsp->name(); }
const char* Vvec_elem_acc::modelName() const { return "Vvec_elem_acc"; }
unsigned Vvec_elem_acc::threads() const { return 1; }

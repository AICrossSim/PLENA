#include "Vvec_shift.h"
#include "verilated.h"
#include <iostream>
#include <iomanip>

#define VDEPTH 8

vluint64_t main_time = 0;
double sc_time_stamp() { return main_time; }

// Simulate one clock tick
void tick(Vvec_shift* dut) {
    dut->clk = 0;
    dut->eval();
    main_time += 5;

    dut->clk = 1;
    dut->eval();
    main_time += 5;
}

int main(int argc, char** argv) {
    Verilated::commandArgs(argc, argv);
    Vvec_shift* dut = new Vvec_shift;

    // Reset state
    dut->clk = 0;
    dut->v_in_ready = 0;
    dut->shift = 0;
    for (int i = 0; i < VDEPTH; i++) {
        dut->V_in[i] = 0;
    }

    // Test vector
    for (int i = 0; i < VDEPTH; i++) {
        dut->V_in[i] = i + 1;  // Example: [1, 2, 3, ..., 8]
    }
    dut->shift = 2; // Shift vector by 2 positions
    dut->v_in_ready = 1;

    tick(dut); // One clock to apply the input

    dut->v_in_ready = 0; // Deassert input
    tick(dut);           // Output should be valid now

    std::cout << "Input vector: ";
    for (int i = 0; i < VDEPTH; i++) {
        std::cout << dut->V_in[i] << " ";
    }
    std::cout << "\n";

    std::cout << "Shifted output vector: ";
    for (int i = 0; i < VDEPTH; i++) {
        std::cout << dut->V_out[i] << " ";
    }
    std::cout << "\n";

    std::cout << "v_out_ready: " << (int)dut->v_out_ready << "\n";

    delete dut;
    return 0;
}

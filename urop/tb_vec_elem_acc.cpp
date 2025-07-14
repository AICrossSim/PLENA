#include "Vvec_elem_acc.h"
#include "verilated.h"
#include <iostream>
#include <iomanip>

vluint64_t main_time = 0;
double sc_time_stamp() { return main_time; }

void tick(Vvec_elem_acc* dut) {
    dut->clk = 0;
    dut->eval();
    main_time += 5;

    dut->clk = 1;
    dut->eval();
    main_time += 5;
}

int main(int argc, char** argv) {
    Verilated::commandArgs(argc, argv);
    Vvec_elem_acc* dut = new Vvec_elem_acc;

    // Initialize inputs
    dut->v_in_ready = 0;
    dut->write_en = 0;
    dut->read_en = 0;
    dut->index = 0;
    dut->write_data = 0;

    // Initialize input vector V_in to zero
    for (int i = 0; i < 8; i++) {
        dut->V_in[i] = 0;
    }

    // Load initial vector into memory
    for (int i = 0; i < 8; i++) {
        dut->V_in[i] = i + 10; // example values: 10,11,...17
    }
    dut->v_in_ready = 1;
    tick(dut);
    dut->v_in_ready = 0;
    tick(dut);

    std::cout << "Memory initialized with V_in:" << std::endl;
    for (int i = 0; i < 8; i++) {
        std::cout << "  mem[" << i << "] = " << std::hex << dut->V_out[i] << std::endl;
    }

    // Write a new value at index 3
    dut->index = 3;
    dut->write_data = 0x2025;
    dut->write_en = 1;
    tick(dut);
    dut->write_en = 0;
    tick(dut);

    std::cout << "After write to index 3:" << std::endl;
    for (int i = 0; i < 8; i++) {
        std::cout << "  mem[" << i << "] = " << std::hex << dut->V_out[i] << std::endl;
    }

    // Read from index 3
    dut->index = 3;
    dut->read_en = 1;
    tick(dut);
    dut->read_en = 0;
    tick(dut);

    std::cout << "Read data at index 3: 0x" << std::hex << dut->read_data << std::endl;

    // Read from index 5 (should be initial value)
    dut->index = 5;
    dut->read_en = 1;
    tick(dut);
    dut->read_en = 0;
    tick(dut);

    std::cout << "Read data at index 5: 0x" << std::hex << dut->read_data << std::endl;

    delete dut;
    return 0;
}

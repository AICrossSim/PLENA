#include "Vprefix_scan_bk.h"
#include "verilated.h"
#include <iostream>
#include <cstdlib>
#include <ctime>

#define N 8
#define DATA_WIDTH 32

int main(int argc, char **argv) {
    Verilated::commandArgs(argc, argv);

    Vprefix_scan_bk *dut = new Vprefix_scan_bk;

    // Random input
    uint32_t input[N];
    srand(time(0));
    for (int i = 0; i < N; ++i) {
        input[i] = rand() % 10; // small values for easy viewing
        dut->data_in[i] = input[i];
    }

    dut->eval();

    // Print input
    std::cout << "Input: ";
    for (int i = 0; i < N; ++i)
        std::cout << input[i] << " ";
    std::cout << std::endl;

    // Print output
    std::cout << "Output (inclusive scan): ";
    for (int i = 0; i < N; ++i)
        std::cout << dut->data_out[i] << " ";
    std::cout << std::endl;

    // Reference calculation
    std::cout << "Expected: ";
    uint32_t acc = 0;
    for (int i = 0; i < N; ++i) {
        acc += input[i];
        std::cout << acc << " ";
    }
    std::cout << std::endl;

    delete dut;
    return 0;
}

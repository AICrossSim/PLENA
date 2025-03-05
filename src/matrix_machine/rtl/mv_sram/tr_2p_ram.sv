// This is the module that is responsible for mapping the sram address to the sub_sram_addr_array
// Note: Here we assume that the sram_addr refers to the start of the tile matrix we want to read.

module ram_access_mapping # (
    parameter int unsigned DataWidth = 4,
    parameter int unsigned MLEN = 16,
    parameter int unsigned ParallelRdDim = 4,
    parameter int unsigned AddrLen = 6, 
    parameter int unsigned SubSRAMDim = MLEN / ParallelRdDim;                 // The number of sub SRAMs
    parameter type logic [AddrLen-1:0] AddrType [SubSRAMDim]

)(
    input logic clk,
    input logic rst,
    input logic [AddrLen-1:0] sram_addr,
    input logic write_valid,
    input logic transpose_read,
    output AddrType sub_sram_addr_array,
    output logic end_of_tile_read
);


// -----
// Params
// -----

localparam int unsigned CRAWidth = $clog2(SubSRAMDim);      // Continuous Rd Amount Width

// -----
// Wires
// -----
logic [CRAWidth - 1 : 0] current_rd_amount;

initial begin
    for (int i = 0; i < MLEN; i++) begin
        sub_sram_addr_array[i] = 'x;
    end
    current_rd_amount = 'h0;
end

always_ff @(posedge clk or negedge rst) begin
    if (!rst) begin
        for (int i = 0; i < SubSRAMDim; i++) begin
            sub_sram_addr_array[i] = 'x;
        end
        current_rd_amount = CRAWidth'('h0);
    end
    else begin
        if (write_valid) begin
            current_rd_amount += CRAWidth'('h1);
        end
    end
end

assign end_of_tile_read = (current_rd_amount == CRA - 1);

always_comb begin
    if (transpose_read) begin
        
        sub_sram_addr_array[current_rd_amount] = sram_addr;
        for (int i = current_rd_amount; i < SubSRAMDim; i++) begin
            sub_sram_addr_array[i+1] = sub_sram_addr_array[i] + 1;
        end
        for (int i = 0; i < current_rd_amount; i++) begin
            sub_sram_addr_array[i] = sub_sram_addr_array[i] + 1;
        end

    else begin
        for (int i = 0; i < MLEN; i++) begin
            sub_sram_addr_array[i] = sram_addr + current_rd_amount;
        end
    end
end

    
endmodule
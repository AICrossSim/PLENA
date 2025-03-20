

/*
Module      : data_concatenator
Description : 
*/


module direct_mapped_cache #(
    parameter int ADDR_WIDTH = 16,  // Address width
    parameter int DATA_WIDTH = 32,  // Data width per cache line
    parameter int CACHE_SIZE = 256  // Number of cache lines
)(
    input  logic                     clk,
    input  logic                     rst_n,
    input  logic                     read,      // Read request
    input  logic                     write,     // Write request
    input  logic [ADDR_WIDTH-1:0]    addr,      // Memory address
    input  logic [DATA_WIDTH-1:0]    write_data,// Data to write
    output logic                     hit,       // Cache hit
    output logic [DATA_WIDTH-1:0]    read_data  // Data read from cache
);

    // Derived Parameters
    localparam INDEX_BITS = $clog2(CACHE_SIZE); // Bits for cache index
    localparam TAG_BITS = ADDR_WIDTH - INDEX_BITS; // Bits for tag

    // Cache Storage
    logic [CACHE_SIZE-1:0][TAG_BITS-1:0] tag_array;  // Tag storage
    logic [CACHE_SIZE-1:0][DATA_WIDTH-1:0] data_array; // Data storage
    logic [CACHE_SIZE-1:0] valid_array; // Valid bit storage

    // Address Breakdown
    wire [TAG_BITS-1:0] tag = addr[ADDR_WIDTH-1:INDEX_BITS]; // Extract tag
    wire [INDEX_BITS-1:0] index = addr[INDEX_BITS-1:0]; // Extract index

    // Check if cache hit
    assign hit = valid_array[index] && (tag_array[index] == tag);

    // Read Operation
    assign read_data = hit ? data_array[index] : '0; // Return valid data

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            valid_array <= '0; // Invalidate all cache lines
        end else begin
            if (write) begin
                // On write, update cache entry
                tag_array[index] <= tag;
                data_array[index] <= write_data;
                valid_array[index] <= 1'b1; // Mark as valid
            end
        end
    end

endmodule

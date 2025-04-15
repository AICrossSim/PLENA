module matrix_collector #(
    parameter int DATA_WIDTH = 32,
    parameter int MLEN       = 64,
    parameter int Collect_Dim = 8
)(
    input  logic                                clk,
    input  logic                                rst_n,

    // Input port
    input  logic [Collect_Dim*DATA_WIDTH-1:0]   in_data,
    input  logic                                in_valid,
    output logic                                in_ready,

    // Output port
    output logic [MLEN*DATA_WIDTH-1:0]          out_matrix,
    output logic                                out_valid,
    input  logic                                out_ready
);

    localparam int NUM_CYCLES = MLEN / Collect_Dim;
    localparam int ADDR_WIDTH = $clog2(NUM_CYCLES + 1);

    // Internal storage
    logic [DATA_WIDTH-1:0] buffer [0:MLEN-1];
    logic [ADDR_WIDTH-1:0] cycle_count;

    logic collecting;
    assign collecting = (cycle_count < NUM_CYCLES);
    assign in_ready   = collecting && (!out_valid || out_ready);

    // Flatten and register output matrix
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            cycle_count <= 0;
            out_valid   <= 0;
        end else begin
            if (in_valid && in_ready) begin
                // Write incoming data into buffer
                for (int i = 0; i < Collect_Dim; i++) begin
                    buffer[cycle_count * Collect_Dim + i] <= in_data[i*DATA_WIDTH +: DATA_WIDTH];
                end
                cycle_count <= cycle_count + 1;

                // If last cycle, prepare output matrix
                if (cycle_count + 1 == NUM_CYCLES) begin
                    out_valid <= 1;
                    for (int j = 0; j < MLEN; j++) begin
                        out_matrix[j*DATA_WIDTH +: DATA_WIDTH] <= buffer[j];
                    end
                    cycle_count <= 0;
                end
            end

            // Accepting output
            if (out_valid && out_ready) begin
                out_valid <= 0;
            end
        end
    end

endmodule

module fp_prefix_scan_syn#(
    parameter N = 8, //N must be a power of 2
    parameter int EXP_WIDTH = 8,
    parameter int MANT_WIDTH = 23,
    parameter int ADDER_CYCLES = 1
)
(
    input  logic clk,
    input  logic rst,
    input  logic  [N-1:0][EXP_WIDTH + MANT_WIDTH : 0] vin,
    output logic  [N-1:0][EXP_WIDTH + MANT_WIDTH : 0] vout,
    input  logic in_ready,
    output logic out_ready
);
    localparam LOGN = $clog2(N);
    // Pipeline registers for each stage
    logic [LOGN:0][N-1:0][EXP_WIDTH + MANT_WIDTH:0] temp ;
    // logic valid_pipe [LOGN-1:0];
    // logic signed [LOGN:0][N-1:0][OUT_EXP_WIDTH-1:0] temp_exp;
    // logic signed [LOGN:0][N-1:0][OUT_FIX_WIDTH-1:0] temp_mant;
    logic [LOGN:0][ADDER_CYCLES:0] valid_pipe;
    // Input stage - register the inputs
    always_ff @(posedge clk) begin
        if (rst) begin
            valid_pipe[0][0] <= 1'b0;
            for (int i = 0; i < N; i++) begin
                temp[0][i] <= '0;
            end
        end else begin
            valid_pipe[0][0] <= in_ready;
            if (in_ready) begin
               for (int i = 0; i < N; i++) begin
                  temp[0][i] <= vin[i];
               end
           end
        end
    end
    // Generate adders and pipeline registers for each stage
    genvar i, s;
    generate
        for (s = 0; s < LOGN; s++) begin : stage_gen
            logic [N-1:0][EXP_WIDTH + MANT_WIDTH:0] stage;
              always_ff @(posedge clk) begin
                if (rst) begin
                    for (int j = 1; j <= ADDER_CYCLES; j++)
                        valid_pipe[s][j] <= 1'b0;
                end else begin
                    for (int j = 1; j <= ADDER_CYCLES; j++)
                        valid_pipe[s][j] <= valid_pipe[s][j-1];
                end
            end
            for (i = 0; i < N; i++) begin : adder_gen
                if (i >= (1 << s)) begin: addition_node
                    DW_fp_add_inst #(
                        .EXP_WIDTH(EXP_WIDTH),
                        .MANT_WIDTH(MANT_WIDTH),
                        .IEEE_COMPLIANCE(0)
                    ) fp_add_inst (
                        .clk(clk),
                        .rst(rst),
                        .data_a(temp[s][i]),
                        .data_b(temp[s][i-(1<<s)]),
                        .data_in_valid(valid_pipe[s][0]),
                        .data_in_ready(), // can be left unconnected if not used
                        .data_out(stage[i]),
                        .data_out_valid(), // can be left unconnected if not used
                        .data_out_ready(1'b1) // always ready
                    );
                end else begin: direct_through
                    assign stage[i] = temp[s][i];
                end
            end
            
            // Logic for stage valid check (combinational)
         always_ff @(posedge clk) begin
                if (rst) begin
                    valid_pipe[s+1] <= 1'b0;
                    for (int j = 0; j < N; j++) begin
                        temp[s+1][j] <= '0;
                    end
                end else begin
                    valid_pipe[s+1][0] <= valid_pipe[s][ADDER_CYCLES]; // All outputs must be valid
                    if (valid_pipe[s][ADDER_CYCLES]) begin
                       for (int j = 0; j < N; j++) begin
                           temp[s+1][j] <= stage[j];
                       end
                   end
                end
            end
            // Add after temp register updates in each stage
            // always_ff @(posedge clk) begin
            //     if (!rst && valid_pipe[s][ADDER_CYCLES]) begin
            //         for (int j = 0; j < N; j++) begin
            //             $display("Stage %0d output: temp[%0d][%0d] = %h (exp=%d, mant=%d)", 
            //                     s, s+1, j, temp[s+1][j],
            //                     (temp[s+1][j] >> MANT_WIDTH) & ((1 << EXP_WIDTH) - 1),
            //                     temp[s+1][j] & ((1 << MANT_WIDTH) - 1));
            //         end
            //     end
            // end
        end
    endgenerate
    assign vout = temp[LOGN];
    assign out_ready = valid_pipe[LOGN];
    
endmodule
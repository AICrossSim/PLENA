module fp_prefix_scan#(
    parameter N = 8, //N must be a power of 2
    parameter int IN_EXP_WIDTH = 5,
    parameter int IN_FIX_WIDTH = 10,
    parameter int IN_FIX_FRAC_WIDTH = IN_FIX_WIDTH - 1,
    // Amount of bits needed to shift mantissas for alignment
    parameter int OUT_EXP_WIDTH = -1,
    parameter int OUT_FIX_WIDTH = -1,
    parameter int OUT_FIX_FRAC_WIDTH = -1
)
(
    input  logic clk,
    input  logic rst,
    // input  logic signed [N-1:0][EXP_WIDTH + MANT_WIDTH : 0] vin,
    // output logic signed [N-1:0][EXP_WIDTH + MANT_WIDTH : 0] vout,
    input logic signed [N-1:0][IN_EXP_WIDTH -1:0] exp_in,
    input logic signed [N-1:0][IN_FIX_WIDTH -1:0] mant_in,
    output logic signed [N-1:0][OUT_EXP_WIDTH -1:0] exp_out,
    output logic signed [N-1:0][OUT_FIX_WIDTH -1:0] mant_out,
    input  logic in_ready,
    output logic out_ready
);
    localparam LOGN = $clog2(N);
    localparam FRAC_DIFF = OUT_FIX_FRAC_WIDTH - IN_FIX_FRAC_WIDTH;
    // Pipeline registers for each stage
    // logic signed [EXP_WIDTH + MANT_WIDTH:0] temp [LOGN+1:0][N-1:0];
    // logic valid_pipe [LOGN-1:0];
    logic signed [LOGN:0][N-1:0][OUT_EXP_WIDTH-1:0] temp_exp;
    logic signed [LOGN:0][N-1:0][OUT_FIX_WIDTH-1:0] temp_mant;
    logic [LOGN:0] valid_pipe;
    always_ff @(posedge clk) begin
            if (in_ready) begin
                $display("--------------------------------");
                $display("[HW DEBUG] Time: %0t", $time);
                $display("[HW DEBUG] mant_in[0] = %d", mant_in[0]);
                $display("[HW DEBUG] mant_in[1] = %d", mant_in[1]);
                $display("[HW DEBUG] exp_in[0] = %d", exp_in[0]);
                $display("[HW DEBUG] exp_in[1] = %d", exp_in[1]);
                $display("--------------------------------");
            end
    end
    initial begin
        $display("HARDWARE PARAMS: OUT_FIX_WIDTH=%0d, OUT_EXP_WIDTH=%0d", OUT_FIX_WIDTH, OUT_EXP_WIDTH);
        $display("HARDWARE SIGNAL WIDTHS: mant_out=%0d bits, exp_out=%0d bits", $bits(mant_out), $bits(exp_out));
    end
    // Input stage - register the inputs
    always_ff @(posedge clk) begin
        if (rst) begin
            valid_pipe[0] <= 1'b0;
            for (int i = 0; i < N; i++) begin
                // temp[0][i] <= '0;
                temp_exp[0][i] <= '0;
                temp_mant[0][i] <= '0;
            end
        end else begin
            valid_pipe[0] <= in_ready;
            for (int i = 0; i < N; i++) begin
                // Explicit assignment to ensure proper bit positioning
                //temp[0][i] <= vin[i];
                temp_exp[0][i] <= exp_in[i];
                temp_mant[0][i] <= signed'(mant_in[i]) << FRAC_DIFF;
                //temp_mant[0][i] <= mant_in[i] << FRAC_DIFF; // Scale mantissa by frac_diff
            end
        end
    end
    //logic signed [EXP_WIDTH + EXT_EXP_WIDTH + MANT_WIDTH + EXT_MANT_WIDTH:0] stage_result [N-1:0][LOGN-1:0];
   // logic stage_valid [N-1:0][LOGN-1:0];
    // Generate adders and pipeline registers for each stage
    genvar i, s;
    generate
        for (s = 0; s < LOGN; s++) begin : stage_gen
            logic signed [N-1:0][OUT_EXP_WIDTH-1:0] stage_exp;
            logic signed [N-1:0][OUT_FIX_WIDTH-1:0] stage_mant;
            
            for (i = 0; i < N; i++) begin : adder_gen
                if (i >= (1 << s)) begin: addition_node
                    fp_adder#(
                        .IN_EXP_WIDTH(IN_EXP_WIDTH),
                        .IN_FIX_WIDTH(IN_FIX_WIDTH),
                        .IN_FIX_FRAC_WIDTH(IN_FIX_FRAC_WIDTH),
                        .OUT_EXP_WIDTH(OUT_EXP_WIDTH),
                        .OUT_FIX_WIDTH(OUT_FIX_WIDTH),
                        .OUT_FIX_FRAC_WIDTH(OUT_FIX_FRAC_WIDTH)
                    ) fp_add_inst (
                        .exp_a(temp_exp[s][i]),
                        .mant_a(temp_mant[s][i]),
                        .exp_b(temp_exp[s][i-(1<<s)]),
                        .mant_b(temp_mant[s][i-(1<<s)]),
                        .exp_out(stage_exp[i]),
                        .mant_out(stage_mant[i])
                    );
                end else begin: direct_through
                    assign stage_exp[i] = temp_exp[s][i];
                    assign stage_mant[i] = temp_mant[s][i];
                end
            end
            
            // Logic for stage valid check (combinational)
         always_ff @(posedge clk) begin
                if (rst) begin
                    valid_pipe[s+1] <= 1'b0;
                    for (int j = 0; j < N; j++) begin
                        temp_exp[s+1][j] <= '0;
                        temp_mant[s+1][j] <= '0;
                    end
                end else begin
                    valid_pipe[s+1] <= valid_pipe[s];
                    for (int j = 0; j < N; j++) begin
                        temp_exp[s+1][j] <= stage_exp[j];
                        temp_mant[s+1][j] <= stage_mant[j];
                    end
                end
            end
        end
    endgenerate

    
    // Debug tap for all pipeline stages
    // Add a way to easily check values at each stage
    //logic [LOGN:0] debug_valid;
    //logic [LOGN:0][N-1:0][EXP_WIDTH + MANT_WIDTH:0] debug_values;
    
    // always_comb begin
    //     for (int s = 0; s <= LOGN; s++) begin
    //         debug_valid[s] = valid_pipe[s];
    //         for (int i = 0; i < N; i++) begin
    //             debug_values[s][i] = temp[s][i];
    //         end
    //     end
    // end
    
    // Force direct-through test mode - bypass adders for debugging
    //   logic [LOGN:0] debug_valid;
    // always_comb begin
    //     debug_valid = valid_pipe;
    // end
    
    // Output assignment - directly from the final pipeline stage
    assign exp_out = temp_exp[LOGN];
    // assign mant_out = temp_mant[LOGN]>>FRAC_DIFF;
    genvar k;
    generate
        for (k = 0; k < N; k++) begin : final_descaling
            // Use an arithmetic shift for proper sign handling
            // assign mant_out[k] = (temp_mant[LOGN][k]) >>> FRAC_DIFF;
            assign mant_out[k] = (temp_mant[LOGN][k]);
        end
    endgenerate
    assign out_ready = valid_pipe[LOGN];
    
endmodule
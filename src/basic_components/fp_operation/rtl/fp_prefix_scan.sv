module fp_prefix_scan#(
    parameter N = 8, //N must be a power of 2
    parameter IN_EXP_WIDTH = 5,
    parameter IN_FIX_WIDTH = 10,
    parameter OUT_EXP_WIDTH = 6,        // Wider to handle accumulation
    parameter OUT_FIX_WIDTH = 12 
)
(
    input  logic clk,
    input  logic signed [IN_EXP_WIDTH-1:0] exp_in [N-1:0],
    input  logic signed [IN_FIX_WIDTH-1:0] mant_in [N-1:0],
    output logic signed [OUT_EXP_WIDTH-1:0] exp_out [N-1:0],
    output logic signed [OUT_FIX_WIDTH-1:0] mant_out [N-1:0],
    input  logic in_ready,
    output logic out_ready
);
    localparam LOGN = $clog2(N);
    
    logic signed [OUT_EXP_WIDTH-1:0] temp_exp [LOGN:0][N-1:0];
    logic signed [OUT_FIX_WIDTH-1:0] temp_mant [LOGN:0][N-1:0];
    logic [$clog2(LOGN+1):0] stage;
    logic processing;
    logic done;

    // Intermediate signals for adder outputs
    logic signed [OUT_EXP_WIDTH-1:0] fp_add_exp [LOGN:0][N-1:0];
    logic signed [OUT_FIX_WIDTH-1:0] fp_add_mant [LOGN:0][N-1:0];
    
    // Create fp_adder instances for each possible addition
    genvar i, s;
    generate
        for (s = 1; s <= LOGN; s++) begin : stage_gen
            for (i = 0; i < N; i++) begin : adder_gen
                fp_adder #(
                    .IN_EXP_WIDTH(OUT_EXP_WIDTH),
                    .IN_FIX_WIDTH(OUT_FIX_WIDTH),
                    .IN_FIX_FRAC_WIDTH(OUT_FIX_WIDTH-1),
                    .OUT_EXP_WIDTH(OUT_EXP_WIDTH),
                    .OUT_FIX_WIDTH(OUT_FIX_WIDTH),
                    .OUT_FIX_FRAC_WIDTH(OUT_FIX_WIDTH-1)
                ) fp_add_inst (
                    .exp_a(temp_exp[s-1][i]),
                    .mant_a(temp_mant[s-1][i]),
                    .exp_b(temp_exp[s-1][i-(1<<(s-1))]),
                    .mant_b(temp_mant[s-1][i-(1<<(s-1))]),
                    .exp_out(fp_add_exp[s][i]),
                    .mant_out(fp_add_mant[s][i])
                );
            end
        end
    endgenerate

    /* verilator lint_off WIDTH */
    always_ff @(posedge clk) begin
        if (in_ready && !processing) begin
            // Initialize first stage with input values, converting to output width
            for (int i = 0; i < N; i++) begin
                temp_exp[0][i] <= exp_in[i];
                temp_mant[0][i] <= mant_in[i];
            end
            stage <= 1;
            processing <= 1;
            done <= 0;
        end
        else if (processing && stage <= LOGN) begin
            // Update intermediate values with adder results
            for (int i = 0; i < N; i++) begin
                // Elements that need updating
                if (i >= (1<<(stage-1))) begin
                    temp_exp[stage][i] <= fp_add_exp[stage][i];
                    temp_mant[stage][i] <= fp_add_mant[stage][i];
                end
                // Elements that pass through unchanged
                else begin
                    temp_exp[stage][i] <= temp_exp[stage-1][i];
                    temp_mant[stage][i] <= temp_mant[stage-1][i];
                end
            end
            
            // Move to next stage
            stage <= stage + 1;
            
            // Check if this was the last stage
            if (stage == LOGN) begin
                done <= 1;
                processing <= 0;
            end
        end

        // Handle output assignment
        if (done) begin
            for (int i = 0; i < N; i++) begin
                exp_out[i] <= temp_exp[LOGN][i];
                mant_out[i] <= temp_mant[LOGN][i];
            end
            out_ready <= 1;
        end else begin
            out_ready <= 0;
        end
        
        // Reset done flag after one cycle
        if (done) begin
            done <= 0;
        end
    end
endmodule
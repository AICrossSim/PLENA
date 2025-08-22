// Combinational lane barrel shifter (right shift by 'shift', zero fill)
module fp_vec_shift #(
    parameter int VLEN   = 32,   // number of lanes
    parameter int VDEPTH = 16    // bits per element
)(
    input  logic [VLEN-1:0][VDEPTH-1:0] v_in,
    input  logic [$clog2(VLEN):0]       shift,
    output logic [VLEN-1:0][VDEPTH-1:0] v_out,
    input logic clk
);

    // Intermediate signals per stage
    logic [VLEN-1:0][VDEPTH-1:0] stage [$clog2(VLEN):0];

    // Stage 0 = input vector
    assign stage[0] = v_in;

    // Barrel shifter stages
    genvar s;
    generate
        for (s = 0; s < $clog2(VLEN); s++) begin : shift_stage
            localparam int OFFSET = 1 << s;
            for (genvar i = 0; i < VLEN; i++) begin : lane
                always_comb begin
                    if (shift[s]) begin
                        if (i < OFFSET) 
                            stage[s+1][i] = '0;                  // shifted past start → zero fill
                        else
                            stage[s+1][i] = stage[s][i - OFFSET]; // shifted by OFFSET
                    end else begin
                        stage[s+1][i] = stage[s][i];             // no shift at this stage
                    end
                end
            end
        end
    endgenerate

    // Final output
    assign v_out = stage[$clog2(VLEN)];

endmodule

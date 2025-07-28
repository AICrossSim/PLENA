module fp_vec_shift #(
    parameter VLEN = 32,
    parameter VDEPTH = 8
)(
    input  logic clk,
    input  logic [VDEPTH-1:0][VLEN-1:0] V_in ,
    output logic [VDEPTH-1:0][VLEN-1:0] V_out,
    input  logic v_in_ready,
    output logic v_out_ready,
    input  logic [5:0] shift
);

    genvar i;
    generate
        for (i = 0; i < VDEPTH; i++) begin
            always_ff @(posedge clk) begin
                if (v_in_ready) begin
                    if (i < shift)
                        V_out[i] <= '0;
                    else
                        V_out[i] <= V_in[i - shift];
                end
            end
        end
    endgenerate

    // v_out_ready handled separately to avoid multiple drivers
    always_ff @(posedge clk) begin
        if (v_in_ready)
            v_out_ready <= 1;
        else
            v_out_ready <= 0;
    end

endmodule

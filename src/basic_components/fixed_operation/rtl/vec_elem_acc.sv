module vec_elem_acc #(
    parameter VLEN = 32,
    parameter VDEPTH = 8
)(
    input  logic clk,
    input  logic [VLEN-1:0] V_in [VDEPTH-1:0],
    output logic [VLEN-1:0] V_out [VDEPTH-1:0],
    input  logic [5:0] index,
    input  logic write_en,
    input  logic [VLEN-1:0] write_data,
    input  logic read_en,
    input  logic v_in_ready,
    output logic [VLEN-1:0] read_data
);

    logic [VLEN-1:0] mem [VDEPTH-1:0];

    // Copy V_in to mem element-wise on v_in_ready
    always_ff @(posedge clk) begin
        if (v_in_ready) begin
            for (int i = 0; i < VDEPTH; i++) begin
                mem[i] <= V_in[i];
            end
        end
        else if (write_en) begin
            mem[index] <= write_data;
        end
    end

    // Read data combinationally or registered?
    always_ff @(posedge clk) begin
        if (read_en) begin
            read_data <= mem[index];
        end
    end

    // Drive output memory vector
    genvar j;
    generate
        for (j = 0; j < VDEPTH; j++) begin
            assign V_out[j] = mem[j];
        end
    endgenerate

endmodule

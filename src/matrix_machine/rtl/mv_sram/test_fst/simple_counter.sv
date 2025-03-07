module simple_counter (
    input wire clk,
    input wire rst_n,
    input wire en,
    output reg [1:0] count
);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            count <= 2'b00;
        else if (en)
            count <= count + 1;
    end

    // Ensure simulation runs long enough for tracing
    `ifdef VM_TRACE_FST
    initial begin
        $display("Tracing enabled: Verilator will generate dump.fst");
        repeat (50) @(posedge clk);  // Wait for 50 clock cycles instead of using `#500;`
        $finish;  // Ensure Verilator writes the trace file
    end
    `endif

endmodule

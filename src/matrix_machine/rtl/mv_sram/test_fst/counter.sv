module counter (
    input wire clk,
    input wire rst_n,
    input wire en,
    output reg [3:0] count
);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            count <= 4'b0000;
        else if (en)
            count <= count + 1;
    end

    // // `ifdef COCOTB_SIM
    // initial begin
    //     $dumpfile("dump.vcd");
    //     $dumpvars(0, counter);
    // end
    // // `endif


endmodule


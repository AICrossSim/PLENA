`timescale 1ns/1ps

/// Assuming the input data is {a, b, c, d}
/// The output will be [ a, c, b, d ]


module subtile_transpose #(
    parameter Dim = 2,
    parameter DataWidth = 4
) (
    input  logic [Dim*Dim*DataWidth-1:0] in_data,  // Packed input vector
    input  logic transposed_read,
    output logic [Dim*Dim*DataWidth-1:0] out_data  // Unpacked output array
);

    
    // initial begin
    //     $dumpfile("dump.vcd");  // Save waveform to dump.vcd
    //     $dumpvars(0, subtile_transpose); // Dump all signals in my_design
    //     for (int i = 0; i < Dim*Dim; i++) begin
    //         $dumpvars(0, out_data[i]);
    //     end
    // end

    // Transpose the matrix
    genvar row, col;
    generate
        for (row = 0; row < Dim; row++) begin : transpose_rows
            for (col = 0; col < Dim; col++) begin : transpose_cols
                assign out_data[((col * Dim + row) + 1) * DataWidth - 1 +: DataWidth] = transposed_read ?
                    in_data[((row * Dim + col) + 1) * DataWidth - 1 +: DataWidth] :
                    in_data[((col * Dim + row) + 1) * DataWidth - 1 +: DataWidth];
            end
        end
    endgenerate

endmodule
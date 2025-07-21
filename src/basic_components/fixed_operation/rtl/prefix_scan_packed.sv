module prefix_scan_packed#(
	parameter N = 8, //N must be a power of 2
	parameter WIDTH = 32
)
(
	input  logic clk,
	input  logic [N-1:0][WIDTH-1:0] vin,
	output logic [N-1:0][WIDTH-1:0] vout,
	input  logic in_ready,
	output logic out_ready
);
	localparam LOGN = $clog2(N);
	//more memory needed for intermediate storage than naive implementation
	logic [WIDTH-1:0] temp [LOGN:0][N-1:0];
	logic [$clog2(LOGN+1):0] stage;
	logic processing;
	logic done;
/* verilator lint_off WIDTH */
	always_ff @(posedge clk) begin
		if (in_ready && !processing) begin
			for (int i = 0; i < N; i++) begin
				// Access each bit of each element separately
				for (int w = 0; w < WIDTH; w++) begin
					temp[0][i][w] <= vin[i][w];
				end
			end
			stage <= 1;
			processing <= 1;
			done <= 0;
		end
		else if (processing && stage <= LOGN) begin
			int offset = 1 << (stage - 1);
			for (int i = 0; i < N; i++) begin
				if (i>=offset)
					temp[stage][i] <= temp[stage-1][i] + temp[stage-1][i-offset];
				else
					temp[stage][i] <= temp[stage-1][i];
			end
			stage <= stage + 1;
			if (stage == LOGN) begin		
				done <= 1;
			end
		end

		if (done) begin
			for (int i = 0; i < N; i++) begin
				// Copy each bit to output array
				for (int w = 0; w < WIDTH; w++) begin
					vout[i][w] <= temp[LOGN][i][w];
				end
			end
			out_ready <= 1;
			processing <= 0;
		end else begin
			out_ready <= 0;
		end
	end
endmodule


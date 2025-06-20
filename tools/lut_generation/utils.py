def fxtodouble(data_width: int, f_width: int, fx_num: str):
    intstr, fracstr = fx_num[: data_width - f_width], fx_num[data_width - f_width :]
    intval = float(BitArray(bin=intstr).int)
    fracval = float(BitArray(bin=fracstr).uint) / 2 ** (f_width)

    return intval + fracval


def doubletofx(data_width: int, f_width: int, num: float, type="hex"):
    assert type == "bin" or type == "hex", "type can only be: 'hex' or 'bin'"
    intnum = int(num * 2 ** (f_width))
    intbits = BitArray(int=intnum, length=data_width)
    return str(intbits.bin) if type == "bin" else str(intbits)

def inttobit(data_width:int, num: float, signed: bool = True):
    intbits = BitArray(int=num, length=data_width) if signed else BitArray(uint=num, length=data_width)
    return intbits

def lookup_to_sv_file(
    in_data_width: int,
    in_f_width: int,
    data_width: int,
    f_width: int,
    function: str,
    file_path=None,
    path_with_dtype=False,
    constant_mult=1,
    floor=False,
):
    dicto = aligned_generate_lookup(
        in_data_width=in_data_width,
        in_f_width=in_f_width,
        data_width=data_width,
        f_width=f_width,
        function=function,
        type="bin",
        constant_mult=constant_mult,
        floor=floor,
    )
    dicto = {
        k: v
        for k, v in dicto.items()
        if k not in ["data_width", "f_width", "func", "in_data_width", "in_f_width"]
    }
    # Format for bit sizing
    key_format = f"{in_data_width}'b{{}}"
    value_format = f"{data_width}'b{{}}"
    if path_with_dtype:
        end = f"_{data_width}_{f_width}"
    else:
        end = ""
    # Starting the module and case statement
    sv_code = f"""
`timescale 1ns / 1ps
/* verilator lint_off UNUSEDPARAM */
module {function}_lut{end} #(
    parameter DATA_IN_0_PRECISION_0  = {in_data_width},
    parameter DATA_IN_0_PRECISION_1  = {in_f_width},
    parameter DATA_OUT_0_PRECISION_0 = {data_width},
    parameter DATA_OUT_0_PRECISION_1 = {f_width}
) (
    /* verilator lint_off UNUSEDSIGNAL */
    input  logic [{in_data_width - 1}:0] data_in_0,
    output logic [{data_width - 1}:0] data_out_0
);

"""
    sv_code += """
  always_comb begin
    case (data_in_0)
"""

    # Adding each case
    for key, value in dicto.items():
        formatted_key = key_format.format(key)
        formatted_value = value_format.format(value)
        sv_code += f"      {formatted_key}: data_out_0 = {formatted_value};\n"

    # Ending the case statement and module
    sv_code += f"      default: data_out_0 = {data_width}'b0;\n"
    sv_code += "    endcase\n"
    sv_code += "  end\n"
    sv_code += "endmodule\n"

    # Write the code to a SystemVerilog file
    with open(file_path, "w") as file:
        file.write(sv_code)

    print(f"SystemVerilog module generated and saved as {file_path}.")
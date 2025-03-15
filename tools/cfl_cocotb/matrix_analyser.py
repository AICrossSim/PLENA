def binary_string_to_hex(binary_str: str, datawidth: int) -> list:
    """
    Splits a binary string into chunks of specified datawidth and converts each to hex.
    
    :param binary_str: The binary string to process.
    :param datawidth: The width of each data chunk.
    :return: A list of hexadecimal strings corresponding to each chunk.
    """
    # Ensure binary_str length is a multiple of datawidth by padding if necessary
    remainder = len(binary_str) % datawidth
    if remainder:
        binary_str = binary_str.zfill(len(binary_str) + (datawidth - remainder))
    
    # Split into chunks of datawidth
    chunks = [binary_str[i:i+datawidth] for i in range(0, len(binary_str), datawidth)]
    
    # Convert each chunk to hexadecimal
    hex_list = [hex(int(chunk, 2))[2:].zfill(datawidth // 4) for chunk in chunks]
    
    return hex_list

class packed_array_analyser:
    def __init__(self, Data_Width, MLEN, Parallel_Wr_Dim, Parallel_Rd_Dim):
        self.Data_Width = Data_Width
        self.MLEN = MLEN
        self.Parallel_Wr_Dim = Parallel_Wr_Dim
        self.Parallel_Rd_Dim = Parallel_Rd_Dim
        self.SRAM_Amount = MLEN // Parallel_Rd_Dim
        self.ElementWidth = Data_Width * (Parallel_Rd_Dim * Parallel_Rd_Dim)
        self.ElementAmount = self.Parallel_Rd_Dim * self.Parallel_Rd_Dim
    
    def print_wdata_from_hbm(self, wdata):
        print("[")
        for i in range(self.Parallel_Wr_Dim):
            row_wdata = binary_string_to_hex(wdata[i * self.MLEN * self.Data_Width: (i + 1) * self.MLEN * self.Data_Width], self.Data_Width)
            print(row_wdata)
        print("]")

    def print_in_matrix_format(self, element_data):
        print("--------------------")
        for i in range (self.Parallel_Rd_Dim):
            for j in range (self.Parallel_Rd_Dim):
                print(element_data[i * self.Parallel_Rd_Dim + j], end = ", ")
            print()
        print("--------------------")
    
    def print_write_data_to_sram(self, input_data, sram_to_monitor):
        # Packed array struct  = []
        print("Write data from SRAM")
        wdata_width_per_sram = self.Data_Width * self.Parallel_Wr_Dim * self.Parallel_Rd_Dim
        for sram_index in sram_to_monitor:
            wdata_per_sram = binary_string_to_hex(input_data[sram_index * wdata_width_per_sram: (sram_index + 1) * wdata_width_per_sram], self.Data_Width)
            for i in range(self.Parallel_Wr_Dim // self.Parallel_Rd_Dim):
                self.print_in_matrix_format(wdata_per_sram[i * self.ElementAmount : (i + 1) * self.ElementAmount])
    
    def print_read_data_from_sram(self, output_data, sram_to_monitor):
        print("Read data from SRAM")
        for sram_index in sram_to_monitor:
            print("element", self.ElementWidth)
            rdata_per_sram = binary_string_to_hex(output_data[sram_index * self.ElementWidth : (sram_index + 1) * self.ElementWidth], self.Data_Width)
            print(rdata_per_sram)
            self.print_in_matrix_format(rdata_per_sram)


if __name__ == "__main__":
    binary_data = "110101110011"  # Example binary string
    width = 4  # Example data width
    hex_output = binary_string_to_hex(binary_data, width)
    print(hex_output)
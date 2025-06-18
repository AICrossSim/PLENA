from fp_generation import FpGenerator

class FP_mem_data_analyser:
    def __init__(self, exp_width, mant_width, num_per_row, directory=None):
        self.exp_width = exp_width
        self.mant_width = mant_width
        self.directory = directory
        self.num_per_row = num_per_row
        self.fp_generator = FpGenerator(exp_width, mant_width)

    def read_fp_mem(self, start_index=0, end_index=None):
        """Read a file containing FP values in hexadecimal format."""
        loaded_values = []
        with open(self.directory, 'r') as file:
            hex_values = file.readlines()
            for i, line in enumerate(hex_values):
                if i < start_index or (end_index is not None and i >= end_index):
                    continue
                line = line.strip()
                loaded_values.append(int(line, 16))
        return loaded_values

    
    def extract_result_fp(self, start_index, end_index):
        loaded_fp_bin = self.read_fp_mem(start_index=start_index, end_index=end_index)
        translated_fp_matrix = []
        for value in loaded_fp_bin:
            translated_fp_array = self.fp_generator.translate_packed_array_fp(self.num_per_row, self.exp_width, self.mant_width, value)
            translated_fp_matrix.append(translated_fp_array)
        return translated_fp_matrix
       



if __name__ == "__main__":
    exp_width = 7
    mant_width = 8
    num_per_row = 8
    directory = "../../test/result_mem/vector_result.mem"

    analyser = FP_mem_data_analyser(exp_width, mant_width, num_per_row, directory)
    fp_values = analyser.extract_result_fp(start_index=8, end_index=12)  # Adjust indices as needed
    print(fp_values)
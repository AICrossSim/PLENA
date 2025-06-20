from fp_generation import FpGenerator
from mx_fp_generation import MXBlockFPConverter

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


class MX_FP_mem_data_analyser:
    def __init__(self, mxfp_exp_width, mxfp_mant_width, mxfp_scale_width, blocksize, num_per_row, directory=None):
        self.mxfp_exp_width = mxfp_exp_width
        self.mxfp_mant_width = mxfp_mant_width
        self.mxfp_scale_width = mxfp_scale_width
        self.ele_directory = f"{directory}/hbm_ele.mem"
        self.scale_directory = f"{directory}/hbm_scale.mem"
        self.blocksize = blocksize
        self.num_per_row = num_per_row
        self.block_num = num_per_row // blocksize
        # Initialize the FP generator for MXFP format if needed
        self.mxfp_analyser = MXBlockFPConverter(elem_exp_width=mxfp_exp_width,
                                                elem_mant_width=mxfp_mant_width,
                                                scale_width=mxfp_scale_width,
                                                block_size=blocksize)
    
    def read_mxfp_mem(self, start_index=0, end_index=None):
        loaded_element = []
        with open(self.ele_directory, 'r') as file:
            hex_values = file.readlines()
            for i, line in enumerate(hex_values):
                if i < start_index or (end_index is not None and i >= end_index):
                    continue
                line = line.strip()
                loaded_element.append(int(line, 16))
        
        loaded_scale = []
        with open(self.scale_directory, 'r') as file:
            hex_values = file.readlines()
            for i, line in enumerate(hex_values):
                if i < start_index or (end_index is not None and i >= end_index // 2): # TODO: need to be optimised. current only support the case where block size * element = scale width * 2
                    continue
                line = line.strip()
                loaded_scale.append(int(line, 16))
        return loaded_element, loaded_scale
        

    def extract_result_mxfp(self, start_index, end_index):
        loaded_element, loaded_scale = self.read_mxfp_mem(start_index=start_index, end_index=end_index)
        for i in range(len(loaded_element)):
            print(f"Element {i}: 0x{loaded_element[i]:X}")
        for i in range(len(loaded_scale)):
            print(f"Scale {i}: 0x{loaded_scale[i]:X}")
        translated_mxfp_matrix = []
        scale_per_row_block = self.block_num * self.mxfp_scale_width
        print(f"Scale per row block: {scale_per_row_block}")
        lower_scale_mask = (1 << scale_per_row_block) - 1
        print(f"Lower scale mask: {lower_scale_mask:#0{scale_per_row_block + 2}x}")

        for i in range(len(loaded_element)):

            mxfp_elements = loaded_element[i]
            if i % 2 == 0:
                # load upper scale
                mxfp_scale = (loaded_scale[i // 2] >> scale_per_row_block) & lower_scale_mask
            else:
                # load lower scale
                mxfp_scale = loaded_scale[i // 2] & lower_scale_mask
            print(f"Element: 0x{mxfp_elements:X}\nScale:   0x{mxfp_scale:X}")
            translated_mxfp_array = self.mxfp_analyser.blockwise_convert_to_float(mxfp_elements, mxfp_scale, self.block_num)
            translated_mxfp_matrix.append(translated_mxfp_array)
        return translated_mxfp_matrix
    
    def visualise_mxfp_in_mem(self, tranlated_mxfp_matrix):
        for row_index, row in enumerate(tranlated_mxfp_matrix):
            print(f"Row {row_index}: ", end="")
            for col_index, value in enumerate(row):
                for element in value:
                    print(f"{element:.4f}", end=", " )
            print()



if __name__ == "__main__":
    # exp_width = 7
    # mant_width = 8
    # num_per_row = 8
    # directory = "../../test/result_mem/vector_result.mem"

    # analyser = FP_mem_data_analyser(exp_width, mant_width, num_per_row, directory)
    # fp_values = analyser.extract_result_fp(start_index=8, end_index=12)  # Adjust indices as needed
    # print(fp_values)
    hbm_width = 256
    mxfp_exp_width = 4
    mxfp_ele_mant = 3
    mxfp_scale_width = 16
    blocksize = 4
    num_per_row = hbm_width // (mxfp_exp_width + mxfp_ele_mant + 1)
    directory = "../../test/load_mem"
    analyser = MX_FP_mem_data_analyser(mxfp_exp_width, mxfp_ele_mant, mxfp_scale_width, blocksize, num_per_row, directory)
    mxfp_values = analyser.extract_result_mxfp(start_index=0, end_index=2)  # Adjust indices as needed
    print(mxfp_values)
    analyser.visualise_mxfp_in_mem(mxfp_values)
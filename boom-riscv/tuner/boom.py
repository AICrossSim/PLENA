import re
import subprocess
from .generalchip import General_Chip_Tuner
import time

class BOOM_Chip_Tuner(General_Chip_Tuner):

    def __init__(self, cpu_info, config_matcher_enabled):
        super().__init__(cpu_info, config_matcher_enabled)
        # Log file for the generated reports
        self.generation_path = '../processors/chipyard/sims/verilator'
        self.cpu_level_config_file = '../processors/chipyard/generators/chipyard/src/main/scala/config/BoomConfigs.scala'
        self.core_level_configuration_file = '../processors/chipyard/generators/boom/src/main/scala/v3/common/config-mixins.scala'
        self.top_level_design_name = "ChipTop"
        
    
    def modify_cpu_config(self, num_cores):
        with open(self.cpu_level_config_file, 'r') as file:
            lines = file.readlines()
        pattern = re.compile(r'new boom\.v3\.common\.WithNCustomBooms\(\d+\)')
        for i, line in enumerate(lines):
            if 'class CustomisedBoomV3Config' in line:
                for j in range(i+1, len(lines)):
                    if pattern.search(lines[j]):
                        lines[j] = pattern.sub(f'new boom.v3.common.WithNCustomBooms({num_cores})', lines[j])
                break
        with open(self.cpu_level_config_file, 'w') as file:
            file.writelines(lines)

    def modify_peripheral_and_core_config(self, input_vals):
        params_name = list(self.cpu_info.config_params.params_map.keys())[1:]
        issueparams_index = None
        for param in params_name:
            if param == 'issueParams_IQT_MEM_issueWidth':
                issueparams_index = params_name.index(param)

        with open(self.core_level_configuration_file, 'r') as file:
            lines = file.readlines()

        new_lines = []
        in_custom_boom_class = False  # Flag to check if within the correct class block
        peripheral_settings = None  # Track whether we're inside a dcache or icache block
        issue_param_positon = 0

        for index, line in enumerate(lines):
            # Check for start of WithNCustomBooms class
            if line.strip().startswith('class WithNCustomBooms'):
                in_custom_boom_class = True
                start_index = index
            elif line.strip().startswith('class') and 'WithNCustomBooms' not in line:
                in_custom_boom_class = False  # Exit block when a new class definition starts

            if in_custom_boom_class:

                # Peripheral Tuning
                if 'DCacheParams' in line:
                    peripheral_settings = 'dcache'

                elif 'ICacheParams' in line:
                    peripheral_settings = 'icache'

                elif peripheral_settings and ')' in line:  # Check for end of cache block
                    peripheral_settings = None
                
                else:
                    peripheral_settings = None
                
                if peripheral_settings:
                    for param, value in zip(params_name, input_vals):
                        if param.startswith(peripheral_settings):
                            param_name = param.split('_')[1]
                            pattern = re.compile(rf'(\b{param_name}\s*=\s*)(\d+)')
                            modified_line = pattern.sub(r'\g<1>' + str(value), line)  # Replace with new value
                else:
                    if index == start_index + 1:
                        # Branch prediction configs, TODO assuming the vairable is at the start of the customised processor config            
                        modified_line = f"new {input_vals[0]} ++\n"
                    else:
                        unit_name = line.split('=')[0].strip()
                        if unit_name in params_name:
                            unit_index = params_name.index(unit_name)
                            modified_line = f"              {unit_name} = {input_vals[unit_index]},\n"
                        
                        elif unit_name == 'issueParams':
                            issue_param_positon = index
                            modified_line = line
                        
                        elif index == issue_param_positon + 1:
                            modified_line = f"                  IssueParams(issueWidth={input_vals[issueparams_index]}, numEntries={input_vals[issueparams_index+1]}, iqType=IQT_MEM.litValue, dispatchWidth={input_vals[issueparams_index+2]}),\n"
                        
                        elif index == issue_param_positon + 2:
                            modified_line = f"                  IssueParams(issueWidth={input_vals[issueparams_index+3]}, numEntries={input_vals[issueparams_index+4]}, iqType=IQT_INT.litValue, dispatchWidth={input_vals[issueparams_index+5]}),\n"

                        elif index == issue_param_positon + 3:
                            modified_line = f"                  IssueParams(issueWidth={input_vals[issueparams_index+6]}, numEntries={input_vals[issueparams_index+7]}, iqType=IQT_FP.litValue, dispatchWidth={input_vals[issueparams_index+8]})),\n"
                        
                        else:
                            modified_line = line
                new_lines.append(modified_line)

            else:
                new_lines.append(line)  # Keep lines outside WithNCustomBooms class unchanged

        with open(self.core_level_configuration_file, 'w') as file:
            file.writelines(new_lines)

    def modify_config_files(self, input_vals):
        # CPU's overall configuration, Only modify the number of Cores
        self.modify_cpu_config(input_vals[0])
        # Core's internal configuration
        self.modify_peripheral_and_core_config(input_vals[1:])


    def tune_and_run_performance_simulation(self, new_value):
        try:
            # generate the design
            self.modify_config_files(new_value)
            # clean_command = ["make", "clean"]
            # subprocess.run(clean_command, cwd = self.generation_path, check=True)
            t1 = time.monotonic()
            run_configure_command = ["make", "-j12", "CONFIG=MediumBoomV3Config"]
            subprocess.run(run_configure_command, cwd = self.generation_path, check=True)
            t2 = time.monotonic()
            print(f"Time taken to configure the design: {t2 - t1} seconds")
            raise
            performance_results = {}
            simulation_status = "Success"
            for benchmark_to_examine in self.cpu_info.supported_output_objs.benchmark.metrics:
                run_benchmark_command = ["make", "run-binary", "CONFIG=CustomisedBoomV3Config", f"BINARY=../../toolchains/riscv-tools/riscv-tests/build/benchmarks/{benchmark_to_examine}.riscv"]
                try:
                    with open(self.processor_generation_log + benchmark_to_examine + '.log', 'w') as f:
                        subprocess.run(run_benchmark_command, check=True, stdout=f, stderr=f, cwd=self.generation_path)

                    # dhrystone, median, memcpy, multiply, qsort, rsort, spmv, tower, memcpy, vvadd
                    if benchmark_to_examine in ['dhrystone', 'median', 'multiply', 'qsort', 'rsort', 'spmv', 'towers', 'memcpy', 'vvadd']:
                        performance_results[benchmark_to_examine] = self.extract_metrics_from_mcycle_report(True, benchmark_to_examine)
                        print("<---------------------->")
                        print(benchmark_to_examine)
                        print(performance_results[benchmark_to_examine])
                    # mm
                    elif benchmark_to_examine == 'mm':
                        performance_results[benchmark_to_examine] = self.extract_instructions_and_cycles(benchmark_to_examine)
                        print("<---------------------->")
                        print(benchmark_to_examine)
                        print(performance_results[benchmark_to_examine])
                    # mt-matmul, mt-memcpy, mt-vvadd
                    elif benchmark_to_examine in ['mt-matmul', 'mt-memcpy', 'mt-vvadd']:
                        performance_results[benchmark_to_examine] = self.extract_metric_from_cycles_and_cpi_report(benchmark_to_examine)
                        print("<---------------------->")
                        print(benchmark_to_examine)
                        print(performance_results[benchmark_to_examine])
                except subprocess.CalledProcessError as e:
                    print(f"Error occurred for the current benchmark {benchmark_to_examine}")
                    performance_results[benchmark_to_examine] = self.extract_metrics_from_mcycle_report(False, benchmark_to_examine)
                    simulation_status = "Partial"
            if len(performance_results) == 0:
                return "Fail", None
            return simulation_status, performance_results
        except subprocess.CalledProcessError as e:
            # Optionally, log the error message from the exception
            print(f"Error occurred: {e}")
            return "Fail", None
        
    def build_new_processor(self, new_config):
        try:
            self.modify_config_files(new_config)
            run_configure_command = ["make", "-j12", "CONFIG=CustomisedBoomV3Config"]
            subprocess.run(run_configure_command, cwd = self.generation_path, check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error occurred: {e}")
            return False
    
    
    



if __name__ == '__main__':

    # print(extract_wns('../processors/Logs/Syn_Report/BOOM_timing_synth.rpt'))
    pass
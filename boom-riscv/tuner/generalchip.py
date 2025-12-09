import re
import subprocess
import os
import shutil


class General_Chip_Tuner:
    """This is the tuner for scr1 Cores, it could automatically customise the processor according to the param settings"""
    def __init__(self, cpu_info, config_matcher_enabled):

        self.generation_path = '../processors/chipyard/sims/verilator'
        self.vivado_project_path = f'../processors/Vivado_Prj/{cpu_info.cpu_name}_Prj/'
        self.tcl_path = f'../../tools/{cpu_info.cpu_name}/run_{cpu_info.cpu_name}_synthesis.tcl'
        # Log file for the generated reports
        self.generated_report_num = 0
        self.generated_report_directory = '../processors/Logs/Syn_Report/'
        self.stored_report_directory = f'../processors/Logs/Syn_Report/{cpu_info.cpu_name}dynamic_set/'
        self.generated_utilisation_filename = f'{cpu_info.cpu_name}_utilization_synth.rpt'
        self.generated_power_filename = f'{cpu_info.cpu_name}_power_synth.rpt'
        self.generated_time_filename = f'{cpu_info.cpu_name}_timing_synth.rpt'
        self.processor_generation_log = '../processors/Logs/Generation_Log/Processor_Generation'
        self.processor_synthesis_log = '../processors/Logs/Generation_Log/Synthesis.log'
        self.cpu_info = cpu_info
        self.top_level_design_name = None
        self.processor_config_matcher = None
        synthesis_methods = {
            "With_Acceleration": self.run_synthesis_with_acceleration,
            "Without_Acceleration": self.run_synthesis_without_acceleration,
        }
        if config_matcher_enabled == True:
            self.selected_synthesis_function = synthesis_methods["With_Acceleration"]
        else:
            self.selected_synthesis_function = synthesis_methods["Without_Acceleration"]

    
    def extract_metrics_from_mcycle_report(self, train_validity, benchmark_name):
        # Define the regular expressions to capture the required metrics
        time_pattern = rf"Microseconds for one run through {benchmark_name.capitalize()}: (\d+)"
        throughput_pattern = rf"{benchmark_name.capitalize()}s per Second: +(\d+)"
        mcycles_pattern = r"mcycle = (\d+)"
        minstret_pattern = r"minstret = (\d+)"
        # Prepare to store the values
        metrics = {
            "exe_time": None,
            "throughput": None,
            "mcycles": None,
            "minstret": None
        }
        if not train_validity:
            return metrics
        try:
            # Open the log file
            with open(self.processor_generation_log + benchmark_name + '.log', 'r') as file:
                # Read all lines from the file
                log_content = file.read()

                # Search for exe_time
                time_match = re.search(time_pattern, log_content)
                if time_match:
                    metrics["exe_time"] = int(time_match.group(1))

                # Search for throughput
                throughput_match = re.search(throughput_pattern, log_content)
                if throughput_match:
                    metrics["throughput"] = int(throughput_match.group(1))

                # Search for mcycles
                mcycles_match = re.search(mcycles_pattern, log_content)
                if mcycles_match:
                    metrics["mcycles"] = int(mcycles_match.group(1))

                # Search for minstret
                minstret_match = re.search(minstret_pattern, log_content)
                if minstret_match:
                    metrics["minstret"] = int(minstret_match.group(1))

        except FileNotFoundError:
            print(f"Error: The file {self.processor_generation_log} does not exist.")
        except Exception as e:
            print(f"An error occurred: {e}")

        return metrics

    def extract_metric_from_cycles_and_cpi_report(self, benchmark_name):
        metrics = {
            "exe_time": None,
            "throughput": None,
            "mcycles": None,
            "minstret": None
        }
        # Define regex pattern to extract cycles and CPI
        pattern = re.compile(
            r"(?P<operation>\w+\(.*?\));.*?barrier\(.*?\):\s(?P<cycles>\d+)\s+cycles,.*?(?P<CPI>\d+\.\d+)\s+CPI"
        )

        try:
            with open(self.processor_generation_log + benchmark_name + '.log', 'r') as file:
                for line in file:
                    match = pattern.search(line)
                    if match:
                        metrics["mcycles"] = int(match.group('cycles'))
                        metrics["minstret"] = int(float(metrics["mcycles"]) / float(match.group('CPI')))
        except FileNotFoundError:
            print(f"Error: The file '{self.processor_generation_log + benchmark_name}' was not found.")
        except Exception as e:
            print(f"An error occurred: {e}")

        return metrics
    
    def extract_instructions_and_cycles(self, benchmark_name):
        metrics = {
            "exe_time": None,
            "throughput": None,
            "mcycles": None,
            "minstret": None
        }
        # Regex patterns to capture numeric values
        instructions_pattern = r"C0:\s+(\d+)\s+instructions"
        cycles_pattern = r"C0:\s+(\d+)\s+cycles"
        try:
            with open(self.processor_generation_log + benchmark_name + '.log', 'r') as file:
                log_data = file.read()
            # Search for the matches
            instructions_match = re.search(instructions_pattern, log_data)
            cycles_match = re.search(cycles_pattern, log_data)
            instructions = instructions_match.group(1) if instructions_match else None
            cycles = cycles_match.group(1) if cycles_match else None
            metrics["mcycles"] = int(cycles)
            metrics["minstret"] = int(instructions)
        except FileNotFoundError:
            print(f"Error: The file '{self.processor_generation_log + benchmark_name}'.log was not found.")
        except Exception as e:
            print(f"An error occurred: {e}")

        return metrics
    
    def run_synthesis_with_acceleration(self, new_config):
        '''Run synthesis using the new parameters.'''
        print("Running synthesis with acceleration")
        checkpoint_index = self.processor_config_matcher.match_config(new_config)
        exist_dcp = self.processor_config_matcher.prepare_checkpoint(checkpoint_index)
        if exist_dcp == False:
            command = ["vivado", "-nolog", "-nojournal", "-mode", "batch", "-source", self.tcl_path]
        else:
            command = ["vivado", "-nolog", "-nojournal", "-mode", "batch", "-source", self.tcl_path, "-tclargs", self.top_level_design_name]
        try:
            with open(self.processor_synthesis_log, 'w') as f:
                result = subprocess.run(command, check=True, cwd=self.vivado_project_path, stdout=f, stderr=f)
            if result.returncode == 0:
                self.processor_config_matcher.store_checkpoint(new_config)
                return True
            else:
                print("Error: Vivado synthesis failed.")
                return False
            
        except subprocess.CalledProcessError as e:
            print(f"Error executing Vivado: {e}")
            return False

    def run_synthesis_without_acceleration(self, new_config):
        '''Run synthesis using the new parameters.'''
        print("Running synthesis without acceleration")
        command = ["vivado", "-nolog", "-nojournal", "-mode", "batch", "-source", self.tcl_path]
        try:
            with open(self.processor_synthesis_log, 'w') as f:
                result = subprocess.run(command, check=True, cwd=self.vivado_project_path, stdout=f, stderr=f)
            if result.returncode == 0:
                self.processor_config_matcher.store_checkpoint(new_config)
                return True
            else:
                print("Error: Vivado synthesis failed.")
                return False
        except subprocess.CalledProcessError as e:
            print(f"Error executing Vivado: {e}")
            return False
    
    def run_synthesis(self, new_config):
        self.selected_synthesis_function(new_config)

    def parse_vivado_resource_utilisation_report(self):
        # Define the dictionary to hold the results
        resource_info = {
            "LUTs": 0,
            "FFs": 0,
            "BRAM": 0,
            "DSP": 0
        }
        
        # Define the regular expressions for each resource type
        patterns = {
            "LUTs": re.compile(r"\|\s*CLB LUTs\*\s*\|\s*(\d+)\s*\|"),
            "FFs": re.compile(r"\|\s*CLB Registers\s*\|\s*(\d+)\s*\|"),
            "BRAM": re.compile(r"\|\s*Block RAM Tile\s*\|\s*(\d+)\s*\|"),
            "DSP": re.compile(r"\|\s*DSPs\s*\|\s*(\d+)\s*\|")
        }
        # Open the report file
        with open(self.generated_report_directory + self.generated_utilisation_filename, 'r') as file:
            # Read through each line of the file
            for line in file:
                # Check each pattern to see if it matches the line
                for key, pattern in patterns.items():
                    match = pattern.search(line)
                    if match:
                        # If there's a match, store the number in the corresponding dictionary key
                        resource_info[key] = int(match.group(1))
        
        return resource_info
    
    def parse_vivado_power_report(self):
        power_info = {
            "Dynamic": 0.0,
            "Static": 0.0
        }
        pattern = {
            "Dynamic": re.compile(r"\|\s*Dynamic \(W\)\s*\|\s*([\d.]+)\s*\|"),
            "Static": re.compile(r"\|\s*Device Static \(W\)\s*\|\s*([\d.]+)\s*\|")
        }
        with open(self.generated_report_directory + self.generated_power_filename, 'r') as file:
            for line in file:
                for key, pat in pattern.items():
                    match = pat.search(line)
                    if match:
                        power_info[key] = float(match.group(1))
        return power_info
    
    def extract_wns(self):
        wns = None
        wns_pattern = re.compile(r"\s+(-?\d+\.\d+)\s+")
        with open(self.generated_report_directory + self.generated_time_filename, 'r') as file:
            in_timing_summary = False     
            for line in file:
                if 'WNS(ns)' in line and 'TNS(ns)' in line:
                    in_timing_summary = True
                    continue
                if in_timing_summary and '-------' not in line:
                    wns_match = wns_pattern.search(line)
                    if wns_match:
                        wns = float(wns_match.group(1))
                        break
        return wns
    
    def parse_vivado_timing_report(self):
        timing_info = {
            "Period": 20, # Default value acc to time_constraints.xdc
            "WNS" : 0,
            "Setup_Worst_Slack": 0,
            "Hold_Worst_Slack": 0,
            "PW_Worst_Slack": 0
        }

        # Define regex patterns to match the lines with worst slack values
        setup_pattern = r"Setup\s*:\s*\d+\s*Failing Endpoints,\s*Worst Slack\s*([-+]?\d*\.?\d+ns)"
        hold_pattern = r"Hold\s*:\s*\d+\s*Failing Endpoints,\s*Worst Slack\s*([-+]?\d*\.?\d+ns)"
        pw_pattern = r"PW\s*:\s*\d+\s*Failing Endpoints,\s*Worst Slack\s*([-+]?\d*\.?\d+ns)"
        
        setup_worst_slack = None
        hold_worst_slack = None
        pw_worst_slack = None
        
        # Read the file and search for the patterns
        with open(self.generated_report_directory + self.generated_time_filename, 'r') as file:
            for line in file:
                if not setup_worst_slack:
                    setup_match = re.search(setup_pattern, line)
                    if setup_match:
                        setup_worst_slack = setup_match.group(1)
                        
                if not hold_worst_slack:
                    hold_match = re.search(hold_pattern, line)
                    if hold_match:
                        hold_worst_slack = hold_match.group(1)
                if not pw_worst_slack:
                    pw_match = re.search(pw_pattern, line)
                    if pw_match:
                        pw_worst_slack = pw_match.group(1)
                # If both values are found, no need to continue reading
                if setup_worst_slack and hold_worst_slack and pw_worst_slack:
                    break
        timing_info["Setup_Worst_Slack"] = float(setup_worst_slack.split('ns')[0])
        timing_info["Hold_Worst_Slack"] = float(hold_worst_slack.split('ns')[0])
        timing_info["PW_Worst_Slack"] = float(pw_worst_slack.split('ns')[0])
        timing_info["WNS"] = self.extract_wns()
        return timing_info

    def store_synthesis_report(self):
        '''Store the synthesis report in a file.'''
        name, extension = os.path.splitext(self.generated_utilisation_filename)
        new_name = name + '_' + str(self.generated_report_num) + extension
        shutil.copy(self.generated_report_directory + self.generated_utilisation_filename, self.stored_report_directory + new_name)
        self.generated_report_num += 1
    
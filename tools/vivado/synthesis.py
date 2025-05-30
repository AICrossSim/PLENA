import re
import subprocess
import os
import shutil

def run_synthesis_without_acceleration(tcl_path, log_path, prj_path):
    '''Run synthesis using the new parameters.'''
    print("Running synthesis")
    command = ["vivado", "-nolog", "-nojournal", "-mode", "batch", "-source", tcl_path]
    try:
        with open(log_path, 'w') as f:
            result = subprocess.run(command, check=True, cwd=prj_path, stdout=f, stderr=f)
        if result.returncode == 0:
            print("Vivado synthesis completed successfully.")
            return True
        else:
            print("Error: Vivado synthesis failed.")
            return False
    except subprocess.CalledProcessError as e:
        print(f"Error executing Vivado: {e}")
        return False




if __name__ == "__main__":
    tcl_path = "../tools/vivado/run_synthesis.tcl"
    log_path = "../synthesis_report/synthesis.log"
    prj_path = "../../Coprocessor_Vivado_Prj"
    run_synthesis_without_acceleration(tcl_path, log_path, prj_path)
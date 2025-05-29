import re
import subprocess
import os
import shutil

def run_synthesis_without_acceleration(tcl_path, log_path, prj_path):
    '''Run synthesis using the new parameters.'''
    print("Running synthesis without acceleration")
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

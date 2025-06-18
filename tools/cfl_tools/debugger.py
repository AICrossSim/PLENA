import sys, pdb, traceback

def set_excepthook():
    def excepthook(exc_type, exc_value, exc_traceback):
        traceback.print_exception(exc_type, exc_value, exc_traceback)
        print("\nEntering debugger...")
        pdb.post_mortem(exc_traceback)

    sys.excepthook = excepthook

def detect_signal(attr):
    if attr.startswith("_") or attr == "get_definition_file" or attr == "get_definition_name":
        return False
    else:
        return True

def get_dut_attributes(dut, log, value_rep: str = None):
    for attr in dir(dut):
        if detect_signal(attr):
            if value_rep is None:
                value = getattr(dut, attr).value
            else:
                try:
                    value = getattr(getattr(dut, attr).value, value_rep)
                except:
                    value = getattr(dut, attr).value
        else:
            continue
        log.debug(f"{attr}: {value}")
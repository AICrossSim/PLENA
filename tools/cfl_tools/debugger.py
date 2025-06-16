import sys, pdb, traceback

def set_excepthook():
    def excepthook(exc_type, exc_value, exc_traceback):
        traceback.print_exception(exc_type, exc_value, exc_traceback)
        print("\nEntering debugger...")
        pdb.post_mortem(exc_traceback)

    sys.excepthook = excepthook
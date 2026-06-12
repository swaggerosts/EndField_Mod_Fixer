def pre_find_module_path(_hook_api):
    # The bundled Tcl/Tk files are supplied manually in the project spec.
    # Keep PyInstaller from excluding tkinter when its automatic probe fails.
    return

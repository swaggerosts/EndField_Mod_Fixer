from __future__ import annotations

import os
import sys
from pathlib import Path


def _set_if_present(env_name: str, path: Path, marker: str) -> None:
    if (path / marker).is_file():
        os.environ[env_name] = str(path)


base_dir = Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))

_set_if_present("TCL_LIBRARY", base_dir / "tcl" / "tcl8.6", "init.tcl")
_set_if_present("TK_LIBRARY", base_dir / "tcl" / "tk8.6", "tk.tcl")

_set_if_present("TCL_LIBRARY", base_dir / "_tcl_data", "init.tcl")
_set_if_present("TK_LIBRARY", base_dir / "_tk_data", "tk.tcl")

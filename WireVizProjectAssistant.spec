# WireVizProjectAssistant.spec

import os
from pathlib import Path
import sys
import sysconfig
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

_spec_file = globals().get("__file__")
root = Path(_spec_file).resolve().parent if _spec_file else Path.cwd()

graphviz_root = root / "vendor" / "graphviz"
graphviz_bin = graphviz_root / "bin"
starter_dir = root / "starter"
template_file = root / "engineering-sheet.html"
gitignore_file = root / ".gitignore"

os.environ["PATH"] = (
    str(graphviz_bin) + os.pathsep +
    os.environ.get("PATH", "")
)

def safe_collect(package: str) -> list[str]:
    try:
        return collect_submodules(package)
    except Exception:
        return []


hidden = (
    safe_collect("FreeSimpleGUI")
    + safe_collect("PySimpleGUI")
    + safe_collect("wireviz")
    + ["tkinter"]
)

tcl_tk_datas = collect_data_files("tkinter")
tcl_library = sysconfig.get_config_var("TCL_LIBRARY")
tk_library = sysconfig.get_config_var("TK_LIBRARY")
if tcl_library:
    tcl_tk_datas.append((tcl_library, "_tcl_data"))
if tk_library:
    tcl_tk_datas.append((tk_library, "_tk_data"))

python_base = Path(sys.base_prefix)
python_dlls = python_base / "DLLs"
tcl_tk_bins = []
for dll_name in ("tcl86t.dll", "tk86t.dll"):
    candidate = python_dlls / dll_name
    if candidate.exists():
        tcl_tk_bins.append((str(candidate), "."))

a = Analysis(
    ["gui.py"],
    pathex=[str(root)],
    binaries=tcl_tk_bins,
    datas=[
        (str(graphviz_root), "graphviz"),
        (str(starter_dir), "starter"),
        (str(template_file), "."),
        (str(gitignore_file), "."),
    ] + tcl_tk_datas,
    hiddenimports=hidden,
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    name="WireVizProjectAssistant",
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="WireVizProjectAssistant",
)

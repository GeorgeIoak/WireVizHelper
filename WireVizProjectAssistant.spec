# WireVizProjectAssistant.spec

import os
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules

root = Path(__file__).resolve().parent

graphviz_bin = root / "vendor" / "graphviz" / "bin"
wkhtml_bin = root / "vendor" / "wkhtmltopdf" / "bin"
starter_dir = root / "starter"

os.environ["PATH"] = (
    str(graphviz_bin) + os.pathsep +
    str(wkhtml_bin) + os.pathsep +
    os.environ.get("PATH", "")
)

hidden = collect_submodules("PySimpleGUI")

a = Analysis(
    ["gui.py"],
    pathex=[str(root)],
    binaries=[
        (str(graphviz_bin), "graphviz/bin"),
        (str(wkhtml_bin), "wkhtmltopdf/bin"),
    ],
    datas=[
        (str(starter_dir), "starter"),
    ],
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

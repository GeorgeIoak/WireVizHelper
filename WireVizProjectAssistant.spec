# WireVizProjectAssistant.spec

import os
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules

root = Path(__file__).resolve().parent

graphviz_bin = root / "vendor" / "graphviz" / "bin"
wkhtml_bin = root / "vendor" / "wkhtmltopdf" / "bin"
starter_dir = root / "starter"
template_file = root / "engineering-sheet.html"
gitignore_file = root / ".gitignore"

os.environ["PATH"] = (
    str(graphviz_bin) + os.pathsep +
    str(wkhtml_bin) + os.pathsep +
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
    + safe_collect("weasyprint")
)

a = Analysis(
    ["gui.py"],
    pathex=[str(root)],
    binaries=[],
    datas=[
        (str(graphviz_bin), "graphviz/bin"),
        (str(wkhtml_bin), "wkhtmltopdf/bin"),
        (str(starter_dir), "starter"),
        (str(template_file), "."),
        (str(gitignore_file), "."),
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

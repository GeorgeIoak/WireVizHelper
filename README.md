# WireVizHelper / WireViz Project Assistant

WireVizHelper extends WireViz to produce single-file engineering sheets and richer BOM output while keeping YAML as the source of truth.

The **WireViz Project Assistant** adds a graphical interface (GUI) and automated build tooling to make project creation and diagram generation easier for both technical and non-technical users.

---

## What It Does

### Core WireVizHelper Features
- Generates an engineering-sheet style HTML output with title block, notes, and branding.
- Merges photo helper rows into the matching BOM part row (`SPN` becomes `Product Photo`).
- Attempts single-page PDF generation from the rendered HTML (`wkhtmltopdf` on Windows, then `weasyprint` fallback).
- Scaffolds new project folders with starter YAML, images, and templates.

### WireViz Project Assistant (GUI)
- Create new WireViz project folders with a simple dialog.
- Build existing projects without using the command line.
- Optional automatic opening of the output folder after build.
- Works as a standalone EXE (simple or fully portable).

---

## Downloads

You can obtain builds from GitHub Actions artifacts or GitHub Releases:

- `WireVizProjectAssistant-full.zip`: portable folder build (EXE + bundled runtime files).
- `WireVizProjectAssistant-simple.exe`: single-file standalone build.

Both Windows builds are intended to run without manual Graphviz/wkhtmltopdf installs or PATH edits.

## Install And Use (Windows Release)

1. Download either `WireVizProjectAssistant-full.zip` (recommended) or `WireVizProjectAssistant-simple.exe`.
2. For `full.zip`: extract to a normal local folder (for example `C:\Tools\WireVizProjectAssistant`).
3. Run `WireVizProjectAssistant.exe` from the extracted full folder, or run `WireVizProjectAssistant-simple.exe`.
4. In the app, use `Create New Project` to scaffold starter files and `Build Existing Project` to generate HTML/SVG/PNG/TSV/PDF outputs.

Notes:
- Keep all files together in the extracted `full.zip` folder.
- On first run, if a required runtime file is missing, the app now shows a startup error dialog.

## Local EXE Build (Windows)

```powershell
pip install -r requirements.txt pyinstaller
```

Populate `vendor/` with portable binaries (same layout used in CI):

- `vendor/graphviz/bin/dot.exe`
- `vendor/wkhtmltopdf/bin/wkhtmltopdf.exe`

Then build:

```powershell
# full portable folder build
pyinstaller WireVizProjectAssistant.spec

# single-file standalone build
pyinstaller WireVizProjectAssistant.simple.spec
```

`vendor/graphviz/.gitkeep` and `vendor/wkhtmltopdf/.gitkeep` are placeholders so folder structure is tracked in git.

## Manual Dependencies (Source/Dev Use)

If you run from source instead of packaged EXEs, install runtime dependencies on your system:

```bash
# macOS
brew install graphviz
brew install pango cairo gdk-pixbuf libffi  # WeasyPrint libs
brew install wkhtmltopdf                    # Optional fallback
```

```bash
# Ubuntu / Debian
sudo apt-get update
sudo apt-get install -y graphviz wkhtmltopdf
```

Verify Graphviz:

```bash
dot -V
```

GUI dependency note: this project uses `FreeSimpleGUI` (community fork API-compatible with classic PySimpleGUI).

## Quick Start

```powershell
# 1) Create a new project
python scaffold.py --name "My Cable Drawing" --dest "C:\Users\me\Documents\Design"

# 2) Edit the YAML in the new project folder
cd "C:\Users\me\Documents\Design\My_Cable_Drawing"

# 3) Build output files
python "C:\path\to\WireVizHelper\build.py" drawing.yaml
```

```bash
# macOS / Linux equivalent
python scaffold.py --name "My Cable Drawing" --dest ~/Design
cd ~/Design/My_Cable_Drawing
python /path/to/WireVizHelper/build.py drawing.yaml
```

First run of `scaffold.py` or `build.py` may auto-install Python dependencies from `requirements.txt`.

## Typical Workflow

1. Keep this repo separate from your cable project folders.
2. Scaffold once per project.
3. Edit project YAML (`drawing.yaml` or custom name).
4. Run `build.py` against that YAML from any location.

```bash
python /path/to/WireVizHelper/build.py /path/to/project/drawing.yaml
```

## Output Summary

- BOM column header `SPN` is renamed to `Product Photo`.
- Photo helper rows are merged into matching rows (by `Designators` or `MPN`) and removed.
- Image paths are rewritten for output-folder correctness.
- PDF is emitted when a supported engine is available.

## Scaffold Options

```bash
# New project folder
python scaffold.py --name "My Cable Project" --dest /path/to/projects

# Custom YAML file name
python scaffold.py --name "My Cable Project" --dest /path/to/projects --yaml-name harness.yaml

# Scaffold in current folder
python scaffold.py --in-place --dest .
```

Generated project contents:

- `drawing.yaml` (or custom YAML name)
- `images/`
- `reference/`
- `README.md`
- `.gitignore`

## Documentation Map

- YAML fields and metadata: [`docs/yaml-options.md`](docs/yaml-options.md)
- Troubleshooting guide: [`docs/troubleshooting.md`](docs/troubleshooting.md)
- Starter YAML example: [`examples/minimal_drawing.yaml`](examples/minimal_drawing.yaml)
l_drawing.yaml)

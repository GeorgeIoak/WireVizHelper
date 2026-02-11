# WireVizHelper / WireViz Project Assistant

WireVizHelper extends WireViz to produce engineering-style drawing sheets and richer BOM output while keeping YAML as the source of truth.

The core focus is the Python build pipeline and engineering-sheet output. The **WireViz Project Assistant** GUI/EXE is a convenience layer on top of that pipeline.

---

## What It Does

### Core WireVizHelper Features

- Generates an engineering-sheet style HTML output with title block, notes, and branding.
- Merges photo helper rows into the matching BOM part row (`SPN` becomes `Product Photo`).
- Generates single-page PDF output from the rendered HTML using a headless Chromium-based browser (Edge/Chrome/Brave/Chromium).
- Scaffolds new project folders with starter YAML, images, and templates.

### WireViz Project Assistant (GUI)

- Create new WireViz project folders with a simple dialog.
- Build existing projects without using the command line.
- Optional automatic opening of the output folder after build.
- Works as a standalone EXE (portable full package).

---

## Downloads

You can obtain builds from GitHub Actions artifacts or GitHub Releases:

- GitHub Actions artifact `WireVizProjectAssistant-full`: portable folder payload (single extraction, no nested zip).
- GitHub Release asset `WireVizProjectAssistant-full.zip`: portable folder build (EXE + bundled runtime files).

The supported Windows distribution is the portable full package.

## Install And Use (Windows Release)

1. Download `WireVizProjectAssistant-full` artifact (Actions) or `WireVizProjectAssistant-full.zip` (Release).
2. Extract to a normal local folder (for example `C:\Tools\WireVizProjectAssistant`).
3. Run `WireVizProjectAssistant.exe` from the extracted folder.
4. In the app, use `Create New Project` to scaffold starter files and `Build Existing Project` to generate HTML/SVG/PNG/TSV/PDF outputs.

Notes:

- Keep all files together in the extracted `full.zip` folder.
- On first run, if a required runtime file is missing, the app now shows a startup error dialog.

## Advanced CLI Use (Packaged EXE)

The packaged EXE supports command-line usage for advanced users.

```powershell
# Print installed version
.\WireVizProjectAssistant.exe --version

# Build from YAML (same pipeline as build.py)
.\WireVizProjectAssistant.exe build .\my-project\drawing.yaml

# Pass extra WireViz arguments after --
.\WireVizProjectAssistant.exe build .\my-project\drawing.yaml -- --output-dir .\out --output-name drawing_v2

# Scaffold a new project folder (same behavior as scaffold.py)
.\WireVizProjectAssistant.exe scaffold --name "Panel Harness A" --dest C:\Work\Drawings
```

## Local EXE Build (Windows)

```powershell
pip install -r requirements.txt pyinstaller
```

Populate `vendor/` with portable binaries (same layout used in CI):

- `vendor/graphviz/bin/dot.exe`

Then build:

```powershell
# full portable folder build
pyinstaller WireVizProjectAssistant.spec
```

`vendor/graphviz/.gitkeep` is a placeholder so folder structure is tracked in git.

Smoke-test packaged EXEs headlessly (used by CI workflows):

```powershell
# full portable
.\dist\WireVizProjectAssistant\WireVizProjectAssistant.exe --smoke-test --workdir .\ci-smoke-full
```

## Manual Dependencies (Source/Dev Use)

If you run from source instead of packaged EXEs, install runtime dependencies on your system:

```bash
# macOS
brew install graphviz
```

```bash
# Ubuntu / Debian
sudo apt-get update
sudo apt-get install -y graphviz
```

Verify Graphviz:

```bash
dot -V
```

GUI dependency note: this project uses `FreeSimpleGUI` (community fork API-compatible with classic PySimpleGUI).

PDF note: packaged EXE builds use a headless Chromium-based browser. You can override the browser path with:

```bash
# macOS / Linux
export WIREVIZ_PDF_BROWSER=/path/to/chrome
```

```powershell
# Windows (PowerShell)
$env:WIREVIZ_PDF_BROWSER = "C:\Path\To\msedge.exe"
```

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
- PDF is emitted through browser print-to-PDF.

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

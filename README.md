# WireVizHelper

WireVizHelper extends WireViz to produce single-file engineering sheets and richer BOM output while keeping YAML as the source of truth.

## What It Does

- Generates an engineering-sheet style HTML output with title block, notes, and branding.
- Merges photo helper rows into the matching BOM part row (`SPN` becomes `Product Photo`).
- Attempts single-page PDF generation from the rendered HTML (`weasyprint`, then `wkhtmltopdf`).
- Scaffolds new project folders with starter YAML, images, and templates.

## Prerequisites

Install once per machine:

1. `Python 3.x`
2. `Graphviz` (required by WireViz)
3. Optional PDF engine:
   - Preferred: `WeasyPrint` (pip package; native libs needed on macOS)
   - Fallback: `wkhtmltopdf` CLI

### Install Commands

```powershell
# Windows (PowerShell)
winget install Graphviz.Graphviz
winget install --id wkhtmltopdf.wkhtmltox --exact  # Optional fallback
```

Windows note: PDF output needs a PDF engine beyond Graphviz. `requirements.txt` installs `weasyprint`, but WeasyPrint may still require native GTK/Pango runtime libraries on Windows. If PDF generation fails, install `wkhtmltopdf` (`winget install --id wkhtmltopdf.wkhtmltox --exact`) and rebuild. This `winget` command works in both PowerShell and `cmd.exe`.

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

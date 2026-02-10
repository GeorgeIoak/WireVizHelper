# Troubleshooting (WireVizHelper)

Use this page for common setup and build issues. Keep `README.md` focused on onboarding; add deeper issue-specific steps here.

## PDF Generation Issues

WireVizHelper attempts PDF generation in this order:

1. Headless Chromium-based browser (Edge / Chrome / Chromium / Brave)
2. `weasyprint` Python package (optional)
3. `wkhtmltopdf` CLI (optional)

If the browser path is unusual, set it explicitly:

```bash
# macOS / Linux
export WIREVIZ_PDF_BROWSER=/path/to/chrome
```

```powershell
# Windows (PowerShell)
$env:WIREVIZ_PDF_BROWSER = "C:\Path\To\msedge.exe"
```

If PDF still fails, open the HTML output in your browser and print to PDF manually.
HTML/SVG/PNG/TSV outputs should still be generated.

## Graphviz / `dot` Not Found

Symptoms:

- Build fails before diagram generation.
- Terminal reports `dot` is missing.

Fix:

1. Install Graphviz.
2. Add Graphviz to PATH (Windows default install path is `C:\Program Files\Graphviz\bin`).
3. Restart terminal.
4. Confirm with:

```bash
dot -V
```

If `dot -V` still fails, ensure Graphviz is on your PATH.
After a permanent change, open a new terminal to pick up the updated PATH.

Windows PATH quick fix (current session):

```cmd
set PATH=%PATH%;C:\Program Files\Graphviz\bin
dot -V
```

PowerShell quick fix (current session):

```powershell
$env:Path = "$env:Path;C:\Program Files\Graphviz\bin"
dot -V
```

PowerShell PATH permanent (user):

```powershell
[Environment]::SetEnvironmentVariable("Path", $env:Path + ";C:\Program Files\Graphviz\bin", "User")
dot -V
```

cmd.exe PATH permanent (user):

```cmd
setx PATH "%PATH%;C:\Program Files\Graphviz\bin"
dot -V
```

## Python Dependency Install Fails

`build.py` and `scaffold.py` attempt auto-install from `requirements.txt`. If that fails:

```bash
python -m pip install -r requirements.txt
```

Run from the WireVizHelper repository root.

## Notes Panel Overflow

If the notes panel shows a vertical scrollbar:

- Increase `metadata.notes_width`
- Shorten `metadata.notes`
- Reduce strip-detail image height in `engineering-sheet.html` (`#strip-detail-image`)

For layout-related YAML keys, see [`docs/yaml-options.md`](yaml-options.md).

## BOM Photo Merge Not Working

Checks:

1. Photo row is in `additional_bom_items`.
2. Photo HTML is placed in `spn`.
3. `Designators` or `MPN` matches the target BOM row.

If matches are missing, the helper row cannot merge into a part row.

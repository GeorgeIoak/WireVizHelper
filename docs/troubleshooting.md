# Troubleshooting (WireVizHelper)

Use this page for common setup and build issues. Keep `README.md` focused on onboarding; add deeper issue-specific steps here.

## PDF Generation Issues

WireVizHelper attempts PDF generation in this order:

1. `weasyprint` Python package
2. `wkhtmltopdf` CLI

If PDF fails, install `wkhtmltopdf` as fallback:

- Windows (PowerShell or cmd.exe): `winget install --id wkhtmltopdf.wkhtmltox --exact`
- macOS: `brew install wkhtmltopdf`
- Ubuntu / Debian: `sudo apt-get update && sudo apt-get install -y wkhtmltopdf`

If no PDF engine is available, HTML/SVG/PNG/TSV outputs should still be generated.

## Graphviz / `dot` Not Found

Symptoms:

- Build fails before diagram generation.
- Terminal reports `dot` is missing.

Fix:

1. Install Graphviz.
2. Restart terminal.
3. Confirm with:

```bash
dot -V
```

If `dot -V` still fails, ensure Graphviz is on your PATH.

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

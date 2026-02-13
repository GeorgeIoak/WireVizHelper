## WireVizHelper v1.1.19

This is the recommended public baseline for WireVizHelper.

### Highlights

- Stabilized packaged PDF flow around browser print-to-PDF (Edge/Chrome family).
- Improved PDF diagnostics and stale-output handling.
- Fixed command logging order so CLI/smoke logs show the WireViz command before execution.
- Finalized naming and packaging around WireVizHelper.
- Added Windows executable metadata and icon.
- Refined documentation for source-first usage, Windows packaged app usage, and troubleshooting.
- Simplified CI/release workflow names and release trigger behavior.

### Workflow Behavior

- `main` push -> **Build WireVizHelper App** (validation build only)
- `v*` tag push -> **Release WireVizHelper App** (release pipeline)

### Packaging Notes

- Supported Windows distribution: portable bundle (`WireVizHelper.exe` + `_internal` folder).
- Keep `WireVizHelper.exe` and `_internal` together after extraction.
- One-file "simple" EXE is not part of the public release path.

### Output Notes

- Engineering-sheet deliverables: HTML + PDF.
- Native WireViz diagram exports remain available: SVG/PNG/TSV.
- BOM product photos remain linked image assets in HTML (share images with HTML, or share PDF for fully portable output).

### Docs & Onboarding

- README separates:
  - Source path (macOS/Linux/Windows)
  - Windows no-Python packaged app path
- Added developer packaging/build notes and refreshed troubleshooting guidance.
- Included updated engineering-sheet preview image in README.

### Known/Planned Follow-ups

- Optional engineering-sheet PNG export (`drawing.sheet.png`) from final PDF.
- Feasibility investigation for full-sheet SVG output.
- DXF export exploration for CAD workflows.

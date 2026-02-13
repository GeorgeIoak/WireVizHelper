# Changelog
All notable changes to **WireVizHelper** will be documented here.

## [Unreleased]

### Changed
- Packaged EXE PDF flow now uses browser print-to-PDF as the default/authoritative engine.
- Disabled public simple-EXE release path for now; release publishes full portable package only.

### Fixed
- PDF generation now clears stale target PDFs before each run to avoid false success/failure signals.
- Browser PDF failures now return detailed diagnostics (browser attempt, mode, exit output, HTML/PDF paths).
- Packaged EXE no longer falls through to WeasyPrint/wkhtmltopdf on browser failure, preventing misleading `weasyprint` errors.

## [1.1.19] - 2026-02-13
### Changed
- Simplified workflow naming to `Build WireVizHelper App` and `Release WireVizHelper App`.
- Isolated CI flow so branch pushes run build validation, while version tags trigger release publishing.
- Added roadmap notes for engineering-sheet PNG/SVG/DXF follow-up outputs.

## [1.1.16] - 2026-02-13
### Changed
- Release workflow now triggers automatically on version tags (`v*`) in addition to manual dispatch.

## [1.1.15] - 2026-02-13
### Fixed
- Print the WireViz command preview before execution in CLI and smoke-test flows for clearer logs.

## [1.1.4] - 2026-02-10
### Fixed
- Capture WireViz stdout/stderr, write `wireviz-error.log`, and surface failures in GUI/CLI.
- Avoid leaving engineering-sheet template in output folders after build.

## [1.1.3] - 2026-02-10
### Fixed
- Bundle Tcl/Tk DLLs from the Python runtime to resolve init.tcl version conflicts.

## [1.1.2] - 2026-02-10
### Fixed
- Force bundled Tcl/Tk runtime selection in frozen builds to resolve init.tcl version conflicts.

## [1.1.1] - 2026-02-10
### Fixed
- Bundle Tk/Tcl runtime data in PyInstaller builds to prevent init.tcl errors.

## [1.1.0] - 2026-02-10
### Added
- Headless browser PDF generation (Edge/Chrome/Brave/Chromium)
- `WIREVIZ_PDF_BROWSER` override for explicit browser paths
- Auto-discovery of `wireviz` user install scripts on Windows/macOS/Linux

### Changed
- Reduced portable build bloat by removing wkhtmltopdf bundling
- Engineering sheet layout spacing adjustments to avoid notes overflow
- Example YAML pin labels normalized to strings for WireViz 0.4.1 compatibility

## [1.0.0] - 2026-02-09
### Added

- GUI for project scaffolding and building
- Full portable EXE build
- Simple EXE build
- GitHub Actions CI and Release workflows
- Version display in GUI
- Troubleshooting section in README

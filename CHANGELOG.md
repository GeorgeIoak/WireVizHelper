# Changelog
All notable changes to **WireViz Project Assistant** will be documented here.

## [Unreleased]

- No changes yet.

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

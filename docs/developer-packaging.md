# Developer Packaging & Build Notes

This guide is for maintainers building the `WireVizHelper.exe` executable or debugging the packaging process.

## Development Environment

1. Follow the "Running from Source" steps in `README.md` to get a working Python environment.
2. Install packaging dependencies:

   ```powershell
   pip install pyinstaller
   ```

## Building Windows Executable

The project uses PyInstaller to bundle the application and its dependencies.

1. **Prepare Vendor Binaries** (required for portable builds):
   - Create a `vendor/` directory in the project root.
   - Download a Windows ZIP distribution of Graphviz.
   - Extract so that `vendor/graphviz/bin/dot.exe` exists.
   - *Note: Portable builds are expected to include bundled Graphviz in `vendor/graphviz`.*

2. **Run PyInstaller**:

   ```powershell
   pyinstaller WireVizHelper.spec
   ```

3. **Locate Output**:
   - The bundled application is generated in `dist/WireVizHelper/`.
   - The main executable is `WireVizHelper.exe`.

## Testing the Package

### Quick Validation (Smoke Test)

Run the internal smoke test to verify the executable starts and can process a basic file:

```powershell
.\dist\WireVizHelper\WireVizHelper.exe --smoke-test --workdir .\ci-smoke-full
```

### PDF Generation Testing

The packaged app relies on the system's browser for PDF generation. To force a specific browser during testing:

```powershell
$env:WIREVIZ_PDF_BROWSER = "C:\Path\To\msedge.exe"
.\dist\WireVizHelper\WireVizHelper.exe build examples\minimal_drawing.yaml
```

## Architecture Notes

- **GUI Framework**: This project uses `FreeSimpleGUI` (community fork API-compatible with classic PySimpleGUI).
- **PDF Engine**: Packaged builds use headless Chromium (Edge/Chrome) via `subprocess` to render the HTML output to PDF.

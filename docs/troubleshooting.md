# Troubleshooting

Use this page for common setup and build issues.

## Build Failures & Logs

If the build fails, check the console output first. If WireViz crashes, a log file is often created in your output folder:

- `output/wireviz-error.log`

## PDF Generation Issues

The application uses your system's web browser (Edge, Chrome, Brave, etc.) to generate PDFs.

**Symptoms:**
- PDF file is missing from `output/`.
- Console says "browser print failed".

**Solutions:**
1. **Ensure a browser is installed**: Edge (Windows) or Chrome/Chromium (macOS/Linux) are preferred.
2. **Force a specific browser**: If the auto-detection fails, set the path explicitly.

   ```powershell
   # Windows PowerShell
   $env:WIREVIZ_PDF_BROWSER = "C:\Program Files\Google\Chrome\Application\chrome.exe"
   .\WireVizHelper.exe build .\my-project\drawing.yaml
   ```

   ```bash
   # macOS / Linux
   export WIREVIZ_PDF_BROWSER="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
   ```

3. **Manual Workaround**: Open the generated `.html` file in your browser and use **Print > Save as PDF**.

## Graphviz / `dot` Not Found

WireViz requires Graphviz. If you see `dot: command not found` or similar:

1. **Install Graphviz**: See `README.md` for install commands.
2. **Check PATH**: The `bin` folder must be in your system PATH.
3. **Verify**:

   ```bash
   dot -V
   ```

**Windows PATH Fixes:**

- **Temporary (Current Terminal)**:
  ```powershell
  $env:Path += ";C:\Program Files\Graphviz\bin"
  ```

- **Permanent**:
  1. Search Windows for "Edit the system environment variables".
  2. Click "Environment Variables".
  3. Edit "Path" under User variables.
  4. Add the Graphviz bin path (e.g., `C:\Program Files\Graphviz\bin`).
  5. Restart your terminal.

## Python Dependency Install Fails

`build.py` and `scaffold.py` attempt auto-install from `requirements.txt`. If that fails:

```bash
python -m pip install -r requirements.txt
```

Run from the WireVizHelper repository root.

## Notes Panel Overflow

If the notes panel shows a vertical scrollbar (which prints poorly):

- Increase `metadata.notes_width` in YAML.
- Shorten `metadata.notes` text.
- Reduce strip-detail image height in `engineering-sheet.html` (`#strip-detail-image`).

For layout keys, see [`docs/yaml-options.md`](yaml-options.md).

## BOM Photo Merge Not Working

If product photos aren't appearing in the main BOM table:

1. **Check `additional_bom_items`**: The photo must be defined here in YAML.
2. **Check Matching Fields**: The helper row must have a `Designators` or `MPN` field that *exactly* matches a component in the main BOM.
3. **Check Column Name**: Ensure you are putting the HTML `<img>` tag in the `spn` field of the helper row.

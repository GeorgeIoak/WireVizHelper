# Quick Setup Guide

## Configuring the GitHub "About" Section

The "About" section on your GitHub repository page needs to be configured separately from the README.

### Quick Steps:

1. **Go to your repository** on GitHub
2. **Click the ⚙️ icon** next to "About" (upper right of the main page)
3. **Add the description**:
   ```
   WireVizHelper extends WireViz to produce engineering-style drawing sheets with enhanced BOM handling and PDF output. Python-based with optional Windows executable.
   ```
4. **Add topics** (click "Add topics" and enter these one by one):
   - wireviz
   - wiring-diagram
   - engineering-drawings
   - python
   - graphviz
   - cable-harness
   - bom
   - pdf-generation
   - engineering-tools
   - electrical-engineering
   - automation
   - yaml

5. **Optionally add website URL**:
   ```
   https://github.com/GeorgeIoak/WireVizHelper/blob/main/docs/yaml-options.md
   ```

6. **Click "Save changes"**

### Alternative: Automated Configuration

If you prefer automated configuration:

1. Install the [Settings GitHub App](https://github.com/apps/settings)
2. Grant it access to this repository
3. The app will read `.github/settings.yml` and automatically configure your repository

### Why This Matters

- Makes your project more discoverable through GitHub search
- Provides a quick summary for visitors
- Shows up in topic-based searches
- Improves the professional appearance of your repository

See [`DESCRIPTION.md`](DESCRIPTION.md) for more details.

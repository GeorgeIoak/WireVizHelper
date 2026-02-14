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

#### How the Settings App Works

The Settings app syncs your repository metadata automatically, but it needs to be **triggered** by one of these events:

- **Initial installation** - The app syncs immediately when first installed (if settings.yml exists)
- **Push to main branch** - Any push that modifies `.github/settings.yml` triggers a sync
- **Manual workflow trigger** - Run the "Sync Repository Settings" workflow from the Actions tab

#### Troubleshooting: Settings Not Updating

If you installed the app but your About section isn't updating:

1. **Trigger the sync manually:**
   - Go to the "Actions" tab in your repository
   - Select "Sync Repository Settings" workflow
   - Click "Run workflow" button
   - Wait 1-2 minutes for the Settings app to process the webhook

2. **Make a small change to settings.yml:**
   - Edit `.github/settings.yml` (add a space or newline)
   - Commit and push to the main branch
   - The app will detect the change and sync automatically

3. **Verify app installation:**
   - Go to https://github.com/settings/installations
   - Confirm "Settings" app is listed and has access to this repository
   - If not, reinstall the app

4. **Try reinstalling the app:**
   - Uninstall the Settings app from your account
   - Reinstall it and grant access to this repository
   - The app should sync immediately upon reinstallation

5. **Manual configuration as fallback:**
   - If the app still doesn't work, use the manual steps above
   - Click the ⚙️ icon next to "About" and configure directly

### Why This Matters

- Makes your project more discoverable through GitHub search
- Provides a quick summary for visitors
- Shows up in topic-based searches
- Improves the professional appearance of your repository

See [`DESCRIPTION.md`](DESCRIPTION.md) for more details.

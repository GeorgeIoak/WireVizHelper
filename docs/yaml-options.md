# YAML Options (WireVizHelper)

This document summarizes the YAML fields and metadata used by WireVizHelper to generate the engineering sheet and BOM. Keep your YAML as the single source of truth.

If you are new to WireViz:

- Start with `examples/minimal_drawing.yaml`.
- Keep your first file simple, then add metadata/layout options one section at a time.

## Core Structure

- `connectors`: list of connectors with standard WireViz fields.
- `cables`: list of cables/harness segments.
- `connections`: wiring between connector pins and cable wires.
- `additional_bom_items`: optional helper rows (used for photos and custom BOM items).

## BOM Fields (per WireViz)

Use native WireViz keys in `connectors` / `cables`:

- `manufacturer`: manufacturer name (HTML allowed for links).
- `mpn`: manufacturer part number (HTML allowed for links).
- `pn`: internal part number (optional).
- `supplier`: distributor name (optional).
- `spn`: spare part number field; WireVizHelper repurposes this as a `Product Photo` column.
- *Note: Do not use unsupported custom keys (like `link`) inside connectors/cables.*

Link examples (HTML embedded):

- `mpn: '<a href="https://example.com/part">12345</a>'`
- `manufacturer: '<a href="https://example.com">Acme</a>'`

## Product Photos in BOM (photo-in-row)

WireViz does not natively attach a photo column to a part row. To include a photo:

- Add a helper entry in `additional_bom_items` that describes the photo.
- Put image HTML (or an `<img>` tag) in `spn`.
- Ensure either `Designators` or `MPN` matches the target BOM row.
- WireVizHelper will merge the photo into the matching part row and remove the helper row.

Minimal example:

```yaml
additional_bom_items:
  - Description: Plug Photo
    Designators: J1
    spn: '<img src="images/plug_example.png" alt="Plug" />'
```

Notes:

- If target row has a blank designator (e.g., `show_name: false`), WireVizHelper backfills the designator from the photo row.
- Image paths are rewritten so they stay valid from the output folder.

## Hiding Items from BOM

To hide certain items (e.g., flying leads):

- Add `ignore_in_bom: true` where supported in your YAML entries.

## Engineering Sheet Metadata

Top-level `metadata` controls template and title-block fields.

### Template & Title Block

- `template.name`: name of the template file (use `engineering-sheet`).
- `template.sheetsize`: `A4`, `A3`, `A2`, `LETTER`, `LEGAL`, `TABLOID` (landscape).
- `notes`: freeform notes text (multiline YAML block recommended).
- `title`, `description`, `project`, `drawing_no`, `revision`, `date`, `author`, `company`.

### Company Branding

- `company_address_line1`, `company_address_line2`, `company_phone`
- `company_logo`: path (relative to YAML) to logo image.
- `company_logo_max_width`, `company_logo_max_height`: constrain logo size (default: `26mm` x `10mm`).

### Layout Configuration

Control the sizing of the notes panel, BOM table, and drawing area.

**Dimensions:**
- `notes_width`: Width of the right-side notes panel.
- `notes_min_width`: Minimum width for notes.
- `bom_height`: Target height for the BOM panel.
- `bom_min_height`, `bom_max_height`: Clamping limits for BOM height.
- `drawing_min_height`: Minimum height reserved for the diagram.
- `drawing_min_width`: Minimum width reserved for the diagram.

**Modes & Priorities:**

- `bom_height_mode`:
  - `fixed`: Uses `bom_height` directly (clamped by min/max).
  - `auto`: Sizes BOM to fit content, while preserving at least `drawing_min_height`.
- `height_priority`:
  - `drawing`: Protects drawing area first; BOM expands only into remaining space.
  - `bom`: Prioritizes BOM height; drawing shrinks to `drawing_min_height` if needed.
- `width_priority`:
  - `notes`: Uses `notes_width` directly.
  - `drawing`: Protects `drawing_min_width`; notes panel shrinks if needed.

**Units:**
Values accept CSS lengths:
- Absolute: `86mm`, `320px`
- Relative: `24%` (percentage of the work-area dimension)

## Strip Detail (Optional)

If your drawing requires a strip detail image and caption:

- `strip_detail_title`: title above the image
- `strip_detail_image`: path to image (relative to YAML)
- `strip_detail_alt`: alt text
- `strip_detail_caption`: descriptive caption

If no image is provided, the strip detail panel is hidden automatically.

## Best Practices

- Place images under `images/` next to your YAML; reference with YAML-relative paths.
- Keep links in `manufacturer` or `mpn` when you want clickable BOM columns.
- Use `additional_bom_items` for photos and any custom BOM note rows.
- Keep `template.name` as `engineering-sheet` unless you provide a custom template.

## See Also

- Engineering sheet template: `engineering-sheet.html`
- Examples: `examples/minimal_drawing.yaml`
- Troubleshooting guide: `docs/troubleshooting.md`
- README overview: `README.md`

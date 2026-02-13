# YAML Configuration Reference

This document summarizes the YAML fields and metadata used by WireVizHelper.

**Tip:** Start with `examples/minimal_drawing.yaml` and add options as needed.

## Core Structure

- `connectors`: List of connectors (standard WireViz).
- `cables`: List of cables/harness segments (standard WireViz).
- `connections`: Wiring definitions (standard WireViz).
- `additional_bom_items`: Helper rows for photos or custom BOM items.
- `metadata`: Configuration for the engineering sheet template.

## BOM Fields

Use these standard WireViz keys inside `connectors` or `cables` entries:

| Key | Description |
| :--- | :--- |
| `manufacturer` | Manufacturer name. |
| `mpn` | Manufacturer Part Number. |
| `pn` | Internal Part Number (optional). |
| `supplier` | Distributor/Supplier name (optional). |
| `spn` | **Product Photo**. WireVizHelper repurposes this field for images. |

**HTML Support:** You can use HTML in `manufacturer` or `mpn` for links:

```yaml
mpn: '<a href="https://example.com/part">12345</a>'
```

## Product Photos in BOM (photo-in-row)

To display a photo in the BOM row for a component:

1. Define the component in `connectors` or `cables` as usual.
2. Add a helper entry in `additional_bom_items`.
3. Set `spn` to an HTML `<img>` tag.
4. Match the `Designators` or `MPN` of the target component.

*WireVizHelper merges this helper row into the main part row during the build.*

**Example:**

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

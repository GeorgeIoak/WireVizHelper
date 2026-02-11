#!/usr/bin/env python
"""WireViz build wrapper with minimal BOM header normalization.

This script intentionally keeps post-processing minimal and generic:
1) Run WireViz on the selected YAML file.
2) Rename BOM header `SPN` -> `Product Photo` in generated HTML/TSV outputs.

Usage:
  python build.py [path/to/drawing.yaml] [-- <extra wireviz args>]
"""

from __future__ import annotations

import csv
import importlib.util
import os
import site
import sysconfig
import tempfile
import re
import runpy
import shutil
import subprocess
import sys
from os.path import relpath
from pathlib import Path
from urllib.parse import quote
try:
    import yaml
except ModuleNotFoundError:
    yaml = None  # type: ignore[assignment]

DEFAULT_YAML_CANDIDATES = ("drawing.yaml",)
DEFAULT_OUTPUT_DIR = "output"
PHOTO_HEADER_FROM = "SPN"
PHOTO_HEADER_TO = "Product Photo"
SHEETSIZE_TO_MM: dict[str, tuple[float, float]] = {
    "A4": (297, 210),
    "A3": (420, 297),
    "A2": (594, 420),
    "LETTER": (279.4, 215.9),
    "LEGAL": (355.6, 215.9),
    "TABLOID": (431.8, 279.4),
}
WKHTML_PAGE_SIZE: dict[str, str] = {
    "A4": "A4",
    "A3": "A3",
    "A2": "A2",
    "LETTER": "Letter",
    "LEGAL": "Legal",
    "TABLOID": "Tabloid",
}


def _runtime_roots() -> list[Path]:
    """Return possible runtime roots for source and frozen execution."""
    roots: list[Path] = []
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            roots.append(Path(meipass))
        roots.append(Path(sys.executable).resolve().parent)
    roots.append(Path(__file__).resolve().parent)

    seen: set[str] = set()
    unique: list[Path] = []
    for root in roots:
        key = str(root.resolve())
        if key in seen:
            continue
        seen.add(key)
        unique.append(root)
    return unique


def configure_portable_runtime() -> None:
    """Prepend packaged Graphviz/wkhtmltopdf bin folders to PATH if present."""
    candidates: list[Path] = []
    for root in _runtime_roots():
        candidates.extend(
            [
                root / "graphviz" / "bin",
                root / "wkhtmltopdf" / "bin",
                root / "vendor" / "graphviz" / "bin",
                root / "vendor" / "wkhtmltopdf" / "bin",
            ]
        )

    existing = [str(p) for p in candidates if p.exists()]
    if existing:
        os.environ["PATH"] = os.pathsep.join(existing + [os.environ.get("PATH", "")])
        for entry in existing:
            dot_exe = Path(entry) / "dot.exe"
            if dot_exe.exists():
                os.environ.setdefault("GRAPHVIZ_DOT", str(dot_exe))
                os.environ.setdefault("GVBINDIR", str(Path(entry)))
                # Prefer portable plugin directory when bundled.
                graphviz_root = Path(entry).parent
                plugin_dir = graphviz_root / "lib" / "graphviz"
                # Graphviz plugins (gvplugin_*.dll) live in bin on Windows.
                os.environ.setdefault("GVPLUGIN_PATH", str(Path(entry)))
                if plugin_dir.exists():
                    os.environ.setdefault("GVCONFDIR", str(plugin_dir))
                # Ensure plugin config exists for portable builds.
                config_file = plugin_dir / "config6" if plugin_dir.exists() else None
                if config_file and not config_file.exists():
                    try:
                        subprocess.run(
                            [str(dot_exe), "-c"],
                            cwd=str(graphviz_root),
                            capture_output=True,
                            text=True,
                        )
                    except Exception:
                        pass
                break


def is_frozen_app() -> bool:
    return bool(getattr(sys, "frozen", False))


def validate_runtime_requirements() -> list[str]:
    """Return user-facing runtime issues for standalone execution."""
    issues: list[str] = []
    wireviz_ready = (shutil.which("wireviz") is not None) or (
        importlib.util.find_spec("wireviz") is not None
    )
    dot_ready = (shutil.which("dot") is not None) or bool(os.environ.get("GRAPHVIZ_DOT"))

    if not wireviz_ready:
        issues.append("WireViz runtime is missing.")
    if not dot_ready:
        issues.append("Graphviz 'dot' binary is missing.")
    return issues


def _run_wireviz_module(args: list[str]) -> int:
    old_argv = sys.argv[:]
    try:
        sys.argv = ["wireviz", *args]
        # WireViz does not expose a package __main__, run the CLI module directly.
        runpy.run_module("wireviz.wv_cli", run_name="__main__", alter_sys=True)
        return 0
    except SystemExit as e:
        if isinstance(e.code, int):
            return e.code
        return 0 if e.code in (None, False) else 1
    except Exception as e:
        print(f"Error: Failed to execute wireviz module: {e}")
        return 1
    finally:
        sys.argv = old_argv


configure_portable_runtime()


def split_args(argv: list[str]) -> tuple[list[str], list[str]]:
    if "--" in argv:
        idx = argv.index("--")
        return argv[:idx], argv[idx + 1 :]
    return argv, []


def resolve_yaml(args: list[str]) -> Path:
    if args:
        yaml_path = Path(args[0])
        if not yaml_path.exists():
            print(f"Error: YAML file not found: {yaml_path}")
            sys.exit(1)
        return yaml_path

    for candidate in DEFAULT_YAML_CANDIDATES:
        yaml_path = Path(candidate)
        if yaml_path.exists():
            return yaml_path

    print(
        "Error: No default YAML file found. Looked for: "
        + ", ".join(DEFAULT_YAML_CANDIDATES)
    )
    sys.exit(1)


def load_yaml_data(yaml_path: Path) -> dict:
    """Load YAML as a dict, returning empty dict on parse/read errors."""
    if yaml is None:
        return {}
    try:
        data = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def wireviz_command(yaml_path: Path, passthrough: list[str]) -> list[str]:
    if is_frozen_app():
        return [
            sys.executable,
            "-m",
            "wireviz",
            str(yaml_path),
            *passthrough,
        ]
    wireviz_bin = shutil.which("wireviz")
    if not wireviz_bin:
        # Fall back to common user-level script locations (Windows/macOS/Linux).
        script_candidates: list[Path] = []
        scripts_path = sysconfig.get_path("scripts")
        if scripts_path:
            script_candidates.append(Path(scripts_path))
        user_base = site.getuserbase()
        if user_base:
            script_candidates.append(Path(user_base) / "Scripts")
            script_candidates.append(Path(user_base) / "bin")
        user_site = site.getusersitepackages()
        if user_site:
            user_site_path = Path(user_site)
            script_candidates.append(user_site_path.parent / "Scripts")
            script_candidates.append(user_site_path.parent / "bin")
        for base in script_candidates:
            if os.name == "nt":
                candidate = base / "wireviz.exe"
            else:
                candidate = base / "wireviz"
            if candidate.exists():
                wireviz_bin = str(candidate)
                break

    if wireviz_bin:
        return [wireviz_bin, str(yaml_path), *passthrough]
    return [
        sys.executable,
        "-m",
        "wireviz",
        str(yaml_path),
        *passthrough,
    ]


def run_wireviz(
    yaml_path: Path, passthrough: list[str], output_dir: Path
) -> tuple[int, str, str, str]:
    yaml_path = yaml_path.resolve()
    passthrough_with_dir = ensure_output_dir_arg(passthrough, output_dir)
    cmd = wireviz_command(yaml_path, passthrough_with_dir)
    cmd_display = " ".join(cmd)

    # In frozen apps, `sys.executable -m wireviz` is not a valid invocation.
    if (
        getattr(sys, "frozen", False)
        and len(cmd) >= 3
        and cmd[0] == sys.executable
        and cmd[1] == "-m"
        and cmd[2] == "wireviz"
    ):
        code = _run_wireviz_module([str(yaml_path), *passthrough_with_dir])
        return (
            code,
            "wireviz " + " ".join([str(yaml_path), *passthrough_with_dir]),
            "",
            "",
        )

    result = subprocess.run(
        cmd, capture_output=True, text=True, cwd=str(yaml_path.parent.resolve())
    )
    stdout = (result.stdout or "").strip()
    stderr = (result.stderr or "").strip()
    if stdout:
        print(stdout)
    if stderr:
        print(stderr)
    return result.returncode, cmd_display, stdout, stderr


def ensure_runtime_dependencies() -> None:
    """Best-effort dependency check/install for first-run convenience."""
    global yaml
    if is_frozen_app():
        return

    wireviz_bin = shutil.which("wireviz")
    wireviz_module = importlib.util.find_spec("wireviz") is not None
    yaml_module = yaml is not None
    if (wireviz_bin or wireviz_module) and yaml_module:
        return

    req = Path(__file__).resolve().parent / "requirements.txt"
    if not req.exists():
        print(
            "Error: WireViz is not installed and requirements.txt was not found.\n"
            "Install dependencies first: python -m pip install wireviz"
        )
        sys.exit(1)

    print("Missing runtime dependencies detected. Installing from requirements.txt ...", flush=True)
    result = subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(req)])
    if result.returncode != 0:
        print(
            "Error: Dependency install failed.\n"
            f"Try manually: {sys.executable} -m pip install -r {req}"
        )
        sys.exit(result.returncode)

    # Re-import PyYAML after successful install if it was missing.
    if yaml is None:
        import yaml as _yaml

        yaml = _yaml


def _flag_value(args: list[str], short_flag: str, long_flag: str) -> str | None:
    for i, a in enumerate(args):
        if a == short_flag or a == long_flag:
            if i + 1 < len(args):
                return args[i + 1]
            return None
        if a.startswith(f"{long_flag}="):
            return a.split("=", 1)[1]
    return None


def resolve_output_paths(yaml_path: Path, passthrough: list[str]) -> tuple[Path, str]:
    output_dir_arg = _flag_value(passthrough, "-o", "--output-dir")
    output_name_arg = _flag_value(passthrough, "-O", "--output-name")

    if output_dir_arg:
        output_dir = Path(output_dir_arg)
        if not output_dir.is_absolute():
            output_dir = (Path.cwd() / output_dir).resolve()
    else:
        output_dir = (yaml_path.parent / DEFAULT_OUTPUT_DIR).resolve()

    output_name = output_name_arg.strip() if output_name_arg else yaml_path.stem
    return output_dir, output_name


def ensure_output_dir_arg(passthrough: list[str], output_dir: Path) -> list[str]:
    has_output_dir = _flag_value(passthrough, "-o", "--output-dir") is not None
    if has_output_dir:
        return passthrough
    return [*passthrough, "--output-dir", str(output_dir)]


def wireviz_command_with_output(yaml_path: Path, passthrough: list[str], output_dir: Path) -> list[str]:
    passthrough_with_dir = ensure_output_dir_arg(passthrough, output_dir)
    return wireviz_command(yaml_path, passthrough_with_dir)


def prepare_local_template_for_output(
    yaml_path: Path, output_dir: Path, yaml_data: dict
) -> Path | None:
    """Ensure custom template files next to YAML are discoverable when using output dir."""
    metadata = yaml_data.get("metadata", {})
    template = metadata.get("template", {}) if isinstance(metadata, dict) else {}
    template_name = template.get("name") if isinstance(template, dict) else None
    if not isinstance(template_name, str) or not template_name.strip():
        return None

    if Path(template_name).is_absolute():
        return None

    src = yaml_path.parent / f"{template_name}.html"
    if not src.exists():
        # Fallback to toolkit-local template when building external projects.
        src = Path(__file__).resolve().parent / f"{template_name}.html"
    if not src.exists():
        for root in _runtime_roots():
            probe = root / f"{template_name}.html"
            if probe.exists():
                src = probe
                break
    if not src.exists():
        return None

    dst = output_dir / src.name
    if src.resolve() == dst.resolve():
        return None
    shutil.copy2(src, dst)
    return dst


def resolve_sheetsize(yaml_data: dict) -> str:
    """Read requested sheet size from YAML metadata, defaulting to A4."""
    metadata = yaml_data.get("metadata", {})
    template = metadata.get("template", {}) if isinstance(metadata, dict) else {}
    sheetsize = template.get("sheetsize") if isinstance(template, dict) else None
    if not isinstance(sheetsize, str):
        return "A4"
    candidate = sheetsize.strip().upper()
    return candidate if candidate in SHEETSIZE_TO_MM else "A4"


def _path_for_chromium_arg(path: Path) -> str:
    """Return a path string suitable for Chromium CLI flags on any OS."""
    resolved = str(path.resolve())
    if os.name == "nt":
        if resolved.startswith("\\\\?\\"):
            resolved = resolved[4:]
        return resolved.replace("\\", "/")
    return resolved


def _file_uri(path: Path) -> str:
    """Build a file:/// URI from a path, safe on all Windows Python versions."""
    resolved = str(path.resolve())
    # Strip \\?\ extended-length prefix that Windows can produce
    if resolved.startswith("\\\\?\\"):
        resolved = resolved[4:]
    posix = resolved.replace("\\", "/")
    return "file:///" + quote(posix, safe=":/@")


def _css_page_size(sheetsize: str) -> str:
    return WKHTML_PAGE_SIZE.get(sheetsize.upper(), sheetsize.upper())


def _pdf_looks_like_error_page(pdf_path: Path) -> bool:
    """Detect common headless browser error pages saved as PDF."""
    try:
        data = pdf_path.read_bytes()
    except Exception:
        return False
    # Check for typical Chromium/Edge error strings embedded in the PDF.
    haystack = data[:200000].lower()
    return (
        b"file not found" in haystack
        or b"err_file_not_found" in haystack
        or b"this page isn\x27t working" in haystack
        or b"couldn\x27t be loaded" in haystack
    )


def _browser_candidates() -> list[tuple[str, str]]:
    """Return candidate Chromium-based browsers for headless PDF export."""
    candidates: list[tuple[str, str]] = []

    env_browser = os.environ.get("WIREVIZ_PDF_BROWSER", "").strip()
    if env_browser:
        if os.path.exists(env_browser):
            candidates.append(("env", env_browser))

    names_by_os: list[str]
    if sys.platform.startswith("win"):
        names_by_os = [
            "msedge",
            "msedge.exe",
            "chrome",
            "chrome.exe",
            "google-chrome",
            "chromium",
            "brave",
            "brave.exe",
        ]
        pf = os.environ.get("ProgramFiles", r"C:\Program Files")
        pf86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
        local = os.environ.get("LocalAppData", "")
        known_paths = [
            os.path.join(pf, "Microsoft", "Edge", "Application", "msedge.exe"),
            os.path.join(pf86, "Microsoft", "Edge", "Application", "msedge.exe"),
            os.path.join(local, "Microsoft", "Edge", "Application", "msedge.exe"),
            os.path.join(pf, "Google", "Chrome", "Application", "chrome.exe"),
            os.path.join(pf86, "Google", "Chrome", "Application", "chrome.exe"),
            os.path.join(local, "Google", "Chrome", "Application", "chrome.exe"),
            os.path.join(pf, "BraveSoftware", "Brave-Browser", "Application", "brave.exe"),
            os.path.join(pf86, "BraveSoftware", "Brave-Browser", "Application", "brave.exe"),
            os.path.join(local, "BraveSoftware", "Brave-Browser", "Application", "brave.exe"),
        ]
    elif sys.platform == "darwin":
        names_by_os = ["chrome", "chromium", "brave", "microsoft-edge"]
        known_paths = [
            "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Chromium.app/Contents/MacOS/Chromium",
            "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
        ]
    else:
        names_by_os = [
            "google-chrome",
            "google-chrome-stable",
            "chromium",
            "chromium-browser",
            "brave-browser",
            "microsoft-edge",
        ]
        known_paths = []

    for name in names_by_os:
        path = shutil.which(name)
        if path:
            candidates.append((name, path))

    for path in known_paths:
        if path and os.path.exists(path):
            candidates.append(("known", path))

    # De-duplicate while preserving order.
    seen: set[str] = set()
    unique: list[tuple[str, str]] = []
    for label, path in candidates:
        key = os.path.abspath(path)
        if key in seen:
            continue
        seen.add(key)
        unique.append((label, path))
    return unique


def generate_pdf_via_browser(html_path: Path, pdf_path: Path, sheetsize: str) -> tuple[bool, str | None]:
    """Generate PDF using a headless Chromium-based browser if available."""
    candidates = _browser_candidates()
    if not candidates:
        return False, "no supported browser found (set WIREVIZ_PDF_BROWSER)"

    html_for_print = html_path
    injected = False
    try:
        html_text = html_path.read_text(encoding="utf-8")
        css_size = _css_page_size(sheetsize)
        base_href = _file_uri(html_path.parent).rstrip("/") + "/"
        base_tag = f'<base href="{base_href}">'
        style_block = (
            "<style>"
            f"@page {{ size: {css_size} landscape; margin: 0; }}"
            "html, body { margin: 0; padding: 0; }"
            "</style>"
        )
        if "</head>" in html_text:
            html_text = html_text.replace("</head>", f"{base_tag}{style_block}</head>", 1)
        else:
            html_text = base_tag + style_block + html_text
        html_for_print = html_path.with_suffix(".print.html")
        html_for_print.write_text(html_text, encoding="utf-8")
        injected = True
    except Exception:
        html_for_print = html_path

    html_url = _file_uri(html_for_print)
    pdf_arg = _path_for_chromium_arg(pdf_path.resolve())
    headless_modes = ["--headless=old", "--headless=new", "--headless"]
    last_error: str | None = None

    for _, browser in candidates:
        browser_lower = os.path.basename(browser).lower()
        is_edge = "edge" in browser_lower or "msedge" in browser_lower
        for headless in headless_modes:
            if pdf_path.exists():
                try:
                    pdf_path.unlink()
                except Exception:
                    pass
            with tempfile.TemporaryDirectory() as profile_dir:
                cmd = [
                    browser,
                    headless,
                    "--disable-gpu",
                    "--no-first-run",
                    "--disable-extensions",
                    "--disable-background-networking",
                    "--disable-sync",
                    "--no-default-browser-check",
                    "--landscape",
                    "--allow-file-access-from-files",
                    "--allow-file-access",
                    f"--user-data-dir={profile_dir}",
                    "--no-pdf-header-footer",
                    f"--print-to-pdf={pdf_arg}",
                    html_url,
                ]
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True)
                except FileNotFoundError:
                    last_error = f"browser not found: {browser}"
                    continue
                if result.returncode == 0 and pdf_path.exists() and pdf_path.stat().st_size > 0:
                    if _pdf_looks_like_error_page(pdf_path):
                        try:
                            pdf_path.unlink()
                        except Exception:
                            pass
                        last_error = "browser rendered error page (file not found)"
                        continue
                    if injected:
                        try:
                            html_for_print.unlink(missing_ok=True)
                        except Exception:
                            pass
                    engine = "edge" if is_edge else "chromium"
                    return True, f"{engine} headless"
                stderr = (result.stderr or "").strip()
                stdout = (result.stdout or "").strip()
                last_error = stderr or stdout or f"exit {result.returncode}"

    if injected:
        try:
            html_for_print.unlink(missing_ok=True)
        except Exception:
            pass
    return False, f"browser print failed: {last_error}"


def generate_pdf(html_path: Path, pdf_path: Path, sheetsize: str) -> tuple[bool, str | None]:
    """Generate a single-page PDF from HTML using an available engine."""
    if not html_path.exists():
        return False, "HTML output was not found"

    browser_ok, browser_note = generate_pdf_via_browser(html_path, pdf_path, sheetsize)
    if browser_ok:
        return True, browser_note

    page_width_mm, page_height_mm = SHEETSIZE_TO_MM.get(sheetsize, SHEETSIZE_TO_MM["A4"])

    # Optional engine: WeasyPrint (Python package).
    weasyprint_error: str | None = None
    try:
        from weasyprint import CSS, HTML  # type: ignore

        css = CSS(
            string=(
                f"@page {{ size: {page_width_mm}mm {page_height_mm}mm !important; margin: 0 !important; }}"
                "html, body { margin: 0 !important; padding: 0 !important; }"
                "#sheet { page-break-inside: avoid; break-inside: avoid; }"
            )
        )
        HTML(filename=str(html_path), base_url=str(html_path.parent)).write_pdf(
            str(pdf_path), stylesheets=[css]
        )
        return True, "weasyprint"
    except Exception as e:
        weasyprint_error = str(e).strip() or e.__class__.__name__

    # Optional fallback: wkhtmltopdf CLI.
    wkhtmltopdf_bin = shutil.which("wkhtmltopdf")
    if wkhtmltopdf_bin:
        wk_page_size = WKHTML_PAGE_SIZE.get(sheetsize, "A4")
        cmd = [
            wkhtmltopdf_bin,
            "--enable-local-file-access",
            "--orientation",
            "Landscape",
            "--page-size",
            wk_page_size,
            "--margin-top",
            "0",
            "--margin-right",
            "0",
            "--margin-bottom",
            "0",
            "--margin-left",
            "0",
            str(html_path),
            str(pdf_path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return True, "wkhtmltopdf"
        wk_error = (result.stderr or result.stdout).strip() or "unknown error"
        parts = []
        if browser_note:
            parts.append(f"browser: {browser_note}")
        if weasyprint_error:
            parts.append(f"weasyprint: {weasyprint_error}")
        parts.append(f"wkhtmltopdf: {wk_error}")
        return False, f"PDF engine failed: {'; '.join(parts)}"

    parts = []
    if browser_note:
        parts.append(f"browser: {browser_note}")
    if weasyprint_error:
        parts.append(f"weasyprint: {weasyprint_error}")
    if parts:
        return False, f"PDF engine failed: {'; '.join(parts)}"
    return False, (
        "browser print failed and no optional PDF engine found "
        "(open the HTML in a browser and print to PDF)"
    )


def _is_photo_row(row: dict[str, str], photo_col: str) -> bool:
    description = (row.get("Description") or "").strip().lower()
    return bool((row.get(photo_col) or "").strip()) and "photo" in description


def merge_photo_rows_in_tsv(tsv_path: Path) -> bool:
    if not tsv_path.exists():
        return False

    with tsv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        rows = list(reader)
        fieldnames = list(reader.fieldnames or [])

    if not rows or not fieldnames:
        return False

    photo_col = PHOTO_HEADER_FROM if PHOTO_HEADER_FROM in fieldnames else PHOTO_HEADER_TO
    if photo_col not in fieldnames:
        return False

    changed = False
    remove_indexes: set[int] = set()

    non_photo_by_designator: dict[str, int] = {}
    non_photo_by_mpn: dict[str, int] = {}
    for idx, row in enumerate(rows):
        if _is_photo_row(row, photo_col):
            continue
        designator = (row.get("Designators") or "").strip()
        mpn = (row.get("MPN") or "").strip()
        if designator and designator not in non_photo_by_designator:
            non_photo_by_designator[designator] = idx
        if mpn and mpn not in non_photo_by_mpn:
            non_photo_by_mpn[mpn] = idx

    for idx, row in enumerate(rows):
        if not _is_photo_row(row, photo_col):
            continue

        designator = (row.get("Designators") or "").strip()
        mpn = (row.get("MPN") or "").strip()
        target_idx: int | None = None

        if designator:
            target_idx = non_photo_by_designator.get(designator)

        # Fallback when Designators are blank (e.g. connector show_name: false):
        # match against the same part number.
        if target_idx is None and mpn:
            target_idx = non_photo_by_mpn.get(mpn)

        if target_idx is None:
            continue

        target = rows[target_idx]
        merged_this_row = False

        # If the matched BOM row has blank designator (common when show_name: false),
        # carry over the explicit designator from the photo helper row.
        if designator and not (target.get("Designators") or "").strip():
            target["Designators"] = designator
            changed = True
            merged_this_row = True

        if not (target.get(photo_col) or "").strip():
            target[photo_col] = row.get(photo_col) or ""
            changed = True
            merged_this_row = True

        if merged_this_row:
            remove_indexes.add(idx)

    if not changed:
        return False

    kept_rows = [row for idx, row in enumerate(rows) if idx not in remove_indexes]

    with tsv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(kept_rows)
    return True


def merge_photo_rows_in_html(html_path: Path) -> bool:
    if not html_path.exists():
        return False
    content = html_path.read_text(encoding="utf-8")

    table_pattern = re.compile(
        r'(<table class="bom">\s*)(.*?)(\s*</table>)',
        re.DOTALL,
    )
    table_match = table_pattern.search(content)
    if not table_match:
        return False

    table_body = table_match.group(2)
    row_pattern_all = re.compile(r"<tr>.*?</tr>", re.DOTALL)
    row_pattern_data = re.compile(r"<tr>\s*(?:<td class=\"[^\"]+\">.*?</td>\s*)+</tr>", re.DOTALL)
    desc_pattern = re.compile(r'<td class="bom_col_description">(.*?)</td>', re.DOTALL)
    desig_pattern = re.compile(r'<td class="bom_col_designators">(.*?)</td>', re.DOTALL)
    spn_pattern = re.compile(r'<td class="bom_col_spn">(.*?)</td>', re.DOTALL)
    mpn_pattern = re.compile(r'<td class="bom_col_mpn">(.*?)</td>', re.DOTALL)

    all_rows = [m.group(0) for m in row_pattern_all.finditer(table_body)]
    data_row_indexes = [i for i, r in enumerate(all_rows) if row_pattern_data.fullmatch(r)]
    if not data_row_indexes:
        return False

    parsed = []
    for row_idx in data_row_indexes:
        row_html = all_rows[row_idx]
        desc_m = desc_pattern.search(row_html)
        desig_m = desig_pattern.search(row_html)
        spn_m = spn_pattern.search(row_html)
        mpn_m = mpn_pattern.search(row_html)
        parsed.append((row_idx, row_html, desc_m, desig_m, spn_m, mpn_m))

    remove_idx: set[int] = set()
    changed = False

    for i, (_, row_html, desc_m, desig_m, spn_m, mpn_m) in enumerate(parsed):
        if not (desc_m and desig_m and spn_m):
            continue

        description = re.sub(r"<.*?>", "", desc_m.group(1)).strip().lower()
        designator = re.sub(r"<.*?>", "", desig_m.group(1)).strip()
        spn_inner = spn_m.group(1).strip()
        mpn = re.sub(r"<.*?>", "", (mpn_m.group(1) if mpn_m else "")).strip()

        if not (spn_inner and "photo" in description):
            continue

        target = None
        for j, (_, t_row_html, t_desc, t_desig, t_spn, t_mpn) in enumerate(parsed):
            if i == j:
                continue
            if not (t_desc and t_desig and t_spn):
                continue
            t_description = re.sub(r"<.*?>", "", t_desc.group(1)).strip().lower()
            t_designator = re.sub(r"<.*?>", "", t_desig.group(1)).strip()
            t_spn_inner = t_spn.group(1).strip()
            t_mpn = re.sub(r"<.*?>", "", (t_mpn.group(1) if t_mpn else "")).strip()
            same_designator = bool(designator) and (t_designator == designator)
            same_mpn = bool(mpn) and (t_mpn == mpn)
            if (same_designator or same_mpn) and "photo" not in t_description and not t_spn_inner:
                target = (j, t_row_html)
                break

        if target is None:
            continue

        j, t_row_html = target
        merged_this_row = False
        updated_target = t_row_html
        if not t_spn_inner:
            next_target = re.sub(
                r'(<td class="bom_col_spn">)\s*(.*?)\s*(</td>)',
                rf"\1{spn_inner}\3",
                t_row_html,
                count=1,
                flags=re.DOTALL,
            )
            if next_target != updated_target:
                updated_target = next_target
                merged_this_row = True
        # Backfill blank designator on target row when helper row has one.
        if designator:
            desig_target_m = desig_pattern.search(updated_target)
            if desig_target_m:
                t_designator_inner = re.sub(r"<.*?>", "", desig_target_m.group(1)).strip()
                if not t_designator_inner:
                    next_target = re.sub(
                        r'(<td class="bom_col_designators">)\s*(.*?)\s*(</td>)',
                        rf"\1{designator}\3",
                        updated_target,
                        count=1,
                        flags=re.DOTALL,
                    )
                    if next_target != updated_target:
                        updated_target = next_target
                        merged_this_row = True
        if not merged_this_row:
            continue
        parsed[j] = (
            parsed[j][0],
            updated_target,
            parsed[j][2],
            parsed[j][3],
            parsed[j][4],
            parsed[j][5],
        )
        remove_idx.add(i)
        changed = True

    if not changed:
        return False

    for idx, (row_idx, row_html, _, _, _, _) in enumerate(parsed):
        if idx in remove_idx:
            all_rows[row_idx] = ""
        else:
            all_rows[row_idx] = row_html

    new_table_body = "\n".join(r for r in all_rows if r)
    content = (
        content[: table_match.start(2)]
        + new_table_body
        + content[table_match.end(2) :]
    )

    html_path.write_text(content, encoding="utf-8")
    return True


def rename_header_in_tsv(tsv_path: Path) -> bool:
    if not tsv_path.exists():
        return False
    lines = tsv_path.read_text(encoding="utf-8").splitlines()
    if not lines:
        return False

    cols = lines[0].split("\t")
    changed = False
    cols_new = []
    for c in cols:
        if c == PHOTO_HEADER_FROM:
            cols_new.append(PHOTO_HEADER_TO)
            changed = True
        else:
            cols_new.append(c)

    if changed:
        lines[0] = "\t".join(cols_new)
        tsv_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return changed


def rename_header_in_html(html_path: Path) -> bool:
    if not html_path.exists():
        return False
    content = html_path.read_text(encoding="utf-8")

    # Primary target: WireViz BOM header cell for the SPN column.
    updated = re.sub(
        r'(<th\s+class="bom_col_spn">)\s*SPN\s*(</th>)',
        rf"\1{PHOTO_HEADER_TO}\2",
        content,
        flags=re.IGNORECASE,
    )

    # Fallback: plain header text if class changes in a future template.
    if updated == content:
        updated = re.sub(
            r"(<th[^>]*>)\s*SPN\s*(</th>)",
            rf"\1{PHOTO_HEADER_TO}\2",
            content,
            flags=re.IGNORECASE,
        )

    changed = updated != content
    if changed:
        html_path.write_text(updated, encoding="utf-8")
    return changed


def _normalize_img_src_path(src: str, from_dir: Path, out_dir: Path) -> str:
    src = src.strip()
    if (
        not src
        or "://" in src
        or src.startswith("data:")
        or src.startswith("/")
        or src.startswith("#")
    ):
        return src

    candidate = (from_dir / src).resolve()
    if not candidate.exists():
        return src

    try:
        rel = Path(relpath(candidate, out_dir.resolve())).as_posix()
    except Exception:
        return src
    return rel


def rewrite_relative_image_paths(path: Path, source_dir: Path, output_dir: Path) -> bool:
    """Rewrite <img src=\"...\"> paths so they stay valid from output_dir."""
    if not path.exists():
        return False
    content = path.read_text(encoding="utf-8")

    changed = False

    def repl_double(m: re.Match[str]) -> str:
        nonlocal changed
        orig = m.group(2)
        new = _normalize_img_src_path(orig, source_dir, output_dir)
        if new != orig:
            changed = True
        return f'{m.group(1)}{new}{m.group(3)}'

    def repl_single(m: re.Match[str]) -> str:
        nonlocal changed
        orig = m.group(2)
        new = _normalize_img_src_path(orig, source_dir, output_dir)
        if new != orig:
            changed = True
        return f"{m.group(1)}{new}{m.group(3)}"

    updated = re.sub(r'(<img\b[^>]*\bsrc=")([^"]+)(")', repl_double, content, flags=re.IGNORECASE)
    updated = re.sub(r"(<img\b[^>]*\bsrc=')([^']+)(')", repl_single, updated, flags=re.IGNORECASE)

    if changed and updated != content:
        path.write_text(updated, encoding="utf-8")
    return changed


def detect_notes_overflow_risk(yaml_data: dict) -> str | None:
    """Return a lightweight layout-risk warning for notes panel overflow."""
    metadata = yaml_data.get("metadata", {})
    if not isinstance(metadata, dict):
        return None

    notes_raw = metadata.get("notes")
    notes = str(notes_raw) if isinstance(notes_raw, (str, int, float)) else ""
    notes_lines = [ln for ln in notes.splitlines() if ln.strip()]

    has_strip_detail = bool(str(metadata.get("strip_detail_image", "")).strip())

    # Conservative heuristic: strip detail plus substantial notes commonly overflows.
    if has_strip_detail and len(notes_lines) >= 9:
        return (
            "Layout warning: notes panel may overflow (strip detail image is enabled and "
            f"notes has {len(notes_lines)} non-empty lines). "
            "If you see a scrollbar, try one: increase metadata.notes_width, reduce "
            "strip detail image max-height in engineering-sheet.html (#strip-detail-image), "
            "or shorten metadata.notes text."
        )
    if len(notes_lines) >= 13:
        return (
            "Layout warning: notes panel may overflow (notes has "
            f"{len(notes_lines)} non-empty lines). "
            "If you see a scrollbar, try increasing metadata.notes_width or shortening notes."
        )
    return None


def main() -> None:
    ensure_runtime_dependencies()
    script_args, passthrough = split_args(sys.argv[1:])
    yaml_path = resolve_yaml(script_args)
    yaml_data = load_yaml_data(yaml_path)
    output_dir, output_name = resolve_output_paths(yaml_path, passthrough)
    sheetsize = resolve_sheetsize(yaml_data)
    output_dir.mkdir(parents=True, exist_ok=True)
    copied_template = prepare_local_template_for_output(yaml_path, output_dir, yaml_data)
    result_code, cmd_display, stdout, stderr = run_wireviz(yaml_path, passthrough, output_dir)
    print(f"Running: {cmd_display}")
    if result_code != 0:
        log_path = output_dir / "wireviz-error.log"
        log_lines = [
            "=== WIREVIZ FAILURE ===",
            f"Command: {cmd_display}",
            f"Exit code: {result_code}",
        ]
        if stdout:
            log_lines.append("")
            log_lines.append("=== STDOUT ===")
            log_lines.append(stdout)
        if stderr:
            log_lines.append("")
            log_lines.append("=== STDERR ===")
            log_lines.append(stderr)
        log_path.write_text("\n".join(log_lines) + "\n", encoding="utf-8")
        print(f"WireViz error log: {log_path}")
        if copied_template and copied_template.exists():
            try:
                copied_template.unlink()
            except Exception:
                pass
        sys.exit(result_code)

    base = output_dir / output_name
    html_path = base.with_suffix(".html")
    pdf_path = base.with_suffix(".pdf")
    tsv_path = Path(f"{base}.bom.tsv")

    merged_tsv = merge_photo_rows_in_tsv(tsv_path)
    merged_html = merge_photo_rows_in_html(html_path)
    html_changed = rename_header_in_html(html_path)
    tsv_changed = rename_header_in_tsv(tsv_path)
    html_img_paths = rewrite_relative_image_paths(html_path, yaml_path.parent, output_dir)
    tsv_img_paths = rewrite_relative_image_paths(tsv_path, yaml_path.parent, output_dir)
    pdf_generated, pdf_note = generate_pdf(html_path, pdf_path, sheetsize)

    if copied_template and copied_template.exists():
        try:
            copied_template.unlink()
        except Exception:
            pass

    print("Generated outputs:")
    html_notes = []
    if merged_html:
        html_notes.append("photo row merged")
    if html_changed:
        html_notes.append("header normalized")
    if html_img_paths:
        html_notes.append("image paths normalized")
    print(f"  {base.with_suffix('.html')}" + (f" ({', '.join(html_notes)})" if html_notes else ""))
    print(f"  {base.with_suffix('.svg')}")
    print(f"  {base.with_suffix('.png')}")
    if pdf_generated:
        print(f"  {base.with_suffix('.pdf')} (single-page via {pdf_note})")
    else:
        print(f"  {base.with_suffix('.pdf')} (not generated: {pdf_note})")
        print("  PDF setup: open the HTML in your browser and print to PDF.")
        print("  Optional: install wkhtmltopdf or WeasyPrint for automated CLI PDF output.")
    tsv_notes = []
    if merged_tsv:
        tsv_notes.append("photo row merged")
    if tsv_changed:
        tsv_notes.append("header normalized")
    if tsv_img_paths:
        tsv_notes.append("image paths normalized")
    print(f"  {base}.bom.tsv" + (f" ({', '.join(tsv_notes)})" if tsv_notes else ""))
    print("Note: SPN is relabeled as Product Photo in HTML/TSV. SVG/PNG are diagram outputs.")
    overflow_warning = detect_notes_overflow_risk(yaml_data)
    if overflow_warning:
        print(f"Warning: {overflow_warning}")


if __name__ == "__main__":
    main()

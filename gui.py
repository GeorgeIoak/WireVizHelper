#!/usr/bin/env python
import argparse
import csv
import os
import shlex
import shutil
import subprocess
import sys
import traceback
from pathlib import Path

import scaffold
import build
from version import __version__


def _configure_tk_runtime() -> None:
    """Point tkinter to bundled Tcl/Tk when running as a frozen app."""
    if not getattr(sys, "frozen", False):
        return
    base = Path(getattr(sys, "_MEIPASS", ""))
    if not base:
        return
    tcl_dir = base / "_tcl_data"
    tk_dir = base / "_tk_data"
    if tcl_dir.exists():
        os.environ.setdefault("TCL_LIBRARY", str(tcl_dir))
    if tk_dir.exists():
        os.environ.setdefault("TK_LIBRARY", str(tk_dir))


def _load_gui_lib():
    _configure_tk_runtime()
    try:
        import FreeSimpleGUI as _sg
    except ModuleNotFoundError:
        import PySimpleGUI as _sg
    return _sg


def run_smoke_test(workdir: Path) -> int:
    """Headless end-to-end check for packaged runtime in CI."""
    output_dir = None
    try:
        workdir.mkdir(parents=True, exist_ok=True)
        class Args:
            pass

        args = Args()
        args.name = "Smoke Project"
        args.dest = str(workdir)
        args.yaml_name = "drawing.yaml"
        args.in_place = False
        args.force = True

        scaffold.ensure_runtime_dependencies()
        target, project_name = scaffold.resolve_target(args)
        yaml_name = scaffold._normalize_yaml_name(args.yaml_name)
        scaffold.ensure_target(target, args.force)
        scaffold.scaffold_project(target, project_name, yaml_name)

        yaml_path = target / yaml_name
        if not yaml_path.exists():
            print(f"Smoke test failed: YAML was not created: {yaml_path}")
            return 1

        build.ensure_runtime_dependencies()
        yaml_data = build.load_yaml_data(yaml_path)
        output_dir, output_name = build.resolve_output_paths(yaml_path, [])
        output_dir.mkdir(parents=True, exist_ok=True)

        _append_smoke_debug(output_dir, "=== SMOKE DEBUG START ===")
        _append_smoke_debug(output_dir, f"YAML: {yaml_path}")
        _append_smoke_debug(output_dir, f"OUTPUT_DIR: {output_dir}")
        _append_smoke_debug(output_dir, f"PATH: {os.environ.get('PATH','')}")
        _append_smoke_debug(output_dir, f"GRAPHVIZ_DOT: {os.environ.get('GRAPHVIZ_DOT','')}")
        _append_smoke_debug(output_dir, f"GVBINDIR: {os.environ.get('GVBINDIR','')}")
        _append_smoke_debug(output_dir, f"GVPLUGIN_PATH: {os.environ.get('GVPLUGIN_PATH','')}")
        _append_smoke_debug(output_dir, f"GVCONFDIR: {os.environ.get('GVCONFDIR','')}")

        # Preflight: verify WireViz + Graphviz before running the build.
        try:
            import wireviz  # noqa: F401
            _append_smoke_debug(output_dir, "WIREVIZ IMPORT: OK")
        except Exception as e:
            _append_smoke_debug(output_dir, f"WIREVIZ IMPORT FAILED: {e}")
            return 1

        dot_path = os.environ.get("GRAPHVIZ_DOT") or shutil.which("dot")
        _append_smoke_debug(output_dir, f"DOT_PATH: {dot_path or ''}")
        if not dot_path:
            _append_smoke_debug(output_dir, "DOT CHECK FAILED: dot not found")
            return 1
        try:
            version = subprocess.run(
                [dot_path, "-V"],
                capture_output=True,
                text=True,
            )
            _append_smoke_debug(
                output_dir,
                "DOT -V STDOUT:\n" + (version.stdout or "") +
                "\nDOT -V STDERR:\n" + (version.stderr or "") +
                f"\nDOT -V EXIT: {version.returncode}",
            )
            if version.returncode != 0:
                _append_smoke_debug(output_dir, "DOT CHECK FAILED: non-zero exit")
                return 1
        except Exception as e:
            _append_smoke_debug(output_dir, f"DOT CHECK EXCEPTION: {e}")
            return 1

        copied_template = build.prepare_local_template_for_output(yaml_path, output_dir, yaml_data)
        result_code, cmd_display, stdout, stderr = build.run_wireviz(yaml_path, [], output_dir)
        print(f"Smoke test WireViz command: {cmd_display}")
        if result_code != 0:
            _write_wireviz_log(output_dir, cmd_display, result_code, stdout, stderr)
            _append_smoke_debug(output_dir, f"WIREVIZ EXIT: {result_code}")
            if stdout:
                _append_smoke_debug(output_dir, f"WIREVIZ STDOUT:\n{stdout}")
            if stderr:
                _append_smoke_debug(output_dir, f"WIREVIZ STDERR:\n{stderr}")
            print(f"Smoke test failed: WireViz returned {result_code}")
            return result_code

        base = output_dir / output_name
        html_path = base.with_suffix(".html")
        svg_path = base.with_suffix(".svg")
        png_path = base.with_suffix(".png")
        tsv_path = Path(f"{base}.bom.tsv")
        pdf_path = base.with_suffix(".pdf")

        # If outputs are missing, run Graphviz diagnostics after WireViz to capture render errors.
        dot_path = os.environ.get("GRAPHVIZ_DOT") or shutil.which("dot")
        dot_input = base.with_suffix(".tmp")
        _append_smoke_debug(output_dir, f"DOT_PATH: {dot_path or ''}")
        _append_smoke_debug(output_dir, f"DOT_INPUT_EXISTS: {dot_input.exists()}")

        build.merge_photo_rows_in_tsv(tsv_path)
        build.merge_photo_rows_in_html(html_path)
        build.rename_header_in_html(html_path)
        build.rename_header_in_tsv(tsv_path)
        build.rewrite_relative_image_paths(html_path, yaml_path.parent, output_dir)
        build.rewrite_relative_image_paths(tsv_path, yaml_path.parent, output_dir)
        pdf_generated, pdf_note = build.generate_pdf(
            html_path,
            pdf_path,
            build.resolve_sheetsize(yaml_data),
            paper_override=build.DEFAULT_AUTO_PDF_PAPER,
        )

        required = [html_path, svg_path, png_path, tsv_path, pdf_path]
        missing = [str(p) for p in required if not p.exists()]
        if missing:
            _write_wireviz_log(output_dir, cmd_display, result_code, stdout, stderr)
            _append_smoke_debug(output_dir, f"MISSING OUTPUTS: {missing}")
            if dot_path and dot_input.exists():
                diag_svg = output_dir / "diagnostic.dot.svg"
                try:
                    version = subprocess.run(
                        [dot_path, "-V"],
                        capture_output=True,
                        text=True,
                    )
                    _append_smoke_debug(
                        output_dir,
                        "DOT -V STDOUT:\n" + (version.stdout or "") +
                        "\nDOT -V STDERR:\n" + (version.stderr or "") +
                        f"\nDOT -V EXIT: {version.returncode}",
                    )
                    render = subprocess.run(
                        [dot_path, "-Tsvg", str(dot_input), "-o", str(diag_svg)],
                        capture_output=True,
                        text=True,
                    )
                    _append_smoke_debug(
                        output_dir,
                        "DOT RENDER STDOUT:\n" + (render.stdout or "") +
                        "\nDOT RENDER STDERR:\n" + (render.stderr or "") +
                        f"\nDOT RENDER EXIT: {render.returncode}",
                    )
                    if version.returncode != 0 or render.returncode != 0:
                        _write_wireviz_log(
                            output_dir,
                            f"{dot_path} -Tsvg {dot_input} -o {diag_svg}",
                            render.returncode,
                            (version.stdout or "") + (render.stdout or ""),
                            (version.stderr or "") + (render.stderr or ""),
                        )
                except Exception as e:
                    _append_smoke_debug(output_dir, f"DOT DIAGNOSTIC EXCEPTION: {e}")
                    _write_wireviz_log(
                        output_dir,
                        f"{dot_path} -Tsvg {dot_input} -o {diag_svg}",
                        1,
                        "",
                        f"Graphviz diagnostic failed: {e}",
                    )
            print("Smoke test failed: Missing required outputs:")
            for p in missing:
                print(f"  - {p}")
            return 1

        if not pdf_generated:
            _write_pdf_log(output_dir, pdf_note)
            print(f"Smoke test failed: PDF was not generated ({pdf_note})")
            return 1

        # Verify files are non-empty and contain expected signatures/content.
        empty = [str(p) for p in required if p.stat().st_size <= 0]
        if empty:
            _write_wireviz_log(output_dir, cmd_display, result_code, stdout, stderr)
            _append_smoke_debug(output_dir, f"EMPTY OUTPUTS: {empty}")
            print("Smoke test failed: Empty output files:")
            for p in empty:
                print(f"  - {p}")
            return 1

        svg_head = svg_path.read_text(encoding="utf-8", errors="ignore")[:512].lower()
        if "<svg" not in svg_head:
            _write_wireviz_log(output_dir, cmd_display, result_code, stdout, stderr)
            _append_smoke_debug(output_dir, f"SVG SIGNATURE MISSING: {svg_path}")
            print(f"Smoke test failed: SVG signature not found in {svg_path}")
            return 1

        with png_path.open("rb") as f:
            png_sig = f.read(8)
        if png_sig != b"\x89PNG\r\n\x1a\n":
            _write_wireviz_log(output_dir, cmd_display, result_code, stdout, stderr)
            _append_smoke_debug(output_dir, f"PNG SIGNATURE MISMATCH: {png_path}")
            print(f"Smoke test failed: PNG signature mismatch in {png_path}")
            return 1

        with pdf_path.open("rb") as f:
            pdf_sig = f.read(5)
        if pdf_sig != b"%PDF-":
            _write_wireviz_log(output_dir, cmd_display, result_code, stdout, stderr)
            _append_smoke_debug(output_dir, f"PDF SIGNATURE MISMATCH: {pdf_path}")
            print(f"Smoke test failed: PDF signature mismatch in {pdf_path}")
            return 1

        html_text = html_path.read_text(encoding="utf-8", errors="ignore")
        if "Product Photo" not in html_text:
            _write_wireviz_log(output_dir, cmd_display, result_code, stdout, stderr)
            _append_smoke_debug(output_dir, "HTML HEADER MISSING: Product Photo")
            print("Smoke test failed: 'Product Photo' header not found in HTML output")
            return 1

        with tsv_path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f, delimiter="\t")
            header = next(reader, [])
        if "Product Photo" not in header:
            _write_wireviz_log(output_dir, cmd_display, result_code, stdout, stderr)
            _append_smoke_debug(output_dir, "TSV HEADER MISSING: Product Photo")
            print("Smoke test failed: 'Product Photo' header not found in TSV output")
            return 1
        if "SPN" in header:
            _write_wireviz_log(output_dir, cmd_display, result_code, stdout, stderr)
            _append_smoke_debug(output_dir, "TSV HEADER STILL CONTAINS: SPN")
            print("Smoke test failed: Legacy 'SPN' header still present in TSV output")
            return 1

        print("Smoke test passed. Generated:")
        for p in [html_path, svg_path, png_path, tsv_path, pdf_path]:
            print(f"  - {p}")
        return 0
    except BaseException:
        debug_dir = output_dir or workdir
        _append_smoke_debug(Path(debug_dir), "UNHANDLED SMOKE BASE EXCEPTION:\n" + traceback.format_exc())
        return 1


def run_gui_smoke_test(timeout_s: float = 5.0) -> int:
    """Lightweight GUI initialization check with a hard timeout."""
    import threading

    result = {"ok": False, "error": None}

    def _target():
        try:
            sg = _load_gui_lib()
            win = sg.Window(
                "GUI Smoke Test",
                [[sg.Text("GUI init OK")], [sg.Button("Close")]],
                finalize=True,
            )
            try:
                win.read(timeout=100)
            finally:
                win.close()
            result["ok"] = True
        except Exception as e:
            result["error"] = str(e)

    t = threading.Thread(target=_target, daemon=True)
    t.start()
    t.join(timeout=timeout_s)
    if t.is_alive():
        print("GUI smoke test failed: timeout")
        return 1
    if result["ok"]:
        print("GUI smoke test passed.")
        return 0
    print(f"GUI smoke test failed: {result['error']}")
    return 1


def _write_wireviz_log(
    output_dir: Path,
    cmd_display: str,
    result_code: int,
    stdout: str,
    stderr: str,
) -> Path:
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
    return log_path


def _write_pdf_log(output_dir: Path, note: str | None) -> Path:
    log_path = output_dir / "pdf-error.log"
    message = note.strip() if isinstance(note, str) and note.strip() else "PDF generation failed."
    log_path.write_text(message + "\n", encoding="utf-8")
    return log_path


def _append_smoke_debug(output_dir: Path, text: str) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    debug_path = output_dir / "smoke-debug.log"
    with debug_path.open("a", encoding="utf-8") as f:
        f.write(text)
        if not text.endswith("\n"):
            f.write("\n")


def run_build_scripted(
    yaml_path: Path, outdir_override: Path | None, extra_args: list[str]
) -> int:
    """Run the same build pipeline as the GUI, without UI prompts."""
    yaml_path = yaml_path.expanduser().resolve()
    if not yaml_path.exists():
        print(f"Error: YAML file not found: {yaml_path}")
        return 1

    build.ensure_runtime_dependencies()
    yaml_path = build.resolve_yaml([str(yaml_path)])
    yaml_data = build.load_yaml_data(yaml_path)

    passthrough = extra_args
    _, resolved_output_name = build.resolve_output_paths(yaml_path, passthrough)

    if outdir_override:
        output_dir = outdir_override.expanduser().resolve()
        output_name = resolved_output_name
    else:
        output_dir, output_name = build.resolve_output_paths(yaml_path, passthrough)

    output_dir.mkdir(parents=True, exist_ok=True)
    copied_template = build.prepare_local_template_for_output(yaml_path, output_dir, yaml_data)
    result_code, cmd_display, stdout, stderr = build.run_wireviz(
        yaml_path, passthrough, output_dir
    )
    if result_code != 0:
        log_path = _write_wireviz_log(output_dir, cmd_display, result_code, stdout, stderr)
        print(f"Build failed. See log: {log_path}")
        return result_code

    base = output_dir / output_name
    html_path = base.with_suffix(".html")
    pdf_path = base.with_suffix(".pdf")
    tsv_path = Path(f"{base}.bom.tsv")
    svg_path = base.with_suffix(".svg")
    png_path = base.with_suffix(".png")

    build.merge_photo_rows_in_tsv(tsv_path)
    build.merge_photo_rows_in_html(html_path)
    build.rename_header_in_html(html_path)
    build.rename_header_in_tsv(tsv_path)
    build.rewrite_relative_image_paths(html_path, yaml_path.parent, output_dir)
    build.rewrite_relative_image_paths(tsv_path, yaml_path.parent, output_dir)
    pdf_generated, pdf_note = build.generate_pdf(
        html_path,
        pdf_path,
        build.resolve_sheetsize(yaml_data),
        paper_override=build.DEFAULT_AUTO_PDF_PAPER,
    )

    if copied_template and copied_template.exists():
        try:
            copied_template.unlink()
        except Exception:
            pass

    required = [html_path, svg_path, png_path, tsv_path, pdf_path]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        print("Build failed: Missing required outputs:")
        for p in missing:
            print(f"  - {p}")
        return 1
    if not pdf_generated:
        _write_pdf_log(output_dir, pdf_note)
        print(f"Build failed: PDF was not generated ({pdf_note})")
        return 1
    return 0


def parse_args() -> tuple[argparse.Namespace, list[str]]:
    p = argparse.ArgumentParser(
        add_help=True,
        description="WireViz Project Assistant GUI and CLI.",
    )
    p.add_argument(
        "--smoke-test",
        action="store_true",
        help="Run a headless end-to-end smoke test and exit.",
    )
    p.add_argument(
        "--workdir",
        default=".",
        help="Working directory for --smoke-test artifacts. Default: current directory.",
    )
    p.add_argument(
        "--version",
        action="store_true",
        help="Print application version and exit.",
    )
    p.add_argument(
        "--gui-smoke",
        action="store_true",
        help="Run a lightweight GUI init test and exit.",
    )
    p.add_argument(
        "--gui-scripted",
        action="store_true",
        help="Run a scripted GUI build (no UI) with prepopulated fields.",
    )
    p.add_argument("--yaml", help="YAML file to build with --gui-scripted.")
    p.add_argument("--outdir", help="Output directory for --gui-scripted.")
    p.add_argument(
        "--extra",
        default="",
        help="Extra WireViz args for --gui-scripted (quoted string).",
    )

    sub = p.add_subparsers(dest="command")

    ps = sub.add_parser("scaffold", help="Create a new project folder (CLI mode).")
    ps.add_argument("--name", help="Project name (required unless --in-place is used).")
    ps.add_argument(
        "--dest",
        default=".",
        help="Destination parent directory (or target directory with --in-place).",
    )
    ps.add_argument(
        "--in-place",
        action="store_true",
        help="Scaffold directly into --dest instead of creating a new subfolder.",
    )
    ps.add_argument(
        "--force",
        action="store_true",
        help="Allow writing into a non-empty existing directory.",
    )
    ps.add_argument(
        "--yaml-name",
        default="drawing.yaml",
        help="YAML file name to create. Default: drawing.yaml",
    )

    pb = sub.add_parser("build", help="Build outputs from YAML (CLI mode).")
    pb.add_argument(
        "yaml",
        nargs="?",
        help="Path to YAML file. Defaults to drawing.yaml in current directory.",
    )

    return p.parse_known_args()


def run_scaffold_cli(args: argparse.Namespace) -> int:
    try:
        scaffold.ensure_runtime_dependencies()
        target, project_name = scaffold.resolve_target(args)
        yaml_name = scaffold._normalize_yaml_name(args.yaml_name)
        scaffold.ensure_target(target, args.force)
        scaffold.scaffold_project(target, project_name, yaml_name)
        print(f"Created project: {target}")
        print("Next steps:")
        print(f"  cd {target}")
        print(f"  edit {yaml_name}")
        print(f"  python /path/to/toolkit/build.py {yaml_name}")
        return 0
    except ValueError as e:
        print(f"Error: {e}")
        return 1
    except SystemExit as e:
        return e.code if isinstance(e.code, int) else 1


def run_build_cli(yaml_arg: str | None, passthrough: list[str]) -> int:
    argv = []
    if yaml_arg:
        argv.append(yaml_arg)
    if passthrough and passthrough[0] == "--":
        passthrough = passthrough[1:]
    if passthrough:
        argv.extend(["--", *passthrough])

    old_argv = sys.argv[:]
    try:
        sys.argv = ["build.py", *argv]
        build.main()
        return 0
    except SystemExit as e:
        return e.code if isinstance(e.code, int) else 1
    finally:
        sys.argv = old_argv


def run_scaffold_gui():
    sg = _load_gui_lib()
    layout = [
        [sg.Text("Project Name"), sg.Input(key="name")],
        [sg.Text("Destination Folder"), sg.Input(key="dest"), sg.FolderBrowse()],
        [sg.Text("YAML Filename"), sg.Input("drawing.yaml", key="yaml_name")],
        [sg.Checkbox("In-place (use destination folder directly)", key="in_place")],
        [sg.Checkbox("Force overwrite existing directory", key="force")],
        [sg.Button("Create"), sg.Button("Cancel")]
    ]

    win = sg.Window("Create New Project", layout, modal=True)

    while True:
        ev, vals = win.read()
        if ev in (sg.WIN_CLOSED, "Cancel"):
            win.close()
            return
        if ev == "Create":
            try:
                class Args:
                    pass

                args = Args()
                args.name = vals["name"]
                args.dest = vals["dest"]
                args.yaml_name = vals["yaml_name"]
                args.in_place = vals["in_place"]
                args.force = vals["force"]

                scaffold.ensure_runtime_dependencies()
                target, project_name = scaffold.resolve_target(args)
                yaml_name = scaffold._normalize_yaml_name(args.yaml_name)
                scaffold.ensure_target(target, args.force)
                scaffold.scaffold_project(target, project_name, yaml_name)

                sg.popup_ok(f"Project created:\n{target}")
                win.close()
                return
            except Exception as e:
                sg.popup_error(f"Error:\n{e}")
            except SystemExit as e:
                msg = str(e) if str(e).strip() else "Operation failed."
                sg.popup_error(f"Error:\n{msg}")


def run_build_gui():
    sg = _load_gui_lib()
    layout = [
        [sg.Text("YAML File"), sg.Input(key="yaml"), sg.FileBrowse(file_types=(("YAML", "*.yaml"), ("YAML", "*.yml")))],
        [sg.Text("Extra WireViz Args"), sg.Input(key="extra")],
        [sg.Text("Output Directory (optional)"), sg.Input(key="outdir"), sg.FolderBrowse()],
        [
            sg.Text("PDF Paper"),
            sg.Combo(
                ["Letter", "Tabloid", "Use YAML"],
                default_value="Letter",
                readonly=True,
                key="pdf_paper",
                size=(16, 1),
            ),
            sg.Checkbox("Also generate both Letter and Tabloid", key="pdf_both"),
        ],
        [sg.Checkbox("Open output folder after build", key="open_after", default=True)],
        [sg.Button("Build"), sg.Button("Cancel")]
    ]

    win = sg.Window("Build Project", layout, modal=True)

    while True:
        ev, vals = win.read()
        if ev in (sg.WIN_CLOSED, "Cancel"):
            win.close()
            return

        if ev == "Build":
            try:
                yaml_path = Path(vals["yaml"])
                if not yaml_path.exists():
                    sg.popup_error("YAML file not found.")
                    continue

                extra_args = shlex.split(vals["extra"]) if vals["extra"] else []
                outdir_override = vals["outdir"].strip()

                build.ensure_runtime_dependencies()

                script_args = [str(yaml_path)]
                passthrough = extra_args

                yaml_path = build.resolve_yaml(script_args)
                yaml_data = build.load_yaml_data(yaml_path)
                _, resolved_output_name = build.resolve_output_paths(yaml_path, passthrough)

                if outdir_override:
                    output_dir = Path(outdir_override).resolve()
                    output_name = resolved_output_name
                else:
                    output_dir, output_name = build.resolve_output_paths(yaml_path, passthrough)

                output_dir.mkdir(parents=True, exist_ok=True)

                copied_template = build.prepare_local_template_for_output(
                    yaml_path, output_dir, yaml_data
                )
                result_code, cmd_display, stdout, stderr = build.run_wireviz(
                    yaml_path, passthrough, output_dir
                )
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
                    sg.popup_error(
                        "Build failed.\n\n"
                        f"See log:\n{log_path}"
                    )
                    continue

                base = output_dir / output_name
                html_path = base.with_suffix(".html")
                pdf_path = base.with_suffix(".pdf")
                tsv_path = Path(f"{base}.bom.tsv")

                build.merge_photo_rows_in_tsv(tsv_path)
                build.merge_photo_rows_in_html(html_path)
                build.rename_header_in_html(html_path)
                build.rename_header_in_tsv(tsv_path)
                build.rewrite_relative_image_paths(html_path, yaml_path.parent, output_dir)
                build.rewrite_relative_image_paths(tsv_path, yaml_path.parent, output_dir)
                paper_choice_raw = str(vals.get("pdf_paper", "Letter")).strip().lower()
                paper_choice = None if paper_choice_raw == "use yaml" else paper_choice_raw
                sheetsize = build.resolve_sheetsize(yaml_data)
                pdf_tasks: list[tuple[Path, str | None]] = []

                if vals.get("pdf_both"):
                    order = ["letter", "tabloid"]
                    if paper_choice == "tabloid":
                        order = ["tabloid", "letter"]
                    for idx, p in enumerate(order):
                        target = pdf_path if idx == 0 else base.with_name(f"{base.name}.{p}.pdf")
                        pdf_tasks.append((target, p.upper()))
                else:
                    pdf_tasks.append((pdf_path, paper_choice.upper() if isinstance(paper_choice, str) else None))

                pdf_failures: list[str] = []
                generated_paths: list[Path] = []
                for target_pdf, paper_override in pdf_tasks:
                    pdf_generated, pdf_note = build.generate_pdf(
                        html_path, target_pdf, sheetsize, paper_override=paper_override
                    )
                    if pdf_generated:
                        generated_paths.append(target_pdf)
                    else:
                        label = (
                            f"{target_pdf.name} ({paper_override.lower()})"
                            if isinstance(paper_override, str)
                            else target_pdf.name
                        )
                        pdf_failures.append(f"{label}: {pdf_note}")

                if copied_template and copied_template.exists():
                    try:
                        copied_template.unlink()
                    except Exception:
                        pass

                if pdf_failures:
                    _write_pdf_log(output_dir, " | ".join(pdf_failures))
                    sg.popup_error(
                        "PDF generation failed.\n\n"
                        f"Reason:\n{chr(10).join(pdf_failures)}\n\n"
                        f"See log:\n{output_dir / 'pdf-error.log'}"
                    )
                    continue

                extra_pdf_msg = ""
                if len(generated_paths) > 1:
                    extras = [p.name for p in generated_paths[1:]]
                    extra_pdf_msg = f"\nAdditional PDF(s):\n" + "\n".join(extras)
                sg.popup_ok(f"Build complete.\nOutput folder:\n{output_dir}{extra_pdf_msg}")

                if vals["open_after"] and hasattr(os, "startfile"):
                    os.startfile(output_dir)

                win.close()
                return

            except SystemExit as e:
                msg = str(e) if str(e).strip() else "Operation failed."
                sg.popup_error(f"Error:\n{msg}")
            except Exception as e:
                sg.popup_error(f"Error:\n{e}")


def main():
    args, passthrough = parse_args()

    build.configure_portable_runtime()

    if args.version:
        print(f"WireViz Project Assistant {__version__}")
        raise SystemExit(0)

    if args.smoke_test:
        workdir = Path(args.workdir).expanduser().resolve()
        code = run_smoke_test(workdir)
        raise SystemExit(code)

    if args.gui_smoke:
        code = run_gui_smoke_test()
        raise SystemExit(code)

    if args.gui_scripted:
        if not args.yaml:
            print("Error: --yaml is required with --gui-scripted.")
            raise SystemExit(2)
        outdir = Path(args.outdir) if args.outdir else None
        extra_args = shlex.split(args.extra) if args.extra else []
        code = run_build_scripted(Path(args.yaml), outdir, extra_args)
        raise SystemExit(code)

    if args.command == "scaffold":
        if passthrough:
            print(f"Error: unrecognized arguments: {' '.join(passthrough)}")
            raise SystemExit(2)
        raise SystemExit(run_scaffold_cli(args))

    if args.command == "build":
        raise SystemExit(run_build_cli(args.yaml, passthrough))

    if passthrough:
        print(f"Error: unrecognized arguments: {' '.join(passthrough)}")
        raise SystemExit(2)

    sg = _load_gui_lib()

    if build.is_frozen_app():
        issues = build.validate_runtime_requirements()
        if issues:
            issue_text = "\n".join(f"- {x}" for x in issues)
            sg.popup_error(
                "Runtime setup problem detected.\n\n"
                f"{issue_text}\n\n"
                "Use the full portable package and keep bundled files together."
            )
            return

    sg.theme("SystemDefault")

    layout = [
        [sg.Text(f"WireViz Project Assistant v{__version__}", font=("Segoe UI", 16))],
        [sg.Button("Create New Project", size=(25, 2))],
        [sg.Button("Build Existing Project", size=(25, 2))],
        [sg.HorizontalSeparator()],
        [sg.Button("Exit", size=(25, 1))]
    ]

    win = sg.Window(f"WireViz Project Assistant v{__version__}", layout)

    while True:
        ev, _ = win.read()
        if ev in (sg.WIN_CLOSED, "Exit"):
            break
        if ev == "Create New Project":
            run_scaffold_gui()
        if ev == "Build Existing Project":
            run_build_gui()

    win.close()

if __name__ == "__main__":
    main()

#!/usr/bin/env python
import PySimpleGUI as sg
import os
import subprocess
from pathlib import Path

import scaffold
import build
from version import __version__


def run_scaffold_gui():
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


def run_build_gui():
    layout = [
        [sg.Text("YAML File"), sg.Input(key="yaml"), sg.FileBrowse(file_types=(("YAML", "*.yaml"), ("YAML", "*.yml")))],
        [sg.Text("Extra WireViz Args"), sg.Input(key="extra")],
        [sg.Text("Output Directory (optional)"), sg.Input(key="outdir"), sg.FolderBrowse()],
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

                extra_args = vals["extra"].split() if vals["extra"] else []
                outdir_override = vals["outdir"].strip()

                build.ensure_runtime_dependencies()

                script_args = [str(yaml_path)]
                passthrough = extra_args

                yaml_path = build.resolve_yaml(script_args)
                yaml_data = build.load_yaml_data(yaml_path)

                if outdir_override:
                    output_dir = Path(outdir_override).resolve()
                    output_name = yaml_path.stem
                else:
                    output_dir, output_name = build.resolve_output_paths(yaml_path, passthrough)

                output_dir.mkdir(parents=True, exist_ok=True)

                build.prepare_local_template_for_output(yaml_path, output_dir, yaml_data)
                cmd = build.wireviz_command_with_output(yaml_path, passthrough, output_dir)

                subprocess.run(cmd)

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
                build.generate_pdf(html_path, pdf_path, build.resolve_sheetsize(yaml_data))

                sg.popup_ok(f"Build complete.\nOutput folder:\n{output_dir}")

                if vals["open_after"]:
                    os.startfile(output_dir)

                win.close()
                return

            except Exception as e:
                sg.popup_error(f"Error:\n{e}")


def main():
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

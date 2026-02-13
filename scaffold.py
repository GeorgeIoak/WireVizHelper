#!/usr/bin/env python
"""Create a new reusable WireViz project folder from sanitized starter files.

Examples:
  python scaffold.py --name "Cable Assembly A"
  python scaffold.py --name "Cable Assembly A" --dest /path/to/projects
  python scaffold.py --in-place --dest /path/to/existing/folder
"""

from __future__ import annotations

import argparse
import importlib.util
import re
import shutil
import subprocess
import sys
from pathlib import Path


def _resolve_root() -> Path:
    code_root = Path(__file__).resolve().parent
    if not getattr(sys, "frozen", False):
        return code_root

    candidates = []
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        candidates.append(Path(meipass))
    candidates.append(Path(sys.executable).resolve().parent)
    candidates.append(code_root)

    for root in candidates:
        if (root / "starter").exists():
            return root
    return code_root


ROOT = _resolve_root()
STARTER_DIR = ROOT / "starter"


def _slug(name: str) -> str:
    s = re.sub(r"[^A-Za-z0-9._-]+", "_", name.strip())
    s = re.sub(r"_+", "_", s).strip("._-")
    return s or "wireviz_project"


def _copy(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def _normalize_yaml_name(name: str) -> str:
    n = (name or "").strip()
    if not n:
        return "drawing.yaml"
    if "/" in n or "\\" in n:
        raise ValueError("--yaml-name must be a file name, not a path.")
    if not n.endswith((".yaml", ".yml")):
        n = f"{n}.yaml"
    return n


def _write_project_readme(dst: Path, project_name: str, yaml_name: str) -> None:
    template = (STARTER_DIR / "README.template.md").read_text(encoding="utf-8")
    rendered = template.replace("__PROJECT_NAME__", project_name)
    rendered = rendered.replace("__YAML_FILE__", yaml_name)
    rendered = rendered.replace("__YAML_STEM__", Path(yaml_name).stem)
    build_cmd = f"python build.py {yaml_name}"
    rendered = rendered.replace("__BUILD_CMD__", build_cmd)
    dst.write_text(rendered, encoding="utf-8")


def ensure_runtime_dependencies() -> None:
    """Check key modules and install from requirements if needed."""
    if getattr(sys, "frozen", False):
        return

    needed = ["wireviz", "yaml"]
    missing = [m for m in needed if importlib.util.find_spec(m) is None]
    if not missing:
        return

    req = ROOT / "requirements.txt"
    if not req.exists():
        print(
            "Warning: Missing dependencies detected "
            f"({', '.join(missing)}), but requirements.txt was not found."
        )
        return

    status = ", ".join(missing)
    print(
        f"Missing dependencies detected ({status}). Installing from requirements.txt ...",
        flush=True,
    )
    result = subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(req)])
    if result.returncode != 0:
        print(
            "Error: Dependency install failed.\n"
            f"Try manually: {sys.executable} -m pip install -r {req}"
        )
        sys.exit(result.returncode)


def resolve_target(args: argparse.Namespace) -> tuple[Path, str]:
    dest = Path(args.dest).expanduser().resolve()
    if args.in_place:
        project_name = args.name.strip() if args.name else dest.name
        return dest, project_name

    if not args.name:
        raise ValueError("--name is required unless --in-place is used.")

    folder = _slug(args.name)
    return dest / folder, args.name.strip()


def ensure_target(target: Path, force: bool) -> None:
    if target.exists():
        if not target.is_dir():
            raise ValueError(f"Target path exists and is not a directory: {target}")
        if any(target.iterdir()) and not force:
            raise ValueError(
                f"Target directory is not empty: {target}. "
                "Use --force to allow writing into an existing non-empty directory."
            )
    else:
        target.mkdir(parents=True, exist_ok=True)


def scaffold_project(target: Path, project_name: str, yaml_name: str) -> None:
    # Project files only (tooling stays in toolkit repo).
    _copy(STARTER_DIR / "drawing.yaml", target / yaml_name)
    _write_project_readme(target / "README.md", project_name, yaml_name)

    # Minimal images used by starter drawing
    _copy(STARTER_DIR / "images" / "plug_example.png", target / "images" / "plug_example.png")
    _copy(
        STARTER_DIR / "images" / "product_photo_example.jpg",
        target / "images" / "product_photo_example.jpg",
    )

    # Optional local reference folder for datasheets/specs.
    (target / "reference").mkdir(parents=True, exist_ok=True)
    (target / "reference" / "README.md").write_text(
        "Place component datasheets/specs here (optional).\n",
        encoding="utf-8",
    )

    # Project-level gitignore
    _copy(ROOT / ".gitignore", target / ".gitignore")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Create a new WireViz project folder.")
    p.add_argument("--name", help="Project name (used for folder name unless --in-place).")
    p.add_argument(
        "--dest",
        default=".",
        help="Destination parent directory (or target directory with --in-place). Default: current directory.",
    )
    p.add_argument(
        "--in-place",
        action="store_true",
        help="Scaffold directly into --dest instead of creating a new subfolder.",
    )
    p.add_argument(
        "--force",
        action="store_true",
        help="Allow writing into a non-empty existing directory.",
    )
    p.add_argument(
        "--yaml-name",
        default="drawing.yaml",
        help="YAML file name to create in scaffolded project. Default: drawing.yaml",
    )
    return p.parse_args()


def main() -> None:
    try:
        ensure_runtime_dependencies()
        args = parse_args()
        target, project_name = resolve_target(args)
        yaml_name = _normalize_yaml_name(args.yaml_name)
        ensure_target(target, args.force)
        scaffold_project(target, project_name, yaml_name)

        print(f"Created project: {target}")
        print("Next steps:")
        print(f"  cd {target}")
        print(f"  edit {yaml_name}")
        print(f"  python build.py {yaml_name}")
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

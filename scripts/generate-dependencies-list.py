"""
Generate a full requirements file for GuardDog from pyproject.toml.
"""

import sys
from pathlib import Path
import tomllib


def main(pyproject_path: str, out_path: str) -> int:
    pyproject_file = Path(pyproject_path)
    if not pyproject_file.is_file():
        raise RuntimeError(f"pyproject.toml not found at {pyproject_file}")

    data = tomllib.loads(pyproject_file.read_text(encoding="utf-8"))

    project = data.get("project", {})
    base_deps = project.get("dependencies", [])
    extras = project.get("optional-dependencies", {})

    # Which extras to include in the "full" file
    extra_order = ["dev", "docs", "test"]

    combined: list[str] = []

    def add_deps(seq: list[str]) -> None:
        for dep in seq:
            if dep not in combined:
                combined.append(dep)

    add_deps(base_deps)

    for extra_name in extra_order:
        add_deps(extras.get(extra_name, []))

    out_file = Path(out_path)
    out_file.write_text("\n".join(combined) + "\n", encoding="utf-8")
    print(f"Wrote {len(combined)} dependencies to {out_file}")


if __name__ == "__main__":
    pyproject_arg = sys.argv[1] if len(sys.argv) > 1 else "pyproject.toml"
    out_arg = sys.argv[2] if len(sys.argv) > 2 else "fpdf2-full-requirements.txt"
    main(pyproject_arg, out_arg)

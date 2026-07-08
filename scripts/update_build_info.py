from __future__ import annotations

import subprocess
from pathlib import Path


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    commit = subprocess.check_output(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=repo_root,
        text=True,
    ).strip()
    (repo_root / "pyodide" / "build_info.js").write_text(
        f'window.STUD_BUILD_ID = "{commit}";\n',
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()

from __future__ import annotations

import os
import subprocess
from pathlib import Path

DEFAULT_BUILD_ID = "dev"


def build_id() -> str:
    env_value = os.environ.get("STUD_BUILD_ID") or os.environ.get("RENDER_GIT_COMMIT")
    if env_value:
        return env_value[:7]
    try:
        repo_root = Path(__file__).resolve().parents[1]
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
        )
    except Exception:
        return DEFAULT_BUILD_ID
    return result.stdout.strip() or DEFAULT_BUILD_ID

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent
NODE_RUNTIME_ERROR = (
    "Node.js runtime is required for this calculator but was not found on PATH. "
    "Install Node.js or set NODE_BINARY."
)


def resolve_node_binary() -> str:
    configured = str(os.environ.get("NODE_BINARY") or "").strip()
    if configured:
        return configured

    detected = shutil.which("node")
    if detected:
        return detected

    raise ValueError(NODE_RUNTIME_ERROR)


def run_node_bridge(script_path: Path, payload: dict[str, Any], error_label: str) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            [resolve_node_binary(), str(script_path.resolve())],
            input=json.dumps(payload, ensure_ascii=False),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            cwd=str(REPO_ROOT),
        )
    except FileNotFoundError as exc:
        raise ValueError(NODE_RUNTIME_ERROR) from exc

    if completed.returncode != 0:
        raise ValueError((completed.stderr or completed.stdout or f"{error_label} failed").strip())

    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{error_label} returned invalid JSON: {exc}") from exc

#!/usr/bin/env python3
"""Create this skill's ``.venv`` and install ``requirements.txt``.

Prints the venv interpreter path on stdout. Uses the stdlib only so it can
bootstrap before third-party packages exist.

Usage (from the skill root or via absolute path)::

    python3 scripts/ensure_venv.py
"""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
VENV_DIR = SKILL_ROOT / ".venv"
REQUIREMENTS = SKILL_ROOT / "requirements.txt"
STAMP = VENV_DIR / ".requirements.sha256"


def _venv_python(venv: Path) -> Path:
    unix = venv / "bin" / "python"
    if unix.is_file():
        return unix
    windows = venv / "Scripts" / "python.exe"
    if windows.is_file():
        return windows
    return unix


def _requirements_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _run(cmd: list[str]) -> None:
    result = subprocess.run(cmd, check=False)
    if result.returncode != 0:
        sys.exit(result.returncode)


def ensure() -> Path:
    if not REQUIREMENTS.is_file():
        sys.stderr.write(f"missing {REQUIREMENTS}\n")
        sys.exit(1)

    python = _venv_python(VENV_DIR)
    if not python.is_file():
        _run([sys.executable, "-m", "venv", str(VENV_DIR)])
        python = _venv_python(VENV_DIR)
        if not python.is_file():
            sys.stderr.write(f"venv python missing after create: {python}\n")
            sys.exit(1)

    digest = _requirements_digest(REQUIREMENTS)
    if STAMP.is_file() and STAMP.read_text(encoding="utf-8").strip() == digest:
        return python

    _run([str(python), "-m", "pip", "install", "-q", "--upgrade", "pip"])
    _run([str(python), "-m", "pip", "install", "-q", "-r", str(REQUIREMENTS)])
    STAMP.write_text(digest + "\n", encoding="utf-8")
    return python


def main() -> None:
    os.chdir(SKILL_ROOT)
    print(ensure())


if __name__ == "__main__":
    main()

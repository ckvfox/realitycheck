#!/usr/bin/env python3
"""Run the complete offline RealityCheck regression suite consistently."""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run(command: list[str], label: str) -> None:
    print(f"\n== {label} ==", flush=True)
    subprocess.run(command, cwd=ROOT, check=True)


def require_executable(name: str) -> str:
    executable = shutil.which(name)
    if not executable:
        raise RuntimeError(f"Required test executable is missing: {name}")
    return executable


def php_sources() -> list[Path]:
    excluded_roots = {"build", "deployment", ".git", ".venv"}
    restricted = Path("analysis-private/real-wages-auth.php")
    result: list[Path] = []
    for path in ROOT.rglob("*.php"):
        relative = path.relative_to(ROOT)
        if relative.parts and relative.parts[0] in excluded_roots:
            continue
        if relative.as_posix() == restricted.as_posix():
            continue
        result.append(relative)
    return sorted(result)


def main() -> int:
    python = sys.executable
    node = require_executable("node")
    php = require_executable("php")

    run([python, "-m", "compileall", "-q", "scripts", "tests"], "Python syntax")
    run([python, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py", "-v"], "Python tests")
    run([python, "scripts/validation.py", "--no-log"], "Committed data snapshot")

    for test_file in sorted((ROOT / "tests").glob("*.test.js")):
        run([node, "--test", str(test_file.relative_to(ROOT))], f"JavaScript: {test_file.name}")

    for source in php_sources():
        run([php, "-l", str(source)], f"PHP lint: {source.as_posix()}")
    for test_file in sorted((ROOT / "tests").glob("*_test.php")):
        run(
            [php, "-d", "zend.assertions=1", "-d", "assert.exception=1", str(test_file.relative_to(ROOT))],
            f"PHP: {test_file.name}",
        )

    print("\nAll offline checks passed.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

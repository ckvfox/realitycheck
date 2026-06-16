#!/usr/bin/env python3
"""Prepare Full and Delta deployment bundles for RealityCheck.

This script implements a controlled transition to the framework target paths:
- build/deployment/full/
- build/deployment/delta/

It can also mirror outputs to legacy operational handover folders:
- deployment/full_deployment/
- deployment/delta_deployment/
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import stat
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

TARGET_FULL = ROOT / "build" / "deployment" / "full"
TARGET_DELTA = ROOT / "build" / "deployment" / "delta"
LEGACY_FULL = ROOT / "deployment" / "full_deployment"
LEGACY_DELTA = ROOT / "deployment" / "delta_deployment"
STATE_FILE = ROOT / "build" / "deployment" / ".deployment_state.json"

# Keep this in sync with standards/deployment.md negative list.
EXCLUDE_PATTERNS = [
    ".git/*",
    ".git/**",
    ".github/*",
    ".github/**",
    ".codex/*",
    ".codex/**",
    ".venv/*",
    ".venv/**",
    "build/*",
    "build/**",
    "deployment/*",
    "deployment/**",
    "docs/*",
    "docs/**",
    "tests/*",
    "tests/**",
    "standards/*",
    "standards/**",
    "profiles/*",
    "profiles/**",
    "PROJECT_MASTER.md",
    "AGENTS.md",
    "README*",
    "CHANGELOG*",
    "TODO*",
    "SECURITY*",
    "*.md",
    "*.py",
    ".env*",
]

ALLOWED_EXTENSIONS = {
    ".html",
    ".css",
    ".js",
    ".json",
    ".xml",
    ".svg",
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".ico",
    ".php",
}

ALLOWED_FILENAMES = {
    ".htaccess",
    "robots.txt",
    "sitemap.xml",
    "LICENSE",
}

PRODUCTIVE_SCRIPT_FILES = {
    "scripts/core.js",
    "scripts/page_about.js",
    "scripts/page_analysis.js",
    "scripts/page_data_glossary.js",
    "scripts/script.js",
    "scripts/script_overall_ranking_countries.js",
    "scripts/script_world.js",
    "scripts/utils_ui.js",
}


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def should_exclude(rel_posix: str) -> bool:
    parts = rel_posix.split("/")
    for i, part in enumerate(parts):
        if not part.startswith("."):
            continue
        # Allow apache root config and security contact endpoint.
        if i == len(parts) - 1 and part == ".htaccess":
            continue
        if part == ".well-known":
            continue
        return True

    for pattern in EXCLUDE_PATTERNS:
        if fnmatch.fnmatch(rel_posix, pattern):
            return True
    return False


def is_allowed_productive(rel_posix: str) -> bool:
    if rel_posix.startswith("scripts/"):
        return rel_posix in PRODUCTIVE_SCRIPT_FILES
    if rel_posix in ALLOWED_FILENAMES:
        return True
    if rel_posix.startswith(".well-known/"):
        return True
    suffix = Path(rel_posix).suffix.lower()
    return suffix in ALLOWED_EXTENSIONS


def iter_productive_files() -> list[Path]:
    files: list[Path] = []
    for p in ROOT.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(ROOT).as_posix()
        if should_exclude(rel):
            continue
        if not is_allowed_productive(rel):
            continue
        files.append(p)
    return sorted(files)


def clear_dir(path: Path) -> None:
    def _on_rm_error(func, target, exc_info):
        try:
            os.chmod(target, stat.S_IWRITE)
            func(target)
        except OSError:
            pass

    path.mkdir(parents=True, exist_ok=True)
    for child in path.iterdir():
        if child.is_dir():
            shutil.rmtree(child, onerror=_on_rm_error)
        else:
            try:
                child.unlink()
            except PermissionError:
                os.chmod(child, stat.S_IWRITE)
                child.unlink()


def copy_files(files: list[Path], target_root: Path) -> None:
    for src in files:
        rel = src.relative_to(ROOT)
        dst = target_root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def build_manifest(files: list[Path]) -> dict[str, str]:
    return {f.relative_to(ROOT).as_posix(): sha256_of(f) for f in files}


def load_previous_manifest() -> dict[str, str]:
    if not STATE_FILE.exists():
        return {}
    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return data.get("manifest", {}) if isinstance(data, dict) else {}


def save_manifest(manifest: dict[str, str]) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    payload = {"manifest": manifest}
    STATE_FILE.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")


def detect_delta(files: list[Path], previous: dict[str, str]) -> list[Path]:
    changed: list[Path] = []
    for f in files:
        rel = f.relative_to(ROOT).as_posix()
        digest = sha256_of(f)
        if previous.get(rel) != digest:
            changed.append(f)
    return changed


def mirror_to_legacy(target: Path, legacy: Path) -> None:
    clear_dir(legacy)
    for p in target.rglob("*"):
        rel = p.relative_to(target)
        dst = legacy / rel
        if p.is_dir():
            dst.mkdir(parents=True, exist_ok=True)
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, dst)


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare deployment bundles (full/delta).")
    parser.add_argument("--mode", choices=["full", "delta", "both"], default="both")
    parser.add_argument(
        "--mirror-legacy",
        action="store_true",
        help="Mirror generated bundles to deployment/full_deployment and deployment/delta_deployment.",
    )
    args = parser.parse_args()

    files = iter_productive_files()
    previous = load_previous_manifest()
    manifest = build_manifest(files)

    if args.mode in {"full", "both"}:
        clear_dir(TARGET_FULL)
        copy_files(files, TARGET_FULL)

    if args.mode in {"delta", "both"}:
        delta_files = detect_delta(files, previous)
        clear_dir(TARGET_DELTA)
        copy_files(delta_files, TARGET_DELTA)

    save_manifest(manifest)

    if args.mirror_legacy:
        if args.mode in {"full", "both"}:
            mirror_to_legacy(TARGET_FULL, LEGACY_FULL)
        if args.mode in {"delta", "both"}:
            mirror_to_legacy(TARGET_DELTA, LEGACY_DELTA)

    print(f"Prepared {len(files)} productive files.")
    if args.mode in {"delta", "both"}:
        print(f"Delta files: {len(detect_delta(files, previous))}")
    if args.mirror_legacy:
        print("Legacy mirror: enabled")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

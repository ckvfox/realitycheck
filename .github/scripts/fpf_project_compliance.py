#!/usr/bin/env python3
"""Validate the repository-level Fox Project Framework baseline."""

from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path

CORE_FILES = (
    "PROJECT_MASTER.md",
    "README.md",
    "AGENTS.md",
    "CHANGELOG.md",
    "TODO.md",
    "SECURITY.md",
    "LICENSE",
    ".gitignore",
)
SECURITY_HEADINGS = (
    "Supported Versions",
    "Vulnerability Reporting",
    "Secret Handling",
    "Production Hardening",
    "Backup Strategy",
    "Installer Policy",
    "Disclosure Policy",
    "Response Targets",
)
ACTION_REF = re.compile(r"(?m)^\s*(?:-\s*)?uses:\s*([^\s#]+)")


def tracked_files(root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "-C", str(root), "ls-files"],
        check=True,
        capture_output=True,
        text=True,
    )
    return [line.replace("\\", "/") for line in result.stdout.splitlines() if line]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument("--profile", choices=("apache-shared-hosting", "github-pages", "generic-static"), required=True)
    parser.add_argument("--production", action="store_true")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    errors: list[str] = []

    for relative in CORE_FILES:
        if not (root / relative).is_file():
            errors.append(f"missing required file: {relative}")
    if not (root / "standards").is_dir():
        errors.append("missing required directory: standards/")

    security = (root / "SECURITY.md").read_text(encoding="utf-8", errors="ignore") if (root / "SECURITY.md").is_file() else ""
    for heading in SECURITY_HEADINGS:
        if heading.lower() not in security.lower():
            errors.append(f"SECURITY.md missing section: {heading}")

    if args.production:
        for relative in ("robots.txt", "sitemap.xml"):
            if args.profile == "github-pages":
                candidates = (root / "docs" / relative, root / relative)
            else:
                candidates = (root / relative, root / "public" / relative)
            if not any(path.is_file() for path in candidates):
                errors.append(f"production SEO file missing: {relative}")
        if args.profile == "apache-shared-hosting" and not (root / ".htaccess").is_file():
            errors.append("Apache production file missing: .htaccess")

    workflow_dir = root / ".github" / "workflows"
    workflows = sorted([*workflow_dir.glob("*.yml"), *workflow_dir.glob("*.yaml")]) if workflow_dir.is_dir() else []
    if not workflows:
        errors.append("no GitHub Actions workflow found")
    for workflow in workflows:
        body = workflow.read_text(encoding="utf-8", errors="ignore")
        if not re.search(r"(?m)^\s*permissions\s*:", body):
            errors.append(f"workflow lacks explicit permissions: {workflow.relative_to(root)}")
        for match in ACTION_REF.finditer(body):
            reference = match.group(1)
            if reference.startswith("./"):
                continue
            revision = reference.rsplit("@", 1)[-1] if "@" in reference else ""
            if not re.fullmatch(r"[0-9a-fA-F]{40}", revision):
                errors.append(
                    f"workflow action is not pinned to a full commit SHA: "
                    f"{workflow.relative_to(root)} ({reference})"
                )

    try:
        tracked = tracked_files(root)
    except (OSError, subprocess.SubprocessError) as exc:
        errors.append(f"unable to inspect tracked files: {exc}")
        tracked = []
    for relative in tracked:
        lowered = relative.lower()
        archive_parts = {"deployment", "deployments", "artifacts", "releases", "release"}
        if lowered.endswith(".zip") and archive_parts.intersection(Path(lowered).parts):
            errors.append(f"deployment archive must not be tracked: {relative}")
        if lowered == ".env" or lowered.endswith((".pem", ".key", ".pfx", ".p12")):
            errors.append(f"secret-bearing file must not be tracked: {relative}")

    if errors:
        print("FPF project baseline: FAILED")
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(f"FPF project baseline: PASS ({args.profile}, production={args.production})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

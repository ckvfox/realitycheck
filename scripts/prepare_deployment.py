#!/usr/bin/env python3
"""Prepare Full and Delta deployment bundles for RealityCheck.

This script writes exclusively to the framework target paths:
- build/deployment/full/
- build/deployment/delta/
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import re
import stat
import shutil
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

TARGET_FULL = ROOT / "build" / "deployment" / "full"
TARGET_DELTA = ROOT / "build" / "deployment" / "delta"
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
    "data/test/*",
    "data/test/**",
    "data/fetch_state.json",
    "data/manual_source_status.json",
    "data/meta/manual_csv_sources.json",
    "data/workflow_fetch_console.log",
    "data/workflow_fetch_summary.md",
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
    "tracking.json",
    "*.md",
    "*.py",
    ".env*",
    "analysis-private/*example.php",
    "analysis-private/real-wages-auth.php",
]

PRODUCTIVE_SCRIPT_FILES = {
    "scripts/environment_colors.js",
    "scripts/core.js",
    "scripts/page_about.js",
    "scripts/page_analysis.js",
    "scripts/page_data_glossary.js",
    "scripts/page_germany_dossier.js",
    "scripts/page_germany_dossier_i18n.js",
    "scripts/page_real_wages_analysis.js",
    "scripts/page_germany_2036_scenarios.js",
    "scripts/page_germany_war_stress_test.js",
    "scripts/page_income_pyramid.js",
    "scripts/script.js",
    "scripts/script_overall_ranking_countries.js",
    "scripts/script_world.js",
    "scripts/utils_ui.js",
}

PRODUCTIVE_MARKDOWN_FILES = {
    "data/analysis.md",
}

# New pages/assets must be registered here; a productive-looking suffix is insufficient.
PRODUCTIVE_ROOT_FILES = {
    ".htaccess", "LICENSE", "about.html", "analysis.html", "countries.html",
    "data_glossary.html", "favicon.ico", "favicon.png", "footer.html",
    "germany-dossier.php", "google-site-verification.html", "google60f6cdba136e03e9.html",
    "header.html", "impressum.html", "index.html", "js_challenge.html", "manifest.json",
    "overall_ranking_countries.html", "privacy.html", "robots.txt", "sitemap.xml",
    "style.css", "tracking.php", "world.html", ".well-known/security.txt",
}
PRODUCTIVE_SERVER_FILES = {
    "analysis-private/.htaccess", "analysis-private/real-wages-auth-lib.php",
    "analysis-private/real-wages-data.php", "analysis-private/real-wages-data-de.php",
    "analysis-private/germany-2036-scenarios.php", "analysis-private/germany-2036-scenarios-de.php",
    "analysis-private/germany-war-stress-test.php", "analysis-private/germany-war-stress-test-b2.php",
    "analysis-private/germany-war-stress-test-de.php", "analysis-private/income-pyramid-data.php",
    "analysis-private/income-pyramid-data-de.php", "analysis-private/germany-reform-agenda.php",
    "analysis-private/germany-reform-agenda-depth.php",
}
PRODUCTIVE_IMAGE_FILES = {"images/logo.png", "images/translate.png", "images/teamwork_wunder.jpg"}
PRODUCTIVE_DATA_FILES = {
    "data/analysis.md", "data/analysis_outliers.json", "data/kpi_analysis.json", "data/fetch_status.json",
    "data/fun_ranking.json", "data/fun_ranking_bottom.json", "data/safe_haven_ranking.json",
    "data/safe_haven_ranking_bottom.json", "data/immigration_ranking.json", "data/immigration_ranking_bottom.json",
    "data/all_kpis_index.json", "data/meta/available_kpis.json", "data/meta/countries.json",
    "data/meta/country_mappings.json", "data/meta/groups.json", "data/meta/region_sets.json",
    "data/meta/world_countries_geo.json",
}
REGISTRY_FILES = ("data/meta/available_kpis.json", "data/all_kpis_index.json",
                  "data/meta/countries.json", "data/meta/region_sets.json")


def safe_source(relative: str) -> Path:
    """Reject symlinks in every path component before opening even a registry."""
    if not relative or Path(relative).is_absolute() or ".." in Path(relative).parts or any(c in relative for c in "\\\r\n"):
        raise ValueError("Unsafe productive path")
    path = ROOT
    for component in Path(relative).parts:
        path /= component
        if path.is_symlink():
            raise ValueError(f"Symlink in productive path: {relative}")
    if not path.resolve().is_relative_to(ROOT.resolve()):
        raise ValueError("Productive path escapes repository")
    return path


@lru_cache(maxsize=8)
def _registered_paths(root: Path, signature: tuple) -> frozenset[str]:
    # root/signature make cached results specific to this checkout and metadata release.
    def read(name):
        return json.loads(safe_source(name).read_text(encoding="utf-8"))

    metadata = read(REGISTRY_FILES[0])
    if not isinstance(metadata, list) or not metadata:
        raise ValueError("KPI registry must be a nonempty list")
    paths = set()
    for entry in metadata:
        name = entry.get("filename", "") if isinstance(entry, dict) else ""
        if not re.fullmatch(r"[a-z0-9_]+", name):
            raise ValueError("Unsafe KPI filename in deployment registry")
        paths.add(f"data/{name}.json")
    index = read(REGISTRY_FILES[1])
    parts = index.get("parts", []) if isinstance(index, dict) else []
    if not isinstance(parts, list) or not parts or not all(isinstance(p, str) for p in parts) or len(set(parts)) != len(parts):
        raise ValueError("Consolidated index must declare unique data parts")
    for name in parts:
        if not isinstance(name, str) or not re.fullmatch(r"all_kpis_part[1-9][0-9]*\.json\.gz", name):
            raise ValueError("Unsafe consolidated data part")
        paths.add(f"data/{name}")
    countries = read(REGISTRY_FILES[2])
    if not isinstance(countries, dict) or not all(isinstance(c, dict) for c in countries.values()):
        raise ValueError("Country metadata must contain country records")
    paths.update({"images/flag/question.svg", "images/flag/de.svg", "images/flag/gb.svg"})
    for country in countries.values():
        flag = country.get("flag", "")
        if flag:
            if not re.fullmatch(r"images/flag/[a-z]{2}(?:-[a-z0-9]+)?\.svg", flag):
                raise ValueError("Unsafe country flag path")
            paths.add(flag)
        iso = country.get("iso_a2", "")
        if isinstance(iso, str) and re.fullmatch(r"[A-Za-z]{2}", iso):
            paths.add(f"images/flag/{iso.lower()}.svg")
    regions = read(REGISTRY_FILES[3])
    if not isinstance(regions, dict) or not all(isinstance(r, dict) for r in regions.values()):
        raise ValueError("Region metadata must contain region records")
    for region in regions.values():
        name = region.get("geo_file", "")
        if not re.fullmatch(r"regions_[a-z0-9_]+_geo\.json", name):
            raise ValueError("Unsafe regional geometry path")
        paths.add(f"data/meta/{name}")
    return frozenset(paths)


def registered_paths() -> frozenset[str]:
    signature = tuple((safe_source(name).stat().st_mtime_ns, safe_source(name).stat().st_size)
                      for name in REGISTRY_FILES)
    return _registered_paths(ROOT, signature)


def productive_paths() -> set[str]:
    return (PRODUCTIVE_ROOT_FILES | PRODUCTIVE_SERVER_FILES | PRODUCTIVE_IMAGE_FILES |
            PRODUCTIVE_DATA_FILES | PRODUCTIVE_SCRIPT_FILES | set(registered_paths()))


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def should_exclude(rel_posix: str) -> bool:
    basename = rel_posix.rsplit("/", 1)[-1].lower()
    if basename in {"auth.json", "id_rsa", "id_ed25519", "known_hosts", ".npmrc", ".pypirc", ".secrets"} or any(
        fnmatch.fnmatch(basename, pattern)
        for pattern in (".env*", "credentials*", "*.pem", "*.key", "*.pfx", "*.p12")
    ):
        return True
    if rel_posix in PRODUCTIVE_MARKDOWN_FILES:
        return False
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
    if should_exclude(rel_posix):
        return False
    if rel_posix in (PRODUCTIVE_ROOT_FILES | PRODUCTIVE_SERVER_FILES | PRODUCTIVE_IMAGE_FILES |
                     PRODUCTIVE_DATA_FILES | PRODUCTIVE_SCRIPT_FILES):
        return True
    if rel_posix.startswith(("data/", "images/flag/")):
        return rel_posix in registered_paths()
    return False


def iter_productive_files() -> list[Path]:
    files = []
    for relative in sorted(productive_paths()):
        if should_exclude(relative):
            continue
        path = safe_source(relative)
        if path.is_file():
            files.append(path)
        elif re.fullmatch(r"data/all_kpis_part[1-9][0-9]*\.json\.gz", relative):
            raise ValueError("Consolidated index references a missing data part")
    return files


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


def load_previous_manifest(baseline_file: Path | None = None) -> dict[str, str]:
    state_file = baseline_file if baseline_file is not None else STATE_FILE
    if not state_file.exists():
        if baseline_file is not None:
            raise FileNotFoundError(f"Explicit deployment baseline does not exist: {state_file}")
        return {}
    try:
        data = json.loads(state_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        if baseline_file is not None:
            raise ValueError("Explicit deployment baseline is not valid JSON")
        return {}
    if baseline_file is not None and (not isinstance(data, dict) or not isinstance(data.get("manifest"), dict) or not data["manifest"]):
        raise ValueError("Explicit deployment baseline requires a nonempty manifest")
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare deployment bundles (full/delta).")
    parser.add_argument("--mode", choices=["full", "delta", "both"], default="both")
    parser.add_argument("--baseline-manifest", type=Path, help="Explicit saved package manifest for cumulative pending delta changes")
    args = parser.parse_args()

    files = iter_productive_files()
    previous = load_previous_manifest(args.baseline_manifest)
    manifest = build_manifest(files)

    # Never leave a stale handover folder from a different packaging mode.
    clear_dir(TARGET_FULL)
    clear_dir(TARGET_DELTA)
    if args.mode in {"full", "both"}:
        copy_files(files, TARGET_FULL)

    if args.mode in {"delta", "both"}:
        delta_files = detect_delta(files, previous)
        copy_files(delta_files, TARGET_DELTA)

    save_manifest(manifest)

    print(f"Prepared {len(files)} productive files.")
    if args.mode in {"delta", "both"}:
        print(f"Delta files: {len(detect_delta(files, previous))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

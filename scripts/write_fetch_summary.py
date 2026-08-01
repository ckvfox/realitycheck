"""Create a concise, non-secret Markdown summary for fetch workflows."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"


def load_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def build_summary(
    *,
    job_status: str,
    run_url: str,
    fetch_status: dict[str, Any],
    fetch_state: dict[str, Any],
    manual_status: dict[str, Any],
) -> str:
    summary = fetch_status.get("summary") if isinstance(fetch_status.get("summary"), dict) else {}
    kpi_status = fetch_status.get("kpis") if isinstance(fetch_status.get("kpis"), dict) else {}
    updated = fetch_state.get("updated_kpis") if isinstance(fetch_state.get("updated_kpis"), list) else []
    manual_summary = manual_status.get("summary") if isinstance(manual_status.get("summary"), dict) else {}

    lines = [
        "# RealityCheck data pipeline",
        "",
        f"- **Workflow status:** {job_status or 'unknown'}",
        f"- **Fetch run:** {summary.get('lastRun') or fetch_state.get('last_run') or 'not available'}",
        f"- **Updated KPIs:** {summary.get('updated', len(updated))}",
        f"- **Skipped KPIs:** {summary.get('skipped', 'not available')}",
        f"- **Fetcher errors:** {summary.get('errors', 'not available')}",
        f"- **Manual CSV update hints:** {manual_summary.get('possible_updates', 'not checked')}",
    ]
    if run_url:
        lines.append(f"- **Complete Actions log:** {run_url}")

    lines.extend(["", "## Updated datasets", ""])
    if updated:
        lines.extend(["| KPI | Latest data year |", "|---|---:|"])
        for kpi in sorted(str(item) for item in updated):
            info = kpi_status.get(kpi) if isinstance(kpi_status.get(kpi), dict) else {}
            lines.append(f"| `{kpi}` | {info.get('data_year', 'n/a')} |")
    else:
        lines.append("No KPI replacement was recorded for this run.")

    lines.extend(
        [
            "",
            "The downloadable diagnostic artifact contains the complete fetch console output, "
            "fetch log, status, state, validation log and manual-source audit when available.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--job-status", default="unknown")
    parser.add_argument("--run-url", default="")
    parser.add_argument("--output", type=Path, default=DATA_DIR / "workflow_fetch_summary.md")
    parser.add_argument("--fetch-status", type=Path, default=DATA_DIR / "fetch_status.json")
    parser.add_argument("--fetch-state", type=Path, default=DATA_DIR / "fetch_state.json")
    parser.add_argument("--manual-status", type=Path, default=DATA_DIR / "manual_source_status.json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    content = build_summary(
        job_status=args.job_status,
        run_url=args.run_url,
        fetch_status=load_object(args.fetch_status),
        fetch_state=load_object(args.fetch_state),
        manual_status=load_object(args.manual_status),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(content, encoding="utf-8")
    print(content)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

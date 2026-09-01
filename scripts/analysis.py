#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📊 RealityCheck – Global KPI Analysis (Final GPT-Compat, Nov 2025)
─────────────────────────────────────────────
Erzeugt (Schema unverändert):
 • data/analysis.md
 • data/analysis.json
 • data/kpi_analysis.json
 • data/analysis_outliers.json
Kompatibel zu openai v1.54 + (Fun/Safe-Logik).
"""

import os, sys, json, time, math, traceback
from collections import defaultdict
from datetime import datetime, timezone, date
from pathlib import Path
from statistics import mean, median, pstdev

try:
    from tqdm import tqdm
except Exception:
    def tqdm(x, **k): return x

from env_utils import get_openai_client
from prompt_templates import (
    build_global_analysis_prompt,
    build_kpi_summary_prompt,
)
from script_utils import ensure_utf8_stdout, safe_write_json, safe_write_text, setup_logger

# === UTF-8 ===
ensure_utf8_stdout()

# === Pfade ===
SCRIPT_DIR = Path(__file__).parent.resolve()
ROOT_DIR = SCRIPT_DIR.parent.resolve()
DATA_DIR = ROOT_DIR / "data"
META_DIR = DATA_DIR / "meta"
AVAILABLE_FILE = META_DIR / "available_kpis.json"
COUNTRIES_FILE = META_DIR / "countries.json"
GROUPS_FILE = META_DIR / "groups.json"
OUT_MD = DATA_DIR / "analysis.md"
OUT_JSON = DATA_DIR / "analysis.json"
OUT_KPI = DATA_DIR / "kpi_analysis.json"
OUT_OUTLIERS = DATA_DIR / "analysis_outliers.json"
LOG_FILE = DATA_DIR / "fetch_log.txt"

# === Logging ===
logger = setup_logger("analysis", LOG_FILE)


def log(msg: str) -> None:
    logger.info(msg)

# === Loader ===
def load_meta():
    with AVAILABLE_FILE.open(encoding="utf-8") as f:
        meta=json.load(f)
    entries = list(meta.values()) if isinstance(meta,dict) else meta
    return [entry for entry in entries if entry.get("publication_status") != "pending_first_fetch"]

def iter_kpi_records(kpi):
    f=DATA_DIR/f"{kpi}.json"
    if not f.exists(): return []
    try: return json.loads(f.read_text(encoding="utf-8"))
    except: return []

def numeric_values(recs):
    for r in recs:
        v=r.get("value")
        if isinstance(v,(int,float)) and not (math.isnan(v) or math.isinf(v)): yield float(v)


GLOBAL_ENTITIES = {"World", "Welt", "Global"}
COMPARATIVE_GROUPS = ("EU", "G7", "BRICS", "AfricanUnion", "ASEAN", "Mercosur", "OECD")


def _valid_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _year(value):
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _format_value(value):
    absolute = abs(value)
    if absolute >= 1_000_000_000:
        return f"{value / 1_000_000_000:.2f}bn"
    if absolute >= 1_000_000:
        return f"{value / 1_000_000:.2f}m"
    if absolute >= 1_000:
        return f"{value:,.0f}"
    if absolute >= 100:
        return f"{value:.1f}"
    return f"{value:.2f}"


def _change_text(base_value, current_value, unit=""):
    delta = current_value - base_value
    normalized_unit = unit.casefold()
    if "°c" in normalized_unit or "temperature anomaly" in normalized_unit:
        return f"{delta:+.2f} °C ({_format_value(base_value)} → {_format_value(current_value)})"
    if unit.strip().startswith("%") or "percent" in normalized_unit or "% of" in normalized_unit:
        return f"{delta:+.2f} percentage points ({_format_value(base_value)} → {_format_value(current_value)})"
    if "index" in normalized_unit:
        return f"{delta:+.2f} index points ({_format_value(base_value)} → {_format_value(current_value)})"
    if "ppm" in normalized_unit:
        return f"{delta:+.2f} ppm ({_format_value(base_value)} → {_format_value(current_value)})"
    if "millimet" in normalized_unit:
        return f"{delta:+.2f} mm ({_format_value(base_value)} → {_format_value(current_value)})"
    if normalized_unit.strip() in {"year", "years"}:
        return f"{delta:+.2f} years ({_format_value(base_value)} → {_format_value(current_value)})"
    if "joule" in normalized_unit or "anomaly" in normalized_unit or "relative" in normalized_unit:
        return f"{delta:+.2f} {unit} ({_format_value(base_value)} → {_format_value(current_value)})"
    if base_value:
        pct = delta / abs(base_value) * 100
        return f"{pct:+.1f}% ({_format_value(base_value)} → {_format_value(current_value)})"
    return f"{delta:+.2f} ({_format_value(base_value)} → {_format_value(current_value)})"


def _trend_text(current_year, current_value, history, unit=""):
    """Return a comparable roughly five-year change without inventing causality."""
    candidates = [(year, value) for year, value in history.items() if year <= current_year - 5]
    if not candidates:
        return "trend unavailable"
    base_year, base_value = max(candidates)
    return f"change since {base_year}: {_change_text(base_value, current_value, unit)}"


def load_comparative_groups():
    """Load stable country-group membership used as regional/group evidence."""
    try:
        with GROUPS_FILE.open(encoding="utf-8") as handle:
            payload = json.load(handle)
    except Exception:
        return {}
    return {
        name: set((payload.get(name) or {}).get("members") or [])
        for name in COMPARATIVE_GROUPS
    }


def _country_comparison_context(records, latest_year, country_names, unit, groups):
    """Add traceable country extremes, group medians and roughly five-year changes."""
    current = {}
    history = defaultdict(dict)
    for record in records:
        country = record.get("country")
        year = _year(record.get("year"))
        value = record.get("value")
        if country not in country_names or year is None or not _valid_number(value):
            continue
        history[country][year] = float(value)
        if year == latest_year:
            current[country] = float(value)
    if len(current) < 3:
        return ""

    ordered = sorted(current.items(), key=lambda item: item[1])
    lower = ", ".join(f"{country}={_format_value(value)}" for country, value in ordered[:3])
    upper = ", ".join(f"{country}={_format_value(value)}" for country, value in reversed(ordered[-3:]))
    parts = [f"Country evidence {latest_year}: upper raw values {upper}; lower raw values {lower}."]

    group_facts = []
    for group, members in groups.items():
        values = [current[country] for country in members if country in current]
        if len(values) >= 3:
            group_facts.append(f"{group}={_format_value(median(values))} (n={len(values)})")
    if group_facts:
        parts.append("Group medians: " + ", ".join(group_facts) + ".")

    changes = []
    for country, current_value in current.items():
        candidates = [(year, value) for year, value in history[country].items() if year <= latest_year - 5]
        if not candidates:
            continue
        base_year, base_value = max(candidates)
        changes.append((current_value - base_value, country, base_year, base_value, current_value))
    if len(changes) >= 3:
        changes.sort()
        decreases = ", ".join(
            f"{country} ({base_year}–{latest_year}: {_change_text(base, current_value, unit)})"
            for _, country, base_year, base, current_value in changes[:2]
        )
        increases = ", ".join(
            f"{country} ({base_year}–{latest_year}: {_change_text(base, current_value, unit)})"
            for _, country, base_year, base, current_value in reversed(changes[-2:])
        )
        parts.append(
            f"Largest observed changes/anomaly candidates (verify before causal interpretation): "
            f"increases {increases}; decreases {decreases}."
        )
    return " ".join(parts)


def build_kpi_snapshot(entry, records=None, country_names=None, groups=None):
    """Create one compact, reproducible latest-state/trend line for the global prompt."""
    kid = entry.get("filename", "").replace(".json", "")
    records = iter_kpi_records(kid) if records is None else records
    title = entry.get("title") or kid
    cluster = entry.get("cluster") or "Other"
    unit = entry.get("unit") or "unit not specified"
    sort_mode = entry.get("sort") or "neutral"
    target_value = entry.get("target_value")
    if sort_mode == "target":
        direction_note = f"Interpretation: values closest to target {target_value} rank better; values above the target are not automatically better."
    elif sort_mode == "lower":
        direction_note = "Interpretation: lower raw values rank better."
    elif sort_mode == "higher":
        direction_note = "Interpretation: higher raw values rank better, subject to the metric caveats."
    else:
        direction_note = "Interpretation: raw direction is not classified as better or worse."
    guardrail = str(entry.get("analysis_guardrail") or "").strip()
    guardrail_note = f" Analysis guardrail: {guardrail}" if guardrail else ""

    global_by_year = {}
    for record in records:
        if record.get("country") not in GLOBAL_ENTITIES:
            continue
        year = _year(record.get("year"))
        value = record.get("value")
        if year is not None and _valid_number(value):
            global_by_year[year] = float(value)

    if global_by_year:
        latest_year = max(global_by_year)
        latest_value = global_by_year[latest_year]
        if entry.get("analysis_trend") == "five_year_average":
            current_years = [year for year in range(latest_year - 4, latest_year + 1) if year in global_by_year]
            previous_years = [year for year in range(latest_year - 9, latest_year - 4) if year in global_by_year]
            if len(current_years) >= 3 and len(previous_years) >= 3:
                current_value = mean(global_by_year[year] for year in current_years)
                previous_value = mean(global_by_year[year] for year in previous_years)
                return (
                    f"[{cluster}] {title} ({kid}; {unit}): global five-year average "
                    f"{_format_value(current_value)} for {min(current_years)}–{max(current_years)}; "
                    f"change versus {min(previous_years)}–{max(previous_years)}: "
                    f"{_change_text(previous_value, current_value, unit)}. {direction_note}"
                    f" Scope: world aggregate only; no country/group evidence is available.{guardrail_note}"
                )
        trend = _trend_text(latest_year, latest_value, global_by_year, unit)
        return (
            f"[{cluster}] {title} ({kid}; {unit}): global value {_format_value(latest_value)} "
            f"in {latest_year}; {trend}. {direction_note}"
            f" Scope: world aggregate only; no country/group evidence is available.{guardrail_note}"
        )

    if country_names is None:
        try:
            with COUNTRIES_FILE.open(encoding="utf-8") as handle:
                country_names = set(json.load(handle))
        except Exception:
            country_names = set()

    by_year = defaultdict(list)
    for record in records:
        if country_names and record.get("country") not in country_names:
            continue
        year = _year(record.get("year"))
        value = record.get("value")
        if year is not None and _valid_number(value):
            by_year[year].append(float(value))

    if not by_year:
        return f"[{cluster}] {title} ({kid}; {unit}): no usable values."

    maximum_coverage = max(len(values) for values in by_year.values())
    coverage_floor = max(5, math.ceil(maximum_coverage * 0.5))
    representative_years = [year for year, values in by_year.items() if len(values) >= coverage_floor]
    latest_year = max(representative_years or by_year)
    latest_values = by_year[latest_year]
    medians = {
        year: median(values)
        for year, values in by_year.items()
        if len(values) >= coverage_floor
    }
    latest_median = median(latest_values)
    trend = _trend_text(latest_year, latest_median, medians, unit)
    base = (
        f"[{cluster}] {title} ({kid}; {unit}): cross-country median {_format_value(latest_median)} "
        f"in {latest_year} across {len(latest_values)} countries; {trend}. {direction_note}{guardrail_note}"
    )
    comparison = _country_comparison_context(
        records, latest_year, country_names, unit, groups if groups is not None else load_comparative_groups()
    )
    return f"{base} {comparison}".strip()


def build_global_kpi_summaries():
    """Always represent the complete active KPI catalogue in the global synthesis."""
    meta = load_meta()
    try:
        country_names = set(json.loads(COUNTRIES_FILE.read_text(encoding="utf-8")))
    except Exception:
        country_names = set()
    groups = load_comparative_groups()
    return [build_kpi_snapshot(entry, country_names=country_names, groups=groups) for entry in meta]


def _rank_numbers(values):
    """Return average ranks for a numeric sequence, preserving ties."""
    ordered = sorted(range(len(values)), key=lambda index: values[index])
    ranks = [0.0] * len(values)
    position = 0
    while position < len(ordered):
        end = position
        while end + 1 < len(ordered) and values[ordered[end + 1]] == values[ordered[position]]:
            end += 1
        rank = (position + end) / 2 + 1
        for offset in range(position, end + 1):
            ranks[ordered[offset]] = rank
        position = end + 1
    return ranks


def _pearson(left, right):
    if len(left) < 2 or len(left) != len(right):
        return None
    left_mean, right_mean = mean(left), mean(right)
    numerator = sum((x - left_mean) * (y - right_mean) for x, y in zip(left, right))
    left_scale = sum((x - left_mean) ** 2 for x in left)
    right_scale = sum((y - right_mean) ** 2 for y in right)
    denominator = math.sqrt(left_scale * right_scale)
    return numerator / denominator if denominator else None


def build_cross_kpi_associations(meta=None, country_names=None, minimum_overlap=25):
    """Create exploratory latest-observation Spearman associations for KPI prompts."""
    meta = load_meta() if meta is None else meta
    if country_names is None:
        try:
            country_names = set(json.loads(COUNTRIES_FILE.read_text(encoding="utf-8")))
        except Exception:
            country_names = set()
    titles = {entry.get("filename", ""): entry.get("title") or entry.get("filename", "") for entry in meta}
    directions = {entry.get("filename", ""): entry.get("sort") or "neutral" for entry in meta}
    series = {}
    for kpi_id in titles:
        latest = {}
        for record in iter_kpi_records(kpi_id):
            country = record.get("country")
            year = _year(record.get("year"))
            value = record.get("value")
            if country not in country_names or year is None or not _valid_number(value):
                continue
            if country not in latest or year > latest[country][0]:
                latest[country] = (year, float(value))
        if latest:
            series[kpi_id] = {country: value for country, (_, value) in latest.items()}

    associations = defaultdict(list)
    kpi_ids = sorted(series)
    for left_index, left_id in enumerate(kpi_ids):
        for right_id in kpi_ids[left_index + 1:]:
            common = sorted(set(series[left_id]) & set(series[right_id]))
            if len(common) < minimum_overlap:
                continue
            left_values = [series[left_id][country] for country in common]
            right_values = [series[right_id][country] for country in common]
            rho = _pearson(_rank_numbers(left_values), _rank_numbers(right_values))
            if rho is None or abs(rho) < 0.45:
                continue
            associations[left_id].append((abs(rho), right_id, rho, len(common)))
            associations[right_id].append((abs(rho), left_id, rho, len(common)))

    result = {}
    for kpi_id, matches in associations.items():
        strongest = sorted(matches, reverse=True)[:3]
        result[kpi_id] = (
            "Exploratory cross-country Spearman associations using each country's latest available observation "
            "(years may differ; association is not causation): "
            + "; ".join(
                f"{titles.get(other_id, other_id)} ({other_id}, raw direction={directions.get(other_id, 'neutral')}): "
                f"rho={rho:+.2f}, n={overlap}"
                for _, other_id, rho, overlap in strongest
            )
            + "."
        )
    return result

# === GPT Helper (Fun/Safe-Style, mit optionalem Silent Mode) ===
VERBOSE = False  # ⬅️ auf True setzen, wenn du Debug-Logs brauchst

def gpt_call(prompt: str, max_tokens: int = 700) -> str:
    """Robuster GPT-Call – mit Fallback und optionalem Silent Mode."""
    text = ""
    last_err = None
    client = get_openai_client()

    for model in ["gpt-4o", "gpt-4-turbo"]:
        if VERBOSE:
            log(f"➡️ GPT call → {model}")
        try:
            rsp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You analyze global datasets objectively."},
                    {"role": "user", "content": prompt.strip()},
                ],
                max_completion_tokens=max_tokens
            )

            usage = getattr(rsp, "usage", {})
            if VERBOSE:
                log(f"🧮 Tokens: {usage}")

            msg = rsp.choices[0].message
            raw = msg.content  # ✅ new SDK compatible

            if not raw:
                if VERBOSE:
                    log("⚠️ Empty content → next model")
                continue

            text = raw.strip()
            if len(text) > 30:
                if VERBOSE:
                    log(f"✅ {model} OK ({len(text)} chars)")
                return text
            else:
                if VERBOSE:
                    log(f"⚠️ Short response ({len(text)} chars) → retry")
                text = ""

        except Exception as e:
            last_err = e
            if VERBOSE:
                log(f"❌ {model} error: {e}")
            time.sleep(1)

    raise RuntimeError(f"Empty GPT response after retries. Last error: {last_err}")


# === Globale Analyse ===
def run_global_analysis(updated=None):
    log("➡️ Starting global analysis …")
    try: summaries=build_global_kpi_summaries()
    except Exception as e:
        log(f"❌ KPI snapshot build failed: {e}")
        safe_write_json(OUT_JSON,{"error":str(e)}); return
    if not summaries:
        txt="⚠️ No KPI values found."; safe_write_text(OUT_MD,txt); safe_write_json(OUT_JSON,{"summary":txt}); return
    registered_count = len(summaries)
    associations = build_cross_kpi_associations()
    priority_ids = [
        entry.get("filename") for entry in load_meta()
        if entry.get("relevance") in {"critical", "very_high", "high"}
    ]
    association_lines = [
        f"[Cross-KPI evidence for {kpi_id}] {associations[kpi_id]}"
        for kpi_id in priority_ids if kpi_id in associations
    ][:24]
    summaries.extend(association_lines)
    log(f"🌐 Global synthesis covers all {registered_count} registered KPIs; updated-only selection is ignored here.")
    prompt = build_global_analysis_prompt(summaries)

    try:
        text = gpt_call(prompt, 2500)
    except Exception as e:
        text = f"⚠️ GPT request failed: {e}"

    safe_write_text(OUT_MD, text)
    safe_write_json(OUT_JSON, {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "kpi_count": registered_count,
        "scope": "all_registered_kpis",
        "summary": text
    })
    log(f"💾 Saved analysis ({len(text)} chars)")


# === KPI Analysen ===
def generate_kpi_analyses(data_dir: Path, updated_only=None):
    generated_at = datetime.now(timezone.utc).isoformat()
    all_meta=load_meta()
    try:
        with COUNTRIES_FILE.open(encoding="utf-8") as handle:
            country_names = set(json.load(handle))
    except Exception:
        country_names = set()
    associations = build_cross_kpi_associations(all_meta, country_names)
    meta=all_meta
    if updated_only and "__force_all__" not in updated_only:
        allow={u.replace(".json","") for u in updated_only}
        meta=[m for m in meta if m.get("filename","").replace(".json","") in allow]
        log(f"⚙️ Limiting KPI analysis to {len(meta)} entries.")
    result={}
    for e in tqdm(meta,desc="🧩 KPI summaries"):
        fname=e.get("filename","").replace(".json","")
        if not fname: continue
        title=e.get("title",fname)
        desc=e.get("description","")
        cluster=e.get("cluster","")
        unit=e.get("unit","")
        prompt = build_kpi_summary_prompt(
            title=title,
            cluster=cluster,
            unit=unit,
            description=desc,
            data_snapshot=build_kpi_snapshot(e, country_names=country_names),
            related_context=associations.get(fname, ""),
        )
        try: summary=gpt_call(prompt,400)
        except Exception as e: summary=f"⚠️ GPT error: {e}"
        result[fname]={
            "summary": summary,
            "generated_at": generated_at,
            "last_update": generated_at[:10],
        }
        time.sleep(0.8)
    existing=json.loads(OUT_KPI.read_text(encoding="utf-8")) if OUT_KPI.exists() else {}
    existing.update(result)
    safe_write_json(OUT_KPI,existing)
    log(f"✅ KPI analyses saved ({len(existing)} total)")

# === Outlier-Berechnung ===
EXCLUDE_AGGREGATES={"World","European Union","Euro area","OECD members",
                     "High income","Upper middle income","Lower middle income","Low income"}

def compute_outliers():
    """Berechnet statistische Ausreißer (Z-Score-basiert), ohne mean/stdev/min/max-Felder."""
    log("🔎 Computing outliers …")
    meta = load_meta()
    out = {}

    for m in tqdm(meta, desc="📈 KPI outliers"):
        kid = m.get("filename", "").replace(".json", "")
        recs = iter_kpi_records(kid)
        if not recs:
            continue

        # Letzter bekannter Wert pro Land (ohne Aggregate)
        latest = {}
        for r in recs:
            c, y, v = r.get("country"), r.get("year"), r.get("value")
            if not c or c in EXCLUDE_AGGREGATES or not isinstance(v, (int, float)):
                continue
            try:
                y = int(float(y))
            except Exception:
                continue
            if c not in latest or y > latest[c][0]:
                latest[c] = (y, float(v))

        if not latest:
            continue

        vals = [v for _, v in latest.values()]
        if len(vals) < 2:
            continue

        mu = mean(vals)
        sigma = pstdev(vals)
        if sigma == 0:
            continue

        zlist = []
        for c, (y, v) in latest.items():
            z = (v - mu) / sigma
            zlist.append({
                "country": c,
                "year": y,
                "value": v,
                "z": round(z, 3)
            })

        highs = sorted([e for e in zlist if e["z"] >= 2], key=lambda x: -x["z"])[:10]
        lows  = sorted([e for e in zlist if e["z"] <= -2], key=lambda x:  x["z"])[:10]

        if highs or lows:
            out[kid] = {"high_outliers": highs, "low_outliers": lows}

    safe_write_json(OUT_OUTLIERS, out)
    log(f"💾 Outliers saved ({len(out)} KPIs, compact format)")


# === Main ===
if __name__=="__main__":
    log("🚀 Running RealityCheck Global Analysis (Final GPT-Compat)")
    state=DATA_DIR/"fetch_state.json"
    updated=[]
    if state.exists():
        try: updated=json.loads(state.read_text(encoding="utf-8")).get("updated_kpis",[])
        except Exception as e: log(f"⚠️ fetch_state read error: {e}")
    if not updated: updated=["__force_all__"]
    try: run_global_analysis(updated)
    except Exception as e: log(f"❌ Global analysis failed: {e}\n{traceback.format_exc()}")
    try:
        generate_kpi_analyses(
            DATA_DIR,
            updated_only=None if "__force_all__" in updated else updated,
        )
    except Exception as e: log(f"⚠️ KPI summary failed: {e}")
    try: compute_outliers()
    except Exception as e: log(f"⚠️ Outlier computation failed: {e}")
    log("✅ RealityCheck analysis completed successfully.")

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

"""
🌍 RealityCheck – Fun, Safe Haven & Immigration Rankings (Nov 2025)
─────────────────────────────────────────────
Erzeugt:
 • fun_ranking.json
 • safe_haven_ranking.json
 • immigration_ranking.json
Verwendet dieselbe GPT-Logik wie analysis.py (OpenAI 1.54.x)
"""

import sys
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from env_utils import get_openai_client
from prompt_templates import (
    build_fun_ranking_prompt,
    build_safe_haven_prompt,
    build_immigration_prompt,
)
from script_utils import ensure_utf8_stdout, safe_write_json, setup_logger

# === UTF-8 Fix ===
ensure_utf8_stdout()

# === Pfade ===
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
LOG_FILE = DATA_DIR / "fetch_log.txt"

# === Logging ===
logger = setup_logger("fun_safe_rankings", LOG_FILE)


def log(msg: str) -> None:
    logger.info(msg)

def save_json(data, path: Path):
    if not data:
        log(f"⚠️ No data to save for {path.name}")
        return
    try:
        safe_write_json(
            path,
            data,
            logger=logger,
            note=f"💾 Saved {path.relative_to(ROOT_DIR)} ({len(data)} entries)",
        )
    except Exception as e:
        log(f"❌ Failed to save {path.name}: {e}")

# === Prompts ===

RANKING_KPIS = {
    "fun": {
        "world_happiness_index": "higher",
        "social_progress_index": "higher",
        "median_income_or_consumption_per_day": "higher",
        "healthy_diet_unaffordable": "lower",
        "urban_inadequate_housing": "lower",
        "interpersonal_trust": "higher",
        "global_peace_index": "lower",
        "air_quality_pm2_5_exposure": "lower",
        "purchasing_power_parity": "higher",
    },
    "safe": {
        "global_peace_index": "lower",
        "number_of_armed_conflicts": "lower",
        "intentional_homicides": "lower",
        "inform_resilience_index": "lower",
        "rule_of_law_index": "higher",
        "human_rights_index_vdem": "higher",
        "democracy_index": "higher",
        "water_stress_level": "lower",
        "climate_disaster_damage_gdp": "lower",
        "energy_import_dependency": "lower",
    },
    "immigration": {
        "unemployment_rate": "lower",
        "purchasing_power_parity": "higher",
        "rule_of_law_index": "higher",
        "social_progress_index": "higher",
        "world_happiness_index": "higher",
        "internet_penetration_rate": "higher",
        "government_effectiveness": "higher",
        "median_income_or_consumption_per_day": "higher",
        "healthy_diet_unaffordable": "lower",
        "urban_inadequate_housing": "lower",
        "interpersonal_trust": "higher",
    },
}

# Bottom lists answer a stronger question than the editorial Top lenses: they
# identify the weakest measured fit worldwide. Their country selection must be
# deterministic; a language model may not substitute a different shortlist.
BOTTOM_WEIGHTS = {
    "fun": {
        "world_happiness_index": 0.25,
        "social_progress_index": 0.15,
        "median_income_or_consumption_per_day": 0.15,
        "healthy_diet_unaffordable": 0.10,
        "urban_inadequate_housing": 0.05,
        "interpersonal_trust": 0.10,
        "global_peace_index": 0.10,
        "air_quality_pm2_5_exposure": 0.05,
        "purchasing_power_parity": 0.05,
    },
    "safe": {
        # GPI already combines ongoing conflict, societal safety and
        # militarisation and is therefore the anchor. The UCDP conflict count
        # is useful context but not a severity measure and can be zero despite
        # severe exposure, so it must not dominate this score.
        "global_peace_index": 0.50,
        "number_of_armed_conflicts": 0.05,
        "intentional_homicides": 0.10,
        "inform_resilience_index": 0.10,
        "rule_of_law_index": 0.03,
        "human_rights_index_vdem": 0.02,
        "water_stress_level": 0.05,
        "climate_disaster_damage_gdp": 0.10,
        "energy_import_dependency": 0.05,
    },
}

BOTTOM_LABELS = {
    "world_happiness_index": "happiness",
    "social_progress_index": "social progress",
    "median_income_or_consumption_per_day": "typical purchasing power",
    "healthy_diet_unaffordable": "essential-cost affordability",
    "urban_inadequate_housing": "urban housing adequacy",
    "interpersonal_trust": "social trust",
    "global_peace_index": "peace",
    "air_quality_pm2_5_exposure": "air quality",
    "purchasing_power_parity": "purchasing power",
    "number_of_armed_conflicts": "active conflicts",
    "intentional_homicides": "homicide safety",
    "inform_resilience_index": "crisis resilience",
    "rule_of_law_index": "rule of law",
    "human_rights_index_vdem": "human rights",
    "democracy_index": "democracy",
    "water_stress_level": "water stress",
    "climate_disaster_damage_gdp": "recent climate-disaster losses",
    "energy_import_dependency": "energy import exposure",
}

RANKING_ROLLING_AVERAGE_YEARS = {
    "climate_disaster_damage_gdp": 5,
}


def _latest_country_values(kpi_id: str, country_names: set[str]) -> dict[str, float]:
    path = DATA_DIR / f"{kpi_id}.json"
    if not path.exists():
        return {}
    try:
        records = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    observations: dict[str, list[tuple[int, float]]] = {}
    for row in records if isinstance(records, list) else []:
        country = row.get("country")
        if country not in country_names or not isinstance(row.get("value"), (int, float)):
            continue
        try:
            year = int(float(row.get("year")))
        except (TypeError, ValueError):
            continue
        observations.setdefault(country, []).append((year, float(row["value"])))
    window = RANKING_ROLLING_AVERAGE_YEARS.get(kpi_id, 1)
    values: dict[str, float] = {}
    for country, country_rows in observations.items():
        latest_by_year: dict[int, float] = {}
        for year, value in country_rows:
            latest_by_year[year] = value
        selected = [value for _, value in sorted(latest_by_year.items(), reverse=True)[:window]]
        if selected:
            values[country] = sum(selected) / len(selected)
    return values


def _percentile_fit(values: dict[str, float], direction: str) -> dict[str, float]:
    """Return direction-aware percentile fit scores in [0, 1]."""
    ordered = sorted(values.items(), key=lambda item: (item[1], item[0]))
    denominator = max(1, len(ordered) - 1)
    raw: dict[str, float] = {}
    start = 0
    while start < len(ordered):
        end = start
        while end + 1 < len(ordered) and ordered[end + 1][1] == ordered[start][1]:
            end += 1
        tied_percentile = ((start + end) / 2) / denominator
        for index in range(start, end + 1):
            raw[ordered[index][0]] = tied_percentile
        start = end + 1
    if direction == "lower":
        return {country: 1.0 - score for country, score in raw.items()}
    return raw


def build_deterministic_bottom_ranking(
    mode: str,
    *,
    count: int = 20,
    excluded_countries: set[str] | None = None,
) -> list[dict[str, Any]]:
    """Build a source-bound weakest-fit list without model country selection."""
    criteria = RANKING_KPIS[mode]
    weights = BOTTOM_WEIGHTS[mode]
    countries_payload = json.loads((DATA_DIR / "meta" / "countries.json").read_text(encoding="utf-8"))
    country_names = set(countries_payload) - (excluded_countries or set())
    series = {kpi: _latest_country_values(kpi, country_names) for kpi in weights}
    percentiles = {
        kpi: _percentile_fit(series[kpi], criteria[kpi])
        for kpi in weights if series[kpi]
    }
    active_weight_total = sum(weight for kpi, weight in weights.items() if kpi in percentiles)
    if not active_weight_total:
        return []
    required_anchor = "global_peace_index" if mode == "safe" else "world_happiness_index"
    candidates: list[tuple[float, str, list[tuple[float, str]]]] = []
    for country in country_names:
        if country not in series.get(required_anchor, {}):
            continue
        available_weight = sum(weight for kpi, weight in weights.items() if country in percentiles.get(kpi, {}))
        if available_weight / active_weight_total < 0.65:
            continue
        fit_score = sum(
            percentiles[kpi][country] * weight
            for kpi, weight in weights.items()
            if country in percentiles.get(kpi, {})
        ) / available_weight
        weakest_dimensions = sorted(
            (
                (percentiles[kpi][country], BOTTOM_LABELS[kpi])
                for kpi in weights if country in percentiles.get(kpi, {})
            ),
            key=lambda item: item[0],
        )[:3]
        candidates.append((fit_score, country, weakest_dimensions))
    candidates.sort(key=lambda item: (item[0], item[1]))

    result = []
    for rank, (_, country, dimensions) in enumerate(candidates[:count], start=1):
        labels = ", ".join(label for _, label in dimensions)
        if mode == "safe":
            reason = (
                f"Weakest relative evidence: {labels}. The score also includes crisis resilience and water stress; "
                "conflict exposure is not a forecast."
            )
        else:
            reason = f"Weakest relative evidence: {labels}. This measures living-condition fit, not the country's culture or people."
        result.append({"rank": rank, "country": country, "reason": reason})
    return result


def build_ranking_evidence(
    mode: str,
    limit: int = 80,
    *,
    direction: str = "top",
    excluded_countries: set[str] | None = None,
) -> str:
    """Build a broad data shortlist plus stable geographic/alliance context."""
    criteria = RANKING_KPIS[mode]
    countries_payload = json.loads((DATA_DIR / "meta" / "countries.json").read_text(encoding="utf-8"))
    excluded = excluded_countries or set()
    country_names = set(countries_payload) - excluded
    try:
        groups_payload = json.loads((DATA_DIR / "meta" / "groups.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        groups_payload = {}
    try:
        context_payload = json.loads((DATA_DIR / "meta" / "country_analysis_context.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        context_payload = {}
    context_fields = context_payload.get("fields") or {}
    country_context = context_payload.get("countries") or {}
    context_groups = ("EU", "NATO", "OECD", "ASEAN", "AfricanUnion", "Mercosur", "GCC")
    series = {kpi: _latest_country_values(kpi, country_names) for kpi in criteria}
    normalized: dict[str, dict[str, float]] = {}
    for kpi, direction in criteria.items():
        values = series[kpi]
        if not values:
            continue
        low, high = min(values.values()), max(values.values())
        span = high - low or 1.0
        normalized[kpi] = {
            country: (value - low) / span if direction == "higher" else 1 - (value - low) / span
            for country, value in values.items()
        }

    minimum_coverage = max(3, round(len(normalized) * 0.6))
    candidates = []
    for country in country_names:
        available = [scores[country] for scores in normalized.values() if country in scores]
        if len(available) < minimum_coverage:
            continue
        candidates.append((sum(available) / len(available), country, len(available)))
    candidates.sort(reverse=direction != "bottom")

    lines = [
        f"Candidate shortlist preselected for a {direction} ranking from {len(criteria)} RealityCheck indicators; values are latest available.",
        "Numeric fields are RealityCheck evidence. Capital, language, coordinates and memberships are stable context; missing values are unknown, not zero.",
    ]
    for _, country, coverage in candidates[:limit]:
        facts = [
            f"{kpi}={series[kpi][country]:.3g}"
            for kpi in criteria if country in series[kpi]
        ]
        info = countries_payload.get(country) or {}
        if info.get("capital"):
            facts.append(f"capital={info['capital']}")
        if info.get("languages"):
            facts.append(f"languages={info['languages']}")
        if isinstance(info.get("lat"), (int, float)) and isinstance(info.get("lon"), (int, float)):
            facts.append(f"location={info['lat']:.1f},{info['lon']:.1f}")
        memberships = [
            group for group in context_groups
            if country in set((groups_payload.get(group) or {}).get("members") or [])
        ]
        if memberships:
            facts.append("memberships=" + "/".join(memberships))
        for field_name, record in (country_context.get(country) or {}).items():
            definition = context_fields.get(field_name) or {}
            if mode not in (definition.get("modes") or []) or not isinstance(record, dict):
                continue
            value = record.get("value")
            source = str(record.get("source") or "").strip()
            as_of = str(record.get("as_of") or "").strip()
            if value in (None, "") or not source or not as_of:
                continue
            unit = record.get("unit") or definition.get("unit") or ""
            confidence = record.get("confidence") or "not rated"
            facts.append(
                f"{field_name}={value}{(' ' + str(unit)) if unit else ''} "
                f"(as_of={as_of}, source={source}, confidence={confidence})"
            )
        lines.append(f"- {country} ({coverage}/{len(criteria)} indicators): " + ", ".join(facts))
    return "\n".join(lines)


# === Core ===
def _attempt_json_load(raw_json: str, mode: str) -> Optional[Any]:
    """Try to parse ``raw_json`` and repair common minor issues."""
    try:
        return json.loads(raw_json)
    except json.JSONDecodeError as exc:
        # Handle trailing commas before ``]`` or ``}``
        cleaned = re.sub(r",(\s*[}\]])", r"\1", raw_json)
        if cleaned != raw_json:
            try:
                return json.loads(cleaned)
            except json.JSONDecodeError:
                pass

        # Replace fancy quotes with straight quotes – occasionally returned by the model
        normalized = cleaned.replace("“", '"').replace("”", '"').replace("’", "'")
        if normalized != cleaned:
            try:
                return json.loads(normalized)
            except json.JSONDecodeError:
                pass

        log(f"⚠️ JSON parse error in {mode}: {exc}")
        snippet = raw_json[:200].replace("\n", " ")
        log(f"Raw excerpt: {snippet}")
        return None


def _validate_ranking_payload(data: Any, mode: str = "", expected_count: int = 10) -> tuple[bool, str]:
    if not isinstance(data, list):
        return False, "Response is not a JSON array"
    if len(data) == 0:
        return False, "JSON array is empty"
    if len(data) != expected_count:
        return False, f"JSON array must contain exactly {expected_count} entries"

    safe_climate_count = 0
    safe_conflict_count = 0
    immigration_access_count = 0
    countries_seen: set[str] = set()
    for entry in data:
        if not isinstance(entry, dict):
            return False, "Entry is not an object"
        rank = entry.get("rank")
        country = entry.get("country")
        reason = entry.get("reason")
        if not isinstance(rank, int):
            return False, "Missing integer rank"
        if not isinstance(country, str) or not country.strip():
            return False, "Missing country string"
        if country in countries_seen:
            return False, f"Duplicate country: {country}"
        countries_seen.add(country)
        if not isinstance(reason, str) or not reason.strip():
            return False, "Missing reason string"
        if len(reason) > 220:
            return False, "Reason exceeds 220 characters"
        reason_lower = reason.lower()
        if mode.startswith("Fun") and re.search(r"\b\d+(?:[.,]\d+)?\s*(?:°\s*c|degrees?|sun(?:shine)?\s*hours?|rainy\s*days?|days?\s+of\s+sun)", reason_lower):
            return False, "Fun reason invents unsupported quantified weather context"
        if mode.startswith("Safe Haven"):
            unsupported_certainty = (
                "minimal climate risk",
                "low climate risk",
                "no climate risk",
                "no exposure to conflict",
                "no conflict exposure",
            )
            if any(claim in reason_lower for claim in unsupported_certainty):
                return False, "Safe Haven reason states unsupported climate or conflict certainty"
            if any(word in reason_lower for word in ("climate", "resilien")):
                safe_climate_count += 1
            if any(word in reason_lower for word in ("conflict", "geograph", "remote", "alliance", "nato", "neutral", "spillover", "border")):
                safe_conflict_count += 1
        if mode.startswith("Immigration") and any(
            word in reason_lower
            for word in ("visa", "work permit", "residen", "immigration", "migration route", "entry barrier", "accessib", "restrict")
        ):
            immigration_access_count += 1
    if sorted(entry["rank"] for entry in data) != list(range(1, expected_count + 1)):
        return False, f"Ranks must be unique integers from 1 through {expected_count}"
    required_dimension_coverage = max(1, (expected_count * 4 + 4) // 5)
    if mode.startswith("Safe Haven") and safe_climate_count < required_dimension_coverage:
        return False, f"Safe Haven climate/resilience coverage is {safe_climate_count}/{expected_count}; require {required_dimension_coverage}"
    if mode.startswith("Safe Haven") and safe_conflict_count < required_dimension_coverage:
        return False, f"Safe Haven conflict/alliance coverage is {safe_conflict_count}/{expected_count}; require {required_dimension_coverage}"
    if mode.startswith("Immigration") and immigration_access_count < required_dimension_coverage:
        return False, f"Immigration accessibility coverage is {immigration_access_count}/{expected_count}; require {required_dimension_coverage}"
    return True, ""


def _extract_json_snippet(text: str) -> str | None:
    clean = text.strip("` \n")
    if clean.lower().startswith("json"):
        clean = clean[4:].strip()
    match = re.search(r"(\[.*\]|\{.*\})", clean, re.DOTALL)
    if match:
        return match.group(1)
    return clean if clean.startswith("[") else None


def generate_ranking(mode: str, prompt: str, path: Path, *, expected_count: int = 10):
    log(f"➡️ Generating {mode} via GPT-4o-Mini …")
    client = get_openai_client()
    messages = [
        {"role": "system", "content": "You answer with JSON arrays that follow the requested schema."},
        {"role": "user", "content": prompt},
    ]

    for attempt in range(4):
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_completion_tokens=3000,
            )
        except Exception as e:
            log(f"❌ GPT request failed in {mode} (attempt {attempt+1}): {e}")
            continue

        text = (response.choices[0].message.content or "").strip()
        if not text:
            log(f"⚠️ Empty response for {mode} (attempt {attempt+1})")
            messages.append({
                "role": "user",
                "content": "Reply again with a JSON array matching the schema.",
            })
            continue

        snippet = _extract_json_snippet(text)
        if not snippet:
            log(f"⚠️ No JSON found in GPT response for {mode}")
            log(f"Raw excerpt: {text[:200]}")
            messages.append({
                "role": "user",
                "content": "No valid JSON array detected. Reply with array only.",
            })
            continue

        parsed = _attempt_json_load(snippet, mode)
        if parsed is None:
            messages.append({
                "role": "user",
                "content": "Previous JSON was invalid. Provide a clean JSON array only.",
            })
            continue

        valid, reason = _validate_ranking_payload(parsed, mode, expected_count)
        if not valid:
            log(f"⚠️ Validation failed for {mode}: {reason}")
            messages.append({
                "role": "user",
                "content": (
                    f"Your JSON failed a required content rule ({reason}). Return the complete corrected {expected_count}-entry array. "
                    "Apply that rule explicitly to every single reason, not only to some entries."
                ),
            })
            continue

        save_json(parsed, path)
        return parsed

    log(f"❌ Unable to generate valid JSON for {mode} after retries.")
    return []

# === Main ===
if __name__ == "__main__":
    FUN = DATA_DIR / "fun_ranking.json"
    FUN_BOTTOM = DATA_DIR / "fun_ranking_bottom.json"
    SAFE = DATA_DIR / "safe_haven_ranking.json"
    SAFE_BOTTOM = DATA_DIR / "safe_haven_ranking_bottom.json"
    IMMIG = DATA_DIR / "immigration_ranking.json"
    IMMIG_BOTTOM = DATA_DIR / "immigration_ranking_bottom.json"

    log("🎬 Starting Top/Bottom 20 Fun, Safe & Immigration ranking generation…")
    fun = generate_ranking(
        "Fun Mode Top",
        build_fun_ranking_prompt(build_ranking_evidence("fun"), direction="top", count=20),
        FUN,
        expected_count=20,
    )
    fun_bottom = build_deterministic_bottom_ranking(
        "fun", count=20, excluded_countries={entry["country"] for entry in fun}
    )
    save_json(fun_bottom, FUN_BOTTOM)
    safe = generate_ranking(
        "Safe Haven Mode Top",
        build_safe_haven_prompt(build_ranking_evidence("safe"), direction="top", count=20),
        SAFE,
        expected_count=20,
    )
    safe_bottom = build_deterministic_bottom_ranking(
        "safe", count=20, excluded_countries={entry["country"] for entry in safe}
    )
    save_json(safe_bottom, SAFE_BOTTOM)
    immigr = generate_ranking(
        "Immigration Mode Top",
        build_immigration_prompt(datetime.now().year, build_ranking_evidence("immigration"), direction="top", count=20),
        IMMIG,
        expected_count=20,
    )
    immigr_bottom = generate_ranking(
        "Immigration Mode Bottom",
        build_immigration_prompt(
            datetime.now().year,
            build_ranking_evidence(
                "immigration",
                direction="bottom",
                excluded_countries={entry["country"] for entry in immigr},
            ),
            direction="bottom",
            count=20,
        ),
        IMMIG_BOTTOM,
        expected_count=20,
    )

    generated = (fun, fun_bottom, safe, safe_bottom, immigr, immigr_bottom)
    if all(generated):
        log("✅ All six Top/Bottom ranking lists generated successfully.")
    elif any(generated):
        log("⚠️ Partial success – at least one ranking list generated.")
    else:
        log("❌ No ranking data generated.")

"""Centralized prompt templates for GPT interactions within RealityCheck scripts."""
from __future__ import annotations

from datetime import datetime
from textwrap import dedent
from typing import Iterable


def build_csv_update_prompt(
    *,
    title: str,
    last_year: int | None,
    source_url: str | None = None,
    publisher: str | None = None,
    source_code: str | None = None,
    description: str | None = None,
) -> str:
    """Prompt used for asking GPT about the freshest CSV release year."""
    source_bits = []
    if publisher:
        source_bits.append(f"Publisher: {publisher}")
    if source_url:
        source_bits.append(f"Official URL: {source_url}")
    if source_code:
        source_bits.append(f"Internal ID: {source_code}")
    if description:
        source_bits.append(f"Description: {description.strip()[:400]}")
    meta_text = "\n".join(source_bits)

    return dedent(
        f"""
        You are a meticulous research assistant verifying whether a KPI dataset has a newer public release.

        Dataset title: "{title}"
        Last ingested year in our system: {last_year if last_year else "unknown"}
        {meta_text}

        Instructions:
        1. Use the official publisher link above or otherwise reliable primary sources.
        2. Determine the latest release year that is currently available to download.
        3. Only confirm a newer release if a publication, download page or press release explicitly mentions a year > {last_year or "unknown"}.
        4. If you cannot verify a fresher release, report null and explain why.

        Respond **only** with a compact JSON object using this schema:
        {{
          "dataset": "{title}",
          "latest_year": <integer|null>,
          "confidence": "high"|"medium"|"low",
          "evidence": "Short description of the page or report you checked"
        }}
        Do not add markdown, explanations, prose or code fences – JSON only.
        """
    ).strip()


def build_global_analysis_prompt(summary_lines: Iterable[str]) -> str:
    joined = "\n".join(summary_lines)
    return dedent(
        f"""
        You are a senior geopolitical, climate-impact, and socio-economic analyst preparing a comprehensive synthesis of global KPI trends.

        Your task: write a **structured, insightful, and readable report** (8–10 clearly separated sections) interpreting
        cross-domain patterns across economy, security, environment, society, governance, and technology, based only on these reproducible KPI snapshots:

        {joined}

        **Formatting requirements:**
        • Start with `## Executive verdict` and answer directly whether the measured world has become safer or less safe, over which period, and with what confidence.
        • Include dedicated sections `## Security and instability`, `## Climate change and measured impacts`, `## Country and group patterns`, `## Noteworthy changes and outliers`, `## Potential best practices`, `## Connections and hypotheses`, followed by economy, society/governance, technology, data limits, and outlook.
        • Use short paragraphs (max 5 lines each).
        • Add bullet points or numbered lists when summarizing contrasts or correlations.
        • Highlight key figures, countries, or anomalies in **bold**.
        • Avoid walls of text — readability and structure are essential.

        **Analytical focus:**
        - Major global progress and regression trends, prioritizing comparable five-year changes
        - Whether insecurity is broad-based or driven by conflict incidence, conflict deaths, geopolitical risk, displacement, military burden, or domestic violence
        - How strongly climate change is already visible: separate physical change and emissions from exposure, damage, ecosystem condition, adaptation, and resilience
        - Interconnections between indicators (e.g., GDP ↔ CO₂, democracy ↔ happiness)
        - Contrasts between democracies vs autocracies, and rich vs poor countries
        - Country and group patterns, including EU, G7, BRICS, African Union, ASEAN, Mercosur or OECD when supplied
        - Countries with unusually strong, weak, improving or deteriorating observations
        - Potential best-practice cases worth investigating, without claiming that the KPI data prove the underlying policy cause
        - Plausible cross-KPI connections; explicitly distinguish measured association, interpretation and hypothesis
        - Long-term implications, risks, and opportunities
        - A forward-looking outlook (climate, stability, prosperity)

        **Evidence rules:**
        - Do not claim causation from correlation. In particular, do not attribute every natural disaster to climate change.
        - Disaster counts, deaths, people affected and damage estimates are volatile and historically incomplete. Describe them as recorded outcomes, prefer the supplied five-year averages, and do not infer climate attribution or a general rise in disaster severity from one of these series alone.
        - Use country and group findings only when explicitly supplied in the evidence. Cite the KPI name or ID and year next to material country/group claims so readers can trace them.
        - Never describe a cross-country median or its change as a global total or global population change. Keep `global value` and `cross-country median` conceptually separate.
        - Do not attach named conflicts, policies or explanations to an observed country value unless the evidence supplies them; label any proposed explanation as a hypothesis.
        - A group claim must quote a supplied group median, KPI ID and year. Do not infer group conflict exposure, policy coherence or performance from unrelated global-only series.
        - Raw upper/lower values are descriptive, not automatically good/bad; interpret direction and targets from the KPI context.
        - Treat the largest reported country changes as anomaly candidates first. Flag implausible jumps, stale years or likely revisions instead of celebrating or alarming without qualification.
        - Describe a best-practice country as a case to examine, not proof that one policy caused the result.
        - Label proposed explanations as `Possible connection` or `Hypothesis to investigate`; correlation and co-movement are not causation.
        - Treat a latest year with thin coverage cautiously and mention important recency or coverage limitations.
        - If the indicators point in different directions, give a mixed verdict rather than forcing one conclusion.
        - Do not interpret growth in nominal or current-price monetary values as real prosperity without inflation adjustment.
        - For temperature anomalies and percentage-based indicators, use the supplied absolute change rather than turning it into a relative percentage.

        Style: clear, engaging, and accessible English (B2 level).
        Be factual but interpretative, analytical but not technical.
        """
    ).strip()


def build_kpi_summary_prompt(
    *, title: str, cluster: str, unit: str, description: str,
    data_snapshot: str = "", related_context: str = "",
) -> str:
    return dedent(
        f"""
        Write a concise (≤1,250 chars) analysis for '{title}' ({cluster}, unit: {unit}).
        Explain the measure, the current cross-country or global pattern, notable country changes/outliers,
        supplied group differences and a cautious outlook. Name a strong result as a possible best-practice case
        to examine, not proof of policy causation. If related indicators are supplied, describe them only as
        exploratory associations and label any explanation `Possible connection`, never as established cause.
        Cite years and KPI names/IDs from the evidence. Do not invent country, regional, causal or trend claims.
        Treat listed largest changes as anomaly candidates: explicitly question implausible jumps or likely data revisions.
        If the snapshot says `world aggregate only`, do not name any country, group, policy or best-practice case.
        Follow the supplied raw direction/target and analysis guardrail. Do not treat an above-target value as better.
        Never call a value a projection unless the evidence explicitly identifies it as projected; a current-year value may be partial.
        Do not interpret nominal/current-price monetary growth as real prosperity without inflation and exchange-rate qualification.
        Correlation signs refer to raw values: use the supplied direction before describing whether an association is favourable.
        Context: {description}
        Data snapshot: {data_snapshot or "No validated numeric snapshot is available; explain the measure only."}
        Related-indicator context: {related_context or "No sufficiently robust cross-KPI association supplied."}
        """
    ).strip()


def build_fun_ranking_prompt(evidence: str = "", *, direction: str = "top", count: int = 20) -> str:
    bottom = direction == "bottom"
    ranking_goal = (
        f"the Bottom {count} countries that currently look least convincing for this lens"
        if bottom else f"the Top {count} countries that look especially cool and enjoyable to live in"
    )
    rank_rule = "Rank 1 is the weakest match." if bottom else "Rank 1 is the strongest match."
    return dedent(
        f"""
        You are generating RealityCheck's deliberately light-hearted **Fun Ranking**: {ranking_goal}.
        Combine the supplied RealityCheck evidence with a gently humorous editorial view of pleasant climate, many sunshine hours,
        relatively few rainy days, affordable restaurant beer, happiness (WHI), social life, health, peace and purchasing power.
        Give a bonus where the country hosts cities recognised for liveability or travel appeal by sources such as Lonely Planet, EIU, Mercer or Monocle.
        The result may make the reader smile. Never state a specific temperature, sunshine/rain total, beer price or city-ranking position unless that exact fact is present in the evidence; currently those dimensions should be phrased qualitatively.

        Evidence:
        {evidence or "No candidate evidence supplied."}

        Output rules:
        - Respond with a JSON array only.
        - Each entry must include rank (int), country (string), reason (string ≤ 220 chars).
        - Return exactly {count} entries. {rank_rule}
        - Select countries only from the evidence shortlist. RealityCheck facts may be quoted numerically; qualitative lifestyle context must remain clearly qualitative.
        - Make each reason informative and mildly witty rather than turning the ranking into a joke.
        - For a Bottom ranking, use a neutral-to-gently-witty description of trade-offs without ridiculing a country or its people.
          Avoid stereotypes and metaphors about backwardness, boredom, depressing places, or someone's relatives.
        - Do not include trailing commas, comments or explanations outside the JSON.
        """
    ).strip()


def build_safe_haven_prompt(evidence: str = "", *, direction: str = "top", count: int = 20) -> str:
    bottom = direction == "bottom"
    ranking_goal = (
        f"the Bottom {count} countries with the weakest current Safe Haven fit"
        if bottom else f"the Top {count} safest and most resilient countries to live in"
    )
    rank_rule = "Rank 1 is the weakest match." if bottom else "Rank 1 is the strongest match."
    return dedent(
        f"""
        You are an analyst generating the **Safe Haven Ranking** – produce a JSON array with {ranking_goal}.
        Assess internal safety (peace, homicide, rule of law, rights and democracy), crisis resilience and how climate risks affect daily life.
        Also consider geographic proximity to active conflict areas, plausible spillover, and whether alliances reduce risk through deterrence or could create obligations and exposure.
        Do not treat alliance membership as automatically safe or unsafe, and do not predict that a country will enter a war.
        INFORM resilience measures coping capacity, not absence of climate hazards; do not call climate risk minimal merely because resilience is high.

        Evidence:
        {evidence or "No candidate evidence supplied."}

        Output rules:
        - Respond with a JSON array only.
        - Each entry must include rank (int), country (string), reason (string ≤ 220 chars).
        - Return exactly {count} entries. {rank_rule}
        - Select countries only from the evidence shortlist. Use numeric claims only from the evidence; geographic and geopolitical judgments must be cautious and qualitative.
        - Explicitly balance domestic safety, conflict exposure and climate/resilience rather than using only crime statistics.
        - Structure every reason as three short clauses: `Domestic: ...; Climate/resilience: ...; Conflict/alliance: ...`.
        - For a Bottom ranking, describe measured vulnerability or exposure carefully; do not predict war or label a population as dangerous.
        - No comments, markdown, prose or code fences.
        """
    ).strip()


def build_immigration_prompt(
    year: int | None = None,
    evidence: str = "",
    *,
    direction: str = "top",
    count: int = 20,
) -> str:
    target_year = year or datetime.now().year
    bottom = direction == "bottom"
    ranking_goal = (
        f"the Bottom {count} countries that appear least accessible or least attractive for immigration"
        if bottom else f"the Top {count} countries that appear both attractive and comparatively accessible for immigration"
    )
    rank_rule = "Rank 1 is the weakest match." if bottom else "Rank 1 is the strongest match."
    return dedent(
        f"""
        You are an international migration and labor-mobility analyst.

        Identify and rank **{ranking_goal} in {target_year}**.

        Consider these dimensions:
        Consider visa and work-permit barriers, realistic paths to permanent residence, job opportunities,
        integration friendliness and social acceptance, language accessibility, purchasing power, rule of law,
        social progress, life satisfaction, connectivity and government effectiveness.

        Evidence:
        {evidence or "No candidate evidence supplied."}

        This is a comparative orientation, not legal advice or a promise of individual eligibility. Immigration rules vary by
        nationality, qualifications, family status and route and can change. Do not invent named visa programmes, thresholds,
        processing times or legal entitlements. Phrase policy accessibility as a cautious current editorial assessment.
        Do not rank a clearly restrictive destination highly on prosperity alone. Every reason must cover both destination quality
        and a cautious qualitative assessment of visa/work/residence accessibility; lower the rank where those barriers are substantial.

        Output strictly as valid JSON array – no comments or text – where each entry contains:
        {{
          "rank": <int>,
          "country": "<string>",
          "reason": "<string ≤ 220 chars>"
        }}
        Return exactly {count} entries. {rank_rule}
        Select countries only from the evidence shortlist. Numeric claims must come from the evidence; qualitative policy context
        may guide the ranking but must not be presented as a guaranteed legal outcome.
        For a Bottom ranking, discuss barriers and destination conditions without judging immigrants or a country's population.
        Structure every reason exactly as two short clauses: `Access: ... visa/work/residence ...; Destination: ...`.
        The Access clause must explicitly contain at least one of the words visa, work permit, residence, immigration,
        migration route, entry barrier, accessibility or restriction. Never omit this clause, even when destination quality is weak.
        """
    ).strip()


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
        You are a senior geopolitical and socio-economic analyst preparing a comprehensive synthesis of global KPI trends.

        Your task: write a **structured, insightful, and readable report** (8–10 clearly separated sections) interpreting
        cross-domain patterns across economy, environment, society, governance, and technology, based on these aggregated KPI highlights:

        {joined}

        **Formatting requirements:**
        • Use Markdown with clear section headers (## Economy, ## Environment, ## Society & Governance, ## Technology, ## Regional Insights, ## Outlook, etc.).
        • Use short paragraphs (max 5 lines each).
        • Add bullet points or numbered lists when summarizing contrasts or correlations.
        • Highlight key figures, countries, or anomalies in **bold**.
        • Avoid walls of text — readability and structure are essential.

        **Analytical focus:**
        - Major global progress and regression trends
        - Interconnections between indicators (e.g., GDP ↔ CO₂, democracy ↔ happiness)
        - Contrasts between democracies vs autocracies, and rich vs poor countries
        - Regional differences (Europe, Africa, Asia, Americas)
        - Long-term implications, risks, and opportunities
        - Noteworthy outliers or anomalies
        - A forward-looking outlook (climate, stability, prosperity)

        Style: clear, engaging, and accessible English (B2 level).
        Be factual but interpretative, analytical but not technical.
        """
    ).strip()


def build_kpi_summary_prompt(*, title: str, cluster: str, unit: str, description: str) -> str:
    return dedent(
        f"""
        Write a concise (≤900 chars) analysis for '{title}' ({cluster}, unit: {unit}).
        Describe what it measures, notable high/low performers, regional patterns and a short outlook.
        Context: {description}
        """
    ).strip()


def build_fun_ranking_prompt() -> str:
    return dedent(
        """
        You are an analyst generating the **Fun Ranking** – produce a JSON array with the Top 10 countries that best match a 'Fun & Easy Living' lifestyle.
        Criteria: pleasant climate (18–26 °C), many sunny days (280-300), few rainy days (60-90), high happiness (World Happiness Index) and low beer price in restaurants (< 3.50 USD).
        Countries that host cities ranked in the top 5 of the EIU Global Liveability Index, Mercer Quality of Living Index, or Monocle Quality of Life Survey should receive a bonus.

        Output rules:
        - Respond with a JSON array only.
        - Each entry must include rank (int), country (string), reason (string ≤ 220 chars).
        - Do not include trailing commas, comments or explanations outside the JSON.
        """
    ).strip()


def build_safe_haven_prompt() -> str:
    return dedent(
        """
        You are an analyst generating the **Safe Haven Ranking** – produce a JSON array with the Top 10 safest and most resilient countries to live in.
        Criteria: strong human rights records, low conflict risk, moderate climate risk, high resilience (e.g., INFORM), and stable democracies (e.g., Democracy Index).

        Output rules:
        - Respond with a JSON array only.
        - Each entry must include rank (int), country (string), reason (string ≤ 220 chars).
        - No comments, markdown, prose or code fences.
        """
    ).strip()


def build_immigration_prompt(year: int | None = None) -> str:
    target_year = year or datetime.now().year
    return dedent(
        f"""
        You are an international migration and labor-mobility analyst.

        Identify and rank the **Top 10 countries that are easiest and most attractive for immigration in {target_year}**, based on realistic and data-driven reasoning.

        Consider these dimensions:
        • Openness of immigration policies (visa, work permits, permanent residence)
        • Job opportunities and demand for skilled workers
        • Integration friendliness and social acceptance of migrants
        • Language accessibility (English or another major world language)
        • Quality of life, rule of law, and long-term stability

        Reference credible sources such as the Migration Policy Index, Global Talent Competitiveness Index, UN Migration Data Portal, World Happiness Index, and Rule of Law metrics.

        Output strictly as valid JSON array – no comments or text – where each entry contains:
        {{
          "rank": <int>,
          "country": "<string>",
          "reason": "<string ≤ 220 chars>"
        }}
        """
    ).strip()


# Analysis methodology

RealityCheck produces two related but distinct types of AI-supported interpretation. Measured statements are grounded in the site's current KPI data; editorial ranking modes may also use explicitly qualitative context where no structured source is connected.

## Global and per-KPI analysis

The global report synthesizes the complete registered KPI catalogue. Each KPI snapshot includes its representative latest year, coverage, trend, direction or target and metric-specific interpretation guardrails. Country KPIs additionally provide raw upper and lower observations, medians for selected comparison groups and roughly five-year changes that are labelled as anomaly candidates.

Per-KPI insights use the same evidence. They may highlight notable country and regional developments, concerning or encouraging changes and potential best-practice candidates. A high value alone is not proof of a best practice: the generated text must describe such cases as candidates for further examination. World-only series must not produce country rankings or country best practices.

Exploratory cross-KPI links are calculated as Spearman rank associations over the latest available country observation for each KPI. The output includes both KPI identifiers and sample size. These associations may reveal leads for investigation, but mixed observation years, confounders and metric direction mean that they are neither causal evidence nor proof that a policy worked.

## Fun, Safe Haven and Immigration modes

These modes are deliberately editorial hybrids rather than purely mechanical KPI rankings:

- **Fun** asks whether a country feels like a cool and enjoyable place to live. It combines RealityCheck evidence such as happiness, health, peace and purchasing power with a gently humorous qualitative view of sunshine, climate, social life, beer affordability and internationally recognised liveable or travel-worthy cities.
- **Safe Haven** combines domestic safety, crime, rights, institutions and resilience with qualitative consideration of conflict proximity, likely spillovers, climate effects on daily life and whether geography or alliances reduce or increase exposure. It is not a prediction of war.
- **Immigration** combines quality of life, jobs, integration context and stability with qualitative consideration of visa, work-permit and longer-term residence barriers. It is general comparison, not legal or immigration advice.

Each lens presents a Top 20 and a Bottom 20. Rank 1 means the strongest fit in the Top list and the weakest fit in the Bottom list. Fun and Safe Haven Bottom country selection is deterministic and direction-aware: weighted percentile scores, a 65% coverage threshold across the datasets that are actually active and a required anchor KPI replace model-selected shortlists. Fun additionally uses typical purchasing power, essential-cost affordability, housing adequacy and social trust once those source files are active. Safe Haven adds five-year-average climate-disaster losses and guarded energy-import exposure while remaining anchored primarily in the Global Peace Index because it already combines ongoing conflict, societal safety and militarisation; armed-conflict counts are supporting context rather than a severity measure. The counter-list is a comparison of measured fit for the stated lens, not a blanket judgment about a country or its population. The UI therefore uses separate, non-stigmatising symbols: 😎/☔ for Fun, 🛡️/💥 for Safe Haven and 🧳/🚧 for Immigration. A country is excluded from the Bottom shortlist once it appears in the corresponding Top list.

The numeric evidence supplied to these prompts comes from current RealityCheck datasets. Sunshine, beer prices, city-list recognition, conflict geography and immigration procedures are not yet maintained as structured, release-bound datasets. The generator may therefore discuss them only qualitatively and must not invent exact prices, rankings, legal thresholds, processing times or entitlements. These dimensions should be treated as editorial orientation and checked against current primary sources before a personal decision.

`data/meta/country_analysis_context.json` is the controlled extension point for these dimensions. Context is admitted to a prompt only when a value, source and as-of date are all present. Empty or partially documented fields are treated as unknown. This permits reviewed manual evidence or future automated adapters without silently turning general model knowledge into a measured fact.

## Traceability and limits

Generated artifacts store a UTC timestamp. Prompts require KPI identifiers and years for factual claims, distinguish global totals from cross-country medians and label possible explanations as hypotheses. Source revisions, different reporting years, missing countries and model error remain possible. RealityCheck analyses are orientation aids, not forecasts, legal advice or substitutes for the cited primary sources.

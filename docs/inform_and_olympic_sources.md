# INFORM Risk and Olympic medal sources

## INFORM Risk Index

The legacy KPI ID is `inform_resilience_index`. The 1,910 input values for
2016–2025 match the checked-in JRC workbook, whose indicator column contains
`INFORM Risk Index` throughout. This is the overall score, which combines
hazard and exposure, vulnerability, and lack of coping capacity. The UI title
and interpretation describe the overall score.

The fetch pipeline reads the [JRC INFORM API](https://drmkc.jrc.ec.europa.eu/inform-index/About)
and appends complete, contiguous release years of the same indicator.
Historical values remain the verified local baseline, even when the API
recalculates earlier releases. The API must retain the baseline country
coverage and incoming editions must pass uniqueness and range checks.
Source: European Union, JRC, [CC BY 4.0 for EU-owned content](https://commission.europa.eu/legal-notice_en).
RealityCheck filters to one indicator, joins the country registry, and
appends verified editions.

## Olympic medal totals

The unit is one medal for each medal-winning result, including one for a
team result. The source CSVs contain delegation totals by Games and season.
The adapter normalizes these totals before publication. It checks for
conflicting totals, rejects unknown delegations, and limits the target
registry to the [193 current UN member states](https://www.un.org/about-us/member-states).

Former states and neutral or multinational teams are excluded. No Soviet,
Yugoslav, Czechoslovak, East German or Russian Olympic Committee totals are
transferred to a present-day state. The Federal Republic of Germany's
`FRG` and the unified German delegation's `EUA` retain the existing
Germany mapping. The latter represented Germany jointly. Former names of
continuing states, such as Ceylon, retain their country mapping. Olympic
codes take precedence over generic aliases where they differ. In particular
`SLO` is Slovenia, `LAT` is Latvia, and `ROC` is excluded.

The 2026 winter counts are factual medal totals from the
[Wikimedia medal table](https://en.wikipedia.org/wiki/2026_Winter_Olympics_medal_table),
cross-checked against [CONI](https://www.coni.it/en/italia-team/medals-milano-cortina-2026.html).
RealityCheck retains the totals for 29 eligible delegations and omits the
neutral delegation. Only country codes and totals were extracted. Any
licensable adaptation of the Wikimedia table is attributed to its
contributors and available under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).

Edition acquisition remains reviewed manually. Ingest reviewed totals as
`country,year,value` in the appropriate season's source CSV. The normal
fetch applies the delegation rules automatically.

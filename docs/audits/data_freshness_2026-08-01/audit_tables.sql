-- The reviewed table rows are stored in artifact.json so that report rendering
-- and audit handoff use one bounded snapshot. These DuckDB queries expose the
-- native report tables from that canonical snapshot.

SELECT manual_source.*
FROM read_json_auto('docs/audits/data_freshness_2026-08-01/artifact.json') AS artifact,
UNNEST(artifact.snapshot.datasets.manual_sources) AS row(manual_source);

SELECT candidate.*
FROM read_json_auto('docs/audits/data_freshness_2026-08-01/artifact.json') AS artifact,
UNNEST(artifact.snapshot.datasets.candidates) AS row(candidate);

SELECT remaining.*
FROM read_json_auto('docs/audits/data_freshness_2026-08-01/artifact.json') AS artifact,
UNNEST(artifact.snapshot.datasets.remaining) AS row(remaining);

SELECT gap.*
FROM read_json_auto('docs/audits/data_freshness_2026-08-01/artifact.json') AS artifact,
UNNEST(artifact.snapshot.datasets.kpi_gaps) AS row(gap);

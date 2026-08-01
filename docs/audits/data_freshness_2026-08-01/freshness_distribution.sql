-- Reproduces the chart dataset after the KPI max-year audit.
SELECT *
FROM (VALUES
  ('2019', 1),
  ('2020', 1),
  ('2021', 1),
  ('2022', 7),
  ('2023', 15),
  ('2024', 17)
) AS freshness_distribution(latest_year, kpi_count)
ORDER BY latest_year;

-- Reproduces the exclusive source-portfolio chart.
SELECT *
FROM (VALUES
  ('Manuelle CSV', 12),
  ('Automatisch <2025', 33),
  ('Automatisch >=2025', 30)
) AS source_portfolio("group", kpi_count);

# Tests Baseline

This folder is reserved for automated and manual validation assets.

Planned additions:

- smoke checks for key pages
- data integrity checks for generated JSON datasets
- deployment validation checklists

Implemented targeted checks:

- `python -m unittest discover -s tests -p "test_*.py" -v` validates fail-closed fetch guards, required output formats, JSON-only special sources and isolated test-KPI selection.
- `python scripts/validation.py` validates that every active KPI has non-empty, parseable required output files and exits non-zero on any blocking error.
- `.github/workflows/ci.yml` runs Python, data, JavaScript and PHP checks automatically on pull requests and pushes to `main` without network fetches or deployment.

- `node tests/germany_dossier_tabs.test.js` validates dossier selection from
  direct and nested hashes plus keyboard tab-index navigation.
- `php -d zend.assertions=1 -d assert.exception=1 tests/germany_reform_agenda_data_test.php`
  validates all eleven bilingual reform chapters, compass values, sources and
  the page-level editorial language controls.
- `php -d zend.assertions=1 -d assert.exception=1 tests/germany_dossier_bilingual_data_test.php`
  checks the complete German data variants for prosperity, income, scenarios
  and the war stress test, plus the expanded bilingual depth of all reform
  chapters.
- `node tests/real_wages_analysis.test.js` validates comparison boundaries,
  missing data, the required German value, malformed payloads and trend math.
- `php -d zend.assertions=1 -d assert.exception=1 tests/real_wages_auth_test.php`
  validates lockout, idle expiry and CSRF helper behavior.
- `node tests/germany_2036_scenarios.test.js` validates scenario defaults,
  deterministic and monotonic slider effects, interpolation, band ordering and
  household output boundaries.
- `php -d zend.assertions=1 -d assert.exception=1 tests/germany_2036_data_test.php`
  validates the protected scenario schema, source records and numeric bands.
- `node tests/germany_war_stress_test.test.js` validates the separate war
  stress-test payload boundary, service-debate fields, source index and
  conscription-map categories without touching the standard scenario engine.
- `php -d zend.assertions=1 -d assert.exception=1 tests/germany_war_stress_data_test.php`
  validates all seven phases, evidence labels, household/debate/service
  structures, both detailed service models, refusal-paradox sources, source
  URLs, conscription country coverage, page order and
  separation from the regular tabs.
- `node tests/income_pyramid.test.js` validates gross/net boundary handling,
  household equivalence weights and relative comparisons.
- `php -d zend.assertions=1 -d assert.exception=1 tests/income_pyramid_data_test.php`
  validates the seven benchmark bands, six EU-SILC 2025 household types,
  DINKs caveat inputs and official source metadata.

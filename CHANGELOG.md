# Changelog

All notable changes to this project will be documented in this file.

## Unreleased

## [3.3.0] - 2026-07-31

### Added
- Added a bilingual fourth Germany Dossier file, “Germany 2036 — Reform Agenda”, with eleven consistently structured reform fields, international democratic-country mechanisms, options, opportunities, risks, a six-dimension 2036 compass and direct institutional sources.
- Added an editorial EN/DE language switch for the public Germany Dossier, English by default, with a visible explanation of why precise German copy replaces Google Translate on this complex specialist page.
- Added bilingual reform-agenda schema validation and methodology documentation.
- Added a sourced “If war starts, I will just leave” reality check covering exit restrictions, disrupted routes, admission and status uncertainty, refugee living conditions, NATO burden-sharing and the limits of the 2026 US–Ukraine deportation example without stigmatising flight.
- Added a sourced “Why Germany?” introduction explaining the country's global economic weight, EU leverage, stated conventional-defence ambition, potential democratic counterweight, historical responsibility and the author's personal German perspective.
- Added a sourced two-model service debate to the war stress test: classic German military duty with conscientious-objector service versus an all-gender civic year, including potential social-learning effects, legal feasibility, implementation, enforcement, labour-market and fairness risks.
- Added a protected worldwide conscription map to the war stress test, distinguishing active conscription in V-Dem democracies and autocracies from no active service and unresolved data, with explicit definitions, review dates and democratic safeguards.
- Added a separately activated, non-probabilistic “Germany at War” security stress test below the three regular scenarios, with seven evidence-labelled phases, a BBK-based 72-hour view, five household perspectives, balanced deterrence and conscription debates, historical comparison limits and an HTTP-denied source matrix.
- Added `docs/germany_war_stress_test_method.md`, server-side schema tests, browser-logic tests, responsive/print styling and deployment allowlisting for the new module.
- Added an English, three-file Germany Dossier with a values-based editorial disclosure and card-index navigation for prosperity, 2036 scenarios and the war stress test.
- Restored the Earth Overshoot Day status on About using the announced 30 July 2026 date and added a matching, explicitly non-countdown Doomsday Clock card (85 seconds to midnight, 27 January 2026).
- Added a server-side household gross-income benchmark for singles, couples and families with one to three children using one combined annual household figure.
- Extended the Germany Dossier with the interactive “Deutschland 2036” three-scenario simulation, six macro index bands, eight sensitivity controls and four household perspectives.
- Added a visible source/assumption matrix, robust cross-scenario measures, an HTTP-denied model data include, pure-function model tests and `docs/germany_2036_scenario_method.md`.
- Added an analysis of German real average wages and an OECD PPP wage-level comparison, initially behind a PHP session gate and subsequently released through the public Germany Dossier.
- Added a reproducible OECD wage fetcher, HTTP-denied server-side data includes, a password configuration template, and targeted boundary/auth tests.
- Added methodology, access setup, limitations, and upload instructions in `docs/real_wages_analysis.md`.
- Added Fox Project Framework v2.0.0 anchors: PROJECT_MASTER.md and standards/ baseline.
- Added framework governance files: TODO.md, .env.example and LICENSE.
- Added machine-readable compliance artifacts and Apache shared hosting profile.
- Added deployment transition script: scripts/prepare_deployment.py.
- Added deployment migration runbook: docs/deployment_runbook.md.
- Added deployment cutover plan with criteria and rollback: docs/deployment_cutover_plan.md.
- Added deployment parity report for mirrored cycle validation: docs/deployment_parity_2026-06-14.md.
- Added deployment parity report for mirrored cycle 2 validation: docs/deployment_parity_2026-06-14_cycle2.md.
- Added probation-cycle execution checklist for primary deployment switch: docs/deployment_probation_cycle_checklist.md.
- Added local probation evidence report for primary deployment cycle: docs/deployment_probation_cycle_2026-06-14.md.
- Added compliance audit artifact: docs/compliance_report_2026-06-13.json.
- Added UN Security Council permanent members as a World map country grouping.
- Added structure harmonization notes that distinguish FPF target deployment paths from existing legacy fallback folders.
- Documented existing-project protection for productive root HTML, `scripts/`, `data/` and `images/` paths.

### Changed
- Rewrote the German energy-reform chapter a second time in plain language, expanding compressed administrative phrases into complete explanations of renewable priority areas, environmental review, local participation, grid planning, flexible consumption and fusion research limits.
- Re-edited the complete German Reform Agenda as independent B2-level editorial copy instead of sentence-by-sentence translation: replaced opaque terms such as “employer pathways”, “project pipelines” and “continuity goals” with concrete explanations of actors, instruments, implementation and effects.
- Replaced the opaque “3+ adults” income-list labels with understandable “other household” labels, added EU-SILC child definitions and concrete examples, widened the form controls, and added option/select tooltips plus a permanently visible explanation for the selected household type.
- Replaced the real-wage chart's descriptive closing sentence with a substantive bilingual interpretation connecting long-run purchasing-power growth, near-stagnation since 2019, Germany's OECD average-wage rank and the distinction between a high national level and uneven household experience.
- Made the Germany Dossier publicly accessible without a login while retaining the complete session-authentication workflow behind the disabled `RC_DOSSIER_ACCESS_PROTECTION` feature flag for possible future modules.
- Eliminated the mixed German/English initial render by applying the curated UI dictionary server-side to visible untagged text nodes, while preserving bilingual spans, official source titles and embedded JSON; the browser module remains responsible for route switching and asynchronously inserted interface text.
- Replaced the income ladder's misleading EVS household-size family labels with six official Destatis EU-SILC 2025 household types. The two-adult/no-child option is shown as “DINKs*” with an explicit warning that the source does not prove two earners.
- Clarified the international wage map with an explicit indicator/unit/baseline/exclusions box, a descriptive title, wage-specific legend labels, clearer country statistics and fully localized popup fields.
- Reworked the Reform Agenda energy chapter after source review: replaced France/Sweden nuclear power as the apparent best-practice case with Denmark and Portugal's renewable-system experience, made reduced exposure to authoritarian fossil suppliers explicit, documented nuclear cost/time/waste/acceptance concerns and treated fusion as post-2040 research rather than 2036 supply.
- Kept all Reform Agenda navigation number markers perfectly circular by preventing flex compression beside longer chapter titles.
- Added British and German flag symbols to both Germany Dossier language controls for faster visual recognition.
- Expanded the entire Germany Dossier into an editorial English/German edition: all four files now use dedicated German data, localized interactive results and B2-level interface copy; the security file also receives a clearer English B2 copy.
- Expanded all eleven Reform Agenda chapters with fuller problem analysis, a 2036 outlook, detailed country-case implementation and results, Germany transfer notes and practical prerequisites; repaired the reform header styling that inherited the global site-header layout and made text unreadable.
- Marked `germany-dossier.php` as an intentional Google Translate exception and added the productive bilingual language module to deployment packaging.
- Converted the three Germany Dossier index cards into an accessible tabbed frame: one dossier file is visible at a time, card changes do not scroll the page, and direct links to nested sections still activate the correct file.
- Renamed the main route from `analysis-real-wages.php` to `germany-dossier.php` so the filename reflects its broader prosperity, scenarios and security scope.
- Added “soldiers are murderers” to the war stress test's serious objections, distinguishing Tucholsky's anti-war warning and protected expression from legal murder, while confronting soldiers' exposure to killing, death, conscience and individual responsibility without romanticising armed forces.
- Replaced the dossier page's flat Germany/Europe/module link row with three dossier-style index cards; grouped the Income Ladder into the prosperity analysis and removed the insufficiently modelled Europe 2036 excursion.
- Expanded the “better red than dead” objection with the asymmetry between rights protected by a democracy and potential coercive service under authoritarian control, using current EUAA and UN evidence while marking the Germany extrapolation as a risk rather than a forecast.
- Made the scenario analysis's normative security position explicit: lawful democratic self-defence may require credible military capability; trade remains useful but “change through trade” is insufficient as a security doctrine; renewable energy, grids, storage and efficiency are presented jointly as security, affordability and environmental policy.
- Clarified that the PPP ranking compares equally weighted countries rather than people or households; replaced the ambiguous “position in distribution” label, made “Adaptation under pressure” the visibly first baseline scenario, added an opening narrative to every Germany 2036 scenario and extended the page jump navigation to all major analysis modules.
- Replaced the clipped circular household marker in the income ladder with a high-contrast, fully labelled pill marker.
- Promoted the Earth Overshoot Day day count to the same large, bold visual hierarchy as the Doomsday Clock status.
- Replaced separate earner and optional household-net fields with one total annual household-gross input; the ladder now shows transparent distance from the official EVS household-size average and no longer claims unsupported family-type percentiles.
- Reframed the downside scenario so democratic backsliding and populist-authoritarian government reinforce economic, European, security and social risks rather than forming an unrelated fourth scenario.
- Converted the dossier page's primary interface and core scenario narratives to English.
- Reframed the dossier page around prosperity, purchasing power and 2036 scenarios; added a global World Bank GDP-per-capita PPP distribution context using the existing project KPI.
- Added annual-change bars to the real-wage chart, an explicit explanation of the 34-country OECD coverage and citizen action cards for resilience, skills, energy and democratic implementation.
- Added “Germany Dossier” to the main menu while retaining `noindex` and sitemap exclusion and keeping the existing general “Analysis” destination distinct.
- Extended deployment packaging for the Germany 2036 scenario browser module and server-side data include.
- Split the wage analysis sources: Destatis real-wage index for Germany's time series, OECD constant-PPP average wages for the international level map.
- Extended deployment packaging for the dossier and documented its structure and security behavior.
- Updated AGENTS.md with controlled deployment bundle generation command.
- Extended SECURITY.md to include FPF 2.0 minimum lifecycle sections.
- Hardened HTTP delivery with HSTS, a restrictive CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, and Permissions-Policy headers.
- Removed inline script allowance from CSP and set Referrer-Policy to strict-origin-when-cross-origin for Mozilla Observatory compliance.
- Documented controlled migration path from deployment/full_deployment and deployment/delta_deployment to build/deployment/full and build/deployment/delta.
- Hardened deployment packaging selector to allowlist-only productive artifacts and robust Windows cleanup behavior.
- Updated compliance report findings and score after validated packaging run.
- Activated build/deployment as primary handover command, keeping legacy mirror as fallback mode.
- Set `index.html` language metadata to `en-US` to match the page's primary language.
- Removed the Apache JS challenge gate so search bots, audits, and assistive technology can reach real HTML pages without JavaScript verification.
- Kept trusted crawler and `webcheck-bot` detection markers in `.htaccess` for audit-friendly future rewrite handling.
- Promoted the countries dashboard to the canonical homepage at `/` and kept `countries.html` as a backward-compatible redirect.
- Updated sitemap, canonical URLs, OpenGraph/Twitter URLs, manifest start URL, and navigation to use the canonical production domain and homepage.
- Confirmed security headers remain active without blocking crawlers, audits, or non-JavaScript accessibility checks.
- Updated deployment packaging to include only productive frontend JavaScript files from `scripts/`.
- Updated the NATO country grouping to include Sweden.

### Fixed
- Restored the standard floating scroll-to-top button on the public Germany Dossier page.
- Replaced the dossier language toggle's Unicode flag emoji, which some Windows fonts rendered as separate country-code letters, with reliable British and German SVG flags.
- Fixed the Germany-at-War closing explanation inheriting white global-footer text on its pale-green background; all closing copy now uses explicit high-contrast dark colours.
- Corrected the Germany-at-War source link for Carlo Masala's *Wenn Russland gewinnt* to the verified C.H.Beck book page and added its ISBN for unambiguous identification.
- Fixed the prosperity dossier heading inheriting the global site-header layout and white text, restoring dark readable copy on the light cluster background.
- Fixed the household selector passing a DOM event into the scenario model, which caused repeated `sensitivity.income` console errors.
- Fixed prepare_deployment.py syntax and cleanup robustness issues that blocked packaging runs.
- Added accessible labels for homepage comparison selectors.



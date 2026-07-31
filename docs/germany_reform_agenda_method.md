# Germany 2036 Reform Agenda — method

## Purpose

The fourth public Germany Dossier file complements the descriptive 2036
scenarios with a non-partisan comparative-policy question: which mechanisms
used in democratic industrialised countries could improve Germany's prospects
by 2036?

It is not a manifesto, party comparison or claim that a foreign system can be
copied. Each chapter separates Germany's diagnosis, international examples,
possible options, opportunities, risks and an editorial RealityCheck conclusion.

## Bilingual editorial model

`germany-dossier.php` is an intentional exception to the site's optional Google
Translate workflow. English remains the default. German is selected with the
prominent EN/DE control and stored locally in the browser. Google Translate is
disabled for this route with `translate="no"` and the `notranslate` marker. The
selected language is also carried by `?lang=de`, so PHP can load the matching
editorial data before any browser script runs.

The reform agenda stores English and German copy side by side in
`analysis-private/germany-reform-agenda.php` and the expanded analysis in
`analysis-private/germany-reform-agenda-depth.php`. Every chapter adds two-part
problem and Germany analyses, a 2036 outlook, implementation and result notes
for each country case, transfer limits and practical prerequisites. Both
language versions target clear B2 language. The German text is editorial copy,
not an automated translation. This is important for legal distinctions,
scenario uncertainty and policy trade-offs.

## Compass

Every chapter uses the same six editorial dimensions: expected effect by 2036,
time to effect, investment need, political feasibility, international evidence
and long-term sustainability.

Scores run from 1 (low/short) to 5 (high/long). A high value is not always
"better": for time and investment it means longer or more resource-intensive.
The scores are transparent RealityCheck judgements, not source indices,
probabilities or forecasts.

## Evidence and maintenance

Priority is given to OECD, EU, IEA and NATO material. Sources support mechanisms
and starting conditions; they do not prove transferability. Review the file at
least annually and after major German legislation or new comparative evidence.

The energy chapter treats a complete renewable system—not one generation
technology—as the transferable reform mechanism. Country cases must cover
generation, grids, flexibility, import exposure, affordability and ecological
limits together. Fusion remains research policy until an official prototype has
demonstrated an electricity-system contribution; it is not counted as available
capacity in the 2036 assessment.

Validation:

- `php -l germany-dossier.php`
- `php -l analysis-private/germany-reform-agenda.php`
- `php -l analysis-private/germany-reform-agenda-depth.php`
- `node --check scripts/page_germany_dossier_i18n.js`
- `node tests/germany_dossier_tabs.test.js`
- `php -d zend.assertions=1 -d assert.exception=1 tests/germany_reform_agenda_data_test.php`
- `php -d zend.assertions=1 -d assert.exception=1 tests/germany_dossier_bilingual_data_test.php`

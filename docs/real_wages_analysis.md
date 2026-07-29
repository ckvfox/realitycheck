# Real-wage analysis: data and implementation note

## Pre-implementation data decision

RealityCheck did not contain a wage KPI suitable for either requested wage
view. The existing inflation series cannot be combined with a nominal income
series that is not present. `purchasing_power_parity` is GDP per capita at
current PPP, not a wage measure, so it is never used as a wage proxy. It is now
shown separately as a broad global economic-level context.

The analysis deliberately uses three distinct lenses. The German time series is the
official Destatis real-wage index. The international level comparison uses the
OECD **Average annual wages** dataset
(`OECD.ELS.SAE:DSD_EARNINGS@AV_AN_WAGE(1.0)`). The existing World Bank
GDP-per-capita PPP KPI provides a separate near-global distribution context.

| Use | Selection |
| --- | --- |
| Germany time series | Destatis Reallohnindex, table `62361-0020` |
| Germany unit | Index, 2025 = 100 |
| Germany source | [Destatis GENESIS: Reallohnindex, Deutschland, Jahre](https://genesis.destatis.de/datenbank/online/statistic/62361/table/62361-0020) |
| Germany coverage | 2007–2025 |
| International level comparison | OECD average annual wage per full-time-equivalent dependent employee, same year for every country |
| International unit | 2025 constant US dollars, PPP converted |
| International source | [OECD Data Explorer: Average annual wages](https://data-explorer.oecd.org/vis?bp=true&df%5Bag%5D=OECD.ELS.SAE&df%5Bds%5D=dsDisseminateFinalDMZ&df%5Bid%5D=DSD_EARNINGS%40AV_AN_WAGE&df%5Bvs%5D=1.0&dq=..USD_PPP..Q..&pd=1990%2C&to%5BTIME_PERIOD%5D=false) |
| Map reference year | 2025 |
| Countries with a 2025 value | 34 |
| Dataset price base | 2025 |
| Broad world context | World Bank GDP per capita, PPP (current international dollars) |
| World-context coverage | Latest year with a German value and at least 100 countries; currently 2024 with 179 countries |

### Reference-year rule

The generator examines the most recent ten years and selects the newest year
that has a German value and covers both at least 30 mapped countries and at
least 85% of the maximum country count in that window. Coverage peaks at 38;
2025 has 34 countries (89.5%), so 2025 qualifies. There is no fallback to an
older observation for an individual country.

### Interpretation and limitations

The Destatis index rises from 88.8 to 100.0, or 12.6%, between 2007 and 2025.
The five-year change from 2020 is +0.8%, and the ten-year change from 2015 is
+4.9%. The strongest annual index rise is 2024 (+2.9%); the strongest fall is
2022 (-4.1%). This supports the narrower conclusion that real wage purchasing
power is higher than in 2007, but also shows a long recent stagnation and a
substantial inflation-related setback. It does not support a blanket claim
that every person is continuously becoming poorer or better off.

Destatis changed from the quarterly earnings survey to the earnings survey in
2022. The linked series is calculated back where possible, but the 2021/2022
transition remains methodically restricted. In the 2025 map, 24
of 34 comparable countries are below Germany by more than 5%, five (including
Germany) are within the ±5% band, and five are above it. These results describe
the separate OECD level measure, not every individual's living standard.

The indicator is an average, not a median or distribution. It covers dependent
employees in full-time equivalents and does not directly model wealth, housing
costs, taxes, social contributions, household size, hours distribution or
differences between population groups. The international map covers the OECD
dataset's participating economies, not the entire world. Grey countries mean
"no comparable value", never "below Germany".

## Privacy and access design

`germany-dossier.php` is currently public and does not start an authentication
session. The generated data and dormant authentication library remain below
`analysis-private/`; its `.htaccess` denies direct HTTP access while PHP can
still load the includes server-side. The page remains `noindex` and uses
`no-store` response headers.

The previous session gate is intentionally retained for later private modules.
Set `RC_DOSSIER_ACCESS_PROTECTION` to `true` only when a password-hash
configuration has been prepared and the login flow has been retested. With the
flag set to `false`, no password configuration is read and no login or logout
interface is rendered.

The preferred password-hash location is outside the web root at
`../private/realitycheck-real-wages-auth.php`. For hosts where that is not
available, `analysis-private/real-wages-auth.php` is supported and protected by
the directory deny rule. The local fallback file is gitignored. An environment
variable named `REAL_WAGES_PASSWORD_HASH` is supported as a third option.

An unknown URL is not a security control. Protection is provided by the PHP
session gate; robots directives are defense in depth only.

## Optional future password setup

1. Copy `analysis-private/real-wages-auth.example.php` to one of the supported
   runtime paths above.
2. Generate a hash with `php -r "echo password_hash('YOUR PASSWORD', PASSWORD_DEFAULT), PHP_EOL;"`
   on a trusted machine. Do not put the plain password in a file or command
   history on shared systems.
3. Replace only the `password_hash` placeholder in the non-versioned runtime
   file.
4. Change `RC_DOSSIER_ACCESS_PROTECTION` to `true` and run the authentication
   tests before deployment.
5. Upload the productive files listed in the deployment section below.

The session cookie is HttpOnly, SameSite=Strict and Secure on HTTPS. Sessions
expire after 30 minutes of inactivity. Five failed attempts lock that session
for five minutes, and each failed verification has an additional delay.
Responses use `no-store`, `noindex`, `nofollow`, `noarchive` and an
`X-Robots-Tag` header.

## Refreshing the data

Run `python scripts/fetch_real_wages_analysis.py` from the repository root. The
script downloads the official OECD SDMX CSV, applies the existing
`country_mappings.json`, re-evaluates the coverage rule and combines it with
the normalized Destatis snapshot in
`scripts/source_raw/destatis_reallohnindex_62361-0020.csv`.

To update the German series, download table `62361-0020` as a Flat-File CSV
from GENESIS, verify the base year and method notes, and update the normalized
snapshot. Automated GENESIS POST requests require a free API token since July
2025; no token is stored or required by the repository's default refresh path.

## Production upload set

- `germany-dossier.php`
- `analysis-private/.htaccess`
- `analysis-private/real-wages-auth-lib.php`
- `analysis-private/real-wages-data.php`
- `analysis-private/germany-2036-scenarios.php`
- `analysis-private/germany-war-stress-test.php`
- `scripts/page_germany_2036_scenarios.js`
- `scripts/page_germany_war_stress_test.js`
- `scripts/page_real_wages_analysis.js`
- `style.css`

Upload a separately configured `realitycheck-real-wages-auth.php` outside the
web root if the hosting account permits it. Otherwise upload the untracked
`analysis-private/real-wages-auth.php` after the deny rule is in place. Never
upload the example as the active config and never commit the runtime config.

## Verification on 2026-07-25

Passed automated and local HTTP checks:

- PHP syntax for the page, authentication library, example config and data
  include; JavaScript syntax; Python compilation
- public English and German routes contain the complete analysis without a
  login form or session cookie
- the dormant authentication helpers still pass lock, expiry and CSRF tests;
  direct data includes remain HTTP-denied on Apache
- idle expiry and CSRF helpers
- missing German value, country without a value, malformed/empty payload, and
  the exact inclusive 95% and 105% comparison boundaries
- robots metadata and `X-Robots-Tag`, no-store caching, frame denial
- existing homepage HTTP response; the public dossier remains absent from the
  sitemap because its robots policy is still `noindex`
- source metadata distinguishes the Destatis index from the OECD absolute PPP
  wage measure
- full package contains the protected server includes; example/runtime
  authentication config is excluded

The code contains responsive breakpoints plus explicit Chart.js resize and
Leaflet `invalidateSize()` handling. A visual desktop/tablet/mobile pass and a
browser-console inspection remain operationally pending because the in-app
browser was unavailable in the implementation session. Perform that final
visual smoke test before production upload.

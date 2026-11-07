# Big Mac Index, July 2026

Source: The Economist, [Big Mac data, observation date 2026-07-01](https://github.com/TheEconomist/big-mac-data/blob/0d9710454755a71d7f0c03e662e580b271be456d/output-data/big-mac-full-index.csv), [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). The Economist's [licensing notice](https://github.com/TheEconomist/big-mac-data/blob/0d9710454755a71d7f0c03e662e580b271be456d/README.md#licence) distinguishes Economist-generated data from software and third-party materials.

RealityCheck filters the source to the July observation date and imports only `dollar_price`, the price of one burger in USD. The January 2026 edition is outside the scope of this annual snapshot. Match `iso_a3` exactly against `data/meta/countries.json`, then use its canonical country name and ISO2 code. Append the observations to the existing annual CSV. Preserve the source rows through 2025, including rows excluded by the established country adapter.

| Economist code | Price in USD | Country view |
| --- | ---: | --- |
| EUZ | 7.08 | Euro area aggregate. No German or other national observation is derived from it. |
| HKG | 3.25 | Hong Kong market. The existing country registry excludes it. No value is merged into China. |

The country view takes 52 of the 54 July observations. Historical Germany observations remain available through 2022. The published series contains two existing UAE values for 2018 because separate legacy source names resolve to the same country. This import preserves both and requires one observation per country for 2026.

The regular fetch pipeline now checks the official Economist CSV for new July editions. It preserves existing published values, requires contiguous new years and retains all markets from the preceding edition. Invalid or incomplete releases leave the published data unchanged. The fetch status records the latest imported July date and the source URL.

The Economist reports a euro-area average. It is not a uniform retail price
and cannot be expanded into national observations. The processed index export filters out national euro-area series. The Economist input CSV still contains individual prices, including Germany, Austria and Italy in July 2026. RealityCheck supplements the processed export from July 2023 onward with national EUR observations from that source CSV. It computes USD prices as local_price / dollar_ex, joins on ISO3, and preserves all existing country-year values. This adds 69 observations, including 18 for July 2026.

---
name: Data Issue
about: Report problems with KPI data, country mappings, or data sources
title: '[DATA] '
labels: ['data', 'bug']
assignees: ''
---

## 📊 Data Issue Description
**Clear description of the data problem**

## 🗂️ Affected Data
**Which dataset(s) are affected?**
- **KPI**: [e.g. GDP per capita, Fertility rate, CO2 emissions]
- **Country/Countries**: [e.g. Germany, All countries, Specific region]
- **Year Range**: [e.g. 2020-2023, Latest year only]
- **Data File**: [e.g. gdp_per_capita_current_us.json]

## 🎯 Issue Type
**Select the type of data issue:**
- [ ] Missing data (country/year should have data but doesn't)
- [ ] Incorrect values (data appears wrong)
- [ ] Country name mapping issue
- [ ] Data source problem
- [ ] Outdated information
- [ ] Data format/structure issue
- [ ] Unit or scaling problem

## 🔍 Specific Problem
**Detailed description of what's wrong**

**Expected Value**: [if known]
**Actual Value**: [what's currently shown]
**Source Reference**: [link to authoritative source if available]

## 📈 Data Source Information
- **Current Source**: [e.g. World Bank API, Our World in Data, Manual CSV]
- **Source Code**: [e.g. SP.POP.TOTL for World Bank indicators]
- **Alternative Sources**: [if you know of better sources]

## 🌍 Country Mapping Issue (if applicable)
**For country name mapping problems**
- **Source Country Name**: [how the country appears in source data]
- **Expected Canonical Name**: [how it should map to countries.json]
- **Current Mapping**: [how it's currently mapped, if at all]

## 🔧 Data Validation
**Have you verified this issue?**
- [ ] Checked against original data source
- [ ] Compared with other reliable sources
- [ ] Verified across multiple years/countries
- [ ] Checked data in both web interface and raw JSON file

## 📸 Evidence
**Screenshots, links, or references that support your report**

## 🔄 Data Refresh
**When was this data last updated?**
- Check `fetch_status.json` for last update timestamp
- **Last Fetch**: [if known]

## 📋 Additional Context
**Any other relevant information about this data issue**

## 🏷️ Severity
- [ ] Critical (major KPI completely broken)
- [ ] High (significant country/year missing)
- [ ] Medium (minor data inconsistency)
- [ ] Low (cosmetic or edge case)
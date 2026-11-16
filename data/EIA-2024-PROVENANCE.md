# EIA geocoded ≥1 GW facilities — historical 2024 batch

Source material:

1. **Primary capacity/geography:** U.S. Energy Information Administration (EIA), Inventory of Operable Generators, Forms EIA-860/860M, December 2024 snapshot, via EIA API v2 \`electricity/operating-generator-capacity\`.
   https://www.eia.gov/opendata/browser/electricity/operating-generator-capacity/
2. **Primary net energy output:** EIA, Form EIA-923, calendar 2024 plant-level net generation, API v2 \`electricity/facility-fuel\`.
   https://www.eia.gov/opendata/browser/electricity/facility-fuel/
3. **Auditable machine-readable extraction:** https://github.com/employamericanicholas/50-states-of-electricity/tree/main/data/state
   Methodology: https://github.com/employamericanicholas/50-states-of-electricity/blob/main/SOURCES.md

The extraction, built in August 2026, associates each power plant's official EIA plant ID with its latitude, longitude, operable nameplate capacity in **December 2024**, and net generation in **calendar 2024**. Data are historical; EIA has since released finalized 2025 survey data and monthly preliminary 2026 inventories. Treat the 2024 snapshot as independently traceable evidence of past operation and plant size, **not** evidence of current 2026 operation or capacity.

## Admission rules

- One physical facility per distinct **EIA plant ID**; deduplicate generators to plant level.
- Recorded **operable nameplate capacity ≥ 1,000 MW** in the 2024-12 snapshot.
- Positive reported **2024 net generation > 0 MWh**, corroborating plant operation during that year.
- Finite, explicitly recorded latitude and longitude within valid geographic ranges.
- The original EIA plant name/state and capacity value remain unchanged in imported data.
- Never promote development plans, postponed/retired-only units, aggregated utility portfolios, or facilities with missing locations to an operating site.
- EIA-860 "operable" can include standby, backup, or out-of-service generators. No assumption of 2026 operation is made.
- Nameplate MW is not measured MW, and historical MWh must not be confused with power capacity.
- Facility coordinates represent reported site locations rather than exact surveyed boundaries.

## Reconciliation

Seven read-only regional JSON files: \`data/eia2024-1gw-01.json\` through \`data/eia2024-1gw-07.json\`.

- **302** EIA source records with ≥ 1 GW operable nameplate and positive 2024 MWh, each with an EIA ID and coordinates.
- **22** overlap with the existing 23 manually curated operating plant entries based on plant name, state, coordinates and source identity; these appear only once in the combined map, which favors the curated record.
- **280 additional EIA facilities** plus the original 23 curated = **303 unique map entries**.
- Original \`data/operating-1gw.json\`, state rankings and national project records are kept unchanged.

The standalone EIA historical view retains all **302** source rows to support auditing. A site present in both catalogs is not double-counted in the default combined map. Map markers are approximate; click a record for source links and reporting period.

## Future additions

Before marking a record "verified as operating in 2026", reconcile its EIA plant ID and capacity against the latest **EIA-860 final 2025** and **EIA-860M 2026 monthly** releases; verify cancellations, retirements and capacity changes. New 1 GW+ data-center campuses need separate primary developer or utility siting evidence and must stay distinct from generation facilities and from proposed electrical demand.

This file documents the source and admission method; it is not a claim of current-day verification. EIA primary data are public-domain U.S. Government data. The GitHub extraction is a transformed secondary presentation of those primary sources.

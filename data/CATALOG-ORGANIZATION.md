# EnergyMap unified catalog — November 15, 2026

## Canonical identities and membership

All lists derive from one shared read-only registry. The model preserves the original JSON research snapshots and reconciles identities in memory; it never changes archived source figures.

| View | Sites | Membership |
|---|---:|---|
| All sites | 459 | 303 power generating plants plus 156 campus project profiles |
| All ≥1 GW | 373 | 303 power plants plus 70 proposed campus profiles with published figures ≥1,000 MW |
| Power plants | 303 | 23 curated sites and 280 new EIA records (22 EIA overlaps suppressed) |
| EIA plants (2024) | 302 | Historical source list, including 22 curator overlaps for auditability |
| Curated plants | 23 | Individually curated operating facilities |
| Data centers | 156 | Every state ranking research profile (including <1GW and unknown MW) |
| Data centers ≥1 GW | 70 | Campus profiles with published capacity at least 1,000 MW |
| State rankings | 459 | All 303 generating plants and 156 campus projects, calculated within each of 50 states |
| National top 25 | 25 | Computed largest 25 campus projects by reported MW, from the 156 canonical campus profiles |

Original state source records = 156, original national records = 10, but **all ten national projects are the same physical developments already appearing in the state profile**. National/source and state/source remain separate *observations* attached to the same canonical identity.

## Capacity reconciliation

The master list adopts the national ranking's later published figure for an overlapping project, retains its original state capacity and both source links, and flags the source metric when there is a conflict.

- E2B4 Roswell Information Park: 6,500 MW *planned net onsite generation* versus 4,960 MW *planned critical IT load*, per developer: https://e2b4.com/investors/
- Homer City: latest developer planned gas generation of 4,400 MW versus older 4,500 MW state-profile estimate: https://www.homercityredevelopment.com/project-overview

All other unpublished/unclear campus metrics are labeled as mixed project-scale claims, not actual delivered power. No comparison of generation, data-center IT load, power requests or projected fully built campuses should be treated as scientifically uniform.

## Sorting and categories

Capacity is numeric, descending by default. Clicking the Capacity MW, Project/plant, State, Category or Rank header sorts by the underlying field; clicking the same heading reverses direction. Missing numerical values remain last in both directions. **State rankings** uses all 459 canonical sites, not the 156 archived campus-only state rankings. The computed **State #** is assigned within each state (ties receive the same rank, e.g. 1, 1, 3) and absent MW yields an unranked row. **National top 25** retains the original national project's published Top 10 rank as metadata and independently calculates positions 1–25 among campus proposals; equal reported MW at the cutoff is tie-broken by case-insensitive project name to keep exactly 25 entries. Switching dataset resets stale state and category filters to avoid accidentally hiding facilities.

State filter has All states and all 50 states. Category distinguishes Power generation from Data centers / campuses. Missing coordinates leave a project unplotted, but do not remove it from lists.

## Ranking scope and original editorial records

The originally published national Top 10 remains **10 source records** stored unchanged in the original national JSON. The new Top 25 is a *computed analytical view*, not 15 newly researched or independently verified national projects. Top 25 intentionally keeps the existing national ranking's data-center/energy-campus category. The state rankings intentionally include all categories.

State rank fields are separate from original published state article ranks; both are visible in the selected record's details. A published MW value may represent nameplate generation, planned generation, proposed IT load, a power request, or a proposed full-campus buildout. **Ranking by those MW numbers does not make the projects equivalent in actual energized power.**

## Verification constraints

- EIA records use December 2024 operable nameplate capacity ≥1,000 MW, positive calendar-2024 net generation and reported location. They do **not** certify operation in November 2026. Original methodology: EIA-2024-PROVENANCE.md.
- Original 23 curated generating plants retain their separate operator-reported capacity and source links.
- The 156 2026 editorial profiles include development proposals, permitted concepts and different capacity bases; do not label all as operating or as independently verified commissioned projects.
- The original editorial project records currently have no reliable project lat/lon fields. Do not fabricate map pins.
- MW is power capacity or load, while MWh is energy over time.

Catalog unit tests check all 459 state site memberships, 50 state rank lists, the 25 calculated national selections, the ten published national aliases, 4,400 versus 4,500 MW, 6,500 versus 4,960 MW, and numeric sorting. GUI smoke tests check state/category filters, full datasets and column clicking.

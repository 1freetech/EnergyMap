# Map locality reference layer — provenance and limitations

**Layer:** data/project-localities-01.json through data/project-localities-07.json.

**Derived geographic data license:** Open Database License (ODbL) 1.0.
- Source geographic database: [world-countries-cities-db](https://github.com/srestre/world-countries-cities-db), by srestre, itself derived from dr5hn/countries-states-cities-database, under ODbL 1.0.
- License and required attribution: [source repository LICENSE](https://github.com/srestre/world-countries-cities-db/blob/main/LICENSE); [ODbL full text](https://opendatacommons.org/licenses/odbl/1-0/).
- Each record retains the source state-list URL and its exact location-reference place name. The adapted locality coordinate dataset is offered under ODbL 1.0.

**Method:** The existing October 2026 editorial research profiles contain project names and descriptions identifying nearby communities. City names were matched in the same state to the geographic reference database. Candidates resembling a county, parish, township, unrelated brand or a similarly named town were reviewed and excluded. For example Project Matador is referenced near Amarillo, Texas, not the town of Matador; Golden Valley in Kern County was not plotted at an unrelated place named Kern. These reference points **do not represent surveyed parcel positions or operational plant equipment**.

**Coverage:** 116 of the 156 canonical campus project profiles have approximate reference places (their original research records retain null coordinates). 40 unmatched profiles stay explicitly unlocated. They are shown on the map as purple **state aggregate** markers with the unlocated count—never as site points or invented site coordinates. The 303 distinct generating facilities retain their existing recorded geographic positions. No project is silently dropped from a data view due to missing lat/lon.

**UI semantics:**
- Filled teal circles: previously sourced power generating facility coordinates.
- Hollow orange circles: reference coordinates for a named place near or associated with a campus project; multiple projects in one town may be fanned out by a few display pixels for visibility. These offsets are not geographic coordinates.
- Purple square with a number: count of currently filtered, unlocated project entries in that state; derived from the state boundary map for aggregate display, not a source-provided site location.
- On an orthographic globe only points on the visible hemisphere appear; rotate the globe to bring other locations into view.

Every category, dataset, state and search filter generates markers from the same filtered canonical site records. The original state ranking JSON, EIA history and curated operating plant files have not been rewritten.

Source locations can be upgraded to genuine verified site coordinates only with a publicly documented parcel, approved permit map, utility substation/site filing or operator GIS point that unambiguously identifies the development. Current locality reference dots should never be used for parcel, capacity, regulatory or property analysis.

**Important:** Sharing the locality coordinate derivatives requires preservation of ODbL attribution and license. This location overlay may be redistributed independently from the rest of EnergyMap research data under ODbL 1.0.

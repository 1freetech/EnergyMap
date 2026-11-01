# EnergyMap — BitcoinVersus.Tech U.S. Data Center Power Atlas (2026)

An interactive national atlas based on BitcoinVersus.Tech's published state and national project-power rankings.

## What is included

- **50 U.S. state rankings**, three sites per state except the intentionally expanded **Texas Top 7** and **Virginia Top 5**.
- The independently compiled **America Top 10** (these ten have their own entries; some projects appear in both views).
- **166 ranked records** in seven source datasets, each with its original report URL, title, published date, ranked capacity, short briefing, and ranked order.
- A Leaflet / OpenStreetMap map with clustering, interactive dots, hover snapshots, source links, search, state selection, and ranking/development-stage filters.
- **My map**: add, edit, delete, import and export custom sites, including the map point, latitude, longitude, source link, project type, capacity basis, reported MW, optional measured operating production MW, status and a description.
- A **Refresh rankings** button that reloads the published JSON data files while preserving local custom records.
- A **Suggest for public map** link for custom entries: opens a proposed GitHub issue in the source repository. A public contribution is not published until reviewed.

## Running

From the repository root, use any static HTTP server; for example:

```sh
python3 -m http.server 8000
```

Open **http://localhost:8000/**. An HTTP server is required because browsers restrict `fetch()` of JSON files opened directly via `file://`. For production, serve the repository root and its `data/` subfolder from the same HTTPS host. The page uses Leaflet and OpenStreetMap CDN/tile assets; these require network access.

## Adding your own site

1. Choose **+ Add a site**.
2. Click anywhere on the map to place its pin, or enter latitude and longitude manually.
3. Fill in name, state, site type, stage, measured or proposed capacity, capacity basis, and optional operating power (MW). If reporting generated or consumed energy, enter MWh **and** the associated measurement period.
4. Add an explanatory briefing and public source, then choose **Save new site**.
5. Open **My map** to see only your custom sites. Click a purple marker to **Edit** or **Delete** it.
6. **Export my map** saves your custom records as `bitcoinversus-my-energy-map.json`; **Import map** loads that file in another browser or device. An imported record with the same custom ID replaces the earlier personal version.

### Persistence and moderation boundaries

Personal additions are kept in that browser's `localStorage`, **not** automatically published, synchronized across devices, or submitted to the website. The export file is the portable backup. Browser storage can be cleared, private browsing may not retain it, and some privacy settings may block it. The UI warns when saving fails.

If readers want a site visible to everyone, **Suggest for public map** creates a prefilled GitHub issue (a GitHub account may be required). Editors should verify the location, primary source, capacity basis, status and duplicate risk before merging the accepted record into the published dataset.

## Updating editorial rankings

The map fetches these seven version-controlled JSON files:

- `data/states-01.json` — Alabama through Delaware
- `data/states-02.json` — Florida through Kansas
- `data/states-03.json` — Kentucky through Mississippi
- `data/states-04.json` — Missouri through New York
- `data/states-05.json` — North Carolina through South Carolina
- `data/states-06.json` — South Dakota through West Virginia, including Texas and Virginia expanded rankings
- `data/states-07-national.json` — Wisconsin, Wyoming and America Top 10

To update the public map, edit the relevant JSON record or create an editorially reviewed pull request and deploy the merged site version. The **Refresh rankings** control retrieves the latest served JSON without overwriting visitor-created pins. **New WordPress posts do not automatically appear** merely because they were published: the JSON corpus must be refreshed and deployed. Automatic WordPress-to-JSON synchronization is a future integration that requires a verified, reliable WordPress API pipeline.

Test data integrity and personal-map storage logic:

```sh
node tests/validate.mjs
```

## Important data limitations

- **MW is power, MWh/GWh is energy produced or consumed over time**. A full-build planned rating must not be labeled actual operating consumption or production.
- Generation nameplate, planned generation, contracted grid service, gross campus power, critical IT demand, power-storage discharge and modeled IT capacity are **not equivalent measurements**. Readers must consult the linked reporting before comparing.
- Map dots are **approximate named-city/county or state-level locations**, not validated parcel coordinates. Custom dots use user-selected coordinates and are marked unverified.
- The site is an atlas of **data center and related energy developments**, rather than a definitive statistical dataset of actual energy generation by fuel source.
- Canceled, stalled or paused projects remain included if they appeared in the underlying rankings. They should not be represented as operating.

## Files

`index.html`: user interface and in-browser editor. `data/`: editorial records. `tests/validate.mjs`: automated consistency, syntax and personal-map logic checks. All project text is attributed through its original BitcoinVersus.Tech article URL.


## Repository migration

This is the dedicated home for EnergyMap, migrated from the draft [BitcoinVersus.Tech map PR #2](https://github.com/1freetech/Bitcoinversus.tech/pull/2) on November 1, 2026. The original project rankings and article URLs remain as editorial sources; **all new code, contributions, map-data additions and editorial map issues belong in [1freetech/EnergyMap](https://github.com/1freetech/EnergyMap)**.

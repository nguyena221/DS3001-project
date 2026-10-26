# Wikidata trial inspection

Historical inspection before adding official IMDb data. The current source plan
uses IMDb for ratings and core metadata; see README.md. These findings describe
the original Wikidata trial and remain useful for its supplemental fields.

Inspected October 26, 2026. Input: `data/raw/trial/`. Raw files were not changed.
This is a convenience sample for debugging, not a population-quality estimate.

## Collection integrity

- CSV has 19 rows, 19 distinct Wikidata IDs, and 19 distinct IMDb IDs.
- Compared all eight collected metadata fields in every CSV row with the
  non-deprecated known statements in `entities.json`: no discrepancies.
- `Demain est à nous` matched both the 2019 and 2021 selection queries and appears
  once in the CSV. This explains 19 unique movies from 20 candidate slots.
- Original entity responses and per-year query responses are preserved.

## Completeness

| Field | Present | Missing |
|---|---:|---:|
| IMDb ID | 19 | 0 |
| Release date | 19 | 0 |
| Genre | 18 | 1 |
| Runtime | 16 | 3 |
| Language | 15 | 4 |
| Country | 19 | 0 |
| Director | 17 | 2 |
| Budget | 3 | 16 |

IDs and dates were required by selection; their completeness is not evidence of
complete coverage across Wikidata. Missing values remain missing, not zero.

## Dates and eligibility

- Seven movies have multiple release-date statements.
- Seven movies have at least one year-only date; six have no month-precise or
  day-precise date. Their release month must remain missing.
- `Forgotten Christmas` has repeated calendar dates with separate statements;
  preserve qualifiers before deciding whether these are duplicates or releases
  in different places. Multiple statements do not mean duplicate movie rows.
- Both candidates selected by the 2025 query have earlier releases in 2024:
  `The Brutalist` (September 1, 2024) and `Long Distance` (July 12, 2024).
  Candidate query year is therefore not a valid final split assignment.
- Choose and document a canonical release rule, such as earliest known worldwide
  release, before sampling final years and applying chronological splits. Account
  for date precision and festival versus theatrical releases in that decision.

## Numeric and multi-value fields

- All 16 available runtimes use Q7727 (minutes), ranging from 54 to 215. No
  non-positive values were found. This does not independently verify each runtime.
- Budgets use two currencies: Norwegian kroner (Q132643) and US dollars (Q4917).
  Do not compare raw amounts without currency/year handling.
- Six movies have multiple genres, three multiple languages, four multiple
  countries, and one multiple directors. Those lists survived export intact.
- Names for related entities remain Wikidata IDs, so a readable analysis table
  will need label lookup. Do not use IDs as numeric measurements.

## Wikidata page spot checks

Compared saved values with the retrieved Wikidata pages, rather than independently
checking the underlying sources. Live records can change after collection.

| Movie | Saved value | Page comparison |
|---|---|---|
| [Ukraine on Fire](https://www.wikidata.org/wiki/Q1001400) | Runtime 94 minutes | Matches |
| [Furiosa: A Mad Max Saga](https://www.wikidata.org/wiki/Q100361125) | Runtime 148 minutes; budget USD 168 million | Matches |
| [The Brutalist](https://www.wikidata.org/wiki/Q101112656) | Runtime 215 minutes; earliest saved release September 1, 2024 | Matches |

## Rating discovery

The CSV has no rating column. However, the original downloaded entities include
all claims, and five of the 19 movies contain non-deprecated review-score values
under [P444](https://www.wikidata.org/wiki/Property:P444).

| Movie | Providers represented in saved review-score claims |
|---|---|
| American Murder: The Family Next Door | Rotten Tomatoes |
| Freaks Out | Rotten Tomatoes, Metacritic |
| Mothering Sunday | Metacritic, Rotten Tomatoes |
| Furiosa: A Mad Max Saga | Rotten Tomatoes, Letterboxd, Metacritic |
| The Brutalist | Metacritic, Rotten Tomatoes, IMDb, Letterboxd |

Only one movie has a saved IMDb-attributed review score: The Brutalist, 7.3/10,
dated December 22, 2025. This is a dated statement, not a current IMDb feed.
Furiosa's 7.9 is a Rotten Tomatoes average, not IMDb. Percent positive, critic
averages, and audience averages measure different things; rescaling them does
not make them interchangeable targets.

Wikidata might supply a usable target, but sufficient coverage for one consistent
provider, score type, and date policy has not been established. No permission
conclusion about third-party-derived ratings is made by this inspection. Do not
change the research target or assume copying through Wikidata resolves source-use
questions. A separate ratings source may be necessary, but is not yet proven
necessary. No additional ratings were downloaded during this inspection.

## Next steps

1. Decide on a canonical release-date policy before expanding the year-based sample.
2. Audit coverage of one consistent rating target and confirm acceptable use and
   course requirements before large-scale collection.
3. Keep director, genre, runtime, language, and country as candidates. Retain budget
   for inspection, but do not require it based on this sample.
4. Create readable, cleaned trial columns without changing the raw files; preserve
   missing months and multiple categorical values. Then expand the pilot.

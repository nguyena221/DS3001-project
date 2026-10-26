# IMDb-first title-type audit

## Current policy update

IMDb startYear now determines filtering and splits. Rebuilt from saved data:
100 eligible movies (80 train / 10 validation / 10 test); 20 boundary candidates
excluded. Missing Wikidata dates no longer exclude otherwise eligible records.
Wikidata's month is optional and is used only when its selected date agrees with
IMDb's year. 86 of the 100 eligible records have no usable month. Eleven tests
passed. The original date-policy results below are historical, superseded by
this update; no general IMDb-year fallback decision remains pending.


Counted the complete downloaded `title.basics` snapshot on October 26, 2026.
These are title records, not usable final training examples. Year counts use
IMDb `startYear`, not the canonical earliest worldwide release year.

| Actual titleType | IMDb years 2016–2025 | Our policy |
|---|---:|---|
| movie | 199,022 | Include if rated |
| tvMovie | 28,952 | Include if rated |
| short | 497,989 | Exclude |
| tvShort | 2,660 | Exclude |
| video | 109,788 | Exclude; do not relabel |
| tvSpecial | 24,951 | Exclude |
| tvSeries | 113,873 | Exclude |
| tvMiniSeries | 39,634 | Exclude |
| tvEpisode | 3,735,732 | Exclude |
| videoGame | 17,424 | Exclude |

The complete file additionally had one `tvPilot` record outside 2016–2025. No
additional type was treated as a spelling variation of movie. Types and counts
come from this snapshot rather than an assumed fixed category list.

The new IMDb-first sampler selected ten rated movie/tvMovie records per IMDb
year in 2016–2025 plus ten each from 2015 and 2026 to audit boundary differences.
The seeded hash sample does not select by rating value or vote count. It is a
pilot for coverage and collection checks, not an assertion of representativeness.

Wikidata lookup found 52 unambiguous matching entities among the 120 candidates.
Final in-scope counts depend on canonical release dates. No-match records are
retained in the combined table and held out of the eligible table until their
release year can be established under the chosen rule. Missing optional features
do not cause exclusion. The boundary guard is not an exhaustive completeness check.

Local source snapshots, provenance, title-type counts, candidates, and lookup
responses are under `data/raw/imdb_first/`, ignored by Git. Source documentation:
[IMDb noncommercial datasets](https://data.imdb.com/non-commercial-datasets/).
The new workflow commands are in README.md; the original trial remains intact.

## Completed enrichment result

- All 120 candidates matched IMDb ratings, basics, crew, and principals extracts.
- 52 matched one Wikidata entity; 68 had no Wikidata match; none were ambiguous.
- Of those 52 matches, 13 lacked a known non-deprecated Wikidata release date.
- 27 currently satisfy our canonical-year requirement: 23 training-year, two
  validation-year, and two test-year movies.
- 12 have canonical years outside 2016–2025 and are excluded from scope.
- 81 are held for release-year review (68 unmatched plus 13 missing dates), not
  declared permanently unusable. They are logged in the `_excluded.csv` working
  export with a hold reason. No IMDb-year fallback was silently applied.

Outputs: `data/processed/imdb_first_combined.csv`, its `.summary.json`, and the
`_eligible.csv` / `_excluded.csv` exports. All 120 input records and all old trial
files remain available locally. Nine synthetic tests passed, including scope
boundaries, lookup identifier validation, source handling, and correction provenance.
Live checks confirmed unique IDs, expected row/split counts, and Git exclusions.

This pilot identifies our next bottleneck: requiring Wikidata dates loses many
otherwise rated IMDb records. Before scaling, decide whether to retain that
requirement, source additional verified dates, or explicitly revise the policy
to allow IMDb release years when Wikidata dates are missing. Such a fallback
would change the date policy and has not been enabled.

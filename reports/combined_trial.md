# Combined trial result

Completed October 26, 2026. Inputs: original Wikidata trial and matching rows
streamed from the four official IMDb TSV downloads. Local output:
`data/processed/trial_combined.csv`; provenance is in the adjacent `.summary.json`.

- 19 rows and 19 unique IMDb IDs; unmatched rows were retained.
- 18 matched ratings, basics, crew, and principals records.
- 17 movies have principal actor/actress IDs; other principal occupations are
  intentionally not cast features.
- Six movies still lack a usable release month. Earliest recorded Wikidata
  dates continue to determine years and planned splits.
- Four rows require review: one ID absent from all four IMDb files, two records
  whose IMDb title type is not `movie`, and one disagreement between IMDb's
  release year and the earliest recorded Wikidata year. No silent exclusions
  or automatic year overrides were applied.

The table is a joined pilot, not model-ready data. Resolve those review flags,
check source eligibility, handle missing values and categorical encoding, and
decide how budget should be used before expansion. Genuine 2025 first releases
are still needed. Download snapshots reflect current ratings, not release-time
ratings. Vote count is not a pre-release predictor.

Validation: four synthetic unit tests passed, covering missing matches, source
ownership, cast ordering/filtering, nulls, release-year handling, ambiguous IDs,
stream filtering, and reuse of completed extracts. Live output was checked for
unique IDs, match counts, and retained missing months. Git ignore checks confirmed
that raw extracts, derived datasets, provenance files, and TSV exports are ignored.
No data files are currently tracked by Git.

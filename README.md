# Movie rating prediction

School project predicting IMDb ratings from movie characteristics. Scope:
worldwide movies and TV movies with IMDb release years 2016-2025. No models trained yet.

## Quick update for the group

So far, I've set up the repo, tested a small download, and switched to starting
with IMDb so we know the movies have ratings. I then added extra details from
Wikidata, checked the title categories, and separated usable movies from records
that need review. IMDb now supplies the year for our splits, while Wikidata adds optional months
and other details. This is still a pilot, not our final dataset. I've explained each file below so you
don't have to guess what anything does.

## Start here

The current working file is **data/processed/imdb_first_combined_eligible.csv**.
It contains 100 movies that currently meet our type, rating, and date rules.

| File in data/processed/ | Purpose |
|---|---|
| imdb_first_combined_eligible.csv | Current usable pilot: 100 movies |
| imdb_first_combined_excluded.csv | 20 boundary-check candidates outside 2016-2025 |
| imdb_first_combined.csv | All 120 candidates, including unresolved records |
| imdb_first_combined.summary.json | Match counts and planned split totals |

These are pilot data, not a final training dataset. The 100 eligible movies split
into 80 training-year, ten validation-year, and ten testing-year movies.

## Folder and file guide

### Files at the top of the repo

| File | What it does |
|---|---|
| README.md | Start here: project update, file guide, rules, and run instructions. |
| .gitignore | Keeps downloaded data, outputs, secrets, and temporary files out of Git. |
| requirements.txt | Packages for later analysis/modeling; collection currently needs no extra packages. |

### src/ — the Python code

Run the first three scripts in order; the remaining files support those scripts.

| File | What it does |
|---|---|
| collect_data_imdb.py | Downloads/caches IMDb basics and ratings, counts title categories, and selects the pilot candidates. |
| add_wikidata_to_imdb.py | Matches candidates to Wikidata, adds extra fields and IMDb cast/directors, and saves the combined table. |
| filter_movies.py | Applies our movie-type, rating, and date rules; saves eligible records and exclusion/hold reasons. |
| imdb_merge_helpers.py | Helper functions used by add_wikidata_to_imdb.py to read IMDb records and merge sources. The collector also imports shared utilities here. Do not run directly. |
| request_wikidata.py | Helper functions for requesting Wikidata records, waiting/retrying requests, and preserving multiple values. Do not run directly. |
| handle_release_dates.py | Helper functions for interpreting supplemental Wikidata dates without guessing missing parts, and assigning split labels from IMDb years. Do not run directly. |
| release_overrides.json | Approved date corrections with movie IDs, source links, and reasons. |

**What release_overrides.json means:** it is a small correction list, not a
downloaded dataset or a script. It currently contains one verified correction
for The Man with Hare Ears, whose saved Wikidata date was in 2021 but whose
documented festival premiere was October 10, 2020.

| Part of the entry | Meaning |
|---|---|
| Q100145860 | Wikidata ID: identifies exactly which movie this correction belongs to. |
| imdb_id | Its IMDb ID; the code checks this too so the correction cannot silently apply to a different record. |
| release_date | The verified supplemental date in YYYY-MM-DD format: 2020-10-10. |
| reason | Why the downloaded date needs a correction. |
| source_url | The evidence supporting the corrected date. |

The merge helper reads this list automatically. When the movie appears in a
collection, it preserves the original Wikidata date and records the corrected
supplemental date, reason, and source in the combined table. The current IMDb-first
sample may not contain that movie, so the entry can have no effect on that run.
IMDb startYear still controls the final release_year and split. The corrected
date can provide a month only when its year agrees with IMDb; otherwise the month
is withheld. It does not silently override IMDb's year or change the raw download.
Add entries only for verified, documented corrections. An empty object (`{}`)
would mean no approved supplemental corrections.

### data/ — local data, not uploaded to GitHub

This folder is ignored by Git apart from empty-folder placeholders. Teammates
cloning the repo won't receive the downloads; the scripts generate their own
local copies. The tables above explain every file in data/processed/.

**data/raw/imdb_first/** holds downloaded source records and reusable saved
results. These are inputs to our working table, not files to edit manually.

| File or repeated filename pattern | What it does |
|---|---|
| title.basics.tsv.gz | Compressed IMDb catalog: titles, types, years, runtime, and genres. |
| title.ratings.tsv.gz | Compressed IMDb ratings and vote counts. |
| title.principals.tsv.gz | Compressed principal cast/crew file, cached because it is large. |
| title.basics.json | Original basics rows for the selected candidates, plus source metadata. |
| title.ratings.json | Original rating rows for the candidates, plus source metadata. |
| title.crew.json | Original director/writer rows for the candidates, plus source metadata. |
| title.principals.json | Original principal cast/crew rows for the candidates, plus source metadata. |
| title.basics.tsv.provenance.json | Where and when the basics download came from. |
| title.ratings.tsv.provenance.json | Where and when the ratings download came from. |
| title.principals.tsv.provenance.json | Where and when the principals download came from. |
| candidates.csv | The 120 selected IMDb records before Wikidata enrichment. |
| selection_summary.json | Title-type counts, selection settings, seed, and year totals. |
| wikidata_lookup.sparql | The query used to find Wikidata records by IMDb ID. |
| wikidata_lookup.json | Saved query response showing which IMDb IDs matched Wikidata. |
| wikidata_entities/Q<number>.json | One original downloaded Wikidata entity per matching Q-ID; all these files serve the same purpose. |

The crew source was originally streamed, so it has a matching-row JSON extract
but no full compressed download in this snapshot. Future runs may also create
title.crew.tsv.gz and title.crew.tsv.provenance.json: the full crew download and
its source details. Files ending in .part are unfinished downloads/writes, not
usable source data.

**data/archive/** keeps the early trial for reference; it is not the active dataset.

| Archived file or pattern | What it does |
|---|---|
| trial_combined.csv | The original 19-movie trial joined with IMDb. |
| original_trial/movies.csv | Original metadata export for those 19 movies. |
| original_trial/entities.json | Full Wikidata records from that first collection. |
| original_trial/summary.json | First collection settings and missing-value counts. |
| original_trial/query_YEAR.sparql | One saved selection query per year, 2016–2025. |
| original_trial/selection_YEAR.json | The corresponding saved query response for each year. |

### reports/ — findings in plain English

| File | What it does |
|---|---|
| imdb_title_types.md | Actual IMDb category counts, our inclusion decisions, and the latest pilot results. |

### tests/ — checks that the code behaves correctly

These use made-up records, not downloaded IMDb data. Run them with
`.\.venv\Scripts\python.exe -m unittest discover -s tests`.

| File | What it does |
|---|---|
| test_imdb_first.py | Checks repeatable selection priorities, safe ID lookup queries, and release-year eligibility. |
| test_merge_imdb.py | Checks merging, missing matches, cast ordering, caching, TV-movie eligibility, and date corrections. |

### Automatically generated and hidden folders

- .gitkeep in data/raw/ and data/processed/ is an empty placeholder
  so Git retains those folders; it contains no data or code.
- .venv/ contains the local Python environment and is ignored by Git. Its files
  are installed/generated by Python, not project files to edit.
- __pycache__/ and its .pyc files are automatically generated Python caches and
  are ignored by Git; they are not scripts to run or edit.
- .git/ stores Git's version history and settings. Do not edit its internal files.

## Where the information comes from

| Information | Source |
|---|---|
| Rating (target), vote count | IMDb ratings |
| Genre, runtime, title, type | IMDb basics |
| Directors, principal cast | IMDb crew and principals |
| Original spoken language, country, release dates, budget | Wikidata |

We join by IMDb ID. Principal cast is not full cast. Multiple countries, languages,
and genres are preserved. Budget is often missing and currencies are not yet
converted. People and Wikidata categories remain IDs until later preprocessing.

## Our rules

- Keep IMDb types movie and tvMovie with an available IMDb rating.
- Exclude records not matched in IMDb files, records without ratings, and other
  types such as video, shorts, episodes, and series. Video can include actual films;
  excluding that category is a scope choice. Never relabel it to bypass the rule.
- Use IMDb startYear for filtering and splitting. The population is movies with
  IMDb release years 2016-2025, not verified first worldwide releases.
- Wikidata supplies an optional month from its earliest valid recorded date.
  Use that month only when the selected date agrees with IMDb's year; otherwise
  leave it blank and flag the disagreement. Missing months do not exclude movies.
  Both original dates and sourced corrections remain available for inspection.
- Approved sourced corrections live in src/release_overrides.json. The Man with
  Hare Ears uses the October 10, 2020 festival premiere listed by the
  [Czech film archive](https://www.filmovyprehled.cz/en/film/402182/the-man-with-hare-ears).
  Its original Wikidata date and correction provenance remain in the output.
- Train: 2016–2023; validate: 2024; test: 2025. Fit preprocessing on training only.
- Ratings are download snapshots, not ratings at release. Vote count is not a
  pre-release predictor. Current features still need pre-release justification.

## Run the current workflow

Python 3.10 or newer. Current collection uses only the standard library.
If the environment already exists, skip the first command.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe src\collect_data_imdb.py
.\.venv\Scripts\python.exe src\add_wikidata_to_imdb.py
.\.venv\Scripts\python.exe src\filter_movies.py
```

1. collect_data_imdb.py counts every IMDb type and selects ten rated movie/tvMovie
   candidates per year, plus 2015/2026 boundary checks (120 candidates). A seeded
   hash sample avoids selecting by score or popularity; it is not guaranteed
   representative. The boundary check is not an exhaustive coverage guarantee.
2. add_wikidata_to_imdb.py adds Wikidata fields and IMDb cast/crew. Missing or
   ambiguous Wikidata matches remain visible rather than guessed.
3. filter_movies.py creates the eligible table and logs exclusions/holds.

Completed downloads and lookups are cached under data/raw/imdb_first/ and reused.
The large principal-cast compressed file is roughly 750 MiB; initial collection
can take several minutes or longer during service outages. A failed download
restarts that file; completed stages are retained. No API keys are needed.
imdb_merge_helpers.py, request_wikidata.py, and handle_release_dates.py are helper
files imported by the main scripts; they are not commands to run yourself.
The original trial and its combined table are saved under data/archive/ for
reference. They are no longer part of the active workflow.

## What filter_movies.py separates and why

This is a rule check, not missing-value filling or model training. It reads the
combined CSV and writes two views while leaving the combined file unchanged:

- **eligible.csv:** records with an IMDb match, a rating, accepted movie/tvMovie
  type, and IMDb year 2016-2025. This is the working pilot for later preparation.
- **excluded.csv:** records that fail those rules, with an exclusion_reason column
  explaining why. An unresolved year is held for review, not permanently deleted.

For the current pilot, all 120 candidates already have accepted types and ratings.
The script keeps the 100 from 2016-2025 and excludes the 20 old boundary-check
candidates from 2015/2026. Those extra years came from the earlier date-policy
investigation; they are no longer needed under the IMDb-year policy, although
this collector still selects them. They do not enter our working sample.

Missing month, runtime, language, country, budget, director, or cast does not by
itself exclude a record here. We will handle those gaps during preprocessing.
Saving exclusions lets us explain decisions and reconsider them without repeating
collection. Separate files are convenient, not mandatory. They are also **not**
the training/validation/test files: planned_split labels those groups within the
eligible table. Python can select each group later without three more CSVs.

## Next decision

IMDb year now determines scope, leaving 100 eligible pilot movies. Of those,
86 have no usable release month. Keep unknown months missing; later encode month
as a category with an explicit unknown value, or omit it. Do not substitute January
or an average month. Compare validation MAE with and without month before deciding
whether it helps. No month preprocessing or model training is implemented yet.

Next finalize missing-value handling and categorical encoding, expand collection,
and compare a mean baseline, Ridge, and Random Forest using MAE (RMSE optional).
Optional analysis packages are in requirements.txt.
[Title-type audit and pilot findings](reports/imdb_title_types.md)

## GitHub and sources

All data, caches, archives, and derived tables are ignored by Git. Share code and
documentation; clear data-bearing notebook outputs before publishing. Gitignore
cannot remove already committed files. The original-source IMDb downloads are
still prepackaged data; our merging and preprocessing are project work.

- [IMDb datasets and schema](https://data.imdb.com/non-commercial-datasets/)
- [IMDb use conditions](https://help.imdb.com/article/imdb/general-information/can-i-use-imdb-data-in-my-software/G5JTRESSHJBBHTGX)
- [Wikidata CC0 licensing](https://www.wikidata.org/wiki/Wikidata:Licensing)

The group reports pitch approval. Specific group ML-use permission has not been
independently confirmed; keeping data out of Git does not establish permission
for every use. No scraping, TMDB, Kaggle, or Hugging Face data is used.

Information courtesy of IMDb (https://www.imdb.com). Used with permission.

That is IMDb's requested attribution wording, not a claim of a separate agreement.

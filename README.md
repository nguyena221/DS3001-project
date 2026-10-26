# Movie rating prediction

School project predicting IMDb ratings from movie characteristics. Scope:
worldwide movies and TV movies first released in 2016–2025. No models trained yet.

## Start here

The current working file is **data/processed/imdb_first_combined_eligible.csv**.
It contains 27 movies that currently meet our type, rating, and date rules.

| File in data/processed/ | Purpose |
|---|---|
| imdb_first_combined_eligible.csv | Current usable pilot: 27 movies |
| imdb_first_combined_excluded.csv | 81 held for dates and 12 outside our years |
| imdb_first_combined.csv | All 120 candidates, including unresolved records |
| imdb_first_combined.summary.json | Match counts and planned split totals |

These are pilot data, not a final training dataset. The 27 eligible movies split
into 23 training-year, two validation-year, and two testing-year movies.

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
- Use the earliest valid worldwide release recorded in Wikidata, including festival
  premieres. Keep unknown months blank. Unresolved years are held for review;
  IMDb's year is not automatically substituted. Dates outside 2016–2025 are excluded.
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
.\.venv\Scripts\python.exe src\collect_imdb_first.py
.\.venv\Scripts\python.exe src\enrich_imdb_first.py
.\.venv\Scripts\python.exe src\filter_movies.py
```

1. collect_imdb_first.py counts every IMDb type and selects ten rated movie/tvMovie
   candidates per year, plus 2015/2026 boundary checks (120 candidates). A seeded
   hash sample avoids selecting by score or popularity; it is not guaranteed
   representative. The boundary check is not an exhaustive coverage guarantee.
2. enrich_imdb_first.py adds Wikidata fields and IMDb cast/crew. Missing or
   ambiguous Wikidata matches remain visible rather than guessed.
3. filter_movies.py creates the eligible table and logs exclusions/holds.

Completed downloads and lookups are cached under data/raw/imdb_first/ and reused.
The large principal-cast compressed file is roughly 750 MiB; initial collection
can take several minutes or longer during service outages. A failed download
restarts that file; completed stages are retained. No API keys are needed.
Files beginning with an underscore in src/ are internal helpers, not commands.
The original trial and its combined table are saved under data/archive/ for
reference. They are no longer part of the active workflow.

## Next decision

Of 120 rated candidates, 52 matched Wikidata, and 13 of those had no release date.
We need to decide how to handle missing dates before scaling up. No fallback to
IMDb year has been enabled. Then finalize missing-value handling and categorical
encoding, expand collection, and compare a mean baseline, Ridge, and Random Forest
using MAE (RMSE optional). Optional analysis packages are in requirements.txt.
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

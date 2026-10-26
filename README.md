# Movie rating prediction

Predict IMDb audience ratings using characteristics that could reasonably be
known before release. Scope: worldwide movies first released in 2016–2025.
We combine official IMDb downloads with Wikidata metadata, then do our own
merging, cleaning, preprocessing, and modeling.

## Sources and fields

| Field | Source |
|---|---|
| Average rating (target), vote count | IMDb title.ratings |
| Genre, runtime, title, movie type | IMDb title.basics |
| Director IDs | IMDb title.crew |
| Principal cast IDs | Actor/actress entries in IMDb title.principals |
| Original spoken language | Wikidata P364 |
| Country of origin | Wikidata P495 |
| Release dates and canonical year/month | Wikidata P577 |
| Budget, where available | Wikidata P2130 |

Join on IMDb movie ID, not title text. Principal cast is not the full cast.
Related people and Wikidata categories remain IDs; display labels and model
encoding come later. Budgets retain amounts and currencies, without conversion.
The original trial retains Wikidata genre/runtime/director fields for historical
inspection; the combined table uses IMDb for these fields. Incidental Wikidata
review scores are not our chosen target.

## Setup and run

Python 3.10 or newer; current scripts use only the standard library.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe src\clean_release_dates.py
.\.venv\Scripts\python.exe src\merge_imdb.py
```

Use `py` instead of `python` if that is your Windows launcher. Activation is not
required. Later analysis packages are listed in requirements.txt:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

No API key or account is needed for the official IMDb downloads. The merge script
streams four compressed files and saves only matching rows locally. The principals
file can take several minutes or longer: the whole stream must be checked to
preserve all matching cast rows. It prints progress during scans. Completed
source extracts are cached; interrupted sources restart their scan, while completed
extracts are reused when the requested IDs match. To deliberately refresh a source,
remove its local cache JSON first.

Outputs:

- `data/raw/imdb_trial/`: completed IMDb extracts with source URLs, requested IDs,
  collection times, source modification dates, and original matching rows.
- `data/processed/trial_combined.csv`: combined trial, one row per movie.
- `data/processed/trial_combined.summary.json`: match counts and provenance.

The first combined run is complete: 19 rows, 18 rating matches, and four rows
flagged for review. See [combined trial findings](reports/combined_trial.md).

All trial movies are retained, even unmatched records. Review `merge_review` for
missing source records, non-movie title types, or disagreement between IMDb's year
and the canonical Wikidata year. Unknown IMDb values become empty cells/lists.
Multi-values use JSON lists inside CSV cells. Sources update daily and scans can
span updates; this is not a synchronized historical snapshot.

## Existing Wikidata trial

`data/raw/trial/` contains 19 unique movies collected October 26, 2026, requesting
two candidates per year for 2016–2025. One movie matched two selection years and
was deduplicated. This is a debugging convenience sample, not a representative or
final training dataset. Raw files are preserved unchanged.

- movies.csv: original exported movie metadata.
- entities.json: full downloaded entities, including incidental review scores.
- summary.json: original collection settings and missing-field counts.
- query_YEAR.sparql and selection_YEAR.json: queries and saved year selections.

[Historical trial inspection](reports/trial_inspection.md): verified export
integrity and three page spot checks. Budget was missing for 16/19 movies; six
movies have no usable release month. Rating-source discussion in that report
predates our choice of official IMDb ratings.

## Release-date rule and evaluation

Use the earliest valid worldwide release recorded in Wikidata, including festival
premieres. This is the earliest recorded release, not a guaranteed first release.
Keep original dates and qualifiers. Year-only dates get no invented month/day;
unsupported dates are flagged for review. The code does not independently verify
every release statement. IMDb startYear is retained for comparison, not used to
override this rule.

`clean_release_dates.py` writes `data/processed/trial_release_dates.csv` with the
raw fields plus canonical date, precision, year/month, review note, and planned
split. Training: 2016–2023; validation: 2024; testing: 2025. Unknown years are held
for review; other years are outside scope. The trial has 15 training-year and four
validation-year movies, with no genuine 2025 first releases. Selection-year quotas
do not guarantee canonical-year quotas. We need additional 2025 candidates.

Planned models: mean baseline, Ridge, Random Forest. Main metric: MAE; RMSE optional.
Fit preprocessing on training data only. Ratings are download snapshots, not
ratings at release. Do not use vote counts or ratings as pre-release predictors.
Vote counts may support a documented reliability filter. Current metadata also
requires justification for pre-release availability. No models have been trained.

## GitHub and folders

- src/: collection, date-cleaning, and merge scripts.
- data/raw/: original local metadata and IMDb extracts.
- data/processed/: derived local tables and summaries.
- notebooks/: future exploration; clear data-bearing outputs before publishing.
- reports/: project notes and historical inspection.

All files beneath data/ are ignored except empty folder placeholders. TSV files,
compressed TSVs, partial downloads, environments, and secrets are ignored too.
Do not commit IMDb records, merged tables, or copies elsewhere. Gitignore does not
untrack existing commits. The repository is local; these steps do not publish it.

## Sources and use conditions

- [Official IMDb downloads and schema](https://data.imdb.com/non-commercial-datasets/)
- [IMDb use conditions](https://help.imdb.com/article/imdb/general-information/can-i-use-imdb-data-in-my-software/G5JTRESSHJBBHTGX)
- [Wikidata CC0 licensing](https://www.wikidata.org/wiki/Wikidata:Licensing)
- [Query Service documentation](https://www.mediawiki.org/wiki/Wikidata_Query_Service/User_Manual)

IMDb downloads are original-source but prepackaged data. Our work includes merging
and preprocessing. The group reports pitch approval; confirm it covers this plan.
IMDb permits limited personal/noncommercial use subject to its conditions. Ignoring
data addresses GitHub redistribution, not every use restriction. Specific group
ML-use permission has not been independently confirmed; this repository does not
establish training or redistribution permission.

Information courtesy of IMDb (https://www.imdb.com). Used with permission.

That is IMDb's requested attribution wording, not a claim of a separate agreement.
No IMDb scraping, TMDB, Kaggle, or Hugging Face data is used.

## Next milestone

Inspect the combined trial and match gaps, decide eligibility/missing-value rules,
and then expand. Retain the existing collector for Wikidata supplemental fields:

```powershell
.\.venv\Scripts\python.exe src\collect_wikidata.py --per-year 10
```

This creates a new timestamped folder. Use `merge_imdb.py --input PATH` to merge
its movies.csv. Query requests are spaced 65 seconds apart; outages may cause
longer waits. Completed matching selections, including trial/, are reused.

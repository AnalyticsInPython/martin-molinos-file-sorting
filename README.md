# Exercise 1 — vendor file sorting

Takes a flat directory of vendor interaction files and sorts them into a
`year/month/day/company` tree.

```
dir1/APPLE_20260212.xlsx   ->   processed/2026/02/12/apple/APPLE_20260212.xlsx
dir1/Apple_20260213.csv    ->   processed/2026/02/13/apple/Apple_20260213.csv
```

## Running it

```bash
python3 -m venv .venv
.venv/bin/python -m pip install openpyxl

.venv/bin/python generate_samples.py   # builds dir1/ (already committed)
.venv/bin/python organize.py           # builds processed/ + summary.csv
```

`organize.py --dry-run` reports what would happen without writing anything.

## The two scripts

**`generate_samples.py`** builds the 60 sample files in `dir1/` — 6 vendors ×
10 dates, one file per vendor per day. Deliberately messy in two ways:

- mixed `.xlsx` and `.csv` (39 / 21)
- inconsistent vendor capitalization — `apple`, `Apple`, `APPLE`, and worse
  (`MicroSoft`, `anthroPIC`, `nVidia`)

The dates are shared across all vendors, so every day folder in the output ends
up holding all six companies. They span 2025-12-30 → 2026-03-15 on purpose, so
the tree branches across two years and four months rather than sitting in one
month. A fixed random seed makes runs reproducible.

**`organize.py`** does the sorting. Two things come out of a run: a report
printed to the terminal, and `processed/summary.csv` recording where each file
went.

## Notes on the implementation

The interesting part is not the copying, it's deciding that `MicroSoft_20260212.csv`
and `microsoft_20260213.csv` belong in the same folder.

- **Vendor names are normalized** with `.strip().casefold()` before becoming a
  folder name, so the 20 distinct spellings in `dir1/` collapse to 6 folders.
  `casefold()` rather than `lower()` because it also handles non-English text.
- **Filenames split on the _last_ underscore** (`rpartition`), so a vendor whose
  name contains one — `acme_corp_20260213.csv` — still parses correctly.
- **Dates go through `strptime`**, so `vendor_20261345.xlsx` is rejected rather
  than creating a month-13 folder.
- **Files are copied, not moved.** `dir1/` stays intact and a second run copies
  nothing and reports every file as already in the destination.

Anything that doesn't fit the `vendor_YYYYMMDD.{xlsx,xls,csv}` convention is
skipped and listed in the report with a reason, rather than failing the run.

### A known limitation

Sorting is driven entirely by the filename — no spreadsheet is ever opened. A
file whose internal `vendor` column disagrees with its filename will sort by the
filename, silently. Reading the contents would also allow a consistency check
against the names, and would be the natural place to add an aggregation of the
interaction data itself.

## Repo contents

| Path | What it is |
|---|---|
| `generate_samples.py` | builds the sample input files |
| `organize.py` | the sorting program |
| `dir1/` | 60 generated sample files |
| `docs/summary.csv` | example output from a run |
| `docs/summary-grid.html` | visualization of that summary |
| `docs/SESSION.md` | the working session that produced this |

`processed/` is gitignored — it's regenerated in about a second.

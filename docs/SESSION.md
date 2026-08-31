# Working session — Exercise 1

A record of the session that produced this repo, written up from the
conversation. Prompts are reproduced with spelling and grammar corrected;
Claude's side is condensed to the decisions and what came out of them, rather
than reproduced verbatim.

---

## 1. Setting up

> **Prompt:** In my `Documents/python bootcamp`, create another folder for
> Exercise 1 and take me there.

Created the folder and moved the session into it.

---

## 2. A detour

> **Prompt:** I want to connect my mobile device to this session so I can upload
> pictures.

Claude's first answer was that there was no way to do this — suggesting AirDrop
and synced folders instead.

> **Prompt:** I can see my other usage-metrics session on my phone — there must
> be a way.

This was a correction worth recording. Claude had answered from an assumption
instead of checking, and the user had direct evidence to the contrary. Listing
the active sessions showed two peer sessions already visible across devices;
the link existed and simply wasn't Claude's to initiate.

The lesson generalizes: an agent's confident "you can't" is worth one push-back
when you have evidence otherwise.

---

## 3. The exercise

> **Prompt:** For this exercise we first have to create the files for `dir1`
> (pictured) — a set of Excel spreadsheets from each vendor for each day, with
> the vendor and date in the filename, and entries inside the spreadsheet for
> the interactions we have with that vendor. It doesn't really matter what's in
> there, but we need the type of interaction. Note that we need multiple
> spreadsheets per vendor per date — let's create about 10 per vendor with
> different dates, but the dates also have to be the same across vendors.
> Create a folder inside Exercise 1 and house all of these sample files there.
>
> Once we have a sizeable number of files, we need to work on the actual
> program, which needs to process the `dir1` spreadsheets and organize them into
> a new directory by year/month/day/company.
>
> Ask me questions if you need more context.

Attached was a photo of the whiteboard:

```
        ⎧ apple_20260212.xls
1DIR    ⎨ anthropic_20260213.csv
        ⎩ microsoft_20260214.xls
                ⋮
 ①

 ② SUMMARY  ↘  processed/
                 2026/
                   02/
                     12
                     13
                     14
```

### Questions asked before building

Three ambiguities were worth resolving up front rather than guessing:

**File format.** The board showed both `.xls` and one `.csv`.

> **Answer:** Mixed `.xlsx` and `.csv` — and make the capitalization differ
> between companies, capitalized and not, and make sure the script can handle
> these edge cases where it's different but obviously referencing the same
> vendor.

This turned out to be the most valuable answer of the session. It's what makes
the exercise about normalization rather than about `shutil.copy2`.

**File count.** The prompt said both "multiple per vendor per date" and "10 per
vendor with different dates" — which conflict, since two files for the same
vendor on the same date would collide on the filename convention.

> **Answer:** One file per vendor per date, 10 dates.

**Output.** Copy into the tree, or also produce a summary?

> **Answer:** Copy files into `YYYY/MM/DD/company/`.

### What got built

`generate_samples.py` produced 60 files — 6 vendors × 10 shared dates, roughly
one in four a CSV, with vendor spellings drawn at random from per-vendor
variants. Dates were spread from 2025-12-30 to 2026-03-15 so the output tree
would branch across two years and four months instead of sitting in one month.

`organize.py` parsed each filename, normalized the vendor, and copied the file
into place. All 60 landed; the six vendor folders absorbed 20 distinct
spellings.

---

## 4. Deciding what "SUMMARY" meant

> **Prompt:** I'm not quite sure what he meant by "summary" — what do you think
> it meant?

Claude checked the course syllabus first (it turned out to be course-level only
and didn't describe the exercise), then argued for a specific reading:

The strongest evidence was that **step ① never opens a single file.** Sorting
into `YYYY/MM/DD/company/` is pure filename manipulation — not one cell is
parsed. If the exercise ended there, the interaction rows inside those
spreadsheets would be decoration nobody reads. That suggested the summary was
the analytics half: an aggregation of interactions per vendor, per day, per
type.

Two weaker readings were also on the table: a run report of what the script did,
and a per-day summary file dropped in each date folder.

Claude also flagged that the ①/② numbering was ambiguous in a photographed
whiteboard, and that the instructor was the cheap source of truth.

> **Prompt:** Let's do both the run report and a summary file of where things
> went.

So the file-movement reading, not the data aggregation. `organize.py` was
rewritten to emit both:

- a **run report** to the terminal — totals, per-vendor counts with the raw
  spellings that collapsed into each, per-date, per-format, tree shape, and a
  skip list with reasons
- **`processed/summary.csv`** — one row per source file, with `vendor_raw` kept
  alongside the normalized `vendor` so the normalization is auditable rather
  than merely trusted

### Edge cases tested

| Input | Result |
|---|---|
| `acme_corp_20260213.csv` | vendor `acme_corp` — splits on the *last* underscore |
| `  Spaced  _20260214.csv` | vendor `spaced` |
| `vendor_20261345.xlsx` | skipped — "not a valid YYYYMMDD date" |
| `no-date.xlsx`, `_20260212.xlsx` | skipped — "name is not vendor_YYYYMMDD" |
| `notes.txt`, `README.md` | skipped — unsupported extension |

Also confirmed that `--dry-run` writes nothing at all, and that a second run
copies zero files rather than duplicating.

---

## 5. Visualizing the result

> **Prompt:** Can you visualize the `summary.csv`?

A vendor × date grid — 6 rows, 10 columns, every cell labelled with the raw
spelling as it appears in `dir1/` and coloured by file format. Saved here as
`summary-grid.html`.

Three things it showed that the CSV doesn't:

1. **The grid is completely full.** 60 cells, no gaps — which is what makes
   every day folder hold all six companies. A hole would mean a missing file or
   a date that failed to parse.
2. **The casing chaos, per cell.** The `anthropic` row reads `anthropic` →
   `Anthropic` → `ANTHROPIC` → `anthroPIC`. Four spellings, one folder. Without
   `casefold()` that's 20 vendor folders instead of 6.
3. **Format is scattered, not clustered.** The CSVs follow no vendor or date
   pattern, so the program can't shortcut by assuming a vendor always ships one
   format.

---

## Open questions

Two things were deliberately left undone:

1. **`summary.csv` describes the last run, not the cumulative tree.** Re-run the
   script and every row reads `skipped / already in destination`. The
   `destination` column stays populated, so "where things went" survives — but
   it isn't a standing manifest of the tree's contents.
2. **The sort is filename-driven.** Nothing opens a spreadsheet, so a file whose
   internal `vendor` column contradicts its filename sorts by the filename,
   silently. That's also the seam where the data-aggregation reading of SUMMARY
   would attach, if that turns out to be what was meant.

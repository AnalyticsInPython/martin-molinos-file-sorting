"""Sort the flat pile of vendor files in dir1/ into processed/YYYY/MM/DD/company/.

    dir1/APPLE_20260212.xlsx  ->  processed/2026/02/12/apple/APPLE_20260212.xlsx
    dir1/Apple_20260213.csv   ->  processed/2026/02/13/apple/Apple_20260213.csv

Vendor names in dir1 are not spelled consistently (apple / Apple / APPLE), so the
name is normalized before it becomes a folder -- one company, one folder.
Files are copied, not moved, so dir1 stays intact and the script can be re-run.

Two things come out of a run:
  * a run report printed to the terminal (totals, per-vendor, per-date, skips)
  * processed/summary.csv -- one row per source file recording where it went
"""

import argparse
import csv
import shutil
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).parent

# Only these are treated as vendor data files; anything else is ignored.
SUPPORTED_EXTENSIONS = {".xlsx", ".xls", ".csv"}

SUMMARY_NAME = "summary.csv"

SUMMARY_COLUMNS = [
    "source_file",
    "vendor_raw",
    "vendor",
    "date",
    "year",
    "month",
    "day",
    "extension",
    "size_bytes",
    "destination",
    "status",
    "reason",
]


def normalize_vendor(raw):
    """Collapse the spelling variants of a vendor into one canonical name.

    'Apple', 'APPLE' and ' apple ' all become 'apple'. casefold() is used
    rather than lower() because it handles non-English text correctly too.
    """
    return raw.strip().casefold()


def parse_filename(path):
    """Split 'APPLE_20260212.xlsx' into ('APPLE', 'apple', date(2026, 2, 12)).

    Returns (None, reason) if the name does not follow vendor_YYYYMMDD.
    """
    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        return None, f"unsupported extension '{path.suffix}'"

    # Split on the LAST underscore: vendor names may contain underscores.
    vendor_raw, separator, date_part = path.stem.rpartition("_")
    if not separator or not vendor_raw:
        return None, "name is not vendor_YYYYMMDD"

    try:
        day = datetime.strptime(date_part, "%Y%m%d").date()
    except ValueError:
        return None, f"'{date_part}' is not a valid YYYYMMDD date"

    vendor = normalize_vendor(vendor_raw)
    if not vendor:
        return None, "empty vendor name"

    return (vendor_raw, vendor, day), None


def organize(source, dest, dry_run=False):
    """Copy every recognized file in source into the dest date/company tree.

    Returns a list of record dicts, one per file seen -- the raw material for
    both the run report and summary.csv.
    """
    records = []

    for path in sorted(p for p in source.iterdir() if p.is_file()):
        if path.name == SUMMARY_NAME:
            continue  # never treat our own output as input

        record = {column: "" for column in SUMMARY_COLUMNS}
        record["source_file"] = path.name
        record["extension"] = path.suffix.lower()
        record["size_bytes"] = path.stat().st_size

        parsed, reason = parse_filename(path)
        if parsed is None:
            record["status"] = "skipped"
            record["reason"] = reason
            records.append(record)
            continue

        vendor_raw, vendor, day = parsed
        target_dir = dest / f"{day:%Y}" / f"{day:%m}" / f"{day:%d}" / vendor
        target = target_dir / path.name

        record.update(
            {
                "vendor_raw": vendor_raw,
                "vendor": vendor,
                "date": day.isoformat(),
                "year": f"{day:%Y}",
                "month": f"{day:%m}",
                "day": f"{day:%d}",
                "destination": str(target.relative_to(dest.parent)),
            }
        )

        if target.exists():
            record["status"] = "skipped"
            record["reason"] = "already in destination"
        else:
            if not dry_run:
                target_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, target)
            record["status"] = "would copy" if dry_run else "copied"

        records.append(record)

    return records


def write_summary(records, dest):
    """Write one row per source file to processed/summary.csv."""
    dest.mkdir(parents=True, exist_ok=True)
    path = dest / SUMMARY_NAME
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=SUMMARY_COLUMNS)
        writer.writeheader()
        writer.writerows(records)
    return path


def print_report(records, source, dest, dry_run):
    """Print the human-readable run report."""
    moved = [r for r in records if r["status"] in ("copied", "would copy")]
    skipped = [r for r in records if r["status"] == "skipped"]

    by_vendor = Counter(r["vendor"] for r in moved)
    by_date = Counter(r["date"] for r in moved)
    by_format = Counter(r["extension"] for r in moved)
    # canonical vendor -> every raw spelling seen for it
    spellings = defaultdict(set)
    for record in moved:
        spellings[record["vendor"]].add(record["vendor_raw"])

    line = "=" * 52
    print(line)
    print("RUN REPORT" + ("  (dry run -- nothing written)" if dry_run else ""))
    print(line)
    print(f"Source : {source}")
    print(f"Dest   : {dest}")
    print(f"Ran    : {datetime.now():%Y-%m-%d %H:%M:%S}")
    print()
    print(f"Files seen : {len(records)}")
    print(f"{'Would copy' if dry_run else 'Copied':<11}: {len(moved)}")
    print(f"Skipped    : {len(skipped)}")

    if by_vendor:
        print(f"\nBy vendor ({len(by_vendor)}):")
        for vendor, count in sorted(by_vendor.items()):
            variants = ", ".join(sorted(spellings[vendor]))
            print(f"  {vendor:<12} {count:>3}   <- {variants}")

    if by_date:
        print(f"\nBy date ({len(by_date)}):")
        for day, count in sorted(by_date.items()):
            print(f"  {day}  {count:>3}")

    if by_format:
        print("\nBy format:")
        for extension, count in sorted(by_format.items()):
            print(f"  {extension:<6} {count:>3}")

    if moved:
        years = {r["year"] for r in moved}
        months = {(r["year"], r["month"]) for r in moved}
        print(
            f"\nTree: {len(years)} year(s) / {len(months)} month(s) / "
            f"{len(by_date)} day(s) / {len(by_vendor)} vendor(s)"
        )

    if skipped:
        print(f"\nSkipped detail ({len(skipped)}):")
        for record in skipped:
            print(f"  {record['source_file']}: {record['reason']}")


def main():
    parser = argparse.ArgumentParser(description="Sort vendor files by date and company.")
    parser.add_argument(
        "--source", type=Path, default=HERE / "dir1", help="folder to read (default: dir1)"
    )
    parser.add_argument(
        "--dest",
        type=Path,
        default=HERE / "processed",
        help="folder to build the tree in (default: processed)",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="show what would happen, write nothing"
    )
    args = parser.parse_args()

    if not args.source.is_dir():
        parser.error(f"source folder not found: {args.source}")

    records = organize(args.source, args.dest, args.dry_run)
    print_report(records, args.source, args.dest, args.dry_run)

    if not args.dry_run:
        path = write_summary(records, args.dest)
        print(f"\nSummary written to {path.relative_to(args.dest.parent)}")


if __name__ == "__main__":
    main()

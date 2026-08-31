"""Generate the sample vendor files that live in dir1/.

Each file is one vendor's interactions for one day, named vendor_YYYYMMDD.xlsx
(or .csv). Vendor spelling is deliberately inconsistent between files --
apple / Apple / APPLE all refer to the same vendor -- so that organize.py has
to normalize names instead of trusting the filename as-is.
"""

import csv
import random
from datetime import date, datetime, timedelta
from pathlib import Path

from openpyxl import Workbook

DIR1 = Path(__file__).parent / "dir1"

# The same 10 dates are used for every vendor, so each day folder in the
# processed/ tree ends up holding several companies.
DATES = [
    date(2025, 12, 30),
    date(2025, 12, 31),
    date(2026, 1, 5),
    date(2026, 1, 15),
    date(2026, 2, 12),
    date(2026, 2, 13),
    date(2026, 2, 14),
    date(2026, 2, 28),
    date(2026, 3, 1),
    date(2026, 3, 15),
]

# Every spelling of a vendor points at the same real company.
VENDOR_SPELLINGS = {
    "apple": ["apple", "Apple", "APPLE"],
    "anthropic": ["anthropic", "Anthropic", "ANTHROPIC", "anthroPIC"],
    "microsoft": ["microsoft", "Microsoft", "MicroSoft", "MICROSOFT"],
    "google": ["google", "Google", "GOOGLE"],
    "amazon": ["amazon", "Amazon", "AMAZON"],
    "nvidia": ["nvidia", "Nvidia", "NVIDIA", "nVidia"],
}

INTERACTION_TYPES = [
    "Email",
    "Phone Call",
    "Meeting",
    "Invoice",
    "Support Ticket",
    "Contract Review",
    "Quote Request",
    "Escalation",
    "Onsite Visit",
    "Renewal",
]

CHANNELS = ["Inbound", "Outbound"]

CONTACTS = [
    "J. Rivera",
    "M. Chen",
    "S. Okafor",
    "P. Nowak",
    "L. Haddad",
    "T. Bergström",
    "D. Sharma",
    "K. Alvarez",
]

OWNERS = ["procurement", "engineering", "finance", "legal", "support"]

HEADERS = [
    "interaction_id",
    "date",
    "vendor",
    "contact",
    "interaction_type",
    "channel",
    "duration_min",
    "owner",
    "notes",
]


def build_rows(vendor_label, day, rng):
    """Return a list of interaction rows for one vendor on one day."""
    rows = []
    for n in range(1, rng.randint(3, 12) + 1):
        interaction_type = rng.choice(INTERACTION_TYPES)
        stamp = datetime(day.year, day.month, day.day, 9, 0) + timedelta(
            minutes=rng.randint(0, 480)
        )
        rows.append(
            [
                f"{vendor_label.lower()}-{day:%Y%m%d}-{n:03d}",
                stamp.strftime("%Y-%m-%d %H:%M"),
                vendor_label,
                rng.choice(CONTACTS),
                interaction_type,
                rng.choice(CHANNELS),
                rng.randint(5, 90),
                rng.choice(OWNERS),
                f"{interaction_type} re: PO-{rng.randint(1000, 9999)}",
            ]
        )
    return rows


def write_xlsx(path, rows):
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "interactions"
    sheet.append(HEADERS)
    for row in rows:
        sheet.append(row)
    workbook.save(path)


def write_csv(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(HEADERS)
        writer.writerows(rows)


def main():
    rng = random.Random(20260212)  # fixed seed keeps runs reproducible
    DIR1.mkdir(exist_ok=True)

    created = 0
    for vendor, spellings in VENDOR_SPELLINGS.items():
        for day in DATES:
            label = rng.choice(spellings)
            # Roughly one file in four is a CSV instead of a spreadsheet.
            extension = ".csv" if rng.random() < 0.25 else ".xlsx"
            path = DIR1 / f"{label}_{day:%Y%m%d}{extension}"

            rows = build_rows(label, day, rng)
            if extension == ".csv":
                write_csv(path, rows)
            else:
                write_xlsx(path, rows)
            created += 1

    print(f"Wrote {created} files to {DIR1}")


if __name__ == "__main__":
    main()

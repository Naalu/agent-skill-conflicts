"""Check a coder's labelling file before it is handed in. The file is only read, never changed.

Input:  one coder file copied from pairs.csv, e.g. labelling/calibration-180/coder-b.csv. The pairs.csv in the same
        folder is the reference.
Output: a report on screen. Exit code 0 when no errors were found (blank rows count as progress, not errors), else 1.
Implements the procedure in labelling/README.md and docs/codebooks/competing-pairs.md (label C, N or U; type D, S or O
for C rows only) and the language-handling entry of docs/runlog.md (2026-10-15).

Standard library only, so it runs without installing anything:

    python3 labelling/check_labels.py labelling/calibration-180/coder-b.csv      (macOS)
    py labelling\\check_labels.py labelling\\calibration-180\\coder-b.csv          (Windows)
"""

import csv
import sys
from pathlib import Path

LABELS = {"C", "N", "U"}
TYPES = {"D", "S", "O"}
CODER_COLUMNS = {"label", "type", "notes"}
SHOW = 25


def read(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return reader.fieldnames or [], list(reader)


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    coder_path = Path(sys.argv[1])
    ref_path = coder_path.with_name("pairs.csv")
    if not coder_path.exists():
        sys.exit(f"File not found: {coder_path}")
    if coder_path.resolve() == ref_path.resolve():
        sys.exit("Check your own copy (coder-a.csv or coder-b.csv), not pairs.csv.")
    ref_cols, ref = read(ref_path)
    try:
        cols, rows = read(coder_path)
    except UnicodeDecodeError:
        sys.exit("The file is not saved as UTF-8. Save it again as 'CSV UTF-8' (see labelling/getting-started.md).")

    if cols != ref_cols:
        sys.exit(
            f"The columns differ from pairs.csv (expected {len(ref_cols)}, found {len(cols)}). The file was probably "
            "saved with ';' separators, or columns were moved or deleted. Save again as 'CSV UTF-8' with commas."
        )
    if len(rows) != len(ref):
        sys.exit(f"Expected {len(ref)} rows, found {len(rows)}. Rows were added or deleted.")

    errors = []
    for r_ref, r in zip(ref, rows, strict=True):
        rid = r_ref["id"]
        if r["id"] != rid:
            sys.exit(f"Row order changed (found id {r['id']} where id {rid} should be). Do not sort the rows.")
        changed = [c for c in ref_cols if c not in CODER_COLUMNS and r[c] != r_ref[c]]
        if changed:
            errors.append(
                f"id {rid}: {', '.join(changed)} changed compared with pairs.csv (edited, or altered on save)"
            )
        label, typ = r["label"].strip(), r["type"].strip()
        if label and label not in LABELS:
            errors.append(f"id {rid}: label '{label}' should be C, N or U (capital letter, nothing else)")
        if label == "C" and typ not in TYPES:
            errors.append(f"id {rid}: label C needs a type D, S or O (found '{typ}')")
        if label != "C" and typ:
            errors.append(f"id {rid}: type '{typ}' is only used with label C")

    blank = [r["id"] for r in rows if not r["label"].strip()]
    print(f"{coder_path}: {len(rows) - len(blank)} of {len(rows)} pairs labelled.")
    if blank:
        more = " ..." if len(blank) > SHOW else ""
        print(f"Still blank ({len(blank)}): ids {', '.join(blank[:SHOW])}{more}")
    if errors:
        print(f"\n{len(errors)} problem(s) to fix:")
        for e in errors[:SHOW]:
            print("  " + e)
        if len(errors) > SHOW:
            print(f"  ... and {len(errors) - SHOW} more")
        return 1
    print("No problems found." + (" Finished: every pair has a label." if not blank else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())

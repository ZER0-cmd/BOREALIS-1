#!/usr/bin/env python3
"""
Strips black (color=0) pixels from CSV image files in place.
Format: first row is "width,height", rest are "x,y,color"
"""

import csv, os, glob, sys

PICTURES_DIR = "./Pictures/Internal/csv"

csv_files = glob.glob(os.path.join(PICTURES_DIR, "*.csv"))

if not csv_files:
    print(f"No CSV files found in {PICTURES_DIR}")
    sys.exit(1)

for csv_path in csv_files:
    dim = None
    kept = []
    total = 0

    with open(csv_path, newline="") as f:
        for row in csv.reader(f):
            row = [r.strip() for r in row]
            if len(row) == 2:
                dim = row  # width, height header
            elif len(row) == 3:
                total += 1
                if int(row[2]) != 0:
                    kept.append(row)

    removed = total - len(kept)
    savings = 100 * removed // total if total else 0

    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        if dim:
            writer.writerow(dim)
        writer.writerows(kept)

    print(f"{os.path.basename(csv_path)}: {total} -> {len(kept)} pixels (removed {removed} black, {savings}% smaller)")

print("\nDone.")
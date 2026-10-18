"""Fixed CSV transformation executed in a child process. No agent-supplied code."""

import argparse
import csv
import os
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    seen = set()
    output = []
    with args.source.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != ["record_id", "value"]:
            raise ValueError("Unexpected CSV schema")
        for row in reader:
            if None in row or not row["record_id"]:
                raise ValueError("Malformed CSV row")
            value = int(row["value"])
            if row["record_id"] not in seen:
                seen.add(row["record_id"])
                output.append((row["record_id"], value))
    temporary = args.output.with_suffix(".tmp")
    try:
        with temporary.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(["record_id", "value"])
            writer.writerows(output)
        os.replace(temporary, args.output)
    finally:
        temporary.unlink(missing_ok=True)
    print(f"Completed: wrote {len(output)} deduplicated rows", flush=True)


if __name__ == "__main__":
    main()


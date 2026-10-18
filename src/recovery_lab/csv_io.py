"""Strict, intentionally narrow CSV schema: record_id,value (integer)."""

import csv
from pathlib import Path

from recovery_lab.types import Row

MAX_ROWS = 10000
MAX_BYTES = 2_000_000


def read_csv(path: Path) -> tuple[Row, ...]:
    if path.stat().st_size > MAX_BYTES:
        raise ValueError("CSV exceeds the 2 MB limit")
    result = []
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != ["record_id", "value"]:
            raise ValueError("CSV header must be exactly record_id,value")
        for line, row in enumerate(reader, start=2):
            if len(result) >= MAX_ROWS:
                raise ValueError("CSV exceeds 10000 rows")
            if None in row or not row["record_id"] or row["value"] is None:
                raise ValueError(f"Malformed CSV row at line {line}")
            result.append(Row(row["record_id"], int(row["value"])))
    if not result:
        raise ValueError("CSV must contain at least one row")
    return tuple(result)


def write_csv(path: Path, rows: tuple[Row, ...]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["record_id", "value"])
        writer.writerows((row.record_id, row.value) for row in rows)


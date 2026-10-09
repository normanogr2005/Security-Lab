#!/usr/bin/env python3
"""Read Security-Lab NDJSON events and validate the shared JSON Schema."""

from __future__ import annotations

import json
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker


REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = REPO_ROOT / "schemas" / "security_event.schema.json"


with SCHEMA_PATH.open("r", encoding="utf-8") as schema_file:
    SCHEMA = json.load(schema_file)

VALIDATOR = Draft202012Validator(
    SCHEMA,
    format_checker=FormatChecker(),
)


def validate_event(event: dict[str, Any]) -> None:
    """Validate one event against the repository's canonical JSON Schema."""

    errors = sorted(
        VALIDATOR.iter_errors(event),
        key=lambda error: list(error.path),
    )

    if not errors:
        return

    messages = []
    for error in errors:
        location = ".".join(str(part) for part in error.path) or "<root>"
        messages.append(f"{location}: {error.message}")

    raise ValueError("; ".join(messages))


def iter_events(path: Path) -> Iterator[dict[str, Any]]:
    """Yield validated NDJSON events one at a time.

    Input lines are read incrementally so the CLI does not need to retain the
    full event batch in memory. Event IDs are tracked for duplicate detection
    within this input file.
    """

    seen_event_ids: set[str] = set()

    with path.open("r", encoding="utf-8") as event_file:
        for line_number, line in enumerate(event_file, 1):
            if not line.strip():
                continue

            try:
                event = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"line {line_number}: invalid JSON: {exc}"
                ) from exc

            if not isinstance(event, dict):
                raise ValueError(
                    f"line {line_number}: event must be a JSON object"
                )

            try:
                validate_event(event)
            except ValueError as exc:
                raise ValueError(f"line {line_number}: {exc}") from exc

            event_id = event["event_id"]
            if event_id in seen_event_ids:
                raise ValueError(
                    f"line {line_number}: duplicate event_id: {event_id!r}"
                )

            seen_event_ids.add(event_id)
            yield event


def read_events(path: Path) -> list[dict[str, Any]]:
    """Read and validate all events; retained for callers needing a list."""

    return list(iter_events(path))


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} EVENTS.ndjson", file=sys.stderr)
        return 2

    counts: dict[str, int] = {}
    total = 0

    try:
        for event in iter_events(Path(sys.argv[1])):
            event_type = event["event_type"]
            counts[event_type] = counts.get(event_type, 0) + 1
            total += 1
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"validated_events={total}")
    for event_type, count in sorted(counts.items()):
        print(f"{event_type}={count}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

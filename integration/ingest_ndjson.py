#!/usr/bin/env python3
"""Read Security-Lab NDJSON events and validate the shared JSON Schema."""

from __future__ import annotations

import json
import sys
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


def read_events(path: Path) -> list[dict[str, Any]]:
    """Read and validate NDJSON, rejecting duplicate event IDs in one batch."""

    events: list[dict[str, Any]] = []
    seen_event_ids: set[str] = set()

    for line_number, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(),
        1,
    ):
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
        events.append(event)

    return events


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} EVENTS.ndjson", file=sys.stderr)
        return 2

    try:
        events = read_events(Path(sys.argv[1]))
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    counts: dict[str, int] = {}
    for event in events:
        counts[event["event_type"]] = counts.get(event["event_type"], 0) + 1

    print(f"validated_events={len(events)}")
    for event_type, count in sorted(counts.items()):
        print(f"{event_type}={count}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

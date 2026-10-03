#!/usr/bin/env python3
"""Read Security-Lab NDJSON events from NetScope and validate the contract."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


REQUIRED = {"event_id", "timestamp", "source", "event_type", "severity"}
SOURCES = {"netscope", "socforge"}
SEVERITIES = {"info", "low", "medium", "high", "critical"}


def validate_event(event: dict[str, Any]) -> None:
    missing = REQUIRED - event.keys()
    if missing:
        raise ValueError(f"missing required fields: {sorted(missing)}")

    if event["source"] not in SOURCES:
        raise ValueError(f"invalid source: {event['source']!r}")

    if event["severity"] not in SEVERITIES:
        raise ValueError(f"invalid severity: {event['severity']!r}")

    for field in ("source_port", "destination_port"):
        if field in event and event[field] is not None:
            if not isinstance(event[field], int) or not 0 <= event[field] <= 65535:
                raise ValueError(f"invalid {field}: {event[field]!r}")


def read_events(path: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []

    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue

        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"line {line_number}: invalid JSON: {exc}") from exc

        if not isinstance(event, dict):
            raise ValueError(f"line {line_number}: event must be a JSON object")

        try:
            validate_event(event)
        except ValueError as exc:
            raise ValueError(f"line {line_number}: {exc}") from exc

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

#!/usr/bin/env python3
"""Replay durable C6 Win Events into the Command Centre.

Usage:
  python tools/replay_win_outbox.py [path]
Environment:
  C6_WIN_ENGINE_URL  defaults to http://127.0.0.1:5000/api/wins/batch
  C6_WIN_ENGINE_TOKEN optional X-C6-Win-Token
  C6_WIN_OUTBOX optional path to logs/win_events.jsonl
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from urllib.request import Request, urlopen

DEFAULT_OUTBOX = Path(os.getenv("C6_WIN_OUTBOX", "logs/win_events.jsonl"))
DEFAULT_URL = os.getenv("C6_WIN_ENGINE_URL", "http://127.0.0.1:5000/api/wins/batch")


def main() -> int:
    outbox = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_OUTBOX
    if not outbox.exists():
        print(f"No outbox found: {outbox}")
        return 0

    events = []
    with outbox.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError as exc:
                print(f"Skipping invalid JSON on line {line_no}: {exc}")
                continue
            if isinstance(event, dict):
                events.append(event)

    if not events:
        print("Outbox is empty.")
        return 0

    headers = {"Content-Type": "application/json"}
    token = os.getenv("C6_WIN_ENGINE_TOKEN")
    if token:
        headers["X-C6-Win-Token"] = token

    request = Request(
        DEFAULT_URL,
        data=json.dumps({"events": events}).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    with urlopen(request, timeout=10) as response:
        result = json.loads(response.read().decode("utf-8"))

    print(json.dumps(result, indent=2))
    if result.get("status") != "processed":
        return 1

    rejected = result.get("rejected") or []
    if not rejected:
        outbox.unlink()
        print(f"Replayed {len(events)} event(s); outbox cleared.")
        return 0

    print(f"Replayed with {len(rejected)} rejection(s); outbox retained for retry.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

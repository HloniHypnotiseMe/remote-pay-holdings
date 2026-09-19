"""Fail-open Winner Effect event producer for C6 Tax Secretarial."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen


def emit_win_event(event: dict) -> None:
    payload = {
        "project": "Tax Secretarial",
        "actor": "tax_secretarial",
        "tier": "EXECUTION",
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        **event,
    }

    url = os.getenv("C6_WIN_ENGINE_URL")
    token = os.getenv("C6_WIN_ENGINE_TOKEN")
    if url:
        try:
            headers = {"Content-Type": "application/json"}
            if token:
                headers["X-C6-Win-Token"] = token
            request = Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
            with urlopen(request, timeout=3):
                return
        except Exception:
            pass

    outbox = Path(os.getenv("C6_WIN_OUTBOX", "logs/win_events.jsonl"))
    outbox.parent.mkdir(parents=True, exist_ok=True)
    with outbox.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")

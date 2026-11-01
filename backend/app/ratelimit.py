"""Tiny in-memory limiter so a public demo can't burn through your API credits.

Per-IP: PER_IP_LIMIT requests per WINDOW seconds. Global: DAILY_LIMIT requests per day.
In-memory means limits reset if the server restarts or sleeps, which is fine for a demo.
The real safety net is also setting a monthly spend limit in the Anthropic console.
"""
import os
import time
from collections import defaultdict, deque

PER_IP_LIMIT = int(os.environ.get("ASK_PER_IP_LIMIT", "10"))
WINDOW = int(os.environ.get("ASK_WINDOW_SECONDS", "3600"))
DAILY_LIMIT = int(os.environ.get("ASK_DAILY_LIMIT", "200"))

_hits: dict[str, deque] = defaultdict(deque)
_day = {"start": time.time(), "count": 0}


def check(ip: str, now: float | None = None) -> str | None:
    """Return None if allowed, otherwise a message explaining why not."""
    now = time.time() if now is None else now
    if now - _day["start"] >= 86400:
        _day["start"], _day["count"] = now, 0
    if _day["count"] >= DAILY_LIMIT:
        return "The demo has reached its daily question limit. Please try again tomorrow."
    q = _hits[ip]
    while q and now - q[0] >= WINDOW:
        q.popleft()
    if len(q) >= PER_IP_LIMIT:
        return f"Limit of {PER_IP_LIMIT} questions per hour reached. Please try again later."
    q.append(now)
    _day["count"] += 1
    return None

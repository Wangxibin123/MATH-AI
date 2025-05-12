from __future__ import annotations
from queue import Queue
from typing import Any, Dict

_event_q: Queue[Dict[str, Any]] = Queue()


def publish(event_type: str, payload: Dict[str, Any]) -> None:
    _event_q.put({"type": event_type, "payload": payload})


def pop() -> Dict[str, Any] | None:
    try:
        return _event_q.get_nowait()
    except Exception:
        return None

"""One cached, encoded model.json per revision — shared by ``haus serve`` and the PWA worker.

Both engines hold a :class:`PayloadCache`; both serve exactly the bytes :meth:`encoded`
returns (the HTTP body, and a transferable ``ArrayBuffer`` out of the worker). Kept free of
fastapi/starlette so the Pyodide worker can import it.

A check-tier landing changes only ``findings``/``ok``/``checksPending``/``perf``:
:meth:`with_findings` swaps those keys in a shallow copy instead of rebuilding the payload
(``findings`` feeds nothing else in ``model_to_dict``).
"""

from __future__ import annotations

import json
import threading
import time
from collections.abc import Callable
from typing import Any

from typehaus.findings import Finding


def _ms(t0: float) -> float:
    return (time.perf_counter() - t0) * 1000.0


class PayloadCache:
    def __init__(self) -> None:
        self._key: str | None = None
        self._payload: dict[str, Any] | None = None
        self._bytes: bytes | None = None
        # Reentrant: `encoded` may run on a warm-up thread while a request builds.
        self._lock = threading.RLock()
        # ``payload.model_to_dict`` / ``payload.encode`` of the last build, in ms.
        self.timings: dict[str, float] = {}

    def invalidate(self) -> None:
        with self._lock:
            self._key = self._payload = self._bytes = None

    def get(self, key: str, build: Callable[[], dict[str, Any]],
            tail: dict[str, Any] | None = None) -> dict[str, Any]:
        """The payload for ``key``, building it once. ``tail`` keys (ok, perf, …) are set
        on a fresh build; a cache hit keeps the ones it was built or swapped with."""
        with self._lock:
            if self._key == key and self._payload is not None:
                return self._payload
            t0 = time.perf_counter()
            payload = build()
            self.timings = {"payload.model_to_dict": _ms(t0)}
            payload.update(tail or {})
            if isinstance(payload.get("perf"), dict):
                payload["perf"] = {**payload["perf"], **self.timings}
            self._key, self._payload, self._bytes = key, payload, None
            return payload

    def with_findings(self, key: str, findings: list[Finding], ok: bool,
                      tail: dict[str, Any] | None = None) -> None:
        """Swap a check-tier result into the cached payload for ``key``, if it is cached."""
        with self._lock:
            if self._key != key or self._payload is None:
                return
            self._payload = {**self._payload,
                             "findings": [f.model_dump(mode="json") for f in findings],
                             "ok": ok, **(tail or {})}
            self._bytes = None

    def encoded(self) -> bytes | None:
        """The cached payload as compact UTF-8 JSON, encoded once. ``None`` before a build."""
        with self._lock:
            if self._payload is None:
                return None
            if self._bytes is None:
                t0 = time.perf_counter()
                body = json.dumps(self._payload, ensure_ascii=False, separators=(",", ":"))
                self._bytes = body.encode("utf-8")
                self.timings["payload.encode"] = _ms(t0)
            return self._bytes

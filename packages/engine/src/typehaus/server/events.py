"""WebSocket event bus for ``WS /events`` — build done / findings / file changed (→ 20)."""

from __future__ import annotations

import asyncio
from typing import Any


class EventBus:
    """Fan-out of server-push events to every connected UI client."""

    def __init__(self) -> None:
        self._clients: set[Any] = set()
        self._lock = asyncio.Lock()

    async def connect(self, ws: Any) -> None:
        await ws.accept()
        async with self._lock:
            self._clients.add(ws)

    def disconnect(self, ws: Any) -> None:
        self._clients.discard(ws)

    async def broadcast(self, event: dict[str, Any]) -> None:
        dead: list[Any] = []
        for ws in list(self._clients):
            try:
                await ws.send_json(event)
            except Exception:  # noqa: BLE001 - a dropped client must not break the fan-out
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)

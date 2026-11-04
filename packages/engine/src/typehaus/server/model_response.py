"""``GET /model``'s body: the cached payload bytes, the engine stamp spliced in, gzipped once.

The one transport-only piece of the payload path (the PWA has no HTTP hop): 27 MB of JSON
is 2.9 MB gzipped, which is the load time over a LAN or iPad link. Loopback skips it: there
the ~190 ms compress per revision costs more than the transfer it saves.
"""

from __future__ import annotations

import gzip
import json

from typehaus.server.engine_stamp import engine_stamp

# Measured on catlin: level 1 143 ms / 3.4 MB, 3 187 ms / 2.9 MB, 6 563 ms / 2.3 MB.
GZIP_LEVEL = 3
_LOOPBACK = frozenset({"127.0.0.1", "::1", "localhost", "testclient"})


class ModelResponse:
    def __init__(self) -> None:
        self._source: bytes | None = None  # the payload bytes the cached bodies came from
        self._plain = self._gzipped = b""

    def body(self, payload: bytes, accept_encoding: str,
             client_host: str | None) -> tuple[bytes, dict[str, str]]:
        # The engine stamp rides on /model so the browser learns the server is running stale
        # engine code on the same poll that brings it that code's geometry (engine_stamp.py).
        stamp = json.dumps({"engine": engine_stamp()}, separators=(",", ":")).encode("utf-8")
        plain = payload[:-1] + b"," + stamp[1:]
        if self._source is not payload or self._plain != plain:
            self._source, self._plain, self._gzipped = payload, plain, b""
        if "gzip" not in accept_encoding or client_host in _LOOPBACK:
            return plain, {}
        if not self._gzipped:
            self._gzipped = gzip.compress(plain, compresslevel=GZIP_LEVEL, mtime=0)
        return self._gzipped, {"Content-Encoding": "gzip", "Vary": "Accept-Encoding"}

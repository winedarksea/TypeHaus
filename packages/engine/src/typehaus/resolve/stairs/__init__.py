"""Resolve authored stairs into framed geometry: flights, landings, winder turns.

Split out of ``resolve/envelope.py`` (which had grown past the 500-line guideline) and
then split again into a package when the single ``resolve/stairs.py`` module crossed the
same line. One file per verified seam:

- :mod:`typehaus.resolve.stairs.common`   — shared constants + small pure helpers
- :mod:`typehaus.resolve.stairs.dispatch` — validation + layout dispatch (the public entry)
- :mod:`typehaus.resolve.stairs.straight` — the straight flight generator
- :mod:`typehaus.resolve.stairs.u_split`  — the U split-landing generator
- :mod:`typehaus.resolve.stairs.winder`   — the right-angle winder generator + turn frame
- :mod:`typehaus.resolve.stairs.bearing`  — the subfloor clip and wall-bearing pass

``resolve_envelope_geometry`` is the only caller; ``_resolve_stair`` is the whole public
surface and is re-exported here so ``from typehaus.resolve.stairs import _resolve_stair``
keeps working unchanged.
"""

from __future__ import annotations

from typehaus.resolve.stairs.dispatch import _resolve_stair

__all__ = ["_resolve_stair"]

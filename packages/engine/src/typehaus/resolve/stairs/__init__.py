"""Resolve authored stairs into framed geometry: flights, landings, winder turns.

Split into a package along verified seams, one file per generator/concern, to stay under
the 500-line guideline.

``resolve_envelope_geometry`` is the only caller; ``_resolve_stair`` is the whole public
surface and is re-exported here so ``from typehaus.resolve.stairs import _resolve_stair``
keeps working unchanged.
"""

from __future__ import annotations

from typehaus.resolve.stairs.dispatch import _resolve_stair

__all__ = ["_resolve_stair"]

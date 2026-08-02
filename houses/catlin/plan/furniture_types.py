"""House-local furniture catalog for items specific to the Catlin plan.

Empty since 2026-08-02: both mudroom closets have been reframed as real rooms. The north
closet became RM-M-MECH (2026-07-28) and the south closet FURN-M-MUD-CLOSET-S became
RM-M-MUD-CLOSET (2026-08-02, storeys/main.py) — a framed 2x4 partition closet with a
sliding bypass door, keeping the original's no-swing intent. The workbench and the shoe
bench were generic and moved to ``library.placeables.furniture`` as FURN-G-WORKBENCH /
FURN-M-MUD-BENCH.

The module (and the empty tuple) stays so ``plan/manifest.py`` keeps one stable seam for
house-local furniture types; ``*FURNITURE_TYPES`` unpacks an empty tuple cleanly.
"""

from __future__ import annotations

FURNITURE_TYPES = ()

"""The guard's frame: post stations, posts, and the horizontal rails between them."""

from __future__ import annotations

from typehaus.model.structure import Railing
from typehaus.resolve.geometry import Vec, length, rect_between, square, sub
from typehaus.resolve.model import ResolvedModel, ResolvedSolid
from typehaus.resolve.railings.parts import RAILING_CATEGORY, RailingParts
from typehaus.resolve.railings.spans import RailingSurface

#: A post cannot be closer than this o.c. — a zero or negative authored spacing would
#: otherwise walk a segment forever.
MIN_POST_SPACING_M = 0.3


def railing_post_stations(path: list[Vec], spacing: float) -> list[Vec]:
    """Posts at every segment start plus interior spacing stations; final vertex closes.

    Each segment's loop restarts at ``t=0``, so every authored path vertex is itself a
    station and two consecutive stations never straddle a corner. That is the property the
    infill relies on: one walk of this list yields the bays, and a bay is always straight.

    KNOWN DEFECT, flagged not fixed: ``int(seg // spacing)`` wants ``ceil``. A segment whose
    length is not a whole number of bays leaves its remainder in the *last* bay, which can
    make that bay approach 2x ``post_spacing`` — RL-A-STAIR gets a 9'-3" bay in a guard
    authored at 5'-0" o.c. Balusters absorb it invisibly (they re-space to the bay they are
    given); a glass lite would become an unmanufacturable 9'-3" panel, which is why
    :func:`~typehaus.resolve.railings.infill.emit_infill` warns on it. Fixing the spacing
    moves existing post positions and their test fixtures, so it is its own change.
    """
    placed: list[Vec] = []
    for a, b in zip(path[:-1], path[1:]):
        seg = length(sub(b, a))
        n = max(int(seg // spacing), 1)
        for k in range(n):
            t = (k * spacing) / seg if seg else 0.0
            placed.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
    placed.append(path[-1])
    return placed


def emit_posts(model: ResolvedModel, el: Railing, storey: str, stations: list[Vec],
               surface: RailingSurface, parts: RailingParts, rail_h: float) -> None:
    """One prism per station, standing on the walking surface under it."""
    half = parts.post_section_m / 2.0
    for index, (px, py) in enumerate(stations):
        z0 = surface.height_at((px, py))
        model.solids.append(ResolvedSolid(
            uid=f"{el.uid}-p{index:02d}", tag=f"{el.tag}-POST{index + 1}", storey=storey,
            category=RAILING_CATEGORY, outline=square(px, py, half, half),
            z0_m=z0, z1_m=z0 + rail_h, assembly=el.assembly, material=parts.post_material,
        ))


def emit_rails(model: ResolvedModel, el: Railing, storey: str, path: list[Vec],
               surface: RailingSurface, parts: RailingParts, rail_h: float) -> None:
    """``rail_count`` evenly spaced horizontal runs, top rail at the guard height.

    Banded per *path segment*: a flat run is one band, a raking one is a ladder of short
    ones (→ :mod:`.spans`). Rails are the guard line a plan reader looks for, so they stay
    one solid per segment where the surface is flat rather than being chopped into bays.
    """
    half = parts.rail_section_m / 2.0
    levels = el.rail_count if el.rail_count > 0 else 1
    index = 0
    for a, b in zip(path[:-1], path[1:]):
        for pa, pb, surface_z in surface.spans(a, b):
            for level in range(levels):
                frac = 1.0 - (level / max(levels - 1, 1)) if levels > 1 else 1.0
                rz = surface_z + rail_h * frac
                model.solids.append(ResolvedSolid(
                    uid=f"{el.uid}-r{index:02d}", tag=f"{el.tag}-RAIL{index + 1}",
                    storey=storey, category=RAILING_CATEGORY,
                    outline=rect_between(pa, pb, -half, half),
                    z0_m=rz - half, z1_m=rz + half, assembly=el.assembly,
                    material=parts.rail_material,
                ))
                index += 1

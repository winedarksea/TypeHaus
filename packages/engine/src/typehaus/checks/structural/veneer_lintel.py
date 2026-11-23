"""``structural.veneer_lintel`` — masonry veneer over an opening bears on a lintel (R703.8.3).

**Subject.** Every opening hosted in an anchored wythe (``veneer_ties.anchored_wythes``). None
is N/A, from every wythe examined.

**The rule, a table read.** IRC R703.8.3 (2018, MN 2020; 2021 and 2024 the same text): veneer
over an opening is carried on a noncombustible lintel with at least 4" of bearing each side,
a steel one coated against rust (a hot-dip galvanized angle is "treated with coatings to
provide corrosion resistance"), spanning no more than Table R703.8.3.1 allows for its angle
and the stories above it, long leg vertical. The span read is the opening's clear width. A
member bigger than a row's angle in every leg is read at that row (the table's note 3 admits
other members meeting structural design; a larger angle of the same thickness only adds
section, never subtracts it). **Stories above** are read off the model: anything framed
over the wythe's top is a story the no-story column cannot answer, and the finding is UNKNOWN.

**Flashing (R703.8.5):** an authored ``Flashing`` run hosted on the wythe, its top on the lintel's
top and as long as the angle, must lie over each lintel; weeps (R703.8.6) are open joints named
in ``notes/veneer_opening_detail.md``, not modelled. **Separation:** a stainless sheet never lies
on a galvanized angle: an ``epdm`` run as long as the sheet must lie between them (the house keeps
stainless and zinc out of one joint).
Oracle: ``houses/catlin/notes/sunken_garden_veneer_beam.md`` §6l, ``tests/test_veneer_lintel.py``.
"""

from __future__ import annotations

import math
import re
from typing import Any

from shapely.geometry import Polygon

from typehaus import veneer_ties
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, failed, not_applicable, passed, unknown

_ID = "structural.veneer_lintel"
_CODE = "IRC R703.8.3, R703.8.3.1, Table R703.8.3.1"
_IN = 0.0254
_ANGLE = re.compile(r"^L(\d+(?:\.\d+)?)x(\d+(?:\.\d+)?)x(\d+(?:\.\d+)?)$")
MIN_BEARING_IN = 4.0
#: Table R703.8.3.1, steel angles, "no story above" span (in): (long leg, short leg, thickness).
_ROWS = (((3.0, 3.0, 0.25), 72.0), ((4.0, 3.0, 0.25), 96.0), ((5.0, 3.5, 0.3125), 120.0),
         ((6.0, 3.5, 0.3125), 168.0))
_ON_STRIP = " on the EPDM strip {}, so stainless and zinc never touch"
_COATING = re.compile(r"galvaniz|stainless|corrosion-resistant", re.I)
#: A beam's soffit this near an opening's head is the lintel of that opening (the masonry band
#: starts at the soffit, as ``masonry_interference`` reads it).
_HEAD_TOL_M = 0.5 * _IN
_BEARS_TOL_M = 0.25 * _IN


def table_row(size: str) -> tuple[tuple[float, float, float], float] | None:
    """The largest Table R703.8.3.1 row the angle meets in every leg, as ``(angle, span in)``."""
    match = _ANGLE.match(size)
    if not match:
        return None
    legs = sorted((float(match[1]), float(match[2])), reverse=True)
    thickness = float(match[3])
    met = [row for row in _ROWS if legs[0] >= row[0][0] and legs[1] >= row[0][1]
           and thickness >= row[0][2] - 1e-9]
    return met[-1] if met else None


def _framed_over(ctx: CheckContext, wythe: Any, brick: Polygon) -> list[str]:
    """Framing standing on the wythe's top: every wall and floor member over its footprint."""
    out = []
    for owner in (*ctx.model.walls, *ctx.model.floors):
        if owner.tag == wythe.tag:
            continue
        for member in getattr(owner, "members", ()):
            outline = getattr(member, "plan_outline", None)
            if (outline and member.z0_m <= wythe.z1_m + _BEARS_TOL_M
                    and member.z1_m >= wythe.z1_m - _BEARS_TOL_M
                    and Polygon(outline).intersection(brick).area > 1e-6):
                out.append(owner.tag)
                break
    return out


def _head_flashing(ctx: CheckContext, wythe: Any, top_z: float, lo: float, hi: float,
                   material: str | None = None):
    """The tag of a Flashing run on the wythe at the lintel's top and as long as the angle,
    of ``material`` where named (the run's material tag contains it)."""
    (ax, ay), (bx, by) = wythe.axis
    length = math.hypot(bx - ax, by - ay)
    u = ((bx - ax) / length, (by - ay) / length)
    for el in ctx.plan.all_elements():
        path = getattr(el, "path", None)
        if (getattr(el, "host_ref", None) != wythe.tag or path is None
                or abs(el.top_elevation.meters - top_z) > _HEAD_TOL_M
                or (material and material not in (getattr(el, "material", "") or ""))):
            continue
        along = [(p.x.meters - ax) * u[0] + (p.y.meters - ay) * u[1] for p in path]
        if min(along) <= lo + _IN and max(along) >= hi - _IN:
            return el.tag
    return None


def _lintel(ctx: CheckContext, wythe: Any, opening: Any, head_z: float):
    """The authored steel Beam over the opening: bearing past each jamb, soffit on the head."""
    (ax, ay), (bx, by) = wythe.axis
    length = math.hypot(bx - ax, by - ay)
    u = ((bx - ax) / length, (by - ay) / length)
    lo = opening.center_along_m - opening.width_m / 2
    hi = opening.center_along_m + opening.width_m / 2
    for solid in ctx.model.solids:
        element = ctx.plan.by_tag(solid.tag)
        if (solid.category != "beam" or element is None
                or not _ANGLE.match(getattr(element, "size", "") or "")
                or abs(solid.z0_m - head_z) > _HEAD_TOL_M):
            continue
        along = [(x - ax) * u[0] + (y - ay) * u[1] for x, y in solid.outline]
        if min(along) < hi and max(along) > lo:
            return element, lo - min(along), max(along) - hi, solid.z1_m, (min(along), max(along))
    return None


@check(Tier.STRUCTURAL, _ID)
def veneer_lintel(ctx: CheckContext) -> list[Finding]:
    wythes = veneer_ties.anchored_wythes(ctx.model)
    openings = [(w, o) for w in wythes for o in ctx.model.openings if o.host_wall == w.tag]
    if not openings:
        return [not_applicable(_ID, f"no opening is hosted in an anchored masonry wythe, of "
                                    f"{len(wythes)} wythes examined", code=_CODE)]
    out: list[Finding] = []
    for wythe, opening in openings:
        tags = (opening.tag, wythe.tag)
        head_z = wythe.z0_m + opening.sill_m + opening.height_m
        found = _lintel(ctx, wythe, opening, head_z)
        span_in = opening.width_m / _IN
        if found is None:
            out.append(failed(
                _ID, f"{opening.tag}: {span_in:.2f}\" of masonry veneer opening with no steel "
                     f"angle lintel under its head (R703.8.3)", tags, code=_CODE,
                fix="author a Beam angle lintel, soffit on the head, bearing 4\" past each jamb"))
            continue
        beam, west_m, east_m, top_z, (lintel_lo, lintel_hi) = found
        flashing = _head_flashing(ctx, wythe, top_z + 0.0625 * _IN, lintel_lo, lintel_hi,
                                  "stainless")
        sheet = flashing or _head_flashing(ctx, wythe, top_z + 0.0625 * _IN, lintel_lo, lintel_hi)
        strip = _head_flashing(ctx, wythe, top_z + 0.0625 * _IN, lintel_lo, lintel_hi, "epdm")
        tags += (beam.tag,)
        bearing = min(west_m, east_m) / _IN
        row = table_row(beam.size)
        brick = next(ly for ly in wythe.layers if ly.function == "structure" and ly.polygon)
        over = _framed_over(ctx, wythe, Polygon(brick.polygon))
        head = f"{opening.tag}: {span_in:.2f}\" clear under {beam.tag} ({beam.size})"
        if row is None:
            out.append(unknown(_ID, f"{head} is not an angle Table R703.8.3.1 lists",
                               tags, code=_CODE))
        elif over:
            out.append(unknown(_ID, f"{head}: {', '.join(over)} stand over the wythe, so the "
                                    f"no-story-above column does not answer", tags, code=_CODE))
        elif bearing < MIN_BEARING_IN - 1e-6:
            out.append(failed(_ID, f"{head}: bearing {bearing:.2f}\" a side, under R703.8.3's "
                                   f"{MIN_BEARING_IN:g}\"", tags, code=_CODE,
                              fix="lengthen the lintel past both jambs"))
        elif span_in > row[1] + 1e-6:
            out.append(failed(_ID, f"{head} spans past the {row[1] / 12:g}' the table allows "
                                   f"that angle with no story above", tags, code=_CODE,
                              fix="a larger angle's row, or a lintel for the span"))
        elif sheet is None:
            out.append(unknown(_ID, f"{head}: no flashing run lies over the lintel (R703.8.5)",
                               tags, code=_CODE))
        elif flashing and "galvaniz" in (getattr(beam, "engineering_note", "") or "").lower() \
                and strip is None:
            out.append(failed(_ID, f"{head}: stainless flashing {flashing} lies on a galvanized "
                                   f"angle with no EPDM strip between", tags, code=_CODE,
                              fix="author an epdm Flashing run under the sheet, over the angle"))
        elif not _COATING.search(getattr(beam, "engineering_note", "") or ""):
            out.append(unknown(_ID, f"{head}: no corrosion protection is stated (R703.8.3: "
                                    f"rust-inhibitive paint, or galvanized or corrosion-"
                                    f"resistant steel)", tags, code=_CODE))
        else:
            out.append(passed(
                _ID, f"{head}: Table R703.8.3.1's {row[0][0]:g}x{row[0][1]:g}x{row[0][2]:g} "
                     f"row spans {row[1] / 12:g}' with no story above, {bearing:.2f}\" of "
                     f"bearing a side (4\" minimum), long leg vertical, galvanized or "
                     f"corrosion-resistant; flashed over per R703.8.5 by {sheet}"
                     f"{'' if strip is None else _ON_STRIP.format(strip)}"
                     f", weeps per R703.8.6 in the detail notes", tags, code=_CODE))
    return out

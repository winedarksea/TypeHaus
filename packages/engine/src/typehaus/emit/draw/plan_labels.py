"""Room label blocks for the architectural floor plan (→ 20 §Drawing IR).

What a room label has to say is fixed by convention and it is three things: what the room
is, how big it is, and how high its ceiling is. The plan said two of them and said the
first one wrong — ``RM-M-LIVING`` is a uid-adjacent authoring tag, not a name a reader has
any use for, and it was printed at 4" of *building*, which is 4.7 pt at the scale the sheet
actually lands on and vanishes at anything smaller.

The third is new. ``ResolvedCeiling`` has carried a per-deck-region plane since
2026-08-25 and no drawing has ever printed it, which is how a house whose basement ceiling
genuinely steps 1 9/16" could look flat on every sheet in the set.

**A room resolves one ceiling record per deck REGION, not per plane.** ``RM-M-LIVING``
resolves four and ``RM-B-STAIR`` resolves four, all at one height — those are polygon parts
of one flat ceiling, and printing four identical notes over one room would be worse than
printing none. ``RM-B-GYM`` resolves two at genuinely different heights (234 SF at 8'-0
15/16" under ``FS-M-EAST``, 90 SF at 7'-11 3/8" under ``SL-M-DECK``) and both belong on the
drawing. So the grouping key is the *plane*, not the record: one note per distinct height,
placed on its own region when there is more than one, and folded into the block when there
is not.

A ``FollowRoof`` ceiling (the whole attic) resolves ``z0_m is None`` — there is no flat
plane to state — and gets ``CLG FOLLOWS ROOF`` rather than a number derived from something
that is not the ceiling.
"""

from __future__ import annotations

from math import gcd

from shapely.geometry import Polygon
from shapely.geometry import box as shapely_box

from typehaus.emit.draw._shared import PLAN_RESERVATION_SCALE
from typehaus.emit.draw._shared import to_in as _in
from typehaus.emit.draw.scene import SceneBuilder, Text
from typehaus.emit.draw.typography import (
    CHAR_ASPECT,
    DIM_TEXT_PT,
    LINE_SPACING,
    TEXT_PT,
    model_in_per_pt,
)
from typehaus.quantities import M_PER_IN
from typehaus.resolve.model import ResolvedCeiling, ResolvedModel, ResolvedRoom, Ring
from typehaus.resolve.room_floor import room_floor_elevation

SF_PER_M2 = 10.7639
ROOM_LAYER = "A-AREA-IDEN"

#: Vertical pitch of a label block's lines, model inches. The lines are a fixed printed
#: size and the block is model-space geometry, so the pitch has to be reserved at some
#: assumed scale — the same one every other plan annotation reserves at.
BLOCK_LINE_PITCH_IN = LINE_SPACING * TEXT_PT * model_in_per_pt(PLAN_RESERVATION_SCALE)

#: Two ceiling records land on the same plane when their soffits agree within this. Well
#: under the 1 9/16" step the basement's mixed deck makes and well over resolver noise.
CEILING_PLANE_TOLERANCE_IN = 0.25

#: A ceiling region smaller than this is not worth its own note — it is a closet return or
#: a stair-well nib, and a second height caption over 4 SF is clutter, not information.
MIN_NOTED_CEILING_SF = 12.0

#: Fraction of a room's clear-face bbox a label line may span before it is dropped. A block
#: wider than its room is not annotation, it is a caption lying across two partitions.
BLOCK_FIT_FRACTION = 0.8


def feet_inches(total_in: float, denominator: int = 16) -> str:
    """``106.56`` → ``8'-10 9/16"``. Drafting form, reduced fraction, no bare zero inches.

    The writers' own ``_feet_inches`` rounds to whole inches, which is right for a
    dimension string (a framer does not chase a sixteenth across 36 feet) and wrong for a
    ceiling height, where the sixteenth is the whole point: 8'-0 15/16" and 7'-11 3/8" are
    the two numbers the basement's mixed deck actually makes, and rounding both to 8'-0"
    and 7'-11" would state a 1" step where 1 9/16" is built.
    """
    sign = "-" if total_in < -1e-9 else ""
    ticks = int(round(abs(total_in) * denominator))
    whole, fraction = divmod(ticks, denominator)
    feet, inches = divmod(whole, 12)
    text = f"{sign}{feet}'-{inches}"
    if fraction:
        common = gcd(fraction, denominator)
        text += f" {fraction // common}/{denominator // common}"
    return text + '"'


def room_display_name(tag: str) -> str:
    """``RM-M-LIVING`` → ``LIVING``; ``RM-GARAGE`` → ``GARAGE``.

    Derived, not authored: ``Room`` carries no name field, and adding one would put a
    second source of truth for the same thing beside a tag that already reads as a name in
    every house in the repo. The storey letter is dropped because the sheet is already one
    storey — ``M`` on the main floor plan is noise — and a segment is only taken for a
    storey code when it is one or two letters, so ``RM-GARAGE`` keeps its word.
    """
    parts = tag.split("-")
    if parts and parts[0] == "RM":
        parts = parts[1:]
    if len(parts) > 1 and len(parts[0]) <= 2 and parts[0].isalpha():
        parts = parts[1:]
    return " ".join(parts) if parts else tag


def _fitted_lines(lines: list[tuple[str, float]],
                  ring: Ring) -> list[tuple[str, float]]:
    """Trim the block to what its room can actually hold, dropping the least useful line first.

    The three lines are already in priority order — a room that cannot hold its ceiling
    height can still hold its area, and one that cannot hold its area still has to say what
    it is. Sizing is a paper measurement converted at the plan's reservation scale, the same
    conversion ``_shared.dimension_offsets`` reserves dimension strings with; catlin's
    19 SF study is the case that forces it, at 4'-1" wide against a ``CLG 8'-11 1/2"``
    caption that wants 5'-3".
    """
    per_pt = model_in_per_pt(PLAN_RESERVATION_SCALE)
    width_m = (max(p[0] for p in ring) - min(p[0] for p in ring)) * BLOCK_FIT_FRACTION
    height_m = (max(p[1] for p in ring) - min(p[1] for p in ring)) * BLOCK_FIT_FRACTION
    kept = list(lines)
    while len(kept) > 1:
        widest = max(len(text) * height_pt * CHAR_ASPECT * per_pt * M_PER_IN
                     for text, height_pt in kept)
        stack = (len(kept) - 1) * BLOCK_LINE_PITCH_IN * M_PER_IN
        if widest <= width_m and stack <= height_m:
            break
        kept.pop()
    return kept


def _inside_point(ring: Ring) -> tuple[float, float]:
    """A point guaranteed to lie inside ``ring`` — where a label may safely sit.

    The vertex average this replaced falls outside an L-shaped room, which is how the
    mudroom's caption came to sit in the mud closet next door.
    """
    polygon = Polygon(ring)
    if not polygon.is_valid or polygon.is_empty:
        return (sum(p[0] for p in ring) / len(ring), sum(p[1] for p in ring) / len(ring))
    point = polygon.representative_point()
    return (point.x, point.y)


def _clamped_anchor(at: tuple[float, float], lines: list[tuple[str, float]],
                    ring: Ring) -> tuple[float, float]:
    """Pull the block's anchor in until the block itself sits inside the room's bbox.

    :func:`_fitted_lines` guarantees the block *fits*; it does not guarantee it is centred
    on somewhere it fits. ``representative_point`` lands wherever the polygon's own
    geometry puts it — well off centre in a long room — so a block that fits by 4" can
    still hang 10" through a partition. Clamping is enough because the block is centred
    text: it only ever needs to move along the axis it overflows.

    The vertical bound has to allow for the LETTERING as well as the stack. A block hangs
    downward from its anchor, so an anchor clamped to ``maxy`` puts the first line's cap
    height above the room's own bbox and the name lies on the wall over it — which is what
    the mechanical room, the mudroom and both baths did. Half a line at each end is the
    room the glyphs themselves take.
    """
    per_pt = model_in_per_pt(PLAN_RESERVATION_SCALE)
    half_width = max(len(text) * height_pt * CHAR_ASPECT for text, height_pt in lines) \
        * per_pt * M_PER_IN / 2.0
    stack = (len(lines) - 1) * BLOCK_LINE_PITCH_IN * M_PER_IN
    half_line = BLOCK_LINE_PITCH_IN * M_PER_IN / 2.0
    minx, maxx = min(p[0] for p in ring), max(p[0] for p in ring)
    miny, maxy = min(p[1] for p in ring), max(p[1] for p in ring)
    x = at[0]
    if maxx - minx > 2 * half_width:
        x = min(max(x, minx + half_width), maxx - half_width)
    y = at[1]
    if maxy - miny > stack + 2 * half_line:
        y = min(max(y, miny + stack + half_line), maxy - half_line)
    return (x, y)


def _ceiling_planes(model: ResolvedModel, room: ResolvedRoom,
                    floor_z_m: float) -> list[tuple[str, float, list[ResolvedCeiling]]]:
    """``(caption, area_sf, regions)`` per distinct ceiling plane over ``room``.

    Sorted by descending area, so the room's dominant plane is the one that folds into the
    block when the caller has to pick.
    """
    records = [c for c in model.ceilings if c.room_ref == room.tag and len(c.outline) >= 3]
    groups: list[tuple[float | None, list[ResolvedCeiling]]] = []
    for record in sorted(records, key=lambda c: (c.z0_m is None, c.z0_m or 0.0, c.tag)):
        height_in = None if record.z0_m is None else (record.z0_m - floor_z_m) / M_PER_IN
        for index, (key, members) in enumerate(groups):
            if key is None and height_in is None:
                groups[index] = (key, [*members, record])
                break
            if (key is not None and height_in is not None
                    and abs(key - height_in) <= CEILING_PLANE_TOLERANCE_IN):
                groups[index] = (key, [*members, record])
                break
        else:
            groups.append((height_in, [record]))
    out = []
    for key, members in groups:
        area = sum(Polygon(m.outline).area for m in members) * SF_PER_M2
        caption = "CLG FOLLOWS ROOF" if key is None else f"CLG {feet_inches(key)}"
        out.append((caption, area, members))
    out.sort(key=lambda item: -item[1])
    return out


def _block_half_width(lines: list[tuple[str, float]]) -> float:
    """Half the printed width of the widest line, in metres at the reservation scale."""
    per_pt = model_in_per_pt(PLAN_RESERVATION_SCALE)
    return max(len(t) * pt * CHAR_ASPECT for t, pt in lines) * per_pt * M_PER_IN / 2.0


def _block_box(at: tuple[float, float],
               lines: list[tuple[str, float]]) -> tuple[float, float, float, float]:
    """The ``(minx, miny, maxx, maxy)`` box, in metres, a block of ``lines`` anchored at ``at``."""
    half_w = _block_half_width(lines)
    pitch = BLOCK_LINE_PITCH_IN * M_PER_IN
    return (at[0] - half_w, at[1] - (len(lines) - 1) * pitch - pitch / 2.0,
            at[0] + half_w, at[1] + pitch / 2.0)


def _overlaps(box: tuple[float, float, float, float],
              others: list[tuple[float, float, float, float]]) -> bool:
    return any(box[0] < o[2] and box[2] > o[0] and box[1] < o[3] and box[3] > o[1]
               for o in others)


#: Candidate offsets for a dodging block, in (half-block-width, half-line) units. Ordered
#: by total displacement, then by how much of it is horizontal: a block nudged UP still
#: reads as the room's label, and one slid sideways reads as belonging to whatever it
#: ended up over. Vertical-only was tried first and is not enough — an opening mark stands
#: *into* the room beside the block, not above it, so ``CLOSET``'s three lines cleared
#: ``D14`` at no vertical offset the room had room for.
_DODGE_STEPS = sorted(
    ((dx, dy) for dx in (0, 1, -1, 2, -2) for dy in (0, 1, -1, 2, -2, 3, -3)),
    key=lambda d: (abs(d[0]) + abs(d[1]), abs(d[0])))


def _place_block(at: tuple[float, float], lines: list[tuple[str, float]], ring: Ring,
                 avoid: list[tuple[float, float, float, float]],
                 prefer: list[tuple[float, float, float, float]] = (),
                 ) -> tuple[tuple[float, float], list[tuple[str, float]]]:
    """Where the block goes and which of its lines survive: inside the room, clear of ``avoid``.

    Two failures, one search.

    **Inside the room, not inside its bounding box.** Both the clamp and
    :func:`_fitted_lines` measure against ``min``/``max`` of the ring, which is the room only
    when the room is a rectangle. ``RM-M-MUDROOM`` is not: its bbox reaches across the
    partition into the stair, so ``CLG 8'-11 1/2"`` was "fitted" to a width the room does not
    have and printed through the wall onto the stringers. Containment is tested against the
    polygon, and only two of catlin's 37 blocks ever needed it — the bbox is a fine
    approximation right up until it isn't.

    **Shedding beats overprinting, but only just.** The trials run longest-first, so a block
    only drops its ceiling line when no placement of the full three is both inside the room
    and clear of the marks — ``MECH`` at 15 SF, with ``D11`` standing into a closet barely
    wider than the bubble. Line order is already priority order (:func:`_fitted_lines`), and
    dropping the last one is the same concession that function makes for the same reason.

    Nothing is ever dropped to zero and no room goes unnamed: the last resort is the clamped
    anchor with whatever ``_fitted_lines`` allowed, overlap and all.

    **``prefer`` is dodged for free and never paid for.** The drawn fixtures and furniture
    are worth stepping around when there is somewhere to step — but they are not worth a
    line. Measured on catlin: 21 blocks sit over a fixture, and treating those like the mark
    bubbles would cost ten of them a line and leave the play room, the laundry and the attic
    bath saying nothing but their name. A washer outline is drawn light on ``A-FURN`` and a
    label reads perfectly well across it; a heavy mark bubble it does not. So each trial
    tries the full obstacle set first and falls back to ``avoid`` alone at the SAME line
    count, and only then shortens. Preference never causes shedding.
    """
    poly = Polygon(ring)
    step_y = BLOCK_LINE_PITCH_IN * M_PER_IN / 2.0
    for trial in (lines[:count] for count in range(len(lines), 0, -1)):
        step_x = _block_half_width(trial)
        for obstacles in ([*avoid, *prefer], avoid) if prefer else (avoid,):
            for dx, dy in _DODGE_STEPS:
                anchor = _clamped_anchor((at[0] + dx * step_x, at[1] + dy * step_y),
                                         trial, ring)
                extents = _block_box(anchor, trial)
                if poly.contains(shapely_box(*extents)) and not _overlaps(extents, obstacles):
                    return anchor, trial
    return _clamped_anchor(at, lines, ring), lines


def emit_room_blocks(b: SceneBuilder, model: ResolvedModel, storey: str,
                     avoid: list[tuple[float, float, float, float]] = (),
                     prefer: list[tuple[float, float, float, float]] = (),
                     ) -> list[tuple[float, float, float, float]]:
    """Name / area / ceiling height, stacked at a point inside each room on ``storey``.

    Returns the ``(minx, miny, maxx, maxy)`` box, in metres, of every block and region
    caption drawn. A room block is the largest annotation on the plan and it sits at the
    room's own inside point, which is exactly where anything else keyed to the room — a
    smoke/CO glyph at its seed, most of all — also wants to be. Handing the boxes back lets
    those callers step aside rather than print through, which is what ``SD/CO`` was doing
    over ``CLOSET / 48 SF`` and ``PLAY N / 324 SF``.
    """
    boxes: list[tuple[float, float, float, float]] = []

    def _record(at: tuple[float, float], lines: list[tuple[str, float]]) -> None:
        boxes.append(_block_box(at, lines))

    for room in model.rooms:
        if room.storey != storey or len(room.clear_face) < 3:
            continue
        cx, cy = _inside_point(room.clear_face)
        planes = _ceiling_planes(model, room, room_floor_elevation(model, room))
        lines = [(room_display_name(room.tag), TEXT_PT),
                 (f"{room.area_m2 * SF_PER_M2:.0f} SF", DIM_TEXT_PT)]
        # One plane (or none worth splitting) folds its caption into the block; two or more
        # get their own caption over their own region, because the *where* is the finding.
        noted = [item for item in planes if item[1] >= MIN_NOTED_CEILING_SF]
        if len(noted) == 1:
            lines.append((noted[0][0], DIM_TEXT_PT))
        lines = _fitted_lines(lines, room.clear_face)
        (cx, cy), lines = _place_block((cx, cy), lines, room.clear_face, avoid, prefer)
        for index, (content, height_pt) in enumerate(lines):
            b.add(Text(anchor=_in((cx, cy - index * BLOCK_LINE_PITCH_IN * M_PER_IN)),
                       content=content, height_pt=height_pt, layer=ROOM_LAYER,
                       align="center"))
        _record((cx, cy), lines)
        if len(noted) > 1:
            # A region's own point can land on top of the block — the dominant region's
            # usually does, since both are derived from the same room — so anything inside
            # the block's stack drops below it. ``RM-B-GYM`` is the case: its 234 SF region
            # and the room share a centroid, so ``CLG 8'-0 15/16" / 234 SF`` printed
            # straight through ``GYM / 324 SF``.
            block_bottom = cy - (len(lines) - 1) * BLOCK_LINE_PITCH_IN * M_PER_IN
            for caption, area_sf, regions in noted:
                largest = max(regions, key=lambda item: Polygon(item.outline).area)
                rx, ry = _inside_point(largest.outline)
                if block_bottom - BLOCK_LINE_PITCH_IN * M_PER_IN <= ry <= cy + \
                        BLOCK_LINE_PITCH_IN * M_PER_IN:
                    ry = block_bottom - BLOCK_LINE_PITCH_IN * M_PER_IN
                line = [(f"{caption} / {area_sf:.0f} SF", DIM_TEXT_PT)]
                b.add(Text(anchor=_in((rx, ry)), content=line[0][0],
                           height_pt=DIM_TEXT_PT, layer=ROOM_LAYER, align="center"))
                _record((rx, ry), line)
    return boxes

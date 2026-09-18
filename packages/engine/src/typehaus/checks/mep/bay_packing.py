"""Does the bay hold everything in it — the capacity half of ``duct_joist_bay_occupancy``.

That check pairs runs: two parallel legs at one station and one elevation, excused by a
joist between them, a vertical gap or a fitting. What it could not say is the question an
installer actually asks, which is not about a pair at all: **with all of it in, is there room
left?** Its own UNKNOWN said so — "this model gives each run one centreline per bay, so it
cannot place two lanes side by side and cannot confirm they were" — and stopped there.

The width is knowable even though the lanes are not. ``resolve/mep_packing`` answers it by
tiers: runs sharing an elevation share the bay's clear width, runs that stack do not, and the
widest tier is what a new run has to fit beside. That is a *capacity* statement, true wherever
anybody slides the lanes, which is exactly why it can be graded while the lane positions
cannot. So the pair verdict keeps its UNKNOWN about arrangement and gains a real number about
room, and an over-subscribed bay — more duct than clear width at one height — becomes the
FAIL it always was.

The same reading serves the router (``routing/corridors``), which is the point of it living
in ``resolve``: a lane priced as free here and full there is how a proposal and a verdict
come apart.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from typehaus.checks._authoring import failed as _fail
from typehaus.checks._authoring import not_applicable
from typehaus.checks._authoring import passed as _pass
from typehaus.checks._authoring import unknown as _unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.quantities import M_PER_IN
from typehaus.resolve.mep_packing import Occupant, pack

if TYPE_CHECKING:  # pragma: no cover - typing only
    from typehaus.resolve.model import ResolvedDuct, ResolvedFloor

#: A leg shorter than this is a jog into a boot, not travel in the bay. Six inches.
_MIN_TRAVEL_M = 6 * M_PER_IN


def bay_packings(floor: ResolvedFloor, runs: list[ResolvedDuct],
                 lines: list[float], clear_m: float | None) -> list[tuple[float, object]]:
    """``(bay centre, Packing)`` for every bay of ``floor`` that carries two or more legs.

    A leg belongs to the bay its centreline falls in, found against the resolved joist
    stations — the same lines ``mep.duct_joist_bay`` grades a straddle against, so a run
    reported as riding a bay is packed into that bay and not a neighbour.
    """
    if clear_m is None or clear_m <= 0 or len(lines) < 2:
        return []
    along_x = floor.direction == "x"
    buckets: dict[int, dict[str, Occupant]] = {}
    for duct in runs:
        for occupant, station in _legs(duct, along_x):
            index = _bay_index(lines, station)
            if index is None:
                continue
            # One entry per run per bay: a run jogging twice in one bay occupies it once.
            buckets.setdefault(index, {}).setdefault(occupant.tag, occupant)

    out: list[tuple[float, object]] = []
    for index in sorted(buckets):
        occupants = list(buckets[index].values())
        if len(occupants) < 2:
            continue  # one run in a cavity competes with nothing
        centre = (lines[index] + lines[index + 1]) / 2.0
        out.append((centre, pack(clear_m, occupants)))
    return out


def packing_note(floor_tag: str, packings: list[tuple[float, object]]) -> tuple[bool, str]:
    """``(over_subscribed, one sentence)`` for a floor's bays, or ``(False, "")``.

    The sentence names only the bays that carry more than one run, because a floor with
    forty clear bays and one shared one has exactly one fact worth printing.
    """
    if not packings:
        return False, ""
    over = [(centre, p) for centre, p in packings if p.oversubscribed()]
    worst = over or sorted(packings, key=lambda item: item[1].remaining_m)[:2]
    parts = [f"the bay at {centre / M_PER_IN / 12:.2f}' has {p.basis()}"
             for centre, p in worst]
    return bool(over), "; ".join(parts)


def _legs(duct: ResolvedDuct, along_x: bool):
    """Horizontal legs of ``duct`` as ``(Occupant, station across the joists)``.

    Only legs travelling WITH the members are bay travel. A leg crossing them passes through
    however many bays it is long and occupies none of them for its width — whether it may
    cross at all is ``member_window``'s question, asked elsewhere and not re-asked here.
    """
    if not duct.z_m or len(duct.z_m) != len(duct.path):
        return
    width = duct.width_m or duct.diameter_m or 0.0
    depth = duct.depth_m or duct.diameter_m or 0.0
    if width <= 0:
        return
    for index in range(len(duct.path) - 1):
        a, b = duct.path[index], duct.path[index + 1]
        dx, dy = b[0] - a[0], b[1] - a[1]
        travel = abs(dx) if along_x else abs(dy)
        across = abs(dy) if along_x else abs(dx)
        if travel < _MIN_TRAVEL_M or across > 1e-9:
            continue
        mid = (duct.z_m[index] + duct.z_m[index + 1]) / 2.0
        station = a[1] if along_x else a[0]
        yield Occupant(duct.tag, width, mid - depth / 2.0, mid + depth / 2.0), station


def _bay_index(lines: list[float], station: float) -> int | None:
    for index in range(len(lines) - 1):
        if lines[index] - 1e-9 <= station <= lines[index + 1] + 1e-9:
            return index
    return None


#: The plan rectangle a segment sweeps, and one leg of a run reduced to what decides
#: whether it shares a bay: ``(tag, travel axis, section width, x band, y band, z band)``.
_Band = tuple[tuple[float, float], tuple[float, float]]
_Occupant = tuple[str, str, float, tuple[float, float], tuple[float, float],
                  tuple[float, float]]


@check(Tier.STRUCTURAL, "mep.duct_joist_bay_occupancy")
def duct_joist_bay_occupancy(ctx: CheckContext) -> list[Finding]:
    """Two runs drawn through the same joist bay at the same station and the same height.

    ``mep.duct_joist_bay`` grades each run against the *framing*: does it straddle a joist
    line, does it fit the clear bay, does it fit the joist depth. Every one of those
    questions is asked of one run at a time, so a cavity can hold two runs on the identical
    bay centre at the identical elevation and both of them pass — the bay is wide enough for
    either, and nothing ever asks about the pair. That is the hole
    ``mep.duct_soffit_occupancy`` closed for a dropped box; this is its joist-bay half, and
    it reuses that module's ``segment_band`` sweep and its pairwise loop.

    **What it does NOT reuse is ``HANGER_GAP_M``, and that is the whole difference between
    a bay and a soffit.** A soffit hangs its contents on straps off a ladder, so 2" between
    them buys a flange and a hand. A joist bay carries them: a semi-rigid radial lies on the
    bottom chord or threads a web, nothing is strapped to anything, and two 3" radials
    touching in a 14 1/2" clear bay is what the neck of a radial bundle looks like. The
    question a bay asks is not "is there room for a hanger" but **"does the bay hold both"**,
    so the clear width is the criterion (``clear_bay_width_m``, derived from the resolved
    joist lines) and it is asked only of runs that actually overlap.

    **Only parallel segments are paired.** Between two runs that *cross*, the same
    subtraction returns a number with no meaning — the twelve FS-S-WEST radials produce "-112
    inches of gap" where one passes over another. Whether a run may cross a joist line at all
    is a real and different question, and ``mep.duct_joist_bay`` already asks it (an open-web
    floor answers with its chord opening).

    Three things excuse a parallel pair, and all three are earned from the model: **a joist
    between them** when they are separated across the joists (``joist_line_stations``, the
    same derivation ``duct_bay_occupancy`` grades a straddle against — runs separated *along*
    the joists cannot have one between them, and the excuse is not offered there); **no
    vertical overlap**, since an 11 7/8" open-web floor stacks two 3" radials with room to
    spare; and **a fitting**, ``ducts_are_joined``, which is a tee and not a collision.

    An overlapping pair the bay can still hold is UNKNOWN, not FAIL, and the distinction is
    the model's rather than the building's: this model gives a run one centreline per bay, so
    two lanes sharing a bay are necessarily drawn on top of each other. The FS-S-WEST note in
    ``plan/mep_erv.py`` says exactly that about STUDY and LAUNDRY. What the check *can* say —
    and what nothing said before — is that they are in the same bay at all, and that the bay
    is or is not wide enough for both.
    """
    from typehaus.checks.mep.bay_packing import bay_packings, packing_note
    from typehaus.resolve.mep_queries import clear_bay_width_m, joist_line_stations
    from typehaus.resolve.mep_soffit import ducts_are_joined, segment_band

    cid = "mep.duct_joist_bay_occupancy"
    floors = {floor.tag: floor for floor in ctx.model.floors}
    by_floor: dict[str, list[ResolvedDuct]] = {}
    for duct in ctx.model.ducts:
        if duct.routing != "joist_bay" or duct.floor_ref not in floors:
            continue
        by_floor.setdefault(duct.floor_ref, []).append(duct)

    out: list[Finding] = []
    for floor_tag in sorted(by_floor):
        runs = by_floor[floor_tag]
        if len(runs) < 2:
            continue  # one run in a cavity competes with nothing
        floor = floors[floor_tag]
        clear_m = clear_bay_width_m(floor)
        lines = joist_line_stations(floor)
        occupants = _bay_occupants(runs, segment_band)
        overlaps: list[tuple[bool, str]] = []
        for index, first in enumerate(occupants):
            for second in occupants[index + 1:]:
                found = _bay_pair_overlap(ctx, floor, lines, clear_m, first, second,
                                          ducts_are_joined)
                if found is not None:
                    overlaps.append(found)
        too_wide = sorted({text for fits, text in overlaps if not fits})
        drawn_over = sorted({text for fits, text in overlaps if fits})
        # The capacity half — see ``checks/mep/bay_packing.py``. Arrangement stays UNKNOWN
        # (one centreline per bay), but how much width is spoken for at the tightest
        # elevation is knowable and is what an installer is actually asking.
        over, packed = packing_note(
            floor_tag, bay_packings(floor, runs, lines, clear_m))
        room = f". Room: {packed}" if packed else ""
        if too_wide:
            out.append(_fail(cid, f"floor {floor_tag}: " + "; ".join(too_wide) + room,
                             (floor_tag,)))
        elif over:
            out.append(_fail(
                cid, f"floor {floor_tag}: {packed} — more duct than clear width at one "
                     "elevation, which no arrangement of the lanes can fix", (floor_tag,)))
        elif drawn_over:
            out.append(_unknown(
                cid, f"floor {floor_tag}: " + "; ".join(drawn_over)
                     + f" — the bay's {(clear_m or 0.0) / M_PER_IN:.1f}\" clear width "
                       "holds them "
                       "both, but this model gives each run one centreline per bay, so it "
                       "cannot place two lanes side by side and cannot confirm they were"
                     + room,
                (floor_tag,)))
        else:
            out.append(_pass(
                cid, f"floor {floor_tag} carries {len(runs)} JOIST_BAY runs and no two "
                     "parallel legs occupy one bay at one station" + room, (floor_tag,)))
    if not out:
        # Earned, not assumed: every JOIST_BAY run in this model was counted, and no floor
        # holds two of them. There is no pair to grade.
        out.append(not_applicable(
            cid, "no floor carries two or more JOIST_BAY duct runs, so no two runs can "
                 "share a bay", ()))
    return out


def _bay_occupants(runs: list[ResolvedDuct],
                   segment_band: Callable[..., _Band | None]) -> list[_Occupant]:
    """``(tag, travel axis, width, x band, y band, z band)`` for every horizontal bay leg.

    Vertical and oblique legs are dropped rather than squared off: a riser's neighbours are a
    different question, and an oblique leg's bounding box claims bay it never enters.
    """
    occupants: list[_Occupant] = []
    for duct in runs:
        if not duct.z_m or len(duct.z_m) != len(duct.path):
            continue
        for index in range(len(duct.path) - 1):
            a, b = duct.path[index], duct.path[index + 1]
            dx, dy = abs(b[0] - a[0]), abs(b[1] - a[1])
            if (dx > 1e-9 and dy > 1e-9) or (dx <= 1e-9 and dy <= 1e-9):
                continue  # oblique, or a riser
            band = segment_band(a, b, duct.width_m, duct.depth_m)
            if band is None:
                continue
            mid = (duct.z_m[index] + duct.z_m[index + 1]) / 2.0
            occupants.append((duct.tag, "x" if dy <= 1e-9 else "y", duct.width_m,
                              band[0], band[1],
                              (mid - duct.depth_m / 2.0, mid + duct.depth_m / 2.0)))
    return occupants


def _bay_pair_overlap(ctx: CheckContext, floor: ResolvedFloor, lines: list[float],
                      clear_m: float | None, first: _Occupant, second: _Occupant,
                      joined: Callable[..., bool]) -> tuple[bool, str] | None:
    """``(the bay holds both, message)`` for two parallel legs sharing one bay, else None."""
    tag, axis, width, x_band, y_band, z_band = first
    other_tag, other_axis, other_width, other_x, other_y, other_z = second
    if tag == other_tag or axis != other_axis:
        return None
    along, across = ((x_band, y_band) if axis == "x" else (y_band, x_band))
    other_along, other_across = ((other_x, other_y) if axis == "x" else (other_y, other_x))
    shared = min(along[1], other_along[1]) - max(along[0], other_along[0])
    if shared <= 1e-9:
        return None
    if (min(z_band[1], other_z[1]) - max(z_band[0], other_z[0])) <= 1e-9:
        return None  # stacked in the bay's depth, not side by side in it
    lap = min(across[1], other_across[1]) - max(across[0], other_across[0])
    if lap <= 1e-9:
        return None  # side by side in the bay, which is what a bay is for
    # A joist can only stand between them when the separation axis IS the across-joist axis.
    # Two legs separated ALONG the joists have no member between them by definition.
    if axis == floor.direction and any(
            min(across[1], other_across[1]) - 1e-9 <= line
            <= max(across[0], other_across[0]) + 1e-9 for line in lines):
        return None
    if joined(ctx.model, tag, other_tag):
        return None
    together = width + other_width
    fits = clear_m is not None and together <= clear_m + 1e-9
    return (fits, f"ducts {tag} and {other_tag} run through one {floor.tag} bay for "
                  f"{shared / M_PER_IN:.1f}\", overlapping by "
                  f"{lap / M_PER_IN:.2f}\" across it; {together / M_PER_IN:.1f}\" of duct "
                  f"in a {(clear_m or 0.0) / M_PER_IN:.1f}\" clear bay")

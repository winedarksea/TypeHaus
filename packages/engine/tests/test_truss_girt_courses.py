"""The girt COURSE module: one ladder, three edges, and the rake (→ 11 §Framing).

Sibling of `test_truss_girt_geometry.py`, which asks where a block lands and whether a
course is carried. This one asks a different question — *where are the courses at all* —
and it is the question the 2026-08-30 change is about:

* **one module, unbroken.** Every course is at `course_phase + k * spacing`, from the wall
  base through the gable rake, with three named exceptions and no others. Until this change
  a raked wall forced a course at its LOWER top and re-phased everything above it, which put
  the whole rake band 11-1/2" off the module of the wall below it;
* **the module counts from the sills' own datum.** `course_datum="framing-base"` +
  `course_offset` is the phase, and on a main-storey wall extended down over the floor rim
  that is 13-7/16" above the wall base;
* **the rake is nailed, and the field stands clear of it.** One member along each raked top,
  blocked on the stud module, with no field course inside one board face of it;
* **and the openings.** No field course may land in the shadow of an opening's own head or
  sill course — the pathology `notes/outie_window_truss_detail.md` tabulates.
"""

from __future__ import annotations

import pytest

from typehaus.resolve.framing.furring import (
    band_tops,
    course_elevations,
    course_phase,
)
from typehaus.resolve.framing.truss_wall import truss_girt_bands, truss_kind
from typehaus.resolve.geometry import length, sub, unit

IN = 0.0254
_STOCK_FACE = 3.5 * IN
_STUD_SPACING = 16.0 * IN
#: The BLOCK module — every OTHER stud since 2026-09-01, when one tier and one screw per
#: crossing replaced two tiers offset half a bay.
_BLOCK_SPACING = 32.0 * IN

#: The conflict window, bottom to bottom, between a field course and an opening's own head
#: or sill course. Two courses less than this apart are two nailers inside one board face —
#: either half-lapped in elevation or separated by a gap too narrow to be worth a board.
#: Exactly zero apart is the BEST case: the field course *is* the head or sill course.
_CONFLICT_IN = 7.0


def _girt_walls(model):
    return [w for w in model.walls if truss_kind(model.plan, w.assembly) == "girt"]


def _raked(wall) -> bool:
    top0, top1 = band_tops(wall)
    return abs(top0 - top1) > 1e-9


def _spec(model, wall):
    """The OUTER girt band's authored FramingSpec — the one the courses are read off."""
    return truss_girt_bands(model.plan, wall.assembly)[1].framing


def _band_members(wall, model, rake: bool):
    """One band's members, keyed by tier — and only the tiers the wall actually has.

    ``truss_girt_bands`` returns ``inner`` as ``None`` on the ONE-TIER wall the house has
    built since 2026-09-01, so the pair is filtered rather than unpacked blind. The outer
    band is always there: it is the girt.
    """
    inner, outer = truss_girt_bands(model.plan, wall.assembly)
    out = {}
    for tier, band in (("1", inner), ("2", outer)):
        if band is None:
            continue
        prefix = f"strapping-{band.name}-rake-" if rake else f"strapping-{band.name}-"
        members = [m for m in wall.members if m.child_key.startswith(prefix)]
        if not rake:
            members = [m for m in members
                       if not m.child_key.startswith(f"strapping-{band.name}-rake-")]
        out[tier] = members
    return out


def test_the_courses_are_one_module_from_the_base_through_the_rake(catlin_model):
    """`phase + k*spacing`, and the three edges are the only exceptions.

    The starter at the wall base, the top course at `top_low - face` on a level wall, and
    nothing else. Every OTHER course is on the module — including every course of a gable
    rake, which is the whole point: before 2026-08-30 a raked wall forced a course at its
    lower top and counted the rest from THERE, and W-A-N1's rake band sat 11-1/2" off the
    module of W-S-N1 directly below it.
    """
    off_module: list[tuple[str, float]] = []
    over_spacing: list[tuple[str, float]] = []
    checked = 0
    for wall in _girt_walls(catlin_model):
        spec = _spec(catlin_model, wall)
        spacing = spec.spacing.meters
        phase = course_phase(wall, spec)
        elevations = course_elevations(wall, spec, _STOCK_FACE)
        top_low = min(band_tops(wall))
        edges = {round(wall.z0_m, 9)}
        if not _raked(wall):
            edges.add(round(top_low - _STOCK_FACE, 9))
        for z in elevations:
            if round(z, 9) in edges:
                continue
            remainder = (z - phase) % spacing
            if min(remainder, spacing - remainder) > 1e-9:
                off_module.append((wall.tag, (z - wall.z0_m) / IN))
        for below, above in zip(elevations, elevations[1:], strict=False):
            if above - below > spacing + 1e-9:
                over_spacing.append((wall.tag, (above - below) / IN))
        checked += 1
    assert checked >= 30
    assert not off_module, f"girt courses off their own module: {off_module[:6]}"
    assert not over_spacing, f"course bays wider than the authored spacing: {over_spacing[:6]}"


def test_the_module_counts_from_the_datum_the_sills_do(catlin_model):
    """`course_datum="framing-base"`: the phase is the floor line, not the wall base.

    On a main-storey wall the two are 13-7/16" apart — `platform.py` extends the wall down
    over the floor rim band, and the courses were phased off the bottom of that lap while
    every sill in the same wall was phased off the floor above it. Half an inch of that
    mismatch is what the sliver table in `notes/outie_window_truss_detail.md` was.
    """
    main = [w for w in _girt_walls(catlin_model)
            if abs(w.base_ref_z_m - w.z0_m) > 1e-9]
    assert main, "the main storey's girt walls are extended down over the floor rim band"
    for wall in main:
        spec = _spec(catlin_model, wall)
        assert spec.course_datum == "framing-base", wall.tag
        expected = wall.base_ref_z_m + spec.course_offset.meters
        assert course_phase(wall, spec) == pytest.approx(expected, abs=1e-12), wall.tag
        # And it is NOT the wall base: a test that passes either way tests nothing.
        assert abs(course_phase(wall, spec) - wall.z0_m) > 1e-3, wall.tag


def test_every_raked_girt_wall_carries_a_nailer_along_its_rake(catlin_model):
    """One per band, its top face on the rake, blocked on the stud module.

    `plans/TODO.md`'s open hole: the courses stop where the wall runs out from under them,
    which left a gable's raked cladding edge — the most exposed cut on the building —
    lapping nothing at all.
    """
    raked = [w for w in _girt_walls(catlin_model) if _raked(w)]
    assert len(raked) >= 4, "catlin's four gables"
    for wall in raked:
        top0, top1 = band_tops(wall)
        rakes = _band_members(wall, catlin_model, rake=True)
        for tier, members in rakes.items():
            assert members, f"{wall.tag} tier {tier}: no rake nailer"
            for member in members:
                z1_end = member.z1_m if member.z1_end_m is None else member.z1_end_m
                assert member.z1_m == pytest.approx(
                    member.z0_m + _STOCK_FACE, abs=1e-9), member.child_key
                for z in (member.z1_m, z1_end):
                    assert min(top0, top1) - 1e-6 <= z <= max(top0, top1) + 1e-6, (
                        f"{wall.tag}: a rake nailer's top face is off the rake")
        blocks = [m for m in wall.members
                  if m.category == "truss_block" and "-rake-" in m.child_key]
        assert blocks, f"{wall.tag}: a rake nailer with no block under it"
        direction = unit(sub(wall.axis[1], wall.axis[0]))
        for tier in rakes:
            prefix = f"block-{tier}-rake-"
            stations = sorted(
                (m.p0[0] - wall.axis[0][0]) * direction[0]
                + (m.p0[1] - wall.axis[0][1]) * direction[1]
                for m in blocks if m.child_key.startswith(prefix))
            for a, b in zip(stations, stations[1:], strict=False):
                assert b - a <= _BLOCK_SPACING + _STOCK_FACE + 1e-6, (
                    f"{wall.tag} tier {tier}: {(b - a) / IN:.1f}\" between rake blocks")


def test_the_field_stands_one_board_clear_of_the_rake_nailer(catlin_model):
    """The same clearance a field course keeps from an opening's head course.

    A course that ran up to the nailer would be the second half of a 7" slab of wood in a
    wall whose whole point is that it is mostly foam, and it is what left short raked stubs
    at the attic gables — a 4" triangle of girt carrying a block that hung out past its end.
    """
    for wall in (w for w in _girt_walls(catlin_model) if _raked(w)):
        top0, top1 = band_tops(wall)
        rise = top1 - top0
        run = length(sub(wall.axis[1], wall.axis[0]))
        direction = unit(sub(wall.axis[1], wall.axis[0]))
        for members in _band_members(wall, catlin_model, rake=False).values():
            for member in members:
                for point in (member.p0, member.p1):
                    station = ((point[0] - wall.axis[0][0]) * direction[0]
                               + (point[1] - wall.axis[0][1]) * direction[1])
                    top = top0 + rise * (station / run) if run > 1e-9 else top0
                    assert member.z1_m <= top - _STOCK_FACE + 1e-6, (
                        f"{wall.tag}: field course {member.child_key} reaches within a "
                        f"board of the rake at station {station / IN:.1f}\"")


def test_no_field_course_lands_in_the_shadow_of_a_head_or_sill_course(catlin_model):
    """The sliver: two nailers inside one board face, one of them redundant.

    An opening's own head and sill courses are 3-1/2" boards at fixed elevations
    (`GirtFrame.opening_frame`), and a field course near one is either half-lapped with it
    or separated from it by a gap too narrow to be worth a board. Exactly coincident is the
    best case and the design rule — which FLIPPED with the phase on 2026-09-01, because a
    course BOTTOM now lands on the framing-base module rather than a course top: **put the
    HEAD on a 24" multiple above the sole plate, or the SILL 3-1/2" above one.**

    The number is asserted rather than driven to zero because zero is not reachable and the
    plan that asked for it was wrong about that: the second storey carries sills at 152" and
    156", 4" apart, on different walls but on ONE module, so any phase clean for one group
    is 4" off for the other.

    **RE-SWEPT 2026-09-01 for the 24" module**, at 1/8" from -16" to +8", and the winner is
    ``course_offset = 0`` — 13 exact hits and 30 slivers, against 9/24 at the -3.5" phase the
    32" module used. Two things to read before changing either number. A finer module frames
    a third more courses, so *more* of them fall within 7" of an opening edge no matter what
    the phase is: 30 slivers at 24" is not worse layout than 19 at 32", it is more course.
    And the -3.5" phase is no longer available at all — it opens a 24.75" bay on nine walls
    (the forced top course pops the module course under it), which
    ``structural.girt_course_spacing`` fails. Of the phases that keep every bay at or under
    24.00", zero is the one with the most exact hits by a clear margin; the runners-up trade
    5 fewer slivers for all 13 of them. If a window moves, both numbers move — re-sweep
    rather than nudging the bound.
    """
    conflicts: list[tuple[str, str, float]] = []
    exact = 0
    for wall in _girt_walls(catlin_model):
        elevations = course_elevations(wall, _spec(catlin_model, wall), _STOCK_FACE)
        if not elevations:
            continue
        for opening in (o for o in catlin_model.openings if o.host_wall == wall.tag):
            sill = wall.base_ref_z_m + opening.sill_m
            for name, course_z in (("sill", sill - _STOCK_FACE),
                                   ("head", sill + opening.height_m)):
                nearest = min(elevations, key=lambda z, c=course_z: abs(z - c))
                gap = abs(nearest - course_z) / IN
                if gap < 1e-6:
                    exact += 1
                elif gap < _CONFLICT_IN - 1e-6:
                    conflicts.append((wall.tag, f"{opening.tag} {name}", round(gap, 2)))
    assert exact >= 13, f"only {exact} opening edges land on a course line"
    assert len(conflicts) <= 30, (
        f"{len(conflicts)} field courses in the shadow of an opening's own course "
        f"(30 is the swept optimum at 24\" o.c. among the phases that keep every bay "
        f"within the module): {sorted(conflicts)[:8]}")

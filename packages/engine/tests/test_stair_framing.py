"""Stair framing regression coverage (raked stringers, split-landing platforms, well
partition, wall bearing, winder turn framing — plans: "stairs aren't framed properly" and
"stair landing & winder support framing").

Guards the U-stair rebuild: no coincident members, split-landing riser budget
(lower treads · landing · landing+riser · upper treads · arrival), raked stringers that
never read as floor-to-floor prisms, a framed well partition, deduplicated landing-platform
joists, and hanger bands that bear at the landing rather than the arrival deck.

Then the support pass: every landing corner is either ledgered onto a host wall or posted
down to the subfloor (this used to be reachable only on concrete), the host is the wall
that actually carries the run rather than whichever was declared first, and the winder turn
is a real frame — newel, two raked carriages, and the header the straight flight springs on.
"""

from __future__ import annotations

import math
import uuid
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from typehaus.checks.structural.stairs import stair_riser_uniformity
from typehaus.emit.draw import build_floorplan
from typehaus.emit.draw.scene import Polyline
from typehaus.findings import Result
from typehaus.model import (
    Assembly,
    Building,
    FloorOpening,
    FloorSystem,
    FramingSpec,
    JoistSpec,
    Layer,
    LayerFunction,
    Library,
    Material,
    Node,
    PlanModel,
    Project,
    Site,
    Stair,
    Storey,
    Wall,
    degF,
    ft,
    inch,
    pt,
)
from typehaus.model.enums import StructuralRole
from typehaus.resolve import resolve
from typehaus.resolve.framing.profiles import cross_section
from typehaus.source import load_plan

CATLIN_DIR = Path(__file__).resolve().parents[3] / "houses" / "catlin"


@pytest.fixture(scope="module")
def catlin_model():
    result = load_plan(CATLIN_DIR)
    assert result.plan is not None, [f.message for f in result.findings]
    model, findings = resolve(result.plan)
    errors = [f for f in findings if f.severity.value == "error"]
    assert not errors, [f.message for f in errors]
    return model


@pytest.fixture(scope="module")
def basement_stair(catlin_model):
    return next(stair for stair in catlin_model.stairs if stair.tag == "ST-B2M")


@pytest.fixture(scope="module")
def main_stair(catlin_model):
    """ST-M2S: a u_split_landing springing off a *framed* deck, not concrete."""
    return next(stair for stair in catlin_model.stairs if stair.tag == "ST-M2S")


@pytest.fixture(scope="module")
def winder_stair(catlin_model):
    return next(stair for stair in catlin_model.stairs if stair.tag == "ST-S2A")


def _subfloor(catlin_model, stair) -> float:
    storey = catlin_model.plan.storey(stair.storey)
    assert storey is not None
    return storey.elevation.meters


def _landing_zone(stair) -> tuple[float, float]:
    """ST-B2M's landing zone in the run direction: the last landing_depth of the run."""
    ys = [point[1] for point in stair.outline]
    return max(ys) - ft(4).meters, max(ys)


# ------------------------------------------------------------------ 1. no coincidences
def test_no_two_stair_members_are_coincident(catlin_model):
    """Kills both historical coincidence bugs: the byte-identical step-between-landings /
    landing-upper pair, and the min()-clamped duplicate landing joists."""
    for stair in catlin_model.stairs:
        seen = {}
        for member in stair.members:
            key = (member.p0, member.p1, round(member.z0_m, 6), round(member.z1_m, 6))
            assert key not in seen, (
                f"{stair.tag}: {member.child_key} coincides with {seen[key]}")
            seen[key] = member.child_key


# ----------------------------------------------------------------- 2. U riser budget
def test_u_stair_landings_split_one_riser_apart_inside_the_landing_zone(
        catlin_model, basement_stair):
    stair = basement_stair
    riser = stair.riser_height_m
    subfloor = _subfloor(catlin_model, stair)
    members = {member.child_key: member for member in stair.members}
    lower, upper = members["landing-lower"], members["landing-upper"]
    lower_treads = (stair.riser_count - 3 + 1) // 2
    # ``z1_m`` is the landing's finished walking face; the deck board is dropped below it
    # (``_notch_z``) so the risers onto and off the platform are the flight's own.
    assert lower.z1_m == pytest.approx(subfloor + riser * (lower_treads + 1))
    assert upper.z1_m - lower.z1_m == pytest.approx(riser)
    zone_lo, zone_hi = _landing_zone(stair)
    for landing in (lower, upper):
        for point in (landing.p0, landing.p1):
            assert zone_lo - 1e-6 <= point[1] <= zone_hi + 1e-6, landing.child_key
    # The step between the landings IS the riser between them — no separate member.
    assert "step-between-landings" not in members
    # Top upper tread ends one riser below the arrival deck.
    arrival = subfloor + riser * stair.riser_count
    top_tread = max((m for m in stair.members if m.child_key.startswith("tread-upper-")),
                    key=lambda m: m.z0_m)
    assert top_tread.z1_m == pytest.approx(arrival - riser)


# ---------------------------------------------------------------- 3. raked stringers
def test_stringers_are_raked_and_never_drop_below_the_subfloor(catlin_model):
    for stair in catlin_model.stairs:
        subfloor = _subfloor(catlin_model, stair)
        stringers = [m for m in stair.members if m.category == "stringer"]
        assert stringers, stair.tag
        for stringer in stringers:
            assert stringer.z0_end_m is not None and stringer.z1_end_m is not None, (
                f"{stair.tag}:{stringer.child_key} is not raked")
            low = min(stringer.z0_m, stringer.z1_m, stringer.z0_end_m, stringer.z1_end_m)
            assert low >= subfloor - 1e-9, f"{stair.tag}:{stringer.child_key}"
            # A raked stringer is never a full-height prism over its run.
            span = max(stringer.z1_m, stringer.z1_end_m) - min(stringer.z0_m,
                                                               stringer.z0_end_m)
            rise = stair.riser_height_m * stair.riser_count
            assert (max(stringer.z1_m - stringer.z0_m,
                        stringer.z1_end_m - stringer.z0_end_m) < rise - 1e-6), (
                f"{stair.tag}:{stringer.child_key} reads as a floor-to-floor prism")
            assert span <= rise + 1e-6


def test_lower_flight_stringers_top_out_at_the_landing_bearing(catlin_model,
                                                               basement_stair):
    stair = basement_stair
    subfloor = _subfloor(catlin_model, stair)
    lower_treads = (stair.riser_count - 3 + 1) // 2
    landing_z = subfloor + stair.riser_height_m * (lower_treads + 1)
    # The stringer tops out at the landing's *notch* line — the deck it carries sits on it.
    for stringer in (m for m in stair.members
                     if m.child_key.startswith("stringer-lower-")):
        assert stringer.z1_end_m == pytest.approx(landing_z - inch(1.5).meters)


# ----------------------------------------------------------------- 4. well partition
def test_well_partition_is_framed_between_subfloor_and_arrival(catlin_model,
                                                               basement_stair):
    stair = basement_stair
    subfloor = _subfloor(catlin_model, stair)
    arrival = subfloor + stair.riser_height_m * stair.riser_count
    partition = [m for m in stair.members if m.category == "partition"]
    keys = {m.child_key for m in partition}
    assert "well-partition-plate-bottom" in keys and "well-partition-plate-top" in keys
    studs = [m for m in partition if m.child_key.startswith("well-partition-stud-")]
    assert len(studs) >= 2
    for member in partition:
        assert member.z0_m >= subfloor - 1e-9, member.child_key
        assert member.z1_m <= arrival + 1e-9, member.child_key
    for stud in studs:
        assert stud.p0 == stud.p1 and stud.orient is not None, stud.child_key
    # The old single full-height box is gone.
    assert "well-partition" not in {m.child_key for m in stair.members}


# --------------------------------------------------------------- 5. landing platforms
def test_landing_platforms_have_unique_joists_edge_joists_deck_and_rims(basement_stair):
    stair = basement_stair
    for name in ("lower", "upper"):
        deck = next(m for m in stair.members if m.child_key == f"landing-{name}")
        assert deck.profile.startswith("deck ")
        # The platform's own depth: R311.7.6 floors the authored landing_depth at the
        # flight width, so read it off the deck rather than restating the authored number.
        depth = deck.length_m
        joists = [m for m in stair.members
                  if m.child_key.startswith(f"landing-joist-{name}-")]
        positions = sorted(round(joist.p0[1], 6) for joist in joists)
        assert len(positions) == len(set(positions)), f"duplicate {name} landing joists"
        span_lo = min(positions)
        offsets = [position - span_lo for position in positions]
        assert offsets[0] == pytest.approx(0.0)
        assert offsets[-1] == pytest.approx(depth)
        spacings = [b - a for a, b in zip(offsets, offsets[1:])]
        assert all(spacing <= inch(16).meters + 1e-9 for spacing in spacings)
        rims = [m for m in stair.members if m.child_key.startswith(f"landing-rim-{name}-")]
        assert len(rims) == 2
        for rim in rims:
            assert rim.z1_m == pytest.approx(deck.z0_m)  # framing tops at the deck


# ------------------------------------------------------------ 6. concrete-wall hangers
def test_basement_lower_hanger_bears_at_the_landing(catlin_model, basement_stair):
    stair = basement_stair
    lower_hangers = [m for m in stair.members
                     if m.category == "hanger"
                     and "stringer-lower" in m.child_key]
    assert lower_hangers
    for hanger in lower_hangers:
        assert hanger.connection is not None
        assert hanger.connection.startswith("concrete-wall-hanger:")
        # A framed-wall bearing is annotation-only; a hanger band is concrete-only.
        assert not hanger.connection.startswith("framed-wall-ledger:")
        assert hanger.z1_end_m == pytest.approx(-1.410, abs=0.01)
    # The annotated stringer carries the same connection tag.
    tagged = [m for m in stair.members if m.category == "stringer"
              and m.connection is not None]
    assert any("stringer-lower" in m.child_key for m in tagged)


# ------------------------------------------------------------------- 7. cross-sections
def test_stair_profiles_parse_to_explicit_cross_sections():
    hanger = cross_section("hanger")
    assert (hanger.width_m, hanger.depth_m) == (
        pytest.approx(inch(1.5).meters), pytest.approx(inch(8.0).meters))
    tapered = cross_section("tapered tread")
    assert (tapered.width_m, tapered.depth_m) == (
        pytest.approx(inch(1.5).meters), pytest.approx(inch(11.25).meters))
    deck = cross_section("deck 42x1.5")
    assert (deck.width_m, deck.depth_m) == (
        pytest.approx(inch(42).meters), pytest.approx(inch(1.5).meters))
    post = cross_section("4x4")
    assert (post.width_m, post.depth_m) == (
        pytest.approx(inch(3.5).meters), pytest.approx(inch(3.5).meters))


def test_riser_walk_is_continuous_one_riser_steps(catlin_model, basement_stair):
    """Walking the flight bottom-to-top hits every riser exactly once: treads, lower
    landing, upper landing, upper treads, arrival — no 2-riser jump anywhere.

    The walk is measured on the *finished faces* (``z1_m``): a board's top is what a foot
    lands on, and it is dropped to the step elevation rather than stacked on it, so the
    first and last risers match the flight's own. ``structural.stair_riser_uniformity``
    makes the same measurement for every stair in the model.
    """
    stair = basement_stair
    subfloor = _subfloor(catlin_model, stair)
    walk = sorted(m.z1_m for m in stair.members
                  if m.category == "tread" or m.child_key in ("landing-lower",
                                                              "landing-upper"))
    arrival = subfloor + stair.riser_height_m * stair.riser_count
    walk.append(arrival)
    previous = subfloor
    for elevation in walk:
        assert elevation - previous == pytest.approx(stair.riser_height_m, abs=1e-6)
        previous = elevation
    assert math.isclose(previous, arrival, abs_tol=1e-9)


# ------------------------------------------------------- 8. landing corner load path
def _connection_endpoints(stair) -> set[tuple[float, float]]:
    """Plan points carried by a wall — either concrete ledger or framed-wall ledger."""
    out: set[tuple[float, float]] = set()
    for member in stair.members:
        if member.connection is None:
            continue
        if member.connection.startswith(("concrete-wall-hanger:", "framed-wall-ledger:")):
            out.update((round(p[0], 4), round(p[1], 4)) for p in (member.p0, member.p1))
    return out


def test_every_landing_platform_corner_is_supported(catlin_model):
    """The one test that would have caught the bug: ST-M2S's landing platforms had real
    framing (deck + joists + rims) resting on nothing, because the whole support pass sat
    inside a foundation-walls-only branch."""
    for stair in catlin_model.stairs:
        rims = [m for m in stair.members if m.child_key.startswith("landing-rim-")]
        if not rims:
            continue
        subfloor = _subfloor(catlin_model, stair)
        carried = _connection_endpoints(stair)
        posts = [m for m in stair.members if m.p0 == m.p1 and m.orient is not None]
        for rim in rims:
            underside = rim.z0_m
            for point in (rim.p0, rim.p1):
                key = (round(point[0], 4), round(point[1], 4))
                if key in carried:
                    continue
                beneath = [p for p in posts
                           if (round(p.p0[0], 4), round(p.p0[1], 4)) == key
                           and p.z0_m == pytest.approx(subfloor, abs=1e-6)
                           and p.z1_m >= underside - 1e-6]
                assert beneath, (
                    f"{stair.tag}: {rim.child_key} corner {key} bears on nothing")


def test_framed_wall_bearing_picks_the_longest_host(main_stair):
    """W-M-C4B overlaps stringer-upper-1 by 4" and is declared first; W-M-C5 carries
    5'-8" of it. First-match-wins picked the 4" clip."""
    members = {m.child_key: m for m in main_stair.members}
    for key in ("stringer-upper-1", "landing-rim-upper-1"):
        assert members[key].connection == "framed-wall-ledger:W-M-C5", key
    for key in ("stringer-lower-0", "landing-rim-lower-0"):
        assert members[key].connection == "framed-wall-ledger:W-M-STRW", key


def test_framed_hosts_emit_ledger_boards_flush_with_the_wall_face(catlin_model,
                                                                  main_stair):
    """A framed host now carries its stringer/rim on a real ledger board, not an
    annotation alone — but never one drawn on the wall's *centreline* (that would be
    geometry invented inside the stud cavity, the old reason nothing was emitted).
    The board sits flush against the host's face on the member's side: half its own 1.5"
    thickness off that face.

    The face is read from the resolved layer polygons, not from ``axis ± thickness/2``.
    On a wall whose ``alignment`` names a *face* — every exterior wall in this house —
    the axis is not the centre, so the arithmetic version lands mid-wall on one side and
    outside the building on the other. ST-S2A's winder carriage is ledgered on W-S-E1,
    which is exactly such a wall.
    """
    walls = {wall.tag: wall for wall in catlin_model.walls}
    for stair in catlin_model.stairs:
        for member in stair.members:
            if member.category != "hanger":
                continue
            assert member.connection is not None
            if member.child_key.startswith("hanger-"):
                assert member.connection.startswith("concrete-wall-hanger:"), member.child_key
            else:
                assert member.child_key.startswith("ledger-"), member.child_key
                assert member.connection.startswith("framed-wall-ledger:"), member.child_key
                host = walls[member.connection.split(":", 1)[1]]
                (ax, ay), (bx, by) = host.axis
                cross = 0 if abs(bx - ax) < 1e-6 else 1
                depth = [point[cross] for layer in host.depth_layers()
                         for point in layer.polygon]
                near, far = min(depth), max(depth)
                face = far if member.p0[cross] >= (near + far) / 2.0 else near
                assert abs(member.p0[cross] - face) == pytest.approx(
                    inch(0.75).meters), member.child_key
                # And never inside the wall: the board hangs off the face, not in the bays.
                assert not near < member.p0[cross] < far, member.child_key
    # ST-M2S's known framed hosts each carry at least one real ledger board.
    ledger_hosts = {m.connection.split(":", 1)[1] for m in main_stair.members
                    if m.child_key.startswith("ledger-")}
    assert {"W-M-C5", "W-M-STRW"} <= ledger_hosts


def test_no_stair_member_is_degenerate(catlin_model):
    """A member is a line in plan or a vertical with a real height — never a point with
    no z-extent (the shape a collapsed/clipped carriage would take)."""
    for stair in catlin_model.stairs:
        for member in stair.members:
            if member.p0 != member.p1:
                continue
            assert member.orient is not None, f"{stair.tag}:{member.child_key}"
            assert member.z1_m - member.z0_m > 1e-6, f"{stair.tag}:{member.child_key}"


def test_plan_symbols_skip_zero_length_stair_members(catlin_model):
    """A vertical post/newel is a point in plan; drawing it as a polyline emits a
    zero-length A-STAIR entity that reads as a stray tick."""
    for storey in catlin_model.plan.storeys:
        for node in build_floorplan(catlin_model, storey.tag).nodes:
            if not isinstance(node, Polyline) or node.layer != "A-STAIR":
                continue
            (x0, y0), (x1, y1) = node.points[0], node.points[-1]
            assert math.hypot(x1 - x0, y1 - y0) > 1e-9, node.tag


# --------------------------------------------------------------- 9. the winder turn
def _winder_reference(catlin_model, winder_stair):
    subfloor = _subfloor(catlin_model, winder_stair)
    riser = winder_stair.riser_height_m
    return subfloor, riser, winder_stair.winder_count


def test_winder_newel_carries_every_winder_narrow_end(catlin_model, winder_stair):
    subfloor, riser, count = _winder_reference(catlin_model, winder_stair)
    newels = [m for m in winder_stair.members if m.category == "newel"]
    newel = next(m for m in newels if m.child_key == "newel-000")
    assert newel.p0 == newel.p1 and newel.orient is not None
    assert newel.z0_m == pytest.approx(subfloor)
    # The box assembly's inside corner post: it runs from the subfloor to the top box's
    # deck, which every tier's rims and the flight's inner stringer die into.
    assert newel.z1_m == pytest.approx(subfloor + riser * count)
    winders = [m for m in winder_stair.members if m.category == "winder"]
    assert len(winders) == count
    # Each narrow end lands on the newel's own face — between half a face and half a
    # diagonal out from its centreline, whichever face the winder's ray exits through.
    half_face = cross_section(newel.profile).width_m / 2.0
    for winder in winders:
        reach = math.hypot(winder.p0[0] - newel.p0[0], winder.p0[1] - newel.p0[1])
        assert half_face - 1e-9 <= reach <= half_face * math.sqrt(2.0) + 1e-9, winder.child_key
        assert winder.z1_m <= newel.z1_m + 1e-9


def test_winder_turn_is_a_stack_of_platform_boxes(catlin_model, winder_stair):
    """Larry Haun's winder: one platform box per step, each landing flush on the one
    below, rather than a compound-angle carriage cut through the turn.

    A box's sides are ripped to exactly one riser less the deck they carry, so box ``k``'s
    underside is box ``k-1``'s finished face and box 0's is the subfloor. Nothing floats
    and nothing laps.
    """
    subfloor, riser, count = _winder_reference(catlin_model, winder_stair)
    tread_thickness = inch(1.5).meters
    assert not [m for m in winder_stair.members
                if m.child_key.startswith(("winder-carriage-", "winder-header"))], (
        "the compound-angle carriage/header fiction is gone")
    for index in range(count):
        rims = [m for m in winder_stair.members
                if m.child_key.startswith(f"landing-rim-winder{index}-")]
        assert rims, f"box {index} has no sides"
        deck = subfloor + riser * (index + 1)  # the winder tread's finished face
        for rim in rims:
            assert rim.category == "landing", rim.child_key
            assert rim.z1_m == pytest.approx(deck - tread_thickness), rim.child_key
            assert rim.z0_m == pytest.approx(subfloor + riser * index), rim.child_key
            assert rim.profile.endswith(" rim"), rim.child_key
        # The winder tread is this box's deck: its underside is the box's top.
        winder = next(m for m in winder_stair.members
                      if m.child_key == f"winder-{index:03d}")
        assert winder.z1_m == pytest.approx(deck)
        assert winder.z0_m == pytest.approx(rims[0].z1_m)
        # One diagonal block per box, splitting the wedge into two bearing triangles.
        blocks = [m for m in winder_stair.members
                  if m.child_key.startswith(f"landing-joist-winder{index}-")]
        assert len(blocks) == 1 and blocks[0].z1_m == pytest.approx(rims[0].z1_m)


def test_straight_flight_lands_on_the_top_winder_box(catlin_model, winder_stair):
    """The upper flight attaches to the top box's departing edge — Haun's "upper flight
    stringers attach directly to the top edge of the upper winder box".

    That rim is doubled because it carries the whole flight, and the stringers spring one
    riser above the box's deck, on the notch line the first straight tread sits on.
    """
    subfloor, riser, count = _winder_reference(catlin_model, winder_stair)
    tread_thickness = inch(1.5).meters
    stringers = [m for m in winder_stair.members if m.child_key.startswith("stringer-")]
    assert len(stringers) == 2
    spring_notch = subfloor + riser * (count + 1) - tread_thickness
    for stringer in stringers:
        assert stringer.z1_m == pytest.approx(spring_notch)
    first_tread = next(m for m in winder_stair.members if m.child_key == "tread-000")
    assert first_tread.z0_m == pytest.approx(spring_notch)
    # The top box's departing rim (its last edge) is two plies; every other side is one.
    top_rims = [m for m in winder_stair.members
                if m.child_key.startswith(f"landing-rim-winder{count - 1}-")]
    departing = max(top_rims, key=lambda m: int(m.child_key.rsplit("-", 1)[1]))
    assert cross_section(departing.profile).width_m == pytest.approx(inch(3.0).meters)
    for rim in top_rims:
        if rim is not departing:
            assert cross_section(rim.profile).width_m == pytest.approx(inch(1.5).meters)
    # It spans the inside corner to the turn corner: one stair width, which a straight
    # tread also spans, and both stringers spring off its ends.
    width = next(m for m in winder_stair.members if m.category == "tread").length_m
    assert math.hypot(departing.p1[0] - departing.p0[0],
                      departing.p1[1] - departing.p0[1]) == pytest.approx(width)
    newel = next(m for m in winder_stair.members if m.child_key == "newel-000")
    assert newel.p0 in (departing.p0, departing.p1)


def test_winder_nosings_are_never_plan_coincident_with_a_straight_tread(winder_stair):
    """The fan used to divide by ``winder_count``, putting the last nosing on the
    departing edge of the turn square — exactly where ``tread-000`` already is, one riser
    up. That is a riser with zero going: unclimbable."""
    treads = [m for m in winder_stair.members if m.category == "tread"]
    for winder in (m for m in winder_stair.members if m.category == "winder"):
        for tread in treads:
            assert {winder.p0, winder.p1} != {tread.p0, tread.p1}, (
                f"{winder.child_key} is plan-coincident with {tread.child_key}")


# ------------------------------------------------------- 9b. dropped tread boards
def test_every_catlin_stair_has_uniform_risers(catlin_model):
    """The built risers, not the design number: ``riser_height_m`` is rise / count and can
    never disagree with itself, so only the generated members can show a stair you cannot
    walk."""
    ctx = SimpleNamespace(model=catlin_model)
    findings = stair_riser_uniformity(ctx)
    assert len(findings) == len(catlin_model.stairs)
    assert all(finding.result is Result.PASS for finding in findings), (
        [finding.message for finding in findings])


def test_a_tread_stacked_on_its_step_elevation_fails_riser_uniformity(catlin_model):
    """The defect ``_notch_z`` fixes, reconstructed: put every board back *on* its step
    elevation instead of dropping it to it, and the first riser grows by the board
    thickness while the last shrinks by the same — 9" and 6" against a 7.5" design riser.

    Without this the check could be satisfied by a stair with no boards at all.
    """
    def is_walking_surface(member) -> bool:
        if member.category in ("tread", "winder"):
            return True
        return member.child_key in ("landing-lower", "landing-upper")

    stair = next(s for s in catlin_model.stairs if s.tag == "ST-M2S")
    stacked = replace(stair, members=tuple(
        replace(member, z0_m=member.z1_m, z1_m=member.z1_m + inch(1.5).meters)
        if is_walking_surface(member) else member
        for member in stair.members))
    findings = stair_riser_uniformity(SimpleNamespace(model=SimpleNamespace(
        stairs=[stacked])))
    assert [finding.result for finding in findings] == [Result.FAIL]
    assert "R311.7.5.1" in findings[0].message
    assert "9.00" in findings[0].message and "6.00" in findings[0].message


# ------------------------------------------------------------ 10. synthetic bearing
def _stair_plan(*, near_wall_offset=None, near_wall_role=StructuralRole.BEARING,
                **stair_fields) -> PlanModel:
    """A minimal main→second straight stair inside a 20x14 box of framed walls.

    No concrete anywhere, so it exercises exactly the path catlin's ST-M2S takes.
    ``near_wall_offset`` adds a 4.75" partition parallel to (and that far off) the
    y=0 stringer.
    """
    ext = Assembly(tag="EXT", layers=(
        Layer(name="stud", material_ref="wood", thickness=inch(5.5),
              function=LayerFunction.STRUCTURE, framing=FramingSpec(member="2x6")),
    ))
    part = Assembly(tag="PART", layers=(
        Layer(name="stud", material_ref="wood", thickness=inch(4.75),
              function=LayerFunction.STRUCTURE, framing=FramingSpec(member="2x4")),
    ))
    project = Project(
        name="Stair", project_uuid=uuid.UUID("00000000-0000-4000-8000-0000000000a1"),
        site=Site(lat=44.9, lon=-93.2, elevation=ft(830), design_temp_heating=degF(-15),
                  design_temp_cooling=degF(90)), building=Building(name="Stair"))
    main = Storey(uid="STMAIN0001", tag="main", elevation=ft(0), default_ceiling_height=ft(9))
    second = Storey(uid="STSEC00001", tag="second", elevation=ft(9),
                    default_ceiling_height=ft(9))
    nodes = tuple(
        Node(uid=f"N{i:09d}", tag=f"N-{i}", position=position)
        for i, position in enumerate((
            pt(ft(0), ft(0)), pt(ft(20), ft(0)), pt(ft(20), ft(14)), pt(ft(0), ft(14)),
        ), 1))
    walls = tuple(
        Wall(uid=f"W{i:09d}", tag=f"W-{i}", start_node=f"N-{start}", end_node=f"N-{end}",
             assembly="EXT", top=ft(9))
        for i, (start, end) in enumerate(((1, 2), (2, 3), (3, 4), (4, 1)), 1))
    extra: tuple = ()
    if near_wall_offset is not None:
        extra = (
            Node(uid="N000000101", tag="N-101", position=pt(ft(0), -near_wall_offset)),
            Node(uid="N000000102", tag="N-102", position=pt(ft(20), -near_wall_offset)),
            Wall(uid="W000000101", tag="W-NEAR", start_node="N-101", end_node="N-102",
                 assembly="PART", top=ft(9), structural_role=near_wall_role),
        )
    stair = Stair(uid="SR00000001", tag="S-1", floor_opening="FO-1", from_storey="main",
                  to_storey="second", width=ft(3), run_direction="x",
                  start=pt(ft(0), ft(0)), **stair_fields)
    plan = PlanModel(project=project, library=Library(
        materials=(Material(tag="wood", name="Wood", r_per_inch=1.25),),
        assemblies=(ext, part)), storeys=(main, second))
    second_elements = (
        FloorOpening(uid="FO00000001", tag="FO-1", outline=(
            pt(ft(0), ft(0)), pt(ft(14), ft(0)), pt(ft(14), ft(3)), pt(ft(0), ft(3)))),
        FloorSystem(uid="FS00000001", tag="FS-1", joists=JoistSpec(), openings=("FO-1",)),
    )
    return (plan.with_elements("main", (*nodes, *walls, *extra, stair))
                .with_elements("second", second_elements))


def _resolved_stair(plan):
    model, findings = resolve(plan)
    stair = next((s for s in model.stairs if s.tag == "S-1"), None)
    return stair, findings


def test_authored_stair_bearing_refs_promote_a_nonbearing_wall():
    """``bearing_refs`` grants permission it never restricts: W-1 carries the y=0
    stringer geometrically, but its authored role is UNKNOWN until the stair vouches."""
    stair, _ = _resolved_stair(_stair_plan())
    stringer = next(m for m in stair.members if m.child_key == "stringer-0")
    assert stringer.connection is None

    stair, findings = _resolved_stair(_stair_plan(bearing_refs=("W-1",)))
    assert not [f for f in findings if f.check_id == "integrity.stair_bearing"]
    stringer = next(m for m in stair.members if m.child_key == "stringer-0")
    assert stringer.connection == "framed-wall-ledger:W-1"


def test_missing_stair_bearing_ref_is_an_error():
    stair, findings = _resolved_stair(_stair_plan(bearing_refs=("W-NOPE",)))
    assert stair is None
    errors = [f for f in findings if f.check_id == "integrity.stair_bearing"]
    assert len(errors) == 1 and "W-NOPE" in errors[0].message


def test_six_by_six_newel_winder_lands_every_narrow_end_on_the_wider_face():
    """``Stair.newel_profile`` is consumed, not the old module constant: a 6x6 newel's
    faces sit 2.75" off its centreline, and every winder narrow end must land on them.

    The measured narrow-end tread depth is locked too — a quarter turn in three winders
    around a 6x6 delivers half the newel's half-face (1.375"), still 4.625" short of the
    6" IRC R311.7.5.2.1 minimum. That shortfall is a layout fact this generator refuses
    to paper over with invented risers, so the test asserts the honest number.
    """
    stair, findings = _resolved_stair(_stair_plan(
        layout="right_angle_winder", turn_direction="left", winder_count=3,
        newel_profile="6x6"))
    assert stair is not None, [f.message for f in findings]
    newels = [m for m in stair.members if m.category == "newel"]
    assert newels and all(m.profile == "6x6" for m in newels)
    newel = next(m for m in newels if m.child_key == "newel-000")
    half_face = cross_section("6x6").width_m / 2.0
    winders = sorted((m for m in stair.members if m.category == "winder"),
                     key=lambda m: m.z0_m)
    assert len(winders) == 3
    for winder in winders:
        reach = math.hypot(winder.p0[0] - newel.p0[0], winder.p0[1] - newel.p0[1])
        assert half_face - 1e-9 <= reach <= half_face * math.sqrt(2.0) + 1e-9, (
            winder.child_key)
    gaps = [math.hypot(b.p0[0] - a.p0[0], b.p0[1] - a.p0[1])
            for a, b in zip(winders, winders[1:])]
    assert min(gaps) == pytest.approx(half_face / 2.0)  # 1.375" — measured, not invented
    assert min(gaps) == pytest.approx(inch(1.375).meters)
    # A 4x4 (the default) delivers proportionally less: half of ITS half-face, 0.875".
    default_stair, _ = _resolved_stair(_stair_plan(
        layout="right_angle_winder", turn_direction="left", winder_count=3))
    default_winders = sorted((m for m in default_stair.members
                              if m.category == "winder"), key=lambda m: m.z0_m)
    default_gaps = [math.hypot(b.p0[0] - a.p0[0], b.p0[1] - a.p0[1])
                    for a, b in zip(default_winders, default_winders[1:])]
    assert min(default_gaps) == pytest.approx(inch(0.875).meters)


def test_a_wall_four_inches_off_the_stringer_is_not_a_host():
    """Locks the tolerance to the wall's own depth instead of a flat 0.20 m: a 4.75"
    partition reaches 2.375" + a tread board, so it cannot carry a stringer 4" away."""
    stair, _ = _resolved_stair(_stair_plan(near_wall_offset=inch(4)))
    stringer = next(m for m in stair.members if m.child_key == "stringer-0")
    assert stringer.connection is None
    # Two inches away it is within reach, so the rejection is the tolerance, not the wall.
    stair, _ = _resolved_stair(_stair_plan(near_wall_offset=inch(2)))
    stringer = next(m for m in stair.members if m.child_key == "stringer-0")
    assert stringer.connection == "framed-wall-ledger:W-NEAR"

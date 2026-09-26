"""The RF-HOUSE eave has to shed water, and that is a property of how its pieces overlap.

Every individual piece of this eave can be in exactly the right place and the assembly still
fail, because what keeps rain out of the wall is not where any one piece is — it is that each
higher piece laps *over* the next one down, with the whole chain hanging outboard of the
cladding. Those are relationships between pieces, so they are what this module tests:

    roofing → formed drip edge (derived) → box gutter → downspout

The drip edge is one formed piece per edge (resolve/roof_drip_edge.py): a flange on the deck
at the pitch, a nose over the deck edge, a face over the wall panel heads, a kick into the
trough. Its legs are measured off their true section (``member_solid``), not a box.
"""

from __future__ import annotations

import math

import pytest

from typehaus.quantities import inch
from typehaus.resolve.geometry_members import member_solid

# 6:12. Roof-stack offsets are perpendicular to the slope; elevations are vertical.
SLOPE = 6.0 / 12.0
SLOPE_FACTOR = math.hypot(1.0, SLOPE)
#: Structural deck surface at the edge — the plane the drip flange lies on and the membrane
#: laps over. 0.625" of CDX plywood.
DRIP_CEILING_IN = 0.625 * SLOPE_FACTOR
#: Roofing underside == the head of the wall cladding on a continuous-skin edge.
CLADDING_HEAD_IN = 0.665 * SLOPE_FACTOR


@pytest.fixture(scope="module")
def eave(catlin_model):
    """The east eave in its own frame: inches outboard of the roof edge, above the deck."""
    roof = next(r for r in catlin_model.roofs if r.tag == "RF-HOUSE")
    edge = max(p[0] for p in roof.footprint)
    return _EaveFrame(catlin_model, roof, edge)


class _EaveFrame:
    def __init__(self, model, roof, edge_x: float) -> None:
        self.model, self.roof, self.edge_x = model, roof, edge_x

    def _out(self, metres: float) -> float:
        return (metres - self.edge_x) / inch(1).meters

    def _up(self, metres: float) -> float:
        return (metres - self.roof.eave_z_m) / inch(1).meters

    def solid(self, tag: str):
        """One authored solid as ``(out_lo, out_hi, z_lo, z_hi)`` in the eave frame."""
        found = next(s for s in self.model.solids if s.tag == tag)
        xs = [p[0] for p in found.outline]
        return (self._out(min(xs)), self._out(max(xs)),
                self._up(found.z0_m), self._up(found.z1_m))

    def section(self, key: str) -> list[tuple[float, float]]:
        """A swept leg's true section as ``(out, up)`` points — the ring, not its box."""
        member = next(m for m in self.roof.members if m.child_key == key)
        solid = member_solid(member)
        return [(self._out(x), self._up(z)) for x, _y, z in solid.profile]

    def leg(self, name: str):
        """The east eave drip leg's envelope, ``(out_lo, out_hi, z_lo, z_hi)``."""
        points = self.section(f"eave-hi-drip-edge-{name}")
        us = [u for u, _ in points]
        zs = [z for _, z in points]
        return (min(us), max(us), min(zs), max(zs))

    def member(self, key: str):
        """A box member's envelope, same frame (the wall's closure band)."""
        from typehaus.resolve.framing.profiles import cross_section
        found = next(m for m in self.roof.members if m.child_key == key)
        half = cross_section(found.profile).width_m / 2.0
        return (self._out(found.p0[0] - half), self._out(found.p0[0] + half),
                self._up(found.z0_m), self._up(found.z1_m))

    def run_y(self, tag: str) -> tuple[float, float]:
        found = next(s for s in self.model.solids if s.tag == tag)
        ys = [p[1] for p in found.outline]
        return min(ys), max(ys)


def laps_over(upper, lower) -> bool:
    """Whether ``upper`` sheds onto ``lower``: they overlap in plan, and upper reaches higher.

    That is the whole definition of a lap in a rain screen. Two pieces that merely touch,
    or that overlap in plan but where the lower one stands proud, leave a seam pointing up.
    """
    u_lo, u_hi, _uz0, uz1 = upper
    l_lo, l_hi, _lz0, lz1 = lower
    return min(u_hi, l_hi) - max(u_lo, l_lo) > 0.0 and uz1 > lz1


@pytest.mark.parametrize("side", ["W", "E"])
def test_eave_runs_close_the_rake_corners(catlin_model, side) -> None:
    """The gutter and the drip face run the full roof footprint, not the sheathing datum.

    Authoring the eaves from ft(0) to ft(36) once left open roof edge over thin air at all
    four corners — the hole the 3D view showed with the roof stack visible through it.
    """
    roof = next(r for r in catlin_model.roofs if r.tag == "RF-HOUSE")
    lo = min(p[1] for p in roof.footprint)
    hi = max(p[1] for p in roof.footprint)
    frame = _EaveFrame(catlin_model, roof, 0.0)
    y0, y1 = frame.run_y(f"TR-RF-GUTTER-{side}-1-BACK")
    assert (y0, y1) == (pytest.approx(lo), pytest.approx(hi))
    key = "eave-lo" if side == "W" else "eave-hi"
    face = next(m for m in roof.members if m.child_key == f"{key}-drip-edge-face")
    ys = sorted((face.p0[1], face.p1[1]))
    assert ys[0] < lo and ys[1] > hi, "the drip face runs past both rake corners"


def test_no_authored_drip_duplicates_the_derived_piece(catlin_model) -> None:
    """One piece of metal per edge: the old level drips and corner trim are gone."""
    roof = next(r for r in catlin_model.roofs if r.tag == "RF-HOUSE")
    assert not [s for s in catlin_model.solids if s.tag.startswith("TR-RF-DRIP")]
    assert not [m for m in roof.members if m.category == "corner_trim"]
    assert {m.child_key.rsplit("-drip-edge-", 1)[0] for m in roof.members
            if m.category == "drip_edge"} == {
        "eave-lo", "eave-hi", "rake-lo-0", "rake-lo-1", "rake-hi-0", "rake-hi-1"}


def test_the_drip_face_hangs_outboard_of_the_wall_it_laps(eave) -> None:
    """The face caps the panel heads from *outside*, and the nose clears their closure head.

    ** W-S-E1, NOT W-A-E1. ** The attic's east eave wall is a 1 1/2" rafter plate and carries
    no skin, so the closure band the roof edge laps is the second storey's own EXT_2X6 run.
    """
    face = eave.leg("face")
    nose = eave.leg("nose")
    cladding = eave.member("W-S-E1-closure-0-cladding")
    assert face[0] == pytest.approx(1.25 - 1.25 / 3.0), "the face keeps the old trim's plane"
    assert face[1] == pytest.approx(1.25)
    assert cladding[1] <= face[0] + 1e-6, "the wall panels run up inboard of the face"
    assert face[2] < cladding[3], "the face's leg laps down over the panel heads"
    assert nose[2] >= cladding[3] - 1e-6, "the nose clears the closure head"


def test_the_lap_chain_runs_unbroken_from_the_roofing_to_the_trough(eave) -> None:
    """Each piece overlaps the next one down, so no seam in the chain faces upward."""
    setback = next(e for e in eave.roof.layer_edge_setbacks if e["layer"] == "roofing")
    roofing_out = -setback["east"] / inch(1).meters
    roofing = (-6.0, roofing_out, CLADDING_HEAD_IN, (0.665 + 0.5) * SLOPE_FACTOR + 3.0)
    nose, face, kick = eave.leg("nose"), eave.leg("face"), eave.leg("kick")
    back = eave.solid("TR-RF-GUTTER-E-1-BACK")
    front = eave.solid("TR-RF-GUTTER-E-1-FRONT")
    bottom = eave.solid("TR-RF-GUTTER-E-1-BOTTOM")

    assert laps_over(roofing, nose), "the roofing sheds onto the drip edge's nose"
    assert laps_over(face, back) or face[0] >= back[1] - 1e-6, \
        "the drip face stands in front of the gutter's back sheet"
    assert face[2] < back[3], "and reaches below the rim, so water cannot get behind it"
    assert back[1] <= kick[0] + 1e-6 and kick[1] < front[0], "the kick lands in the trough"
    assert kick[2] > bottom[3], "and stops above the floor, so it cannot dam the flow"


def test_the_gutter_is_mounted_tight_to_the_wall(eave) -> None:
    """No open slot behind the trough for water to run down the siding through."""
    face = eave.leg("face")
    back = eave.solid("TR-RF-GUTTER-E-1-BACK")
    assert back[0] < face[1], "the back sheet tucks behind the drip face"
    assert back[3] > face[2], "and reaches above its foot, so the two overlap"


def test_the_drip_flange_lies_on_the_top_deck_and_nothing_else_reaches_it(eave) -> None:
    """The flange lies ON the top deck, at the pitch, and the underlayment laps OVER it.

    The deck top falls 1/2" per inch outboard at 6:12, so the flange's underside is the
    pitched plane ``0.70" - slope * u`` — a level drip left a wedge of air under it.
    """
    points = eave.section("eave-hi-drip-edge-flange")
    underside: dict[float, float] = {}
    for u, z in points:
        underside[round(u, 6)] = min(z, underside.get(round(u, 6), z))
    assert len(underside) == 2
    for u, z in underside.items():
        assert z == pytest.approx(DRIP_CEILING_IN - SLOPE * u, abs=1e-6)
    flange = eave.leg("flange")
    # The deck stops 1 1/4" (the PBR panel) inboard of the roof edge; 2" of flange bears on it.
    assert flange[0] <= -1.25 - 2.0 + 1e-6, "it bears 2\" ONTO the plywood"
    assert flange[1] == pytest.approx(-1.25), "and bends at the deck edge"
    for tag in ("TR-RF-GUTTER-E-1-BACK", "TR-RF-GUTTER-E-1-FRONT"):
        assert eave.solid(tag)[3] < DRIP_CEILING_IN, f"{tag} stands proud of the top deck"


def test_each_eave_drains_to_a_leader_that_reaches_grade(catlin_model, eave) -> None:
    """A gutter sloping to a downspout that does not exist is not a drainage system."""
    # Every gutter in the house, not just this roof's two: the guard was scoped to the
    # TR-RF- prefix while the balcony's and the garage's ran to leaders nobody had authored.
    # A slope note is prose, so what is asserted now is the ref an element can be held to.
    from typehaus.model.trim import Downspout, Gutter

    leaders = {el.tag for el in catlin_model.plan.all_elements()
               if isinstance(el, Downspout)}
    # TR-SG-RUNNEL is an open channel a LEADER discharges into; it lets go through a scupper
    # into FURN-SG-SPLASH-BASIN, and test_drainage_elements.py pins that end instead.
    spouted = {"TR-SG-RUNNEL"}
    gutters = [el for el in catlin_model.plan.all_elements()
               if isinstance(el, Gutter) and el.tag not in spouted]
    assert gutters
    for gutter in gutters:
        assert gutter.downspout_ref in leaders, \
            f"{gutter.tag} falls to {gutter.downspout_ref!r}, which no element declares"
    leader = next(s for s in catlin_model.solids if s.tag == "TR-RF-LEADER-E")
    trough_floor = eave.solid("TR-RF-GUTTER-E-1-BOTTOM")
    assert eave._up(leader.z1_m) == pytest.approx(trough_floor[2]), \
        "the leader takes the outlet straight out of the trough floor"
    # It stops at +1'-0" and goes on as a buried riser into RG-E-BASIN, the west's mirror;
    # the riser bills with the extension. Stopping there with no extension was 3'-9" of free
    # fall onto walk D.
    assert leader.z0_m == pytest.approx(0.3048)
    authored = catlin_model.plan.by_tag("TR-RF-LEADER-E")
    assert authored.discharge_ref == "RG-E-BASIN" and authored.extension is not None
    # It hangs on the trough's centre line, which is also about where a strapped 4" round
    # leader's centre lands off this wall — so it clears the cladding without an offset.
    xs = [p[0] for p in leader.outline]
    assert eave._out(min(xs)) > 0.0, "the leader stands clear of the wall face"

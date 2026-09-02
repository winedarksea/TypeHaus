"""The RF-HOUSE eave has to shed water, and that is a property of how its pieces overlap.

Every individual piece of this eave can be in exactly the right place and the assembly still
fail, because what keeps rain out of the wall is not where any one piece is — it is that each
higher piece laps *over* the next one down, with the whole chain hanging outboard of the
cladding. Those are relationships between pieces, so they are what this module tests:

    roofing → corner trim → drip edge → box gutter → downspout

Every one of these was broken at once before (see houses/catlin/params/roof_trim.py): the
runs stopped 5" short of the roof at both gable ends, the corner trim resolved *inboard* of
the footprint edge instead of outboard, and the roofing's own drip line fell 0.65" behind the
gutter's back sheet — so the roof drained down the siding.
"""

from __future__ import annotations

import math

import pytest

from typehaus.quantities import inch
from typehaus.resolve.framing.profiles import cross_section

# 4:12. Roof-stack offsets are perpendicular to the slope; elevations are vertical.
# 6:12 (params/roof_trim.py hand-copies these; they move together).
SLOPE_FACTOR = math.hypot(1.0, 6.0 / 12.0)
#: Structural deck surface — the plane the drip flashing lies on and the membrane laps over.
#: 0.625" of CDX plywood.
DRIP_CEILING_IN = 0.625 * SLOPE_FACTOR
#: Roofing underside == the head of the wall cladding on a continuous-skin edge. The deck
#: plus the 0.04" adhered butyl membrane, and nothing else.
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

    def member(self, prefix: str):
        """Derived roof members' envelope, same frame. Members carry a centre line + section.

        A prefix rather than an exact key because a *formed* piece is several members: the
        corner trim is a cleat, a face and a hem. What laps what is a property of the
        assembled piece, so the envelope is the honest thing to measure.
        """
        found = [m for m in self.roof.members if m.child_key.startswith(prefix)]
        assert found, f"no member matching {prefix!r}"
        los, his = [], []
        for member in found:
            half = cross_section(member.profile).width_m / 2.0
            los.append(member.p0[0] - half)
            his.append(member.p0[0] + half)
        return (self._out(min(los)), self._out(max(his)),
                self._up(min(m.z0_m for m in found)), self._up(max(m.z1_m for m in found)))

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
    """The gutter and drip run the full roof footprint, not the sheathing datum.

    The roof and its cladding overhang the sheathing plane by the wall's 5.02" of outboard
    stack at *every* edge, gable ends included. Authoring the eaves from ft(0) to ft(36)
    therefore left 5" of open roof edge over thin air at all four corners — which is what the
    3D view showed as a hole at the corner with the roof stack visible through it.
    """
    roof = next(r for r in catlin_model.roofs if r.tag == "RF-HOUSE")
    lo = min(p[1] for p in roof.footprint)
    hi = max(p[1] for p in roof.footprint)
    frame = _EaveFrame(catlin_model, roof, 0.0)
    for tag in (f"TR-RF-GUTTER-{side}-1-BACK", f"TR-RF-DRIP-{side}-1-LAP"):
        y0, y1 = frame.run_y(tag)
        assert y0 == pytest.approx(lo), f"{tag} stops short of the south rake"
        assert y1 == pytest.approx(hi), f"{tag} stops short of the north rake"


def test_corner_trim_hangs_outboard_of_the_wall_it_laps(eave) -> None:
    """The corner trim caps the joint from *outside*, or it caps nothing.

    ``_corner_trim_members`` signed its centre offset in the mitre's inboard-positive frame
    while ``_offset`` reads the outward normal, which buried the trim inside the wall
    cladding — where it can neither shed water nor be seen.
    """
    trim = eave.member("eave-hi-corner-trim")
    assert trim[0] == pytest.approx(0.0, abs=1e-6), "inner face sits on the footprint edge"
    assert trim[1] > 0.0, "the trim must stand outboard of the edge, not inside the cladding"
    # ** W-S-E1, NOT W-A-E1. ** The attic's east eave wall is a 1 1/2"
    # rafter plate now and carries no skin at all, so the closure band the roof edge laps is
    # the one belonging to the wall the plate STANDS ON — the second storey's own
    # CATLIN_EXT_2X6 run (`roof_edge.skin_stand_ins`, keyed off the authored `stacks_on`).
    # The band is in the same place it always was; only the member's parent changed.
    cladding = eave.member("W-S-E1-closure-0-cladding")
    assert cladding[1] <= trim[0] + 1e-6, "the wall panels run up inboard of the trim"
    assert trim[2] < cladding[3] < trim[3], "the trim's leg laps down over the panel heads"


def test_the_lap_chain_runs_unbroken_from_the_roofing_to_the_trough(eave) -> None:
    """Each piece overlaps the next one down, so no seam in the chain faces upward."""
    trim = eave.member("eave-hi-corner-trim")
    drip_lap = eave.solid("TR-RF-DRIP-E-1-LAP")
    gutter_back = eave.solid("TR-RF-GUTTER-E-1-BACK")

    assert laps_over(trim, drip_lap), "the corner trim must shed onto the drip edge"
    assert laps_over(trim, gutter_back), "and onto the back of the trough behind it"
    assert laps_over(drip_lap, gutter_back), "the drip edge must shed into the gutter"


def test_the_gutter_is_mounted_tight_to_the_wall(eave) -> None:
    """No open slot behind the trough for water to run down the siding through.

    The back sheet used to hang 0.75" clear of everything, leaving a 3"-tall gap running the
    whole length of the eave between the head of the wall cladding and the gutter.
    """
    trim = eave.member("eave-hi-corner-trim")
    back = eave.solid("TR-RF-GUTTER-E-1-BACK")
    assert back[0] < trim[1], "the back sheet tucks behind the corner trim's outer face"
    assert back[3] > trim[2], "and reaches above its lower edge, so the two overlap"


def test_the_drip_throws_water_into_the_middle_of_the_trough(eave) -> None:
    """Where the turn-down ends is the whole detail: inside the channel, below its rim."""
    turn_down = eave.solid("TR-RF-DRIP-E-1-DRIP")
    bottom = eave.solid("TR-RF-GUTTER-E-1-BOTTOM")
    front = eave.solid("TR-RF-GUTTER-E-1-FRONT")
    back = eave.solid("TR-RF-GUTTER-E-1-BACK")

    assert back[1] < turn_down[0] and turn_down[1] < front[0], \
        "the turn-down hangs clear inside the trough, touching neither sheet"
    assert turn_down[2] < back[3], "it reaches below the rim, so water cannot blow back out"
    assert turn_down[2] > bottom[3], "but stops above the floor, so it cannot dam the flow"


def test_the_drip_flange_lies_on_the_top_deck_and_nothing_else_reaches_it(eave) -> None:
    """The drip flashing lies ON the top deck and the underlayment laps OVER it.

    This is the constraint that stops the gutter simply being raised until every lap is
    comfortable: the rim has a ceiling, and the ceiling is the top deck's own surface.

    Which makes the drip edge the *exception* the rule exists to protect, not an instance of
    it — and reading it as an instance is what put the drip a whole inch under the deck it is
    nailed to, hanging off the gutter's rim in mid-air with nothing above it to lap. The
    underlayment has to ride over exactly one thing to reach the deck, so: the drip's flange
    sits on the plane, and everything else in the chain stays below it.
    """
    flange = eave.solid("TR-RF-DRIP-E-1-LAP")
    assert flange[2] == pytest.approx(DRIP_CEILING_IN), \
        "the flange's underside IS the deck surface — it is nailed to it, not hung near it"
    assert flange[0] < 0.0, "and it reaches back ONTO the deck, inboard of the roof edge"
    # The turn-down is the drip's own second leg, so it is allowed to reach the flange it is
    # folded from — but no higher, or the fold points back up the slope.
    assert eave.solid("TR-RF-DRIP-E-1-DRIP")[3] <= flange[2] + 1e-9
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
    gutters = [el for el in catlin_model.plan.all_elements() if isinstance(el, Gutter)]
    assert gutters
    for gutter in gutters:
        assert gutter.downspout_ref in leaders, \
            f"{gutter.tag} falls to {gutter.downspout_ref!r}, which no element declares"
    leader = next(s for s in catlin_model.solids if s.tag == "TR-RF-LEADER-E")
    trough_floor = eave.solid("TR-RF-GUTTER-E-1-BOTTOM")
    assert eave._up(leader.z1_m) == pytest.approx(trough_floor[2]), \
        "the leader takes the outlet straight out of the trough floor"
    assert 0.0 < leader.z0_m < 0.5, "and runs down to a splash block just above grade"
    # It hangs on the trough's centre line, which is also about where a strapped 4" round
    # leader's centre lands off this wall — so it clears the cladding without an offset.
    xs = [p[0] for p in leader.outline]
    assert eave._out(min(xs)) > 0.0, "the leader stands clear of the wall face"

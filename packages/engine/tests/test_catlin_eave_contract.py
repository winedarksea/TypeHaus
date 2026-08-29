"""The eave detail is a contract between four things that used to disagree (→ 30 §Details).

``wall_roof:CATLIN_EXT_2X6|CATLIN_ROOF`` is the junction the whole slice-the-IR migration was
about, because it is where every re-derivation met: the section had its own roof plane, its own
layer stack, its own birdsmouth and its own idea of where the wall's foam stopped, and all four
were wrong in a different direction. Each individual piece can be right and the drawing still
lie, so what this module tests is the *agreement*:

    rafter seat == plate top | stack above the deck datum, structure below it
    | wall CI stops at its own mating face | the structure drawn exactly once

Every one of those is now read from one place — ``member_solid``, ``roof_parts``,
``roof_edge``'s closure members — rather than transcribed a second time into ``section.py``.
"""

from __future__ import annotations

import math

import pytest

from typehaus.emit.draw.details import build_detail, derive_detail_slices
from typehaus.emit.draw.scene import Polyline
from typehaus.quantities import M_PER_IN
from typehaus.resolve.geometry_members import member_solid
from typehaus.resolve.roof_edge_geometry import (
    continuous_skin_cladding,
    mating_faces,
    roof_slope,
)
from typehaus.resolve.roof_geometry import roof_height_at
from typehaus.resolve.roof_layer_setbacks import above_structure_layers

_KEY = "wall_roof:CATLIN_EXT_2X6|CATLIN_ROOF"
_ROOF_TAG = "RF-HOUSE"


@pytest.fixture(scope="module")
def eave(catlin_model):
    derived = next(d for d in derive_detail_slices(catlin_model) if d.key == _KEY)
    scene, _findings = build_detail(catlin_model, derived)
    wall = next(w for w in catlin_model.walls if w.tag in derived.condition.element_tags)
    roof = next(r for r in catlin_model.roofs if r.tag in derived.condition.element_tags)
    return _Eave(catlin_model, derived, scene, wall, roof)


class _Eave:
    def __init__(self, model, derived, scene, wall, roof) -> None:
        self.model, self.derived, self.scene = model, derived, scene
        self.wall, self.roof = wall, roof

    @property
    def plate_top_m(self) -> float:
        return self.wall.top_z1_m if self.wall.top_z1_m is not None else self.wall.z1_m

    def polylines(self, layer: str, prefix: str = "") -> list[Polyline]:
        return [n for n in self.scene.nodes
                if isinstance(n, Polyline) and n.layer == layer
                and (not prefix or (n.tag or "").startswith(prefix))]

    def rafters(self):
        return [m for m in self.roof.members if m.category == "rafter"]


def test_the_rafter_bears_on_the_plate(eave):
    """The seat is a flat face *at* the plate top — not 1.17" of string, not a second block.

    ``member_solid`` is the one answer; IFC, glTF, the viewer and this drawing all read it.
    """
    plate_top = eave.plate_top_m
    seated = [m for m in eave.rafters() if m.seat is not None]
    assert seated, "no rafter carries a seat cut"
    for rafter in seated:
        assert rafter.seat.plate_top_z_m == pytest.approx(plate_top, abs=1e-9)
        zs = sorted(z for (_x, _y, z) in member_solid(rafter).profile)
        # Two corners share the lowest elevation: the flat seat, sitting on the plate.
        assert zs[0] == pytest.approx(zs[1], abs=1e-9)
        assert zs[0] == pytest.approx(plate_top, abs=1e-9), \
            "the rafter floats above the plate or buries itself in it"


def test_the_stack_is_above_the_deck_and_the_structure_is_below_it(eave):
    """The section used to mirror the whole above-structure stack about the wrong plane.

    ``roof_parts`` offsets each band perpendicular to the slope *from the deck*, so the test
    is the sign of that offset: every A-ROOF band sits above ``roof_height_at``, and the
    rafters that carry it sit below.
    """
    bands = eave.polylines("A-ROOF", f"{_ROOF_TAG}/")
    assert bands, "the eave detail drew no roof stack"
    slope = math.hypot(1.0, roof_slope(eave.roof))
    for band in bands:
        for (u_in, z_in) in band.points:
            deck = roof_height_at(eave.roof, _plan_point(eave, u_in * M_PER_IN))
            # Allowance: a band's own thickness x sin(theta) of down-slope drift at the clip.
            assert z_in * M_PER_IN > deck - 0.05 * slope, f"{band.tag} hangs under the deck"

    for rafter in eave.rafters():
        assert rafter.z1_m <= roof_height_at(eave.roof, rafter.p1) + 1e-6


def test_the_wall_ci_stops_at_its_own_mating_face(eave):
    """And the *drawing* shows that elevation — not a ``_WEDGE_GAP_M`` below a plane it
    invented for itself.

    ``roof_edge`` carries each skin layer up to its own counterpart in the roof stack
    (``mating_faces`` over the above-structure layers, offset perpendicular to the slope), and
    the section slices those closure members like any other geometry. So this asserts the two
    halves agree: the resolver's elevation, and the one the polyline actually reaches.
    """
    assembly = eave.model.plan.library.resolve_assembly(eave.roof.assembly)
    mating = mating_faces(above_structure_layers(assembly))
    continuous = continuous_skin_cladding(eave.model, eave.roof, (eave.wall,))
    slope = math.hypot(1.0, roof_slope(eave.roof))

    closures = [m for m in eave.roof.members
                if m.child_key.startswith(f"{eave.wall.tag}-closure-")]
    assert closures, "the wall's skin has no closure band at this eave"
    ci = [m for m in closures if m.category == "insulation"]
    assert ci, "the wall's continuous insulation is not carried up"

    drawn = {(n.tag or ""): n for n in eave.polylines("A-WALL-INSU")}
    for band in ci:
        perpendicular = mating.for_layer(band.category, continuous_cladding=continuous)
        want = roof_height_at(eave.roof, band.p0) + perpendicular * slope
        assert band.z1_m == pytest.approx(want, abs=1e-6), band.child_key
        assert band.z0_m == pytest.approx(eave.plate_top_m, abs=1e-6), \
            "the closure starts somewhere other than the wall top it closes"
        node = drawn.get(band.child_key)
        if node is None:
            continue  # out of this detail's crop; the resolver assertion above still holds
        top_in = max(z for (_u, z) in node.points)
        assert top_in * M_PER_IN <= want + 1e-6, \
            f"{band.child_key} is drawn above its own mating face"


def test_the_roof_structure_is_drawn_exactly_once(eave):
    """As framing. An A-ROOF band naming the structure layer is the double-draw returning."""
    assembly = eave.model.plan.library.resolve_assembly(eave.roof.assembly)
    structure = {layer.name for layer in assembly.layers if layer.function.value == "structure"}
    above = {layer.name for layer in above_structure_layers(assembly)}
    bands = [(n.tag or "").split("/", 1)[-1] for n in eave.polylines("A-ROOF", f"{_ROOF_TAG}/")]
    assert bands
    assert not (set(bands) & structure), f"the structure is drawn as a band too: {bands}"
    assert set(bands) <= above
    assert eave.polylines("S-FRAM", "rafter-"), "and it is drawn as framing"


def _plan_point(eave, u_m: float):
    """A section u back into a plan point, on the cut's own station."""
    if eave.derived.direction == "x":
        return (u_m, eave.derived.station)
    return (eave.derived.station, u_m)


def test_the_roof_footprint_laps_the_wall_cladding_and_does_not_collapse_to_the_structure(
        catlin_model):
    """The cladding lap, pinned by its bounds.

    `_resolve_roof` builds the footprint from the bearing walls' OUTERMOST layer so a
    zero-overhang roof reaches past the cladding it has to cover. When a bearing wall has no
    weather skin — a rafter plate laid flat on a deck, which is what a story-and-a-half
    lands its roof on — that read finds the bare 5 1/2" structure band instead, and the
    footprint silently shrinks by the wall stack's whole outboard depth on every side. The
    ridge drops with it, the rafter tails stop short of the cladding, and nothing errors.

    36'-0" of wall axis plus 7 1/4" of stack outboard of the structure face, both sides.
    """
    roof = next(r for r in catlin_model.roofs if r.tag == "RF-HOUSE")
    xs = [point[0] / M_PER_IN for point in roof.footprint]
    ys = [point[1] / M_PER_IN for point in roof.footprint]
    assert min(xs) == pytest.approx(-7.25, abs=1e-3)
    assert max(xs) == pytest.approx(439.25, abs=1e-3)
    assert min(ys) == pytest.approx(-7.25, abs=1e-3)
    assert max(ys) == pytest.approx(439.25, abs=1e-3)

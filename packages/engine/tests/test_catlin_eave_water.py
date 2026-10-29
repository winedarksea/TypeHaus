"""The RF-HOUSE eave sheds water because of how its pieces lap, so that is what this tests.

Cut at true scale through the resolved 3D geometry, per eave, in the eave frame: ``u`` inches
out from the cladding face (the roof footprint edge), ``z`` inches above the deck plane at
the edge (``eave_z_m``). The assembly (``resolve/roof_image_ii_eave.py``, the PBR 5 x 4 box
gutter from ``params/roof_trim.py`` swept by ``resolve/gutter_formed.py``):

    field membrane -> gutter roof flange -> Extended Eave -> strip-in -> Image II pan
    at the face line: cladding -> gutter back -> eave face, kick into the trough
"""

from __future__ import annotations

import itertools

import pytest
from shapely.geometry import LineString, Polygon, box

from typehaus.emit.draw.detail_components.eave_framing import hanger_screw
from typehaus.library.trim.metal_sales import FORMED_GUTTERS
from typehaus.quantities import M_PER_IN
from typehaus.resolve.geometry_build import build_geometry
from typehaus.resolve.geometry_slice import CutPlane, slice_solid
from typehaus.resolve.metal_skin_profiles import SHEET_24_GA_M
from typehaus.resolve.roof_image_ii_eave import eave_stack

FT = 12.0
#: Three relationship stations per eave (ft along y), each mid-pan (the pan end stops at a
#: seam); five for the clash sweep.
STATIONS = (112 / FT, 208 / FT, 304 / FT)
CLASH_STATIONS = (2.0, 9.3, 17.4, 26.0, 33.5)
#: Overlap below this is a shared face, not a clash (sq in).
CLASH_AREA_IN2 = 1e-4
#: Foam closures fill the panel ribs; they live inside the panel's envelope by design.
_FOAM = {"6460800", "6411499", "corrugated-closure", "corrugated-outside-closure",
         "cobra-vented-closure"}
#: The penetrations of the gutter that are open items, not modelled joints: the provisional
#: hanger's sealed screw through the back (plans: work package 1, supports).
KNOWN_OPEN_ROUTES = {"hanger screw"}


@pytest.fixture(scope="module")
def house(catlin_model_ro):
    model = catlin_model_ro
    roof = next(r for r in model.roofs if r.tag == "RF-HOUSE")
    product = {s.uid: s.product for s in model.solids}
    parts = []
    for element in build_geometry(model).elements:
        for part in element.parts:
            role = _role(element, part, product.get(element.uid))
            if role is not None:
                parts.append((role, part))
    return model, roof, parts


def _role(element, part, product) -> str | None:
    """What a sheet is in the eave, or None when it is not sheet metal, membrane or cladding."""
    key = part.key
    if element.kind == "gutter":
        return "gutter"
    if element.kind in ("cladding_trim", "wall_corner", "flashing"):
        return None if product in _FOAM else f"trim:{element.uid}"
    for needle, role in (("image-ii-eave", "eave"), ("eave-strip-in", "strip"),
                         ("pan-end", "pan"), ("image-ii-rake", "rake"),
                         ("closure-0-cladding", "cladding"), ("layer:membrane", "field"),
                         ("layer:roofing", "roofing")):
        if needle in key and element.kind in ("roof", "framing"):
            return role
    if element.kind == "wall" and "cladding" in key:
        return "cladding"
    return None


class Cut:
    """One cut, its sheets as ``(role, polygon)`` in the eave frame (inches)."""

    def __init__(self, house, side: str, axis: str, station_m: float) -> None:
        model, roof, parts = house
        xs = [p[0] for p in roof.footprint]
        self.sign = 1.0 if side == "E" else -1.0
        edge = max(xs) if side == "E" else min(xs)
        z0 = roof.eave_z_m
        plane = CutPlane(axis=axis, station_m=station_m)
        window = box(-14.0, -10.0, 14.0, 8.0) if axis == "x" else box(-1e4, -10.0, 1e4, 8.0)
        self.polys: list[tuple[str, Polygon]] = []
        for role, part in parts:
            for solid in part.solids:
                for profile in slice_solid(solid, plane):
                    if len(profile.outline) < 3:
                        continue
                    points = [(self._u(u, edge) if axis == "x" else u / M_PER_IN,
                               (z - z0) / M_PER_IN) for u, z in profile.outline]
                    poly = Polygon(points).buffer(0)
                    if not poly.is_empty and poly.intersects(window):
                        self.polys.append((role, poly))

    def _u(self, x: float, edge: float) -> float:
        return self.sign * (x - edge) / M_PER_IN

    def of(self, role: str) -> list[Polygon]:
        return [p for r, p in self.polys if r == role]

    def one(self, role: str) -> Polygon:
        found = self.of(role)
        assert len(found) == 1, f"{role}: {len(found)} profiles in the cut"
        return found[0]

    def clashes(self) -> list[tuple[str, str, float]]:
        out = []
        for (ra, a), (rb, b) in itertools.combinations(self.polys, 2):
            area = a.intersection(b).area if ra != rb else 0.0
            if area > CLASH_AREA_IN2:
                out.append((ra, rb, round(area, 4)))
        return out


def _span(poly: Polygon, line: LineString) -> list[tuple[float, float]]:
    """The intervals of ``line`` inside ``poly``, as (lo, hi) of the varying coordinate."""
    hit = poly.intersection(line)
    pieces = getattr(hit, "geoms", [hit])
    vertical = line.coords[0][0] == line.coords[-1][0]
    out = []
    for piece in pieces:
        if piece.is_empty or piece.length == 0:
            continue
        values = [c[1] if vertical else c[0] for c in piece.coords]
        out.append((min(values), max(values)))
    return sorted(out)


def _at_u(poly, u):
    return _span(poly, LineString([(u, -20.0), (u, 20.0)]))


def _at_z(poly, z):
    return _span(poly, LineString([(-20.0, z), (20.0, z)]))


@pytest.fixture(scope="module", params=[(s, y) for s in ("W", "E") for y in STATIONS],
                ids=lambda p: f"{p[0]}-{p[1]:g}ft")
def cut(request, house):
    side, y_ft = request.param
    return Cut(house, side, "x", y_ft * FT * M_PER_IN)


def test_pan_end_wraps_the_lip_over_the_whole_stack(cut) -> None:
    """The pan end rides over every sheet under it and folds round the eave's lip."""
    pan, eave = cut.one("pan"), cut.one("eave")
    under = [*cut.of("strip"), eave, cut.one("gutter"), *cut.of("field")]
    lip = eave.bounds[2]
    assert pan.bounds[2] > lip, "the pan's fold is outboard of the lip"
    tip = _at_u(pan, lip - 0.1)
    assert len(tip) == 2, "a vertical through the lip meets the pan above and below it"
    lip_span = _at_u(eave, lip - 0.1)
    assert tip[0][1] < lip_span[0][0] and tip[1][0] > lip_span[-1][1]
    u = pan.bounds[0] + 0.5
    while u < 0.0:
        pan_bottom = _at_u(pan, u)[0][0]
        for sheet in under:
            for _lo, hi in _at_u(sheet, u):
                assert hi < pan_bottom, f"a sheet stands into the pan at u={u:.2f}"
        u += 0.25


def test_strip_in_covers_both_flange_hems_and_laps_the_field(cut) -> None:
    strip, eave, gutter = cut.one("strip"), cut.one("eave"), cut.one("gutter")
    field = max(cut.of("field"), key=lambda p: p.bounds[2])
    assert strip.bounds[0] < min(eave.bounds[0], gutter.bounds[0]) - 3.0, \
        "the strip runs well upslope of the gutter flange's and the eave hem's ends"
    assert strip.bounds[0] < field.bounds[2], "and laps onto the field membrane"
    for u in (gutter.bounds[0] + 0.02, eave.bounds[0] + 0.02):
        strip_bottom = _at_u(strip, u)[0][0]
        assert all(hi < strip_bottom for sheet in (eave, gutter) for _lo, hi in _at_u(sheet, u))


def test_face_line_order_and_the_trough_takes_every_drip(cut) -> None:
    """cladding -> gutter back -> eave face; kick tip and pan drip land inside the mouth."""
    eave, gutter, pan = cut.one("eave"), cut.one("gutter"), cut.one("pan")
    face_bottom = min(lo for lo, _hi in _at_u(eave, 0.1))
    back_top = max(hi for _lo, hi in _at_u(gutter, 0.04))
    assert back_top - face_bottom >= 1.0, "the back stands 1\" up behind the face"
    z = (face_bottom + back_top) / 2.0
    cladding = max(hi for p in cut.of("cladding") for _lo, hi in _at_z(p, z))
    back = _at_z(gutter, z)[0]
    face = _at_z(eave, z)[0]
    assert cladding <= back[0] and back[1] <= face[0], "cladding, gutter back, eave face"
    front = gutter.bounds[2] - 1.0  # the front wall, inside the 1" bead
    floor = min(hi for _lo, hi in _at_u(gutter, 2.5))
    kick = min(eave.exterior.coords, key=lambda c: c[1])
    drip = min((c for c in pan.exterior.coords if c[0] > 1.0), key=lambda c: c[1])
    for name, (u, zz) in (("kick tip", kick), ("pan drip", drip)):
        assert back[1] < u < front and floor < zz < back_top, f"the {name} misses the trough"


def test_a_full_gutter_spills_outward(house, cut) -> None:
    """The front crest is no higher than the lowest way back toward the wall.

    The routes inward are the flange's upslope end and any joint through the back; the
    provisional hanger's screw is one, below the crest, and stays listed until bracket
    selection gives it a sealed or above-crest fixing.
    """
    model, roof, _ = house
    gutter = cut.one("gutter")
    crest = max(hi for _lo, hi in _at_u(gutter, gutter.bounds[2] - 0.5))
    routes = {"flange upslope end": gutter.bounds[3]}
    girt = next(m for m in model.all_members() if m.connection == "eave:gutter-girt"
                and m.category == "strapping")
    xs = [p[0] for p in roof.footprint]
    edge = (max(xs) if cut.sign > 0 else min(xs)) / M_PER_IN
    screw = hanger_screw(model, edge, cut.sign, "x", 17.4 * FT * M_PER_IN, girt)
    assert screw is not None
    routes["hanger screw"] = screw[1] - roof.eave_z_m / M_PER_IN
    below = {name for name, z in routes.items() if z < crest}
    assert below == KNOWN_OPEN_ROUTES, f"routes below the crest {crest:.2f}: {routes}"
    assert routes["flange upslope end"] - crest >= 1.0


@pytest.mark.parametrize("side", ["W", "E"])
def test_no_two_sheets_cross(house, side) -> None:
    """True gaps: no sheet metal, membrane or cladding passes through another.

    Five stations along each eave, and at both corners: across the eave's run-out past the
    gable face (where the gutter ends under its caps), inside the gable cladding (its top
    and the wide outside corner stop at the head cap), and four cuts square to it through
    the trough, caps and all.
    """
    _model, roof, _ = house
    ys = [p[1] for p in roof.footprint]
    xs = [p[0] for p in roof.footprint]
    edge = max(xs) if side == "E" else min(xs)
    sign = 1.0 if side == "E" else -1.0
    cuts = [("x", y * FT * M_PER_IN) for y in CLASH_STATIONS]
    cuts += [("x", min(ys) - 0.25 * M_PER_IN), ("x", max(ys) + 0.25 * M_PER_IN)]
    cuts += [("x", min(ys) + 0.3 * M_PER_IN), ("x", max(ys) - 0.3 * M_PER_IN)]
    cuts += [("y", edge + sign * u * M_PER_IN) for u in (0.3, 1.0, 3.0, 5.5)]
    found = {f"{axis}={station / M_PER_IN:.2f}": c
             for axis, station in cuts if (c := Cut(house, side, axis, station).clashes())}
    assert not found


def test_gutter_runs_out_under_the_eave_and_is_capped(house) -> None:
    """Placed off the same eave stack the engine builds; run to the eave's end; caps L/R."""
    model, roof, _ = house
    stack = eave_stack(model, roof)
    u0, z0 = stack.gutter_origin()
    xs = [p[0] for p in roof.footprint]
    eaves = {m.child_key: m for m in roof.members if m.child_key.endswith("image-ii-eave")}
    left, right = FORMED_GUTTERS["PBR_BOX_GUTTER_5X4"][2]
    for side, edge, key in (("W", min(xs), "eave-lo"), ("E", max(xs), "eave-hi")):
        gutter = model.plan.by_tag(f"TR-RF-GUTTER-{side}")
        assert abs(gutter.path[0].xy_m[0] - edge) == pytest.approx(u0, abs=1e-9)
        assert gutter.top_elevation.meters - roof.eave_z_m == pytest.approx(z0, abs=1e-9)
        body = next(s for s in model.solids if s.tag == f"TR-RF-GUTTER-{side}-1")
        eave = eaves[f"{key}-image-ii-eave"]
        ends = sorted((eave.p0[1], eave.p1[1]))
        assert body.outline[0][1] <= ends[0] + 1e-6 and body.outline[2][1] >= ends[1] - 1e-6
        caps = {s.product for s in model.solids if s.tag.startswith(f"TR-RF-GUTTER-{side}-CAP")}
        assert caps == {left, right}
        leader = next(s for s in model.solids if s.tag == f"TR-RF-LEADER-{side}")
        floor_underside = z0 - gutter.depth.meters - SHEET_24_GA_M
        assert leader.z1_m - roof.eave_z_m == pytest.approx(floor_underside, abs=1e-6)


def test_every_gutter_drains_to_a_declared_leader(catlin_model_ro) -> None:
    """A gutter falling to a downspout that does not exist is not a drainage system."""
    from typehaus.model.trim import Downspout, Gutter

    elements = list(catlin_model_ro.plan.all_elements())
    leaders = {el.tag for el in elements if isinstance(el, Downspout)}
    # TR-SG-RUNNEL lets go through a scupper (test_drainage_elements.py pins that end).
    for gutter in (el for el in elements if isinstance(el, Gutter) and el.tag != "TR-SG-RUNNEL"):
        assert gutter.downspout_ref in leaders, gutter.tag
    authored = catlin_model_ro.plan.by_tag("TR-RF-LEADER-E")
    assert authored.discharge_ref == "RG-E-BASIN" and authored.extension is not None


def test_membrane_takeoff_bills_the_strip_in(catlin_model_ro) -> None:
    from typehaus.takeoff.envelope import envelope_layer_takeoff

    rows = [r for r in envelope_layer_takeoff(catlin_model_ro)
            if r["scope"] == "roof eave strip-in"]
    # Two eaves x ~37' x the 9" strip, plus its climb over the stack.
    assert [r["material"] for r in rows] == ["roof-adhered-butyl-ht"]
    assert 2 * 37.1 * 0.75 < rows[0]["net_area_sqft"] < 2 * 37.6 * 0.8

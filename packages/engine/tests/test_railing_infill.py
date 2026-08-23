"""Guard infill geometry, for the styles the reference house does not author.

Every Catlin guard is a *flat baluster* guard and its five ``serves_stair`` railings are
handrails with ``infill=None``, so cable, panel, mesh and every raking infill would ship
with zero coverage. These build the missing cases on a synthetic plan and run the real
resolver over them (→ ``_railing_fixtures``), so what is asserted is the geometry that
ships rather than a re-derivation of it.

The Catlin-side coverage lives in ``test_accessories.py`` beside the existing railing
regressions, which is where the balcony guard's own picket reconciliation belongs.
"""

from __future__ import annotations

import math

import pytest

from typehaus.quantities import ft, inch, pt
from typehaus.resolve.railings.infill import INFILL_SOLID_BUDGET, derived_infill_count
from typehaus.resolve.railings.parts import (
    RAILING_GLASS_CATEGORY,
    RAILING_INFILL_CATEGORY,
    resolve_parts,
)
from typehaus.resolve.railings.spans import RAIL_BAND_STEP_M
from typehaus.resolve.round_solids import PIPE_SWEEP_BANDS
from _railing_fixtures import (
    centroid,
    infill_of,
    inches,
    railing,
    railing_type,
    resolve_railings,
    solids_of,
)

IN = 0.0254
#: A ten-foot straight guard at 60" o.c. — two bays, the smallest run that has an interior
#: post and therefore a bay walk worth testing.
_TEN_FOOT = (pt(ft(0), ft(0)), pt(ft(10), ft(0)))


def _z_span(solid) -> float:
    return solid.z1_m - solid.z0_m


# --- cable ------------------------------------------------------------------------------

def _cable_model(gap_in=3.0, **kw):
    return resolve_railings([railing(
        "RL-CABLE", path=_TEN_FOOT, infill="cable", baluster_spacing=inch(gap_in), **kw)])


def test_cable_count_derives_from_the_sphere_rule_and_one_fewer_breaks_it():
    """The count is R312.1.3's own algebra, not an authored number: ``n`` cables leave
    ``n+1`` openings up the clear height, and ``n`` is the smallest that holds every one at
    or under the gap. One fewer cable must break the rule, or the count is not minimal and
    the guard is carrying cable it does not need."""
    model = _cable_model(gap_in=3.0)
    solids = infill_of(model, "RL-CABLE")
    # Two bays, same count in each.
    assert len(solids) % 2 == 0
    per_bay = len(solids) // 2
    parts = resolve_parts(model, model.plan.by_tag("RL-CABLE"))
    clear = inch(42).meters - parts.rail_section_m
    diameter, gap = parts.cable_diameter_m, inch(3).meters
    assert per_bay == derived_infill_count(clear, diameter, gap)
    assert (clear - per_bay * diameter) / (per_bay + 1) <= gap + 1e-12
    # One fewer would open a gap the sphere fits: this is what makes the count minimal.
    fewer = per_bay - 1
    assert (clear - fewer * diameter) / (fewer + 1) > gap + 1e-12


def test_a_cable_is_one_band_not_a_facet_ring():
    """Pins the deliberate decision NOT to route cable through ``round_solids``. Faceting
    exists to fix the silhouette of a 4" pipe; a 3/16" cable is 4.8 mm, so a facet ring
    costs 6x the solids to move an edge under one screen pixel. A well-meaning "make the
    cables round like the pipes" refactor should fail here rather than in a frame budget."""
    model = _cable_model()
    solids = infill_of(model, "RL-CABLE")
    for solid in solids:
        assert len(solid.outline) == 4, "a cable band is a rectangle, not a facet ring"
    # One band per cable per span. Routed through ``round_solids`` each would become
    # PIPE_SWEEP_BANDS bands of a PIPE_FACETS-gon instead — 6x the solids to move an edge
    # under one screen pixel on a 4.8 mm cable.
    posts = [s for s in solids_of(model, "RL-CABLE", "railing") if "POST" in s.tag]
    per_bay = len(solids) // (len(posts) - 1)
    assert len(solids) == per_bay * (len(posts) - 1)
    assert len(solids) < per_bay * (len(posts) - 1) * PIPE_SWEEP_BANDS


def test_cable_bands_are_horizontal_and_span_the_bay():
    model = _cable_model()
    parts = resolve_parts(model, model.plan.by_tag("RL-CABLE"))
    for solid in infill_of(model, "RL-CABLE"):
        assert math.isclose(_z_span(solid), parts.cable_diameter_m, abs_tol=1e-12)


# --- panel and mesh ---------------------------------------------------------------------

def _panel_model(style="panel", material=None, materials=(), types=(), **kw):
    return resolve_railings(
        [railing("RL-PANEL", path=_TEN_FOOT, infill=style, infill_material=material, **kw)],
        types=types, materials=materials)


def test_a_panel_is_one_prism_per_bay_spanning_post_face_to_post_face():
    model = _panel_model()
    guard = model.plan.by_tag("RL-PANEL")
    parts = resolve_parts(model, guard)
    posts = solids_of(model, "RL-PANEL", "railing")
    posts = [s for s in posts if "POST" in s.tag]
    panels = infill_of(model, "RL-PANEL")
    assert len(panels) == len(posts) - 1, "one lite per bay"
    for panel, (a, b) in zip(panels, zip(posts, posts[1:])):
        bay = math.dist(centroid(a), centroid(b))
        xs = [x for x, _y in panel.outline]
        assert math.isclose(max(xs) - min(xs), bay - parts.post_section_m, abs_tol=1e-9)
        # Rail-top to rail-underside: half a rail section trimmed at each end.
        assert math.isclose(_z_span(panel),
                            inch(42).meters - parts.rail_section_m, abs_tol=1e-9)


def test_mesh_draws_as_a_sheet_exactly_as_a_panel_does():
    """Drawing the wire is thousands of solids for a feature invisible past about a metre,
    so mesh IS a sheet and its material is what says mesh."""
    panel = infill_of(_panel_model("panel"), "RL-PANEL")
    mesh = infill_of(_panel_model("mesh"), "RL-PANEL")
    assert len(panel) == len(mesh)
    for a, b in zip(panel, mesh):
        assert a.outline == b.outline
        assert (a.z0_m, a.z1_m) == (b.z0_m, b.z1_m)


def test_a_translucent_material_flips_the_category_and_an_opaque_one_does_not():
    """The split is a material fact, not a tag substring: a material declares itself
    see-through by authoring an 8-digit ``#RRGGBBAA`` colour whose alpha is not ``ff``.
    A panel that never named a translucent material stays ``railing_infill``, which is
    correct — a panel that did not say it was glass isn't."""
    clear = _panel_model(material="lite-glass", materials={"lite-glass": "#8fb7c97a"})
    assert {s.category for s in infill_of(clear, "RL-PANEL")} == {RAILING_GLASS_CATEGORY}

    opaque = _panel_model(material="lite-steel", materials={"lite-steel": "#8fb7c9"})
    assert {s.category for s in infill_of(opaque, "RL-PANEL")} == {RAILING_INFILL_CATEGORY}

    fully = _panel_model(material="lite-solid", materials={"lite-solid": "#8fb7c9ff"})
    assert {s.category for s in infill_of(fully, "RL-PANEL")} == {RAILING_INFILL_CATEGORY}


def test_mesh_never_becomes_glass_however_its_material_is_authored():
    """``railing_glass`` is for a translucent *panel*. Mesh reads through and is still not
    a lite: it must keep the metalness the frame has, which is keyed on the category."""
    model = _panel_model("mesh", material="wire", materials={"wire": "#8fb7c97a"})
    assert {s.category for s in infill_of(model, "RL-PANEL")} == {RAILING_INFILL_CATEGORY}


def test_a_panel_cap_widens_to_swallow_the_lite():
    """The top-rail cap is derived, never authored beside the panel: a 3/4" lite needs a cap
    wider than the 1-1/2" stock, and a 1/4" one does not move it."""
    fat = _panel_model(types=[railing_type("RT-FAT", panel_thickness=inch(1.5))],
                       type_ref="RT-FAT")
    parts = resolve_parts(fat, fat.plan.by_tag("RL-PANEL"))
    assert math.isclose(parts.rail_section_m, inch(1.5 + 0.5).meters, abs_tol=1e-12)
    # A lite thinner than the stock cap does not shrink it: the cap is stock extrusion.
    thin = _panel_model(types=[railing_type("RT-THIN", panel_thickness=inch(0.25))],
                        type_ref="RT-THIN")
    parts = resolve_parts(thin, thin.plan.by_tag("RL-PANEL"))
    assert math.isclose(parts.rail_section_m, inch(1.5).meters, abs_tol=1e-12)


# --- raking ------------------------------------------------------------------------------

class _FakeTread:
    """The shape ``flight_stations`` reads off a resolved tread: its riser line, its flight
    key, and the finished walking elevation of its top face."""

    category = "tread"

    def __init__(self, index: int, x: float, z1: float, width: float) -> None:
        self.child_key = f"tread-{index}"
        self.riser_line = ((x, -width / 2.0), (x, width / 2.0))
        self.p0, self.p1 = (x, -width / 2.0), (x, width / 2.0)
        self.z0_m, self.z1_m = z1 - 0.03, z1


@pytest.fixture(scope="module")
def raking_stair():
    """A straight flight climbing +x, one tread every 11" rising 7.5"."""
    from types import SimpleNamespace

    members = tuple(_FakeTread(index, index * inch(11).meters,
                               (index + 1) * inch(7.5).meters, ft(3).meters)
                    for index in range(12))
    return SimpleNamespace(tag="ST-RAKE", members=members, riser_count=13)


def _raking_model(stair, infill, **kw):
    guard = railing("RL-RAKE", path=(pt(ft(0), ft(0)), pt(ft(10), ft(0))),
                    infill=infill, serves_stair="ST-RAKE", **kw)
    return resolve_railings([guard], stairs=[stair])


def test_raking_balusters_rise_with_the_flight_and_stay_one_length(raking_stair):
    """The reconciliation that catches a wrong surface lookup: a picket's foot lands on the
    nosing line under *it*, so the feet climb — and because the head rises ``rail_h`` from
    that same foot, every picket is the same stick of metal. Read the surface from the wrong
    point and the elevations still look plausible while the lengths drift."""
    model = _raking_model(raking_stair, "balusters", baluster_spacing=inch(4))
    pickets = infill_of(model, "RL-RAKE")
    assert len(pickets) > 10
    by_x = sorted(pickets, key=lambda s: centroid(s)[0])
    feet = [s.z0_m for s in by_x]
    assert feet == sorted(feet), "picket feet must climb with the flight"
    assert feet[-1] - feet[0] > inch(48).meters, "a 10' run of stair rises more than 4'"
    lengths = {round(_z_span(s), 9) for s in by_x}
    assert len(lengths) == 1, f"raking pickets drifted in length: {sorted(lengths)}"


def test_raking_panels_band_at_the_rail_band_step(raking_stair):
    """A prism-only IR fakes a slope by banding it, and a raking panel reuses the very same
    ``spans`` the rails do — so its band count is the rails' band count, not a second story
    about how a slope is approximated."""
    model = _raking_model(raking_stair, "panel")
    guard = model.plan.by_tag("RL-RAKE")
    parts = resolve_parts(model, guard)
    posts = [s for s in solids_of(model, "RL-RAKE", "railing") if "POST" in s.tag]
    panels = infill_of(model, "RL-RAKE")
    expected = 0
    for a, b in zip(posts, posts[1:]):
        clear = math.dist(centroid(a), centroid(b)) - parts.post_section_m
        expected += max(int(math.ceil(clear / RAIL_BAND_STEP_M)), 1)
    assert len(panels) == expected


def test_a_handrail_gets_no_infill_even_when_it_states_one(raking_stair):
    """The gate is ``role``, and it is the same predicate the R312.1.3 census uses to decide
    what a guard is — so the geometry and the code census cannot disagree about it."""
    model = _raking_model(raking_stair, "balusters", role="handrail",
                          baluster_spacing=inch(4))
    assert infill_of(model, "RL-RAKE") == []


# --- budget and bay warnings --------------------------------------------------------------

def test_the_budget_truncates_with_exactly_one_warn():
    """A pathological input becomes a build message rather than a silent viewer stall."""
    model = resolve_railings([railing(
        "RL-HUGE", path=(pt(ft(0), ft(0)), pt(ft(400), ft(0))),
        infill="balusters", baluster_spacing=inch(0.5))])
    solids = infill_of(model, "RL-HUGE")
    assert len(solids) == INFILL_SOLID_BUDGET
    warns = [f for f in model.railing_findings
             if f.check_id == "geometry.railing_infill_truncated"]
    assert len(warns) == 1 and "RL-HUGE" in warns[0].message


def test_a_bay_can_no_longer_run_over_the_authored_post_spacing():
    """``railing_post_stations`` used ``int(seg // spacing)`` where it wanted ``ceil``, so a
    segment's last bay could approach 2x the authored spacing. Balusters absorbed that
    invisibly — they re-space to the bay they are given — but a 9' glass lite does not
    exist, and ``geometry.railing_bay_oversize`` existed to say so.

    Fixed at the source on 2026-08-22: bays are divided evenly, ``ceil(seg / spacing)`` of
    them, so ``spacing`` is a maximum and this warning has nothing left to report on a run
    laid out by that function. It stays as the backstop for a caller that lays out its own
    stations.
    """
    # 5'-11" at 3'-0" o.c.: ``int(5.917 // 3)`` was 1, so the whole run came out as ONE bay
    # of 5'-11" rather than the two a ``ceil`` places — just under 2x the authored spacing.
    wide = (pt(ft(0), ft(0)), pt(ft(5, 11), ft(0)))
    panel = resolve_railings([railing("RL-WIDE", path=wide, infill="panel",
                                      post_spacing=inch(36))])
    assert panel.railing_findings == []
    pickets = resolve_railings([railing("RL-WIDE", path=wide, infill="balusters",
                                        post_spacing=inch(36), baluster_spacing=inch(4))])
    assert pickets.railing_findings == []


# --- the material ladder ------------------------------------------------------------------

def test_the_material_ladder_runs_element_then_type_then_nothing():
    """Three rungs, and the third is deliberately "do nothing": leaving ``material=None``
    with the authored ``assembly`` lets the *existing* third rung of the colour walk run
    unchanged, which is provably the same value a house got before any of this existed."""
    product = railing_type("RT-M", post_material="type-post", rail_material="type-rail",
                           infill_material="type-infill")

    typed = resolve_railings([railing("RL-M", path=_TEN_FOOT, type_ref="RT-M",
                                      infill="balusters", baluster_spacing=inch(4))],
                             types=[product])
    parts = resolve_parts(typed, typed.plan.by_tag("RL-M"))
    assert (parts.post_material, parts.rail_material, parts.infill_material) == (
        "type-post", "type-rail", "type-infill")

    overridden = resolve_railings([railing("RL-M", path=_TEN_FOOT, type_ref="RT-M",
                                           post_material="el-post", infill="balusters",
                                           baluster_spacing=inch(4))], types=[product])
    parts = resolve_parts(overridden, overridden.plan.by_tag("RL-M"))
    assert parts.post_material == "el-post", "the element's own field wins over the type"
    assert parts.rail_material == "type-rail", "...and only for the part it names"

    bare = resolve_railings([railing("RL-M", path=_TEN_FOOT, infill="balusters",
                                     baluster_spacing=inch(4))])
    parts = resolve_parts(bare, bare.plan.by_tag("RL-M"))
    assert (parts.post_material, parts.rail_material, parts.infill_material) == (
        None, None, None)
    for solid in bare.solids:
        assert solid.material is None
        assert solid.assembly == "RAILING_DARK_METAL", (
            "rung three leaves the assembly to drive the colour, exactly as before")


def test_the_product_states_the_picket_width_and_a_length_is_not_dressed_lumber():
    """``baluster_width`` is a ``Length``, not a nominal string: ``_nominal_actual_m``
    applies 2"->1.5" dressed-lumber arithmetic that a 3/4" extruded aluminium picket does
    not obey, and a picket sized through it would be off by a third."""
    product = railing_type("RT-W", baluster_width=inch(0.5))
    model = resolve_railings([railing("RL-W", path=_TEN_FOOT, type_ref="RT-W",
                                      infill="balusters", baluster_spacing=inch(4))],
                             types=[product])
    parts = resolve_parts(model, model.plan.by_tag("RL-W"))
    assert math.isclose(parts.baluster_width_m, inch(0.5).meters, abs_tol=1e-12)
    picket = infill_of(model, "RL-W")[0]
    xs = [x for x, _y in picket.outline]
    ys = [y for _x, y in picket.outline]
    assert math.isclose(max(xs) - min(xs), inch(0.5).meters, abs_tol=1e-9)
    assert math.isclose(max(ys) - min(ys), inch(0.5).meters, abs_tol=1e-9)


def test_a_masonry_railing_frames_nothing():
    """``RailingKind.MASONRY`` is authored as a Wall with ``guard=True``, which keeps its
    layer stack and its cubic-yard take-off. Framing a stick guard here would draw a second,
    wrong guard on top of the real one."""
    from typehaus.model.enums import RailingKind

    model = resolve_railings([railing("RL-MAS", path=_TEN_FOOT, kind=RailingKind.MASONRY,
                                      infill="balusters", baluster_spacing=inch(4))])
    assert model.solids == []


def test_a_diagonal_guard_draws_square_pickets_not_lozenges():
    """A picket on a diagonal run is square to *the run*. Built with an axis-aligned square
    it comes out a lozenge, which is what the balcony guard's angled legs would show."""
    diagonal = (pt(ft(0), ft(0)), pt(ft(7.07106781), ft(7.07106781)))
    model = resolve_railings([railing("RL-DIAG", path=diagonal, infill="balusters",
                                      baluster_spacing=inch(4))])
    parts = resolve_parts(model, model.plan.by_tag("RL-DIAG"))
    for picket in infill_of(model, "RL-DIAG"):
        sides = [math.dist(picket.outline[i], picket.outline[(i + 1) % 4]) for i in range(4)]
        for side in sides:
            assert math.isclose(side, parts.baluster_width_m, abs_tol=1e-9), (
                f"picket sides, in inches: {[round(inches(s), 3) for s in sides]}")


# --- the .glb half of the translucency contract ----------------------------------------------

def test_a_glass_lite_exports_translucent_in_the_glb():
    """The acceptance the live-viewer assertion in ui/src/components/Panel3D.test.ts cannot
    reach: a glass guard has to be see-through in the *export* as well, or the model a
    consultant opens in Revit shows a solid slab where the lite is.

    Both halves read the same fact — the alpha byte of the material's authored
    ``#RRGGBBAA`` — so this pins the engine end of a contract whose browser end is pinned
    over there. ``emit/gltf/scene.py`` keys ``alphaMode: BLEND`` and ``doubleSided`` off the
    alpha this returns, which is why a colour with alpha 1.0 is not merely a cosmetic miss:
    it also makes a thin pane single-sided and invisible from behind.
    """
    from typehaus.emit.gltf.palette import _solid_color

    model = _panel_model(material="lite-glass", materials={"lite-glass": "#8fb7c97a"})
    lite = infill_of(model, "RL-PANEL")[0]
    red, green, blue, alpha = _solid_color(model, lite)
    assert alpha == pytest.approx(0x7a / 255, abs=1e-6), (
        "the lite's own material ref carries its alpha through the solid colour walk")
    assert (red, green, blue) == pytest.approx((0x8f / 255, 0xb7 / 255, 0xc9 / 255), abs=1e-6)

    # An opaque sheet in the same guard shape stays opaque — the alpha is a material fact,
    # never inferred from the category or the tag.
    opaque = _panel_model(material="lite-steel", materials={"lite-steel": "#8fb7c9"})
    assert _solid_color(opaque, infill_of(opaque, "RL-PANEL")[0])[3] == 1.0


def test_the_glb_material_for_a_glass_lite_blends_and_is_double_sided():
    """One step further down the same path: the scene builder's own switch. A pane that
    exports OPAQUE or single-sided is the bug this alpha exists to prevent, and asserting the
    colour alone would not catch a regression in the switch that reads it. Double-sided is not
    a nicety — a lite is a thin prism, so a single-sided one vanishes when you walk around it.
    """
    from typehaus.emit.gltf.palette import _solid_color
    from typehaus.emit.gltf.scene import _SceneBuilder

    model = _panel_model(material="lite-glass", materials={"lite-glass": "#8fb7c97a"})
    builder = _SceneBuilder()
    index = builder._material(_solid_color(model, infill_of(model, "RL-PANEL")[0]))
    material = builder._materials[index]
    assert material["alphaMode"] == "BLEND"
    assert material["doubleSided"] is True

    opaque = _panel_model(material="lite-steel", materials={"lite-steel": "#8fb7c9"})
    index = builder._material(_solid_color(opaque, infill_of(opaque, "RL-PANEL")[0]))
    assert builder._materials[index]["alphaMode"] == "OPAQUE"
    assert builder._materials[index]["doubleSided"] is False

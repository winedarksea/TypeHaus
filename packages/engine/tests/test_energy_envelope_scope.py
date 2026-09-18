"""What the block load counts, and what it comes to — pinned, because nothing pinned it.

**No test or golden held any absolute block-load number before this file.**
``houses/catlin/out/`` is gitignored and every energy assertion in the suite was relational
or structural, so the whole-house scope could drift 20% in either direction and the suite
stayed green. It did drift: a review found every component line wrong, in both directions,
by 0.5–2.0 kBtu/h, with a total that survived by cancellation. This file is the coverage
that would have caught it.

Two kinds of test here, and the second kind is the one worth reading:

* ``test_the_catlin_block_load_is_pinned`` holds the numbers. A diff on it is a diff on a
  Btu/h figure, which tells a reviewer that something moved and nothing about what.
* the rest hold the **classifications** — the sorted wall set, which slab is an interior
  floor and why, which wall is graded at the court floor. A diff on one of those is
  readable in review in a way a Btu/h number is not, and each one is aimed at a specific
  wrong answer the derivation was measured against.

Oracled by ``houses/catlin/notes/block_load_basis.md``; the arithmetic behind §§1-3 is in
``test_energy_ground.py``.
"""

from __future__ import annotations

import pytest

from typehaus.checks.building_science.envelope_geometry import (
    carries_a_weather_skin,
    envelope_geometry,
)
from typehaus.checks.building_science.wwr import _facade_for_wall
from typehaus.checks.registry import Preferences
from typehaus.energy import estimate_block_load

# --- the pinned result ---------------------------------------------------------------------

_HEATING_BTUH = 31_713.5
_COOLING_BTUH = 22_154.4
_COOLING_TONS = 1.8462

# ``(kind, area_ft2, ua_btu_per_hour_f)`` in the order the report emits them.
_COMPONENTS = (
    ("walls", 3233.7, 73.658),
    ("foundation_walls", 763.3, 28.155),
    ("foundation_walls_above_grade", 253.1, 11.532),
    ("roof", 1547.9, 29.103),
    ("slab", 1296.0, 25.468),
    ("windows", 261.0, 61.207),
    ("doors", 120.0, 24.000),
)

# The whole envelope, by tag. 50 walls.
_ENVELOPE_WALLS = (
    "W-A-N1", "W-A-N2", "W-A-N2B", "W-A-S1", "W-A-S2", "W-A-S3",
    "W-B-E1", "W-B-E2", "W-B-N1", "W-B-N2", "W-B-N3", "W-B-N4",
    "W-B-S1", "W-B-S2", "W-B-S2-FR", "W-B-S3", "W-B-S3-FR", "W-B-S4",
    "W-B-W1", "W-B-W2",
    "W-M-E1", "W-M-N1", "W-M-N1B", "W-M-N2", "W-M-N3", "W-M-N3B",
    "W-M-S1", "W-M-S2", "W-M-W1", "W-M-W1B", "W-M-W1C", "W-M-W2", "W-M-W3", "W-M-W4",
    "W-S-E1", "W-S-E2", "W-S-E3", "W-S-E4", "W-S-N1", "W-S-N1B", "W-S-N2", "W-S-N3",
    "W-S-N3B", "W-S-S1", "W-S-S2", "W-S-W1", "W-S-W1B", "W-S-W2", "W-S-W3", "W-S-W4",
)

# The nine stem walls of the DETACHED garage plus the retired breezeway screen wall. They
# are filed on the house's own ``main`` storey key because they share the plan frame.
_DETACHED_GARAGE_WALLS = (
    "W-GF-E", "W-GF-N", "W-GF-N-DR", "W-GF-N2", "W-GF-S-DR",
    "W-GF-S1", "W-GF-S2", "W-GF-S3", "W-GF-W",
)

# The five walls ``both_faces_interior`` is the ONLY test that excludes: they bound a
# conditioned room, they carry a skin or are cast as foundation, and there is interior space
# on both faces. Three basement centre bearing walls and the two tub-deck partitions. The
# naive "conditioned on exactly one side" rule kept all five.
_INTERIOR_BUT_BOUNDING = ("W-B-CN", "W-B-CN2", "W-B-CS2", "W-M-TUBDK-S", "W-M-TUBDK-W")


def _report(model):
    return estimate_block_load(model, Preferences(
        ach50=1.0, window_u=0.25, infiltration_storeys=2.0,
        adequate_overhang_ft=0.0))


# --- 1. the numbers -------------------------------------------------------------------------

def test_the_catlin_block_load_is_pinned(catlin_model_ro) -> None:
    """The only test that holds an absolute figure, and the only one that would have caught
    any of the six defects this file was written for.

    ``rel=0.005`` is deliberate: tighter and a shapely or libm difference between platforms
    breaks it, looser and a real half-kBtu/h component error hides inside it.
    """
    report = _report(catlin_model_ro)
    assert report.unknown_inputs == (), report.unknown_inputs
    assert report.heating_load_btu_per_hour == pytest.approx(_HEATING_BTUH, rel=0.005)
    assert report.cooling_load_btu_per_hour == pytest.approx(_COOLING_BTUH, rel=0.005)
    assert report.cooling_tons == pytest.approx(_COOLING_TONS, rel=0.005)


def test_every_component_line_is_pinned_not_only_the_total(catlin_model_ro) -> None:
    """**The total was right to 1% while every one of its parts was wrong.** A sum is not
    coverage: five corrections of 0.5-2.0 kBtu/h each moved this house's heating figure by
    17 Btu/h, because they pushed in both directions. Pin the parts."""
    report = _report(catlin_model_ro)
    actual = tuple((c.kind, c.area_ft2, c.ua_btu_per_hour_f) for c in report.components)
    assert [kind for kind, _, _ in actual] == [kind for kind, _, _ in _COMPONENTS]
    for (kind, area, ua), (_, want_area, want_ua) in zip(actual, _COMPONENTS, strict=True):
        assert area == pytest.approx(want_area, rel=0.005), kind
        assert ua == pytest.approx(want_ua, rel=0.005), kind


def test_the_two_ground_coupled_components_carry_the_derived_ground_delta(
        catlin_model_ro) -> None:
    """Note §1: 45.14 °F, derived as ``70 - (46.858 - 22)``. It was 23 °F — the annual mean
    — which is nearly a factor of two on every below-grade surface in the house."""
    report = _report(catlin_model_ro)
    by_kind = {c.kind: c for c in report.components}
    assert by_kind["foundation_walls"].heating_delta_f == pytest.approx(45.14, abs=0.01)
    assert by_kind["slab"].heating_delta_f == pytest.approx(45.14, abs=0.01)
    for kind in ("walls", "foundation_walls_above_grade", "roof", "windows", "doors"):
        assert by_kind[kind].heating_delta_f == pytest.approx(85.0), kind


# --- 2. the classifications -----------------------------------------------------------------

def test_the_envelope_wall_set_is_exactly_these_tags(catlin_model_ro) -> None:
    """A diff on this list is readable in review; a diff on a Btu/h number is not.

    The derivation that produced it was measured against the naive alternative — "a wall is
    envelope when conditioned space stands on exactly one side of it", probed off the wall
    faces — which moved 25 walls, 12 right and 13 wrong. The three tests this composes are
    each aimed at one family of those 13 (→ ``envelope_geometry``'s module docstring).
    """
    geometry = envelope_geometry(catlin_model_ro)
    actual = tuple(sorted(wall.tag for wall in catlin_model_ro.walls
                          if geometry.is_envelope_wall(wall)))
    assert actual == tuple(sorted(_ENVELOPE_WALLS))


def test_the_detached_garage_stem_is_not_the_houses_envelope(catlin_ctx) -> None:
    """Two halves of what LOOKS like one question, and they have opposite answers.

    The garage is detached and unconditioned, so its nine stem walls carry no UA against the
    house's interior setpoint and must be out of the block load. But ``GARAGE_ICF_6`` must
    stay IN ``conditioned_envelope_assemblies``, because the condensation FAIL on it is what
    ``houses/catlin/CLAUDE.md`` records as the reason for the coil band's 1/4" vented
    standoff — a real detail on a real wall.

    They are held in one test because the hazard is that they look like the same question.
    Strengthening ``_storey_is_conditioned`` — the obvious way to drop the garage — deletes
    that FAIL, which is why that function was deliberately left alone and only its uses in
    the block load were removed.
    """
    from typehaus.checks.building_science.condensation import (
        conditioned_envelope_assemblies,
    )

    geometry = envelope_geometry(catlin_ctx.model)
    for tag in _DETACHED_GARAGE_WALLS:
        wall = catlin_ctx.model.wall(tag)
        assert wall is not None, tag
        assert not geometry.is_envelope_wall(wall), tag
        assert not geometry.bounds_conditioned_space(wall), tag
    assert "GARAGE_ICF_6" in conditioned_envelope_assemblies(catlin_ctx)


def test_the_sunken_garden_walkout_walls_are_envelope(catlin_model_ro) -> None:
    """The two walls the scope fix ADDS, and the veneer wythe it must still keep out.

    ``W-B-S2-FR`` / ``W-B-S3-FR`` are framed walls standing in the open air of the sunken
    court; no room polygon reaches them and the old rule wanted a cladding layer, so they
    were envelope only by luck of that layer. ``W-B-BRICK`` is a glazed-brick wythe standing
    1" off the court wall — the envelope it appears to be is already counted behind it — and
    its two unglazed rough openings have no window type, so admitting it takes the whole
    block load to UNKNOWN over 0.34 sf of hole.
    """
    geometry = envelope_geometry(catlin_model_ro)
    for tag in ("W-B-S2-FR", "W-B-S3-FR"):
        assert geometry.is_envelope_wall(catlin_model_ro.wall(tag)), tag
    brick = catlin_model_ro.wall("W-B-BRICK")
    assert not geometry.is_envelope_wall(brick)
    # Excluded on GEOMETRY — its body is 0.154 m off the nearest conditioned room's face —
    # not on the ``"W-B-BRICK"`` tag prefix this used to carry.
    assert not geometry.bounds_conditioned_space(brick)

    report = _report(catlin_model_ro)
    brick_openings = {opening.tag for opening in catlin_model_ro.openings
                      if opening.host_wall == "W-B-BRICK"}
    assert brick_openings  # the wythe really does host two, so this is a real exclusion
    assert not any(tag in item for tag in brick_openings
                   for item in report.unknown_inputs)
    # And the real glazing in that elevation is the court wall's, on the south facade.
    for tag in ("D-B-PATIO", "WIN-B-SAUNA"):
        opening = next(o for o in catlin_model_ro.openings if o.tag == tag)
        host = catlin_model_ro.wall(opening.host_wall)
        assert geometry.is_envelope_wall(host), tag
        assert _facade_for_wall(host, catlin_model_ro) == "S", tag


def test_a_chase_and_an_unmodelled_attic_void_are_interior(catlin_model_ro) -> None:
    """``both_faces_interior`` is the only one of the three tests that excludes these five,
    and it is why the rule needs an interior REGION rather than a room-coverage test.

    ``INTERIOR = fill_holes(⋃ rooms ∪ ⋃ wall bodies) − ⋃ wall bodies``. Filling the holes is
    what turns a bath chase and an unmodelled attic void into interior — no room polygon
    covers either — and subtracting the bodies back out is what stops the 1" gap behind
    ``W-B-BRICK`` reading as interior for ``W-B-S2-FR``. A morphological closing reaches
    neither: they are holes, not concavities.

    Pinned as a SET so the repair is not quietly simplified back out.
    """
    geometry = envelope_geometry(catlin_model_ro)
    caught = tuple(sorted(
        wall.tag for wall in catlin_model_ro.walls
        if geometry.bounds_conditioned_space(wall)
        and (carries_a_weather_skin(wall) or wall.is_foundation)
        and geometry.both_faces_interior(wall)))
    assert caught == tuple(sorted(_INTERIOR_BUT_BOUNDING))


def test_an_interior_floor_between_two_conditioned_storeys_carries_no_ua(
        catlin_model_ro) -> None:
    """A slab is envelope when EXACTLY ONE side is conditioned, and the assertion is on the
    REASON rather than on the outcome, so a slab that drops out for the wrong reason fails.

    ``SL-M-DECK`` has the living room above and a play room below; ``SL-M-TUBDK`` has a
    bathroom above and the mechanical room below. Both were in the block load, billed as
    envelope floors at a soil ΔT. The two yard pads are the other error in the same list —
    conditioned on NEITHER side, 6.9 and 9.3 sf of concrete under an outdoor condenser — and
    they were excluded from the MN table by a named tag and from nothing else.
    """
    geometry = envelope_geometry(catlin_model_ro)
    by_tag = {solid.tag: solid for solid in catlin_model_ro.solids
              if solid.category == "slab"}
    for tag in ("SL-M-DECK", "SL-M-TUBDK"):
        is_envelope, reason = geometry.is_envelope_slab(by_tag[tag])
        assert not is_envelope, tag
        assert reason.count("conditioned") == 2, (tag, reason)
    for tag in ("SL-M-HP1PAD", "SL-M-HP3PAD"):
        is_envelope, reason = geometry.is_envelope_slab(by_tag[tag])
        assert not is_envelope, tag
        assert reason == "above=outside(None) below=outside(None)", (tag, reason)
    # The basement floor is the one that IS envelope, and the garage floor faces a BUFFER —
    # a third answer, which is what lets the next house name the gap instead of guessing a
    # garage temperature.
    assert geometry.is_envelope_slab(by_tag["SL-B-FLOOR"])[0]
    assert "buffer" in geometry.is_envelope_slab(by_tag["SL-G-FLOOR"])[1]
    assert not geometry.is_envelope_slab(by_tag["SL-G-FLOOR"])[0]


def test_the_house_roof_is_envelope_and_the_two_outbuilding_roofs_are_not(
        catlin_model_ro) -> None:
    """Nothing is above a roof, so the test is one-sided: is conditioned space below it.
    ``RF-GARAGE`` reads *buffer* and ``RF-BW-CANOPY`` reads *outside* — two different facts,
    and the old per-storey screen could tell neither from the house's own roof."""
    geometry = envelope_geometry(catlin_model_ro)
    by_tag = {roof.tag: roof for roof in catlin_model_ro.roofs}
    assert geometry.is_envelope_roof(by_tag["RF-HOUSE"])[0]
    assert not geometry.is_envelope_roof(by_tag["RF-GARAGE"])[0]
    assert "buffer" in geometry.is_envelope_roof(by_tag["RF-GARAGE"])[1]
    assert not geometry.is_envelope_roof(by_tag["RF-BW-CANOPY"])[0]


# --- 3. the grade split ---------------------------------------------------------------------

def test_the_walkout_wall_is_graded_at_the_court_floor_not_the_site_plane(
        catlin_model_ro) -> None:
    """Note §4. ``Site.grade`` is one plane at -0.864 m; the walkout walls span to -2.596 m
    with the court floor at -2.780. Splitting them at the global plane buries **1.73 m of
    open-air wall in soil ΔT** — a 3.7× understatement on the walls the scope fix just
    added.

    And it has to be a directional STRIP, not a radius. ``W-B-S1`` is collinear with the
    walkout and clips the court's corner, so the radial distances are 0.148 m against
    0.100 m — no separation at all. The strip separates them by about 25×.
    """
    from typehaus.resolve.site_earth import (
        open_excavation_floors,
        site_grade_elevation_m,
        strip_grade_elevation_m,
    )

    geometry = envelope_geometry(catlin_model_ro)
    floors = open_excavation_floors(catlin_model_ro)
    assert [tag for tag, _, _ in floors] == ["SL-SG-FLOOR"]
    site_grade = site_grade_elevation_m(catlin_model_ro)
    assert site_grade == pytest.approx(-0.8636, abs=0.001)

    def graded_at(tag: str) -> tuple[float, str | None]:
        wall = catlin_model_ro.wall(tag)
        strip = geometry.exterior_grade_strip(wall)
        assert strip is not None, tag
        return strip_grade_elevation_m(catlin_model_ro, strip, floors)

    for tag in ("W-B-S2", "W-B-S2-FR", "W-B-S3", "W-B-S3-FR"):
        elevation, governing = graded_at(tag)
        assert governing == "SL-SG-FLOOR", tag
        assert elevation == pytest.approx(-2.780, abs=0.001), tag
    # The collinear neighbour is NOT graded at the court floor, which is the whole point.
    elevation, governing = graded_at("W-B-S1")
    assert governing != "SL-SG-FLOOR"
    assert elevation > -1.1


def test_the_above_grade_band_sees_air(catlin_model_ro) -> None:
    """The split emits THREE wall components, not two, and the third is 253 sf of catlin's
    walkout: cast concrete standing proud of its own local grade, at the 85 °F air ΔT.

    Folded into ``foundation_walls`` it is charged a soil ΔT. Folded into ``walls`` it claims
    to carry cladding, which breaks the ``walls.area_ft2 <= clad_wall_area_ft2`` bound
    ``test_energy_sheet`` asserts. It is a component.
    """
    report = _report(catlin_model_ro)
    by_kind = {c.kind: c for c in report.components}
    proud = by_kind["foundation_walls_above_grade"]
    buried = by_kind["foundation_walls"]
    assert proud.area_ft2 == pytest.approx(253.1, rel=0.005)
    assert proud.ua_btu_per_hour_f == pytest.approx(11.532, rel=0.005)
    assert proud.heating_delta_f == pytest.approx(85.0)
    assert buried.area_ft2 == pytest.approx(763.3, rel=0.005)
    assert buried.ua_btu_per_hour_f == pytest.approx(28.155, rel=0.005)
    # The buried band's U is the soil-path average, so it is BELOW the bare assembly's even
    # though both bands are the same walls at the same R.
    assert (buried.ua_btu_per_hour_f / buried.area_ft2) < (
        0.85 * proud.ua_btu_per_hour_f / proud.area_ft2)


def test_a_raked_gable_wall_is_billed_as_a_trapezoid(catlin_model_ro) -> None:
    """Note §5. ``z1_m`` on a ``ToRoof`` wall is the RIDGE, so ``length × (z1 - z0)`` makes
    every gable a rectangle: 657.6 ft² billed against 414.0 ft² real over catlin's attic
    gables, about 470 Btu/h of invented heating."""
    from typehaus.checks.building_science.energy_load import _wall_top_z_m
    from typehaus.checks.building_science.wwr import _wall_length

    geometry = envelope_geometry(catlin_model_ro)
    gables = [wall for wall in catlin_model_ro.walls
              if geometry.is_envelope_wall(wall)
              and wall.top_z0_m is not None and wall.top_z1_m is not None
              and abs(wall.top_z0_m - wall.top_z1_m) > 0.01]
    assert gables, "catlin has raked gable walls, so this is a real correction"
    prism = sum(_wall_length(w) * (w.z1_m - w.z0_m) for w in gables) * 10.7639104167
    trapezoid = sum(_wall_length(w) * (_wall_top_z_m(w) - w.z0_m)
                    for w in gables) * 10.7639104167
    assert trapezoid < prism
    assert prism - trapezoid == pytest.approx(243.6, rel=0.02)


# --- 4. the other two houses ----------------------------------------------------------------

def test_starter_keeps_every_wall_it_had(starter_dir) -> None:
    """The derivation was measured on ``houses/starter`` as well and moved nothing there:
    ten walls in, ten walls out. A scope rule that only works on the house it was written
    against is the tag-prefix list again in a different shape."""
    from typehaus.resolve import resolve
    from typehaus.source import load_plan

    result = load_plan(starter_dir)
    assert result.plan is not None
    model, _ = resolve(result.plan)
    geometry = envelope_geometry(model)
    assert sorted(w.tag for w in model.walls if geometry.is_envelope_wall(w)) == [
        "W-101", "W-102", "W-103", "W-104",
        "W-201", "W-202", "W-203", "W-203B", "W-204", "W-204B",
    ]


def test_a_house_with_no_conditioned_room_says_so() -> None:
    """``houses/empty`` resolves no rooms and no walls. Every component is zero, the load is
    zero, and the gaps are NAMED — an empty envelope must not read as a tight one."""
    from _helpers import HOUSES
    from typehaus.resolve import resolve
    from typehaus.source import load_plan

    result = load_plan(HOUSES / "empty")
    assert result.plan is not None
    model, _ = resolve(result.plan)
    report = estimate_block_load(model, Preferences(ach50=1.0, window_u=0.25))
    assert report.heating_load_btu_per_hour == 0.0
    assert report.cooling_load_btu_per_hour == 0.0
    assert all(c.ua_btu_per_hour_f == 0.0 for c in report.components)
    assert any("conditioned volume" in item for item in report.unknown_inputs)


# --- 5. the cache ---------------------------------------------------------------------------

def test_the_derivation_is_cached_on_the_ir(catlin_model_ro) -> None:
    """``EnvelopeGeometry`` costs ~30 ms and ``estimate_block_load`` runs eleven times in one
    check pass. Cached on the IR the way ``_tag_index`` is — ``ResolvedModel`` is a mutable
    dataclass with ``__hash__ = None``, so an ``id()``-keyed module map would be unsafe."""
    first = envelope_geometry(catlin_model_ro)
    assert envelope_geometry(catlin_model_ro) is first
    assert catlin_model_ro._envelope_geometry is first

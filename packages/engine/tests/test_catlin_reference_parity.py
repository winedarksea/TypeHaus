"""Dimensional parity with the catlin-house reference details.

The reference drawings (``catlin-house/catlin_house/*_ifc.py`` → ``out/*_ifc.png``) are the
fidelity bar for Catlin's transition details. They are IFC-driven: every dimension they draw
comes from a ``Pset_ifcPlot_*`` ``ParamsJSON`` property, extracted here into
``fixtures/catlin_reference/*.json`` by ``scripts/extract_catlin_reference_params.py``.

These tests assert that TypeHaus resolves the *same dimensions*, not the same pixels, and
only for the facts the reference actually fixes. Catlin is expected to evolve past this
source as the design is refined — a divergence is a decision to record in
``DECLARED_DIVERGENCES`` (with its reason), never a reason to freeze the house.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures" / "catlin_reference"


def _params(name: str) -> dict:
    return json.loads((FIXTURES / f"{name}.json").read_text())


def _layer(library, assembly_tag: str, layer_name: str):
    asm = library.resolve_assembly(assembly_tag)
    assert asm is not None, f"no assembly {assembly_tag}"
    layer = next((ly for ly in list(asm.default_lining) + list(asm.layers)
                  if ly.name == layer_name), None)
    assert layer is not None, f"{assembly_tag} has no layer {layer_name!r}"
    return layer


# Deliberate departures from the reference, each with the reason it is intentional. A test
# failure here means the design moved without the decision being written down.
DECLARED_DIVERGENCES = {
    "wall/sheathing_in": (
        "reference 5/8\" Struct 1; Catlin uses 1/2\" Struct 1 — thinner sheathing over "
        "4\" of exterior CI, where the sheathing is a nailbase rather than the thermal layer"
    ),
    # "slab/xps_under_in" was a declared divergence (Catlin 3" at 40 psi against the
    # reference's 2") until 2026-08-31, when an insulation review took the basement slab
    # back to 2" — the owner's slab target is R-10 and 3" was reading R-16.1 whole-assembly.
    # Catlin and the reference agree again, so the entry is gone and the parity assertion
    # above now holds it. The GARAGE slab is 1" and is not covered here: the reference
    # fixes the basement slab only.
    "wall/polyiso_in": (
        "reference 2\" polyiso as the inner course of a 4\" rigid-CI stack; Catlin sprays "
        "1-1/2\" of closed-cell foam there instead (2026-08-23 truss wall). The 4\" of "
        "exterior insulation is unchanged and is asserted below — what moved is HOW it is "
        "applied: three sprayed bands around two tiers of flat 2x4 girts, no boards, no WRB"
    ),
    "wall/furring_in": (
        "reference 1/2\" furring held off the studs through 4\" of board by 8\" screws; "
        "Catlin's cladding now stands off on the catlin truss's OUTER GIRT (2026-08-26) — a "
        "KDAT 2x4 laid flat, horizontal, 24\" o.c., 1-1/2\" deep, with a 1/2\" vented gap "
        "authored behind it and a second SPF girt tier buried in the foam behind that"
    ),
    "wall/cladding_in": (
        "reference 1/2\" standing-seam pan; Catlin's house walls carry 1-1/4\" of "
        "exposed-fastener PBR panel (2026-08-26). The extra 3/4\" is RIB HEIGHT, not "
        "material — a PBR panel is a 26 ga sheet whose 1-1/4\" major ribs at 12\" o.c. set "
        "the depth of the band, where a snap-lock pan's depth is the pan. The swap is the "
        "cost lever recorded in plans/cost-options.md under \"Do not reopen\" (it is TAKEN "
        "and in the baseline), and it is what moved the house's "
        "cladding face from 6.5\" to 7.25\". The garage (GARAGE_WALL_2X6) keeps the 1/2\" "
        "reference dimension, so that number is still resolved somewhere in the house"
    ),
}


# (fixture, dotted param path, resolver, tolerance in inches)
WALL_PARITY = [
    ("basementtoframedwalldetail", "wall/drywall_in", ("CATLIN_EXT_2X6", "gwb-int")),
    ("basementtoframedwalldetail", "wall/stud_depth_in", ("CATLIN_EXT_2X6", "stud")),
    ("basementtoframedwalldetail", "wall/sheathing_in", ("CATLIN_EXT_2X6", "sheathing")),
    ("basementtoframedwalldetail", "wall/polyiso_in", ("CATLIN_EXT_2X6", "spray-foam")),
    ("basementtoframedwalldetail", "wall/furring_in", ("CATLIN_EXT_2X6", "outer-girt")),
    # ``wall/eps_in`` (the reference's outer 2" CI course) has no layer to name any more.
    # Its replacement is spread across the catlin truss's three foam bands: 1-1/2" continuous
    # (``spray-foam``), 1-1/2" INSIDE the inner girt as a ``CavityFill`` so the engine
    # parallel-paths the wood through it, and 1" continuous again (``foam-vent``). A
    # CavityFill is not a Layer, so it cannot be resolved by name here; the total is asserted
    # by ``test_the_wall_still_carries_four_inches_of_exterior_insulation`` below, which is
    # the fact the reference was actually fixing.
    ("basementtoframedwalldetail", "wall/cladding_in", ("CATLIN_EXT_2X6", "cladding")),
    ("basementconstruction", "foundation/wall_thickness_in",
     ("CATLIN_BASEMENT_12", "concrete")),
    ("basementconstruction", "slab/slab_thickness_in", ("CATLIN_SLAB_FLOOR", "concrete")),
    ("basementconstruction", "slab/xps_under_in", ("CATLIN_SLAB_FLOOR", "xps-below")),
    # Sauna liner, per notes/sauna_basement_wall_detail.md + the shower detail's params.
    ("saunashowerdetail", "finish/tg_in", ("SAUNA_2X4", "shiplap-liner")),
    ("saunashowerdetail", "finish/furring_in", ("SAUNA_2X4", "liner-furring")),
    ("saunashowerdetail", "finish/polyiso_in", ("SAUNA_2X4", "foil-polyiso")),
    ("saunashowerdetail", "adjacent_wall/stud_depth_in", ("SAUNA_2X4", "stud")),
]


def _dig(data: dict, path: str):
    for part in path.split("/"):
        data = data[part]
    return data


@pytest.mark.parametrize("fixture,path,target", WALL_PARITY,
                         ids=[f"{f}:{p}" for f, p, _ in WALL_PARITY])
def test_layer_thickness_matches_the_reference(catlin_model, fixture, path, target):
    expected = float(_dig(_params(fixture), path))
    assembly_tag, layer_name = target
    actual = _layer(catlin_model.plan.library, assembly_tag, layer_name).thickness.inches

    if path in DECLARED_DIVERGENCES:
        assert abs(actual - expected) > 1e-6, (
            f"{path} now matches the reference — remove it from DECLARED_DIVERGENCES"
        )
        return
    assert actual == pytest.approx(expected, abs=1e-6), (
        f"{assembly_tag}/{layer_name} is {actual}\" but the reference fixes {expected}\""
    )


def test_basement_exterior_insulation_matches_the_reference(catlin_model):
    """Two staggered layers of XPS on the foundation, not one thick one — seams matter."""
    params = _params("basementtoframedwalldetail")["basement_exterior"]
    asm = catlin_model.plan.library.resolve_assembly("CATLIN_BASEMENT_12")
    xps = [ly for ly in asm.layers if ly.material_ref == "xps"]
    assert len(xps) == int(params["xps_layers"])
    for layer in xps:
        assert layer.thickness.inches == pytest.approx(float(params["xps_layer_in"]))


def test_basement_wall_layers_run_interior_to_exterior(catlin_model):
    # The XPS used to be the wall's outermost material, which meant bare foam was the finish
    # wherever the wall was not backfilled. A fifth layer closed that on 2026-08-01 (a
    # full-height parge), split in two on 2026-08-18, and came back to one on 2026-09-02:
    # the parge was retired house-wide, and the two south segments whose foam is genuinely
    # exposed took the same GRADE-banded protection panel N/E/W carry. It is last in the
    # stack because it is outboard of everything, and it is 1/2", the same as the parge, so
    # nothing moved (these walls align on face("concrete-ext")). The court walls carry no
    # fifth layer at all and are not perimeter-pour assemblies — see test_layer_extent.py.
    for tag, outermost in (("CATLIN_BASEMENT_12", "protection-panel"),
                           ("CATLIN_BASEMENT_8", "protection-panel")):
        asm = catlin_model.plan.library.resolve_assembly(tag)
        assert [layer.name for layer in asm.layers] == [
            "concrete", "damp-proof", "xps-a", "xps-b", outermost
        ]


def test_basement_exterior_xps_resolves_outboard_of_concrete(catlin_model):
    wall = next(w for w in catlin_model.walls if w.tag == "W-B-S1")
    average_y_by_layer = {
        layer.name: sum(point[1] for point in layer.polygon) / len(layer.polygon)
        for layer in wall.depth_layers()
    }
    # W-B-S1 faces south, so the exterior layer has the lower y coordinate.
    assert average_y_by_layer["xps-b"] < average_y_by_layer["concrete"]


def test_framing_matches_the_reference(catlin_model):
    params = _params("houseframing")
    joist_depth = float(params["floor_joists"]["depth_in"])
    # The freestanding structures frame with their own PT 2x8 deck joists, not the house's
    # I-joists: the sunken-garden porch/balcony decks and the breezeway between the house and
    # the garage. Check only the house floors against the reference.
    freestanding = ("FS-SG-", "FS-BW-")
    floors = [f for f in catlin_model.floors
              if f.members and not f.tag.startswith(freestanding)]
    assert floors, "catlin should resolve framed floors"
    for floor in floors:
        joists = [m for m in floor.members if m.category == "joist"]
        assert joists
        for member in joists:
            assert (member.z1_m - member.z0_m) * 39.37007874015748 == pytest.approx(
                joist_depth, abs=0.01)

    # ** THE PITCH DELIBERATELY NO LONGER MATCHES THE REFERENCE (2026-08-29). ** The old
    # model is 4:12 because the attic was designed around 5'-0" knee walls, which came from
    # a misreading of R305 (Minn. R. 1309.0305 Exception 1 and IRC R304.1/R304.3 scope the
    # sloped-ceiling rule to the REQUIRED floor area, not the whole room). With the knee
    # walls deleted the pitch is free, and 6:12 is the shallowest standard pitch that
    # carries the attic rooms. So this asserts the DIVERGENCE rather than deleting the
    # check: the reference's number is still read, and the house is held to being steeper
    # than it — a silent revert to 4:12 would fail here as loudly as drift ever did.
    roof = next(r for r in catlin_model.roofs if r.tag == "RF-HOUSE")
    reference_pitch = float(params["roof_joists"]["pitch_rise_over_run"])
    xs = [p[0] for p in roof.footprint]
    ys = [p[1] for p in roof.footprint]
    half_span = (max(ys) - min(ys) if roof.ridge_direction == "x"
                 else max(xs) - min(xs)) / 2.0
    rise_over_run = (roof.ridge_z_m - roof.eave_z_m) / half_span
    assert reference_pitch == pytest.approx(4.0 / 12.0, abs=0.005)
    assert rise_over_run == pytest.approx(6.0 / 12.0, abs=0.005)
    assert rise_over_run > reference_pitch


# Shares the house's FT-B- prefix but is not one of its strip footings, so the 20"x8" rule
# below does not govern it: FT-B-BRICK is the shallow plinth under the glazed-brick veneer
# (W-B-BRICK), cast on the house footing's toe over a 2" XPS bed rather than poured with it.
_NON_STRIP_FT_B = {"FT-B-BRICK"}


def test_house_footings_match_the_reference(catlin_model):
    """20\"x8\" footing per IRC Table R403.1, as the reference and the notes both fix it.

    Scoped to the house (``FT-B-*``): the freestanding sunken-garden structure carries its
    own heavier footing, which these basement params do not govern.
    """
    params = _params("basementconstruction")["foundation"]
    depth_in = float(params["footing_thickness_in"])
    footings = [s for s in catlin_model.solids
                if s.category == "footing" and s.tag.startswith("FT-B-")
                and s.tag not in _NON_STRIP_FT_B]
    assert footings, "catlin should resolve house footings"
    for footing in footings:
        assert (footing.z1_m - footing.z0_m) * 39.37007874015748 == pytest.approx(
            depth_in, abs=0.01), footing.tag


def test_house_footing_width_matches_the_reference(catlin_model):
    params = _params("basementconstruction")["foundation"]
    footings = [e for e in catlin_model.plan.elements_of_kind("Footing")
                if e.tag.startswith("FT-B-") and e.tag not in _NON_STRIP_FT_B]
    assert footings, "catlin should author house footings"
    for footing in footings:
        assert footing.width.inches == pytest.approx(
            float(params["footing_width_in"]), abs=1e-6), footing.tag


def test_footing_bedding_carries_the_reference_drainage_vocabulary(catlin_model):
    """The reference draws a geotextile-lined washed-stone bed with drain tile.

    TypeHaus records the bearing prep rather than drawing it, so this asserts the record
    exists and claims those parts — the drain's 4" diameter has nowhere to live on
    ``FootingBedding`` yet (tracked in plans/TODO.md).
    """
    # Every bedding that beds a *footing* on aggregate. Two kinds are excluded:
    # FB-B-BRICK, because the veneer plinth bears on a 2" XPS sheet laid on the house
    # footing's toe (see params/foundations.py) — no stone, no fabric, no tile, and it uses
    # this element only for ``cast_foam_in_aggregate``; and the FB-RG-* levelling pads under
    # the raised-garden apron, which host a dry-stacked wall rather than a footing and are
    # bearing prep with no drainage role (params/raised_garden.py).
    beddings = [e for e in catlin_model.plan.elements_of_kind("FootingBedding")
                if e.tag != "FB-B-BRICK" and not e.tag.startswith("FB-RG-")]
    assert beddings, "every house footing should carry a bearing-prep record"
    for bedding in beddings:
        assert bedding.geotextile
        assert bedding.drain_tile
        assert bedding.undercut.inches > 0


def _detail(catlin_model, key_prefix: str):
    from typehaus.emit.draw.details import build_detail, derive_detail_slices

    derived = next(d for d in derive_detail_slices(catlin_model)
                   if d.key.startswith(key_prefix))
    scene, _ = build_detail(catlin_model, derived)
    return derived, scene


def _component_tags(scene) -> set[str]:
    return {str(n.tag).split(":", 1)[1] for n in scene.nodes
            if str(getattr(n, "tag", "")).startswith("detail-component:")}


def test_below_grade_detail_draws_the_reference_context(catlin_model):
    """Vocabulary, not coordinates: a below-grade detail needs grade and soil drawn.

    The reference's basement detail sits in earth; without the grade line and the soil
    body the drawing gives no clue which side is outdoors.
    """
    _, scene = _detail(catlin_model, "wall_foundation:CATLIN_BASEMENT_12")
    assert {"grade-line", "soil"} <= _component_tags(scene)


def test_interior_foundation_walls_get_no_soil(catlin_model):
    """An interior basement bearing wall has slab on both sides — drawing earth would lie."""
    _, scene = _detail(catlin_model, "wall_foundation:CATLIN_INT_2X6_BRG|FOUNDATION_WALL_12_INT")
    assert not _component_tags(scene) & {"grade-line", "soil", "french-drain"}


def test_detail_components_stay_inside_their_crop(catlin_model):
    """A component that escapes the crop drags the sheet bounds and strands the drawing."""
    for prefix in ("wall_foundation:CATLIN_BASEMENT_12", "wall_roof:CATLIN_EXT_2X6"):
        derived, scene = _detail(catlin_model, prefix)
        (cu0, cz0), (cu1, cz1) = derived.view.crop[0].xy_m, derived.view.crop[1].xy_m
        to_in = 39.37007874015748
        for node in scene.nodes:
            if not str(getattr(node, "tag", "")).startswith("detail-component:"):
                continue
            for (u, z) in node.points:
                assert cu0 * to_in - 1 <= u <= cu1 * to_in + 1, (prefix, node.tag)
                assert cz0 * to_in - 1 <= z <= cz1 * to_in + 1, (prefix, node.tag)


def test_every_reference_fixture_is_reachable():
    """The fixtures are the dimensional source of truth — they must stay committed."""
    expected = {"basementconstruction", "basementplan", "basementtoframedwalldetail",
                "houseframing", "saunashowerdetail"}
    assert {p.stem for p in FIXTURES.glob("*.json")} >= expected


def test_the_wall_still_carries_four_inches_of_exterior_insulation(catlin_model):
    """The reference fixes 4" of CI outboard of the sheathing. The truss wall keeps it.

    The 2026-08-23 change replaced 2" polyiso + 2" EPS with 1-1/2" of closed-cell spray foam
    plus a 2-1/2" band of the same foam packed into the outrigger layer. Two of those three
    numbers are declared divergences above, and this is what stops the pair of them from
    quietly adding up to something else: the depth is the fact, the layer names are not.
    """
    assembly = catlin_model.plan.library.resolve_assembly("CATLIN_EXT_2X6")
    sheathing = next(index for index, layer in enumerate(assembly.layers)
                     if layer.name == "sheathing")
    insulation = 0.0
    for layer in assembly.layers[sheathing + 1:]:
        fill = layer.cavity
        if fill is not None:
            insulation += (fill.thickness or layer.thickness).inches
        elif layer.function.value == "insulation":
            insulation += layer.thickness.inches
    assert insulation == pytest.approx(4.0, abs=1e-6)

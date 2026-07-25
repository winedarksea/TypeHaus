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
    "slab/xps_under_in": (
        "reference 2\"; Catlin uses 3\" (R-15) at 40 psi under the slab — rated for slab "
        "loading rather than the lighter foundation-wall grade"
    ),
}


# (fixture, dotted param path, resolver, tolerance in inches)
WALL_PARITY = [
    ("basementtoframedwalldetail", "wall/drywall_in", ("CATLIN_EXT_2X6", "gwb-int")),
    ("basementtoframedwalldetail", "wall/stud_depth_in", ("CATLIN_EXT_2X6", "stud")),
    ("basementtoframedwalldetail", "wall/sheathing_in", ("CATLIN_EXT_2X6", "sheathing")),
    ("basementtoframedwalldetail", "wall/polyiso_in", ("CATLIN_EXT_2X6", "polyiso")),
    ("basementtoframedwalldetail", "wall/eps_in", ("CATLIN_EXT_2X6", "eps")),
    ("basementtoframedwalldetail", "wall/furring_in", ("CATLIN_EXT_2X6", "furring")),
    ("basementtoframedwalldetail", "wall/cladding_in", ("CATLIN_EXT_2X6", "cladding")),
    ("basementconstruction", "foundation/wall_thickness_in",
     ("CATLIN_BASEMENT_12", "concrete")),
    ("basementconstruction", "slab/slab_thickness_in", ("CATLIN_SLAB_FLOOR", "concrete")),
    ("basementconstruction", "slab/xps_under_in", ("CATLIN_SLAB_FLOOR", "xps-below")),
    # Sauna liner, per notes/sauna_basement_wall_detail.md + the shower detail's params.
    ("saunashowerdetail", "finish/tg_in", ("SAUNA_2X4", "tg-liner")),
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
    asm = catlin_model.plan.library.resolve_assembly("CATLIN_BASEMENT_12")
    assert [layer.name for layer in asm.layers] == [
        "concrete", "damp-proof", "xps-a", "xps-b"
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

    roof = next(r for r in catlin_model.roofs if r.tag == "RF-HOUSE")
    rise_over_run = float(params["roof_joists"]["pitch_rise_over_run"])
    xs = [p[0] for p in roof.footprint]
    ys = [p[1] for p in roof.footprint]
    half_span = (max(ys) - min(ys) if roof.ridge_direction == "x"
                 else max(xs) - min(xs)) / 2.0
    assert (roof.ridge_z_m - roof.eave_z_m) / half_span == pytest.approx(
        rise_over_run, abs=0.005)


def test_house_footings_match_the_reference(catlin_model):
    """20\"x8\" footing per IRC Table R403.1, as the reference and the notes both fix it.

    Scoped to the house (``FT-B-*``): the freestanding sunken-garden structure carries its
    own heavier footing, which these basement params do not govern.
    """
    params = _params("basementconstruction")["foundation"]
    depth_in = float(params["footing_thickness_in"])
    footings = [s for s in catlin_model.solids
                if s.category == "footing" and s.tag.startswith("FT-B-")]
    assert footings, "catlin should resolve house footings"
    for footing in footings:
        assert (footing.z1_m - footing.z0_m) * 39.37007874015748 == pytest.approx(
            depth_in, abs=0.01), footing.tag


def test_house_footing_width_matches_the_reference(catlin_model):
    params = _params("basementconstruction")["foundation"]
    footings = [e for e in catlin_model.plan.elements_of_kind("Footing")
                if e.tag.startswith("FT-B-")]
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
    beddings = [e for e in catlin_model.plan.elements_of_kind("FootingBedding")]
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
    _, scene = _detail(catlin_model, "wall_foundation:CATLIN_CONC_12_INT")
    assert not _component_tags(scene) & {"grade-line", "soil", "french-drain"}


def test_detail_components_stay_inside_their_crop(catlin_model):
    """A component that escapes the crop drags the sheet bounds and strands the drawing."""
    for prefix in ("wall_foundation:CATLIN_BASEMENT_12", "wall_roof:CATLIN_EXT_2X4"):
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

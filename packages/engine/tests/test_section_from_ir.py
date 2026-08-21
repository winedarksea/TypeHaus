"""The section cuts the geometry IR — what that buys, asserted rather than assumed."""

from __future__ import annotations

import pytest

from typehaus.emit.draw.scene import Hatch, Polyline
from typehaus.emit.draw.section import build_section
from typehaus.model.enums import SliceKind


def _slice(model, tag: str):
    return next(s for s in model.plan.elements_of_kind("Slice") if s.tag == tag)


def _tags(scene, layer: str) -> set[str]:
    return {node.tag for node in scene.nodes
            if isinstance(node, Polyline) and node.layer == layer and node.tag}


def test_every_slot_region_of_a_banded_wythe_draws(catlin_model):
    """A plinth, two bands and two fields are one 3 5/8" wythe — and five courses of brick.

    They share a ``Layer.slot``, so ``depth_layers()`` counts them once; building bodies
    from that list left the plinth standing with nothing above it.
    """
    scene = build_section(catlin_model, _slice(catlin_model, "SL-D-WALLTYP"))
    drawn = {tag.split("/")[-1] for tag in _tags(scene, "A-WALL")
             if tag.startswith("W-B-BRICK/")}
    assert {"brick-band-lo", "brick-field-lo", "brick-band-hi", "brick-field-hi"} <= drawn


def test_a_cut_layer_is_never_drawn_across_its_own_opening(catlin_model):
    """The IR jamb-splits into piers, sills and headers, so there is nothing to draw in the
    hole — and unlike the old split, it accounts for *every* opening in the wall rather than
    the first one the cut happens to meet."""
    view = _slice(catlin_model, "SL-D-WALLTYP")
    scene = build_section(catlin_model, view)
    voids = [node for node in scene.nodes
             if isinstance(node, Polyline) and node.layer == "A-GLAZ"]
    assert voids, "the wall-type cut passes no opening — pick another slice"
    for void in voids:
        (u0, z0), (_u1, z1) = void.points
        for node in scene.nodes:
            if not isinstance(node, Polyline) or node.layer != "A-WALL":
                continue
            if node.uid != void.uid:
                continue
            us = [u for (u, _z) in node.points]
            if not (min(us) - 1e-6 <= u0 <= max(us) + 1e-6):
                continue
            zs = [z for (_u, z) in node.points]
            overlap = min(max(zs), z1) - max(min(zs), z0)
            assert overlap < 1e-6, f"{node.tag} spans the opening at u={u0}"


def test_the_cavity_fill_still_draws_though_the_ir_omits_it(catlin_model):
    """``geometry_build`` skips cavity layers to avoid z-fighting the structure layer.

    For a section that omission is wrong — a batt between studs is what the drawing is cut
    to show — so the fill is drawn from the resolved layer, unoutlined.
    """
    scene = build_section(catlin_model, _slice(catlin_model, "SL-D-WALLTYP"))
    fills = [node for node in scene.nodes
             if isinstance(node, Hatch) and node.material == "mineral-wool"]
    assert fills, "no cavity fill in the wall-type section"
    assert not [tag for tag in _tags(scene, "A-WALL-INSU") if tag.endswith("-cavity")], \
        "a cavity fill drew an outline of its own"


def test_a_solid_hatches_as_what_it_is_made_of(catlin_model):
    """Every solid used to hatch as concrete — right for a footing, wrong for a deck."""
    view = next(s for s in catlin_model.plan.elements_of_kind("Slice")
                if s.kind is SliceKind.SECTION or s.kind is SliceKind.DETAIL)
    materials = set()
    for slice_view in catlin_model.plan.elements_of_kind("Slice"):
        scene = build_section(catlin_model, slice_view)
        materials |= {node.material for node in scene.nodes
                      if isinstance(node, Hatch) and node.material}
    assert view is not None
    assert len(materials - {"concrete"}) > 3, materials


def test_a_cut_across_a_void_does_not_draw_a_slab_through_it():
    """``GPrism.voids`` split the cut span; the old cut ignored them outright.

    Built rather than found: catlin's stair wells are cut by details whose crop excludes
    them, so a synthetic deck is what actually pins the behaviour.
    """
    from typehaus.resolve.geometry_ir import GPrism
    from typehaus.resolve.geometry_slice import CutPlane, slice_solid

    deck = GPrism(ring=((0.0, 0.0), (4.0, 0.0), (4.0, 3.0), (0.0, 3.0)), z0_m=0.0, z1_m=0.3,
                  voids=(((1.0, 1.0), (3.0, 1.0), (3.0, 2.0), (1.0, 2.0)),))
    profiles = slice_solid(deck, CutPlane(axis="x", station_m=1.5))
    spans = sorted((round(min(u for (u, _z) in p.outline), 6),
                    round(max(u for (u, _z) in p.outline), 6)) for p in profiles)
    assert spans == [(0.0, 1.0), (3.0, 4.0)]


@pytest.mark.parametrize("tag", ["SL-D-FNDN", "SL-D-WALLTYP"])
def test_a_cut_landing_on_an_end_face_still_shows_that_element(catlin_model, tag):
    """An authored detail is routinely cut exactly at the end of the wall it is about.

    The station is nudged *inward* off a coincident vertex for that reason: outward would
    silently drop the very element the drawing exists for.
    """
    scene = build_section(catlin_model, _slice(catlin_model, tag))
    assert _tags(scene, "A-WALL"), f"{tag} drew no wall at all"


# --- the roof ------------------------------------------------------------------------

def _roof_bands(scene, roof_tag: str) -> list[str]:
    return [node.tag.split("/", 1)[1] for node in scene.nodes
            if isinstance(node, Polyline) and node.layer == "A-ROOF"
            and node.tag and node.tag.startswith(f"{roof_tag}/")]


def test_the_roof_structure_is_drawn_once(catlin_model):
    """It used to be drawn twice: as an assembly band *and* as the rafters.

    ``roof_parts`` emits only the layers above the structure, which is the whole point —
    the structure is framing, and framing is drawn as members.
    """
    from typehaus.emit.draw.details import build_detail, derive_detail_slices
    from typehaus.resolve.roof_layer_setbacks import above_structure_layers

    derived = next(d for d in derive_detail_slices(catlin_model)
                   if d.key == "wall_roof:CATLIN_EXT_2X6|CATLIN_ROOF")
    scene, _findings = build_detail(catlin_model, derived)
    roof = next(r for r in catlin_model.roofs if r.tag == "RF-HOUSE")
    assembly = catlin_model.plan.library.resolve_assembly(roof.assembly)
    structure = [layer.name for layer in assembly.layers
                 if layer.function.value == "structure"]

    bands = _roof_bands(scene, "RF-HOUSE")
    assert bands, "the eave detail drew no roof at all"
    assert not [name for name in bands if name in structure], \
        f"A-ROOF band names the structure layer: {bands}"
    above = {layer.name for layer in above_structure_layers(assembly)}
    assert set(bands) <= above
    # The rafter is there — as a member.
    assert [node for node in scene.nodes
            if isinstance(node, Polyline) and node.layer == "S-FRAM"
            and node.tag and node.tag.startswith("rafter-")]


def test_a_plain_section_shows_the_roof_as_its_real_stack(catlin_model):
    """The coarse single band is gone: a building section reads the assembly it is cut
    through, and the band count is exactly the above-structure layer count."""
    from typehaus.emit.draw.section import build_center_section
    from typehaus.resolve.roof_layer_setbacks import above_structure_layers

    scene = build_center_section(catlin_model)
    roof = next(r for r in catlin_model.roofs if r.tag == "RF-HOUSE")
    assembly = catlin_model.plan.library.resolve_assembly(roof.assembly)
    assert sorted(_roof_bands(scene, "RF-HOUSE")) == \
        sorted(layer.name for layer in above_structure_layers(assembly))


def test_the_bay_fill_still_draws_under_the_rafters(catlin_model):
    """The batt shares the bay's depth, so the IR gives it no solid — and a roof that reads
    as 11-7/8" of solid timber is not what the section is cut to show."""
    from typehaus.emit.draw.details import build_detail, derive_detail_slices

    derived = next(d for d in derive_detail_slices(catlin_model)
                   if d.key == "wall_roof:CATLIN_EXT_2X6|CATLIN_ROOF")
    scene, _findings = build_detail(catlin_model, derived)
    assert [node for node in scene.nodes
            if isinstance(node, Hatch) and node.material == "fiberglass-r19"]


def test_a_roof_off_the_sheet_does_not_label_its_layers(catlin_model):
    """Half the derived details are cut at a wall a long way from any roof."""
    from typehaus.emit.draw.details import build_detail, derive_detail_slices
    from typehaus.emit.draw.scene import Leader

    derived = next(d for d in derive_detail_slices(catlin_model)
                   if d.key == "opening_perimeter:GARAGE_WALL_2X6")
    scene, _findings = build_detail(catlin_model, derived)
    assert not _roof_bands(scene, "RF-GARAGE")
    roof = next(r for r in catlin_model.roofs if r.tag == "RF-GARAGE")
    assembly = catlin_model.plan.library.resolve_assembly(roof.assembly)
    names = {layer.name for layer in assembly.layers}
    labelled = {node.text.split(" ")[0] for node in scene.nodes
                if isinstance(node, Leader)}
    assert not (labelled & names), labelled & names

"""Cavity insulation lives inside its host STRUCTURE layer, not beside it.

A batt between studs shares the framing depth and the framing polygon. Modelling it as a
sibling ``Layer`` (the pre-CavityFill spelling) double-counted the wall depth, overlapped
the outboard layers' polygons, summed R in series instead of parallel, and exported an
``IfcMaterialLayerSet`` thicker than the wall — which is what Revit/SketchUp read on import.
"""

from __future__ import annotations

import pytest

from typehaus.analysis import assembly_r_value
from typehaus.model.assembly import Assembly, CavityFill, FramingSpec, Layer
from typehaus.model.enums import LayerFunction
from typehaus.quantities import inch


def _layer(wall, name):
    return next(ly for ly in wall.layers if ly.name == name)


def _span(layer):
    """The layer's extent across the wall depth, in the polygon's cross-axis."""
    ys = [p[1] for p in layer.polygon]
    xs = [p[0] for p in layer.polygon]
    # the wall runs along whichever axis varies more; depth is the other one
    return (min(ys), max(ys)) if (max(xs) - min(xs)) > (max(ys) - min(ys)) else (min(xs), max(xs))


def test_cavity_shares_its_host_polygon_and_adds_no_depth(catlin_model):
    wall = catlin_model.wall("W-M-S1")
    stud, cavity = _layer(wall, "stud"), _layer(wall, "stud-cavity")

    assert cavity.is_cavity and cavity.cavity_host == "stud"
    assert not stud.is_cavity
    assert _span(cavity) == pytest.approx(_span(stud), abs=1e-9)

    # depth counts every layer once; the cavity rides inside the studs
    depth = sum(ly.thickness_m for ly in wall.depth_layers())
    assert wall.thickness_m == pytest.approx(depth)
    # 0.01 paint + 0.625 gwb + 5.5 stud + 0.5 sheathing + 1.5 spray foam + 1.5 inner girt
    # + 1.0 band-C foam + 0.5 vent gap + 1.5 outer girt + 1.25 PBR panel. The paint film
    # is the interior lining's Class III vapour retarder (IRC R702.7), so it is a layer with
    # a thickness, not a colour note.
    #
    # 11.655" until the Swinburne truss (2026-08-23), when the WRB + 2" polyiso + 2" EPS +
    # 1/2" furring became 1-1/2" of spray foam and a 3-1/2" on-edge outrigger band: 12.135".
    # 13.135" after the catlin truss (2026-08-26) laid four 1-1/2"-and-under layers where
    # that band was — that change was one inch of wall, and this is where it showed.
    # **13.885" since the exposed-fastener swap** later the same day: the cladding layer went
    # from a 1/2" snap-lock pan to a 1-1/4" PBR panel, whose declared thickness is the RIB
    # height and not the sheet's. Nothing inboard of it moved; the whole 3/4" is the skin.
    #
    # The INNER GIRT's own 1-1/2" of foam is a CavityFill and adds no depth, which is exactly
    # what this test is for, one layer further out than it used to reach. Note the outer girt
    # carries no fill at all: nothing vents inside a solid KDAT band, and its gap is the
    # AIRGAP layer behind it.
    assert wall.thickness_m * 39.3701 == pytest.approx(13.885, abs=0.01)


def test_no_wall_layer_overlaps_another(catlin_model):
    """The bug class the sibling-batt spelling produced: two layers claiming one strip."""
    for wall in catlin_model.walls:
        spans = [(ly.name, _span(ly)) for ly in wall.depth_layers() if len(ly.polygon) >= 3]
        spans.sort(key=lambda item: item[1][0])
        for (name_a, (_a0, a1)), (name_b, (b0, _b1)) in zip(spans, spans[1:]):
            assert a1 <= b0 + 1e-6, (
                f"{wall.tag}: layer {name_a} overlaps {name_b} across the wall depth"
            )


def test_cavity_r_value_is_parallel_path_not_series(catlin_model):
    """Framing and fill are two paths through one depth — summing both overstates the wall."""
    library = catlin_model.plan.library
    asm = library.resolve_assembly("CATLIN_EXT_2X6")
    stud = next(ly for ly in asm.layers if ly.name == "stud")
    assert stud.cavity is not None

    parallel = assembly_r_value(asm, library)
    assert parallel.known

    series = asm.model_copy(update={"layers": tuple(
        ly.model_copy(update={"cavity": None}) if ly.name == "stud" else ly
        for ly in asm.layers
    ) + (Layer(name="batt", material_ref=stud.cavity.material_ref,
               thickness=stud.thickness, function=LayerFunction.INSULATION),)})
    assert assembly_r_value(series, library).value.r_us > parallel.value.r_us


def test_shallower_fill_only_counts_its_own_thickness():
    """An R-13 batt in a 2x6 bay is not an R-19 bay — the rest is still air, not credit."""
    from typehaus.model.plan import Library
    from typehaus.model.materials import Material

    library = Library(materials=(
        Material(tag="spf", name="SPF", r_per_inch=1.25),
        Material(tag="wool", name="Mineral wool", r_per_inch=4.2),
    ))
    deep = Assembly(tag="DEEP", layers=(
        Layer(name="stud", material_ref="spf", thickness=inch(5.5),
              function=LayerFunction.STRUCTURE, framing=FramingSpec(member="2x6"),
              cavity=CavityFill(material_ref="wool")),
    ))
    shallow = deep.model_copy(update={"layers": (
        deep.layers[0].model_copy(update={
            "cavity": CavityFill(material_ref="wool", thickness=inch(3.5))}),
    )})
    assert assembly_r_value(shallow, library).value.r_us < \
        assembly_r_value(deep, library).value.r_us


def test_ifc_material_layer_set_sums_to_the_wall_thickness(catlin_model, tmp_path):
    ifcopenshell = pytest.importorskip("ifcopenshell")
    from typehaus.emit.ifc import emit_ifc

    path = emit_ifc(catlin_model, tmp_path / "cavity.ifc")
    f = ifcopenshell.open(str(path))
    walls = {w.Name: w for w in f.by_type("IfcWall")}
    assert "W-M-S1" in walls

    usages = [
        rel.RelatingMaterial for rel in f.by_type("IfcRelAssociatesMaterial")
        if walls["W-M-S1"] in rel.RelatedObjects
        and rel.RelatingMaterial.is_a("IfcMaterialLayerSetUsage")
    ]
    assert usages, "wall should carry an IfcMaterialLayerSetUsage for Revit import"
    layer_set = usages[0].ForLayerSet
    total = sum(ly.LayerThickness for ly in layer_set.MaterialLayers)
    assert total == pytest.approx(catlin_model.wall("W-M-S1").thickness_m, abs=1e-6)
    # the batt is not a layer — it rides as a property set instead
    assert "mineral-wool" not in [
        ly.Material.Name for ly in layer_set.MaterialLayers
    ]
    assert usages[0].LayerSetDirection == "AXIS2"
    assert usages[0].DirectionSense == "POSITIVE"

    wall_type = next(iter(walls["W-M-S1"].IsTypedBy)).RelatingType
    assert wall_type.is_a("IfcWallType")
    body = next(rep for rep in walls["W-M-S1"].Representation.Representations
                if rep.RepresentationIdentifier == "Body")
    axis = next(rep for rep in walls["W-M-S1"].Representation.Representations
                if rep.RepresentationIdentifier == "Axis")
    # The *unbanded* body: ``_emit_wall`` extrudes the full-height layers and re-emits every
    # banded one as an ``IfcBuildingElementPart`` instead, so this count is depth_layers()
    # only while no layer of this wall is banded. Stated rather than assumed — the emitter
    # now walks ``body_layers()`` for the parts, and the two lists differ on a wall with a
    # ``Layer.slot`` (→ test_emitter_band_parity.py).
    wall_ir = catlin_model.wall("W-M-S1")
    assert not any(layer.is_banded for layer in wall_ir.layers), \
        "W-M-S1 gained a banded layer; this assertion is about the unbanded body"
    assert len(body.Items) == len(wall_ir.depth_layers())
    assert len(axis.Items) == 1

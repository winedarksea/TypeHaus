"""IFC roof geometry: the faceted layer shell and its members (→ roof-eave follow-ups).

Two long-standing gaps this pins down, both of which made the IFC export disagree with
every other view of the same building:

* the ``IfcRoof`` was a flat 1" plate extruded at the eave elevation, ignoring both the
  pitch and ``ResolvedRoof.layer_edge_setbacks``;
* its members were bare ``IfcMember`` identities with no representation at all.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from typehaus.emit.ifc import emit_ifc
from typehaus.resolve.roof_layer_setbacks import above_structure_layers

pytest.importorskip("ifcopenshell")

_ROOF_TAG = "RF-HOUSE"


@pytest.fixture(scope="module")
def catlin_roof_ifc(catlin_model, tmp_path_factory) -> Path:
    out = tmp_path_factory.mktemp("ifc-roof") / "catlin.ifc"
    emit_ifc(catlin_model, out, lod="framed")
    return out


@pytest.fixture(scope="module")
def ifc_file(catlin_roof_ifc):
    import ifcopenshell

    return ifcopenshell.open(str(catlin_roof_ifc))


def _roof_product(ifc_file, tag: str = _ROOF_TAG):
    return next(item for item in ifc_file.by_type("IfcRoof") if item.Name == tag)


def _brep_solids(product) -> list:
    return [item for representation in product.Representation.Representations
            for item in representation.Items if item.is_a("IfcFacetedBrep")]


def _solid_points(solid) -> list[tuple[float, float, float]]:
    return [tuple(point.Coordinates)
            for face in solid.Outer.CfsFaces
            for bound in face.Bounds
            for point in bound.Bound.Polygon]


def _children(ifc_file, product) -> dict:
    """Aggregated children by child key. IfcOpenShell does not preserve the order they were
    assigned in, so every lookup here is by key rather than by position."""
    return {child.Name.split("/", 1)[1]: child
            for relation in ifc_file.by_type("IfcRelAggregates")
            if relation.RelatingObject == product for child in relation.RelatedObjects}


# --- the shell -----------------------------------------------------------------------------

def test_the_roof_is_a_pitched_layer_stack_not_a_flat_plate(catlin_model, ifc_file):
    """One closed polyhedron per above-structure layer, spanning the pitch.

    It used to be one per (layer x roof plane): the shell was built plane by plane with
    vertical sides, so the two halves of a gable met at a vertical joint. The IR mitres the
    ridge instead — one band crosses it — which is why the count is now per layer.
    """
    roof = next(item for item in catlin_model.roofs if item.tag == _ROOF_TAG)
    assembly = catlin_model.plan.library.resolve_assembly(roof.assembly)
    layers = above_structure_layers(assembly)
    assert len(layers) > 1  # the catlin roof is a real build-up, not a single skin
    solids = _brep_solids(_roof_product(ifc_file))
    assert len(solids) == len(layers)
    zs = [point[2] for solid in solids for point in _solid_points(solid)]
    # The old flat plate was a 1" prism at the eave; this one climbs the whole pitch and
    # finishes above the ridge, because the stack sits on top of the plane.
    assert min(zs) >= roof.eave_z_m - 1e-6
    assert max(zs) > roof.ridge_z_m
    assert max(zs) - min(zs) > (roof.ridge_z_m - roof.eave_z_m) * 0.9


def test_each_layer_clips_at_its_own_serialized_plan_setback(catlin_model, ifc_file):
    """The clip faces the glTF export and the viewer honor, which IFC used to ignore.

    A band's edge is no longer a vertical face at the authored plan position: the layer is
    offset perpendicular to the slope, so its *bottom* lands on the setback and its top
    drifts down-slope by the layer's own thickness x sin(theta). That is the blessed change
    — IFC used to build vertical sides here and disagree with both other views of the roof —
    so the clip is checked as the band between those two, with the bottom edge exact.
    """
    roof = next(item for item in catlin_model.roofs if item.tag == _ROOF_TAG)
    setbacks = {entry["layer"]: entry for entry in roof.layer_edge_setbacks}
    assert setbacks, "the catlin house roof serializes per-layer setbacks"
    assembly = catlin_model.plan.library.resolve_assembly(roof.assembly)
    layers = above_structure_layers(assembly)
    west_edge = min(point[0] for point in roof.footprint)
    solids = _brep_solids(_roof_product(ifc_file))
    for index, layer in enumerate(layers):
        entry = setbacks.get(layer.name)
        if entry is None:
            continue
        clip = west_edge + float(entry["west"])
        got = min(point[0] for point in _solid_points(solids[index]))
        # West is an eave edge on this ridge-along-y gable. The band's *bottom* lands on the
        # authored clip — that is what the drift compensation buys — and only its top hangs
        # proud, by this layer's own thickness x sin(theta), which is under its thickness.
        assert clip - layer.thickness.meters - 1e-6 <= got <= clip + 1e-6, layer.name
    # And the setbacks genuinely differ: the metal roofing runs proud of the deck's clip.
    assert setbacks[layers[0].name]["west"] > setbacks[layers[-1].name]["west"]


# --- the members ---------------------------------------------------------------------------

def test_every_roof_member_carries_a_swept_solid(catlin_model, ifc_file):
    """They used to aggregate as identities with no geometry — invisible in any viewer."""
    roof = next(item for item in catlin_model.roofs if item.tag == _ROOF_TAG)
    children = _children(ifc_file, _roof_product(ifc_file))
    assert len(children) == len(roof.members) > 0
    without_geometry = [key for key, child in children.items()
                        if child.Representation is None]
    assert without_geometry == []
    items = [item for child in children.values()
             for representation in child.Representation.Representations
             for item in representation.Items]
    # A constant-section member is a real sweep; a closure band that grows from the heel to
    # the ridge is not, and is faceted rather than stretched to a wrong constant depth.
    swept = [item for item in items if item.is_a("IfcExtrudedAreaSolid")]
    faceted = [item for item in items if item.is_a("IfcFacetedBrep")]
    assert len(swept) + len(faceted) == len(items)
    assert swept and all(item.Depth > 0.0 for item in swept)


def test_a_raked_member_sweeps_along_its_own_axis(ifc_file):
    """A rafter is a section on a sloped line, not a bounding prism: its extrusion axis has
    to leave the vertical, or the export cannot express a pitched member at all."""
    rafter = _children(ifc_file, _roof_product(ifc_file))["rafter-000"]
    solid = rafter.Representation.Representations[0].Items[0]
    axis = solid.Position.Axis.DirectionRatios
    assert 1e-6 < abs(axis[2]) < 1.0 - 1e-6
    # The catlin roof is 4:12, so the axis climbs one in three of its horizontal run.
    assert abs(axis[2]) / (axis[0] ** 2 + axis[1] ** 2) ** 0.5 == pytest.approx(4 / 12, abs=1e-6)


def test_members_land_in_the_ifc_class_their_trade_calls_for(ifc_file):
    """Sticks are IfcMember, the skin and trim they carry are IfcCovering finishes."""
    children = _children(ifc_file, _roof_product(ifc_file))
    rafter = children["rafter-000"]
    assert (rafter.is_a(), rafter.PredefinedType) == ("IfcMember", "RAFTER")
    # The house eave has no fascia (continuous standing-seam skin + corner trim), so the
    # garage roof carries the derived fascia boards now.
    fascia = _children(ifc_file, _roof_product(ifc_file, "RF-GARAGE"))["eave-lo-fascia-0"]
    assert (fascia.is_a(), fascia.PredefinedType) == ("IfcCovering", "MOLDING")


# --- the garage gutter ---------------------------------------------------------------------

def test_the_garage_south_eave_carries_a_derived_gutter(catlin_model):
    """Deferred with the truss roof; derived now, so the raised-heel lift carries it.

    The channel is an open-top U of three thin bands (back/bottom/front), not a solid bar.
    """
    roof = next(item for item in catlin_model.roofs if item.tag == "RF-GARAGE")
    gutters = [member for member in roof.members if member.category == "gutter"]
    assert [member.child_key for member in gutters] == [
        "eave-lo-gutter-back", "eave-lo-gutter-bottom", "eave-lo-gutter-front"]
    for gutter in gutters:
        # The ridge runs E-W, so "eave-lo" is the south edge — facing the breezeway.
        assert min(gutter.p0[1], gutter.p1[1]) < min(point[1] for point in roof.footprint) + 0.2
        # Hung off the plane, so it stays under the eave the heel lift raised.
        assert gutter.z1_m < roof.eave_z_m
        assert gutter.z1_m > roof.eave_z_m - 0.2


def test_the_garage_gutter_reaches_the_ifc_export(catlin_model, ifc_file):
    children = _children(ifc_file, _roof_product(ifc_file, "RF-GARAGE"))
    for band in ("back", "bottom", "front"):
        gutter = children[f"eave-lo-gutter-{band}"]
        assert gutter.is_a("IfcBuildingElementProxy")
        assert gutter.Representation is not None

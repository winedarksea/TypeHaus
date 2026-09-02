"""IFC roof geometry: the faceted layer shell and its members (→ roof-eave follow-ups).

Two long-standing gaps this pins down, both of which made the IFC export disagree with
every other view of the same building:

* the ``IfcRoof`` was a flat 1" plate extruded at the eave elevation, ignoring both the
  pitch and ``ResolvedRoof.layer_edge_setbacks``;
* its members were bare ``IfcMember`` identities with no representation at all.
"""

from __future__ import annotations

import pytest

from typehaus.resolve.roof_layer_setbacks import above_structure_layers

pytest.importorskip("ifcopenshell")

_ROOF_TAG = "RF-HOUSE"


@pytest.fixture(scope="module")
def ifc_file(catlin_ifc_path):
    import ifcopenshell

    return ifcopenshell.open(str(catlin_ifc_path))


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

def test_the_roof_is_a_pitched_layer_stack_not_a_flat_plate(catlin_model_ro, ifc_file):
    """One closed polyhedron per above-structure layer, spanning the pitch.

    The IR mitres the ridge — one band crosses it, not one shell per (layer x roof plane)
    with a vertical joint where the two halves of a gable meet.
    """
    roof = next(item for item in catlin_model_ro.roofs if item.tag == _ROOF_TAG)
    assembly = catlin_model_ro.plan.library.resolve_assembly(roof.assembly)
    layers = above_structure_layers(assembly)
    assert len(layers) > 1  # the catlin roof is a real build-up, not a single skin
    solids = _brep_solids(_roof_product(ifc_file))
    assert len(solids) == len(layers)
    zs = [point[2] for solid in solids for point in _solid_points(solid)]
    # Climbs the whole pitch and finishes above the ridge, because the stack sits on top
    # of the plane — not a flat 1" prism at the eave.
    assert min(zs) >= roof.eave_z_m - 1e-6
    assert max(zs) > roof.ridge_z_m
    assert max(zs) - min(zs) > (roof.ridge_z_m - roof.eave_z_m) * 0.9


def test_each_layer_clips_at_its_own_serialized_plan_setback(catlin_model_ro, ifc_file):
    """The clip faces the glTF export and the viewer honor.

    A band's edge is not a vertical face at the authored plan position: the layer is
    offset perpendicular to the slope, so its *bottom* lands on the setback and its top
    drifts down-slope by the layer's own thickness x sin(theta). So the clip is checked as
    the band between those two, with the bottom edge exact.
    """
    roof = next(item for item in catlin_model_ro.roofs if item.tag == _ROOF_TAG)
    setbacks = {entry["layer"]: entry for entry in roof.layer_edge_setbacks}
    assert setbacks, "the catlin house roof serializes per-layer setbacks"
    assembly = catlin_model_ro.plan.library.resolve_assembly(roof.assembly)
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

def test_every_roof_member_carries_a_swept_solid(catlin_model_ro, ifc_file):
    """A member with no geometry aggregates as an identity — invisible in any viewer."""
    roof = next(item for item in catlin_model_ro.roofs if item.tag == _ROOF_TAG)
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


def test_a_birdsmouthed_rafter_exports_its_notch(ifc_file):
    """A notched rafter is a *shaped* profile swept across its own width.

    ``IfcExtrudedAreaSolid`` over an ``IfcArbitraryClosedProfileDef`` is the entity IFC has
    for exactly this, so the notch survives the export instead of being flattened back into a
    bounding section on a sloped axis. The profile stands in a vertical plane — which is why
    the extrusion axis is horizontal here and not up the roof's pitch.
    """
    rafter = _children(ifc_file, _roof_product(ifc_file))["rafter-000"]
    solid = rafter.Representation.Representations[0].Items[0]
    assert solid.is_a("IfcExtrudedAreaSolid")
    assert solid.SweptArea.is_a("IfcArbitraryClosedProfileDef")
    points = solid.SweptArea.OuterCurve.Points
    # Six distinct corners (the polyline repeats the first to close): end-top, far-top,
    # far-bottom, the plumb heel's head, its foot, and the seat's outboard end.
    assert len(points) == 7
    assert points[0].Coordinates == points[-1].Coordinates
    axis = solid.Position.Axis.DirectionRatios
    assert abs(axis[2]) < 1e-9, "the profile plane is vertical, so its normal is horizontal"
    assert solid.Depth > 0.0

    # The seat is flat: two profile corners share the lowest elevation, one seat run apart.
    heights = sorted(point.Coordinates[1] for point in points[:-1])
    assert heights[0] == pytest.approx(heights[1], abs=1e-9)


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

def test_the_garage_south_eave_carries_a_derived_gutter(catlin_model_ro):
    """Deferred with the truss roof; derived now, so the raised-heel lift carries it.

    The channel is an open-top U of three thin bands (back/bottom/front), not a solid bar.
    """
    roof = next(item for item in catlin_model_ro.roofs if item.tag == "RF-GARAGE")
    gutters = [member for member in roof.members if member.category == "gutter"]
    assert [member.child_key for member in gutters] == [
        "eave-lo-gutter-back", "eave-lo-gutter-bottom", "eave-lo-gutter-front"]
    for gutter in gutters:
        # The ridge runs E-W, so "eave-lo" is the south edge — facing the breezeway.
        assert min(gutter.p0[1], gutter.p1[1]) < min(point[1] for point in roof.footprint) + 0.2
        # Hung off the plane, so it stays under the eave the heel lift raised.
        assert gutter.z1_m < roof.eave_z_m
        assert gutter.z1_m > roof.eave_z_m - 0.2


def test_the_garage_gutter_reaches_the_ifc_export(catlin_model_ro, ifc_file):
    children = _children(ifc_file, _roof_product(ifc_file, "RF-GARAGE"))
    for band in ("back", "bottom", "front"):
        gutter = children[f"eave-lo-gutter-{band}"]
        assert gutter.is_a("IfcBuildingElementProxy")
        assert gutter.Representation is not None

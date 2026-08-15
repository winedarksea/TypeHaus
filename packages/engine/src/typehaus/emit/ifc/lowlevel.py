"""Typed low-level IfcOpenShell 0.8 adapter (ported from ifcplot/ifc_utils.py, → 12).

Risk 5 mitigation: *all* IfcOpenShell calls are confined to this ~one-file adapter, so a
0.8→0.9 reshape touches one place and golden IFC snapshots detect drift. Length unit is
standardized to meters project-wide and scaling is centralized here (avoiding the
mm-units gotcha documented at ifc_utils.py:395-406).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from typehaus.resolve.geometry_prims import arch_soffit_circle

if TYPE_CHECKING:
    import ifcopenshell


def require_ifcopenshell() -> Any:
    """Import ifcopenshell lazily with a clear message if the pinned dep is absent."""
    try:
        import ifcopenshell  # noqa: F401

        return ifcopenshell
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise RuntimeError(
            "ifcopenshell (pin 0.8.x) is required for IFC emission. "
            "Install it into the engine environment (conda/prebuilt wheel)."
        ) from exc


def new_file(app_name: str) -> Any:
    """Create an IFC4 file with a project + pinned OwnerHistory (deterministic)."""
    ios = require_ifcopenshell()
    import ifcopenshell.api

    f = ios.file(schema="IFC4")
    # Pin OwnerHistory / timestamps for byte-determinism (SOURCE_DATE_EPOCH style).
    ifcopenshell.api.run("owner.add_person", f, identification="typehaus")
    ifcopenshell.api.run("owner.add_organisation", f, identification=app_name)
    return f


def add_context(f: Any) -> Any:
    import ifcopenshell.api

    ctx = ifcopenshell.api.run("context.add_context", f, context_type="Model")
    body = ifcopenshell.api.run(
        "context.add_context", f, context_type="Model",
        context_identifier="Body", target_view="MODEL_VIEW", parent=ctx,
    )
    return body


def create_entity(f: Any, ifc_class: str, **kwargs: Any) -> Any:
    import ifcopenshell.api

    return ifcopenshell.api.run("root.create_entity", f, ifc_class=ifc_class, **kwargs)


def add_prism_from_profile(f: Any, body_ctx: Any, points_m: list[tuple[float, float]],
                           height_m: float, z0_m: float = 0.0,
                           voids_m: tuple[tuple[tuple[float, float], ...], ...] = ()) -> Any:
    """Extrude a closed polygon profile to a solid (ported add_prism_from_profile)."""
    pts = [f.createIfcCartesianPoint((x, y)) for (x, y) in points_m]
    polyline = f.createIfcPolyline(pts + [pts[0]])
    if voids_m:
        inners = []
        for void in voids_m:
            inner_points = [f.createIfcCartesianPoint((x, y)) for (x, y) in void]
            inners.append(f.createIfcPolyline(inner_points + [inner_points[0]]))
        profile = f.createIfcArbitraryProfileDefWithVoids("AREA", None, polyline, inners)
    else:
        profile = f.createIfcArbitraryClosedProfileDef("AREA", None, polyline)
    origin = f.createIfcCartesianPoint((0.0, 0.0, z0_m))
    placement = f.createIfcAxis2Placement3D(origin, None, None)
    direction = f.createIfcDirection((0.0, 0.0, 1.0))
    solid = f.createIfcExtrudedAreaSolid(profile, placement, direction, height_m)
    return f.createIfcShapeRepresentation(body_ctx, "Body", "SweptSolid", [solid])


def add_arched_opening_prism(f: Any, body_ctx: Any, *, center_m: tuple[float, float],
                             wall_direction: tuple[float, float], wall_thickness_m: float,
                             width_m: float, height_m: float, arch_rise_m: float,
                             z0_m: float) -> Any:
    """Extrude a rectangular-jamb, circular-head opening through a wall.

    The head is the circular *segment* through both springlines and the crown, so a shallow
    ``arch_rise_m`` gives a segmental arch and ``arch_rise_m == width / 2`` gives the
    semicircle this used to assume unconditionally. That assumption made the void taller than
    the opening it voided whenever the rise was smaller — the head went to springline + width/2
    however low the crown was authored — which showed up as an IFC self-diff "move".

    The profile lies in the opening's vertical plane: its local x-axis follows the wall and
    its local y-axis is vertical.  The swept local z-axis points through the wall, avoiding
    the horizontal footprint extrusion used for ordinary rectangular openings.
    """
    ux, uy = wall_direction
    direction_length = (ux * ux + uy * uy) ** 0.5 or 1.0
    ux, uy = ux / direction_length, uy / direction_length
    # Choosing the right-hand wall normal makes local y = local z × local x point upward.
    normal = (uy, -ux)
    half_width = width_m / 2.0
    springline = max(0.0, height_m - arch_rise_m)
    # Same circle the resolver and both renderers use, so the void matches the hole.
    radius, _half_angle, depth = arch_soffit_circle(half_width, arch_rise_m)
    left_bottom = f.createIfcCartesianPoint((-half_width, 0.0))
    right_bottom = f.createIfcCartesianPoint((half_width, 0.0))
    right_spring = f.createIfcCartesianPoint((half_width, springline))
    left_spring = f.createIfcCartesianPoint((-half_width, springline))
    bottom = f.createIfcPolyline((left_bottom, right_bottom))
    right_jamb = f.createIfcPolyline((right_bottom, right_spring))
    circle = f.createIfcCircle(
        f.createIfcAxis2Placement2D(
            f.createIfcCartesianPoint((0.0, springline - depth)), None), radius,
    )
    arch = f.createIfcTrimmedCurve(circle, (right_spring,), (left_spring,), True, "CARTESIAN")
    left_jamb = f.createIfcPolyline((left_spring, left_bottom))
    outer_curve = f.createIfcCompositeCurve([
        f.createIfcCompositeCurveSegment("CONTINUOUS", True, bottom),
        f.createIfcCompositeCurveSegment("CONTINUOUS", True, right_jamb),
        f.createIfcCompositeCurveSegment("CONTINUOUS", True, arch),
        f.createIfcCompositeCurveSegment("CONTINUOUS", True, left_jamb),
    ], False)
    profile = f.createIfcArbitraryClosedProfileDef("AREA", None, outer_curve)
    placement = f.createIfcAxis2Placement3D(
        # Swept solids extrude from their placement plane in one direction; offset the
        # plane by half the wall depth so the resulting void stays centered on the wall axis.
        f.createIfcCartesianPoint((center_m[0] - normal[0] * wall_thickness_m / 2.0,
                                   center_m[1] - normal[1] * wall_thickness_m / 2.0, z0_m)),
        f.createIfcDirection((normal[0], normal[1], 0.0)),
        f.createIfcDirection((ux, uy, 0.0)),
    )
    solid = f.createIfcExtrudedAreaSolid(
        profile, placement, f.createIfcDirection((0.0, 0.0, 1.0)), wall_thickness_m,
    )
    return f.createIfcShapeRepresentation(body_ctx, "Body", "SweptSolid", [solid])


def add_prisms_from_profiles(f: Any, body_ctx: Any,
                             profiles_m: list[list[tuple[float, float]]],
                             height_m: float, z0_m: float = 0.0) -> Any:
    """One Body representation containing the resolved non-overlapping layer solids."""
    solids = []
    for profile_points in profiles_m:
        if len(profile_points) < 3:
            continue
        points = [f.createIfcCartesianPoint(point) for point in profile_points]
        curve = f.createIfcPolyline(points + [points[0]])
        profile = f.createIfcArbitraryClosedProfileDef("AREA", None, curve)
        placement = f.createIfcAxis2Placement3D(
            f.createIfcCartesianPoint((0.0, 0.0, z0_m)), None, None
        )
        solids.append(f.createIfcExtrudedAreaSolid(
            profile, placement, f.createIfcDirection((0.0, 0.0, 1.0)), height_m
        ))
    return f.createIfcShapeRepresentation(body_ctx, "Body", "SweptSolid", solids)


Vec3 = tuple[float, float, float]


def add_faceted_solids(f: Any, body_ctx: Any, shells_m: list[list[list[Vec3]]]) -> Any:
    """One Body representation holding closed polyhedra (``IfcFacetedBrep``).

    Each shell is a list of planar faces, each face an outer loop of 3D points in the shared
    project frame, wound counter-clockwise seen from outside. This is the representation for
    a form that is genuinely faceted rather than a sweep — a pitched roof layer, whose top and
    bottom are parallel sloped planes and whose sides are vertical, is exactly that: an
    extrusion would have to be oblique, which importers read inconsistently.
    """
    cache: dict[tuple[float, float, float], Any] = {}

    def point(value: Vec3) -> Any:
        key = (round(value[0], 9), round(value[1], 9), round(value[2], 9))
        if key not in cache:
            cache[key] = f.createIfcCartesianPoint(key)
        return cache[key]

    solids = []
    for shell in shells_m:
        faces = []
        for loop_points in shell:
            if len(loop_points) < 3:
                continue
            loop = f.createIfcPolyLoop([point(value) for value in loop_points])
            faces.append(f.createIfcFace([f.createIfcFaceOuterBound(loop, True)]))
        if faces:
            solids.append(f.createIfcFacetedBrep(f.createIfcClosedShell(faces)))
    return f.createIfcShapeRepresentation(body_ctx, "Body", "Brep", solids)


def add_swept_member(f: Any, body_ctx: Any, *, origin_m: Vec3, axis: Vec3,
                     ref_direction: Vec3, length_m: float,
                     width_m: float, depth_m: float) -> Any:
    """A rectangular member swept along its own 3D axis (``IfcExtrudedAreaSolid``).

    ``origin_m`` is the centroid of the start section, ``axis`` the unit vector the member
    runs along, and ``ref_direction`` the section's local X. This is how a beam, rafter or
    truss chord is represented in every structural BIM tool, so a sloped member arrives as a
    real profile on a real axis rather than a bounding prism.
    """
    profile = f.createIfcRectangleProfileDef("AREA", None, None, width_m, depth_m)
    placement = f.createIfcAxis2Placement3D(
        f.createIfcCartesianPoint(origin_m),
        f.createIfcDirection(axis), f.createIfcDirection(ref_direction),
    )
    solid = f.createIfcExtrudedAreaSolid(
        profile, placement, f.createIfcDirection((0.0, 0.0, 1.0)), length_m,
    )
    return f.createIfcShapeRepresentation(body_ctx, "Body", "SweptSolid", [solid])


def add_axis_representation(f: Any, body_ctx: Any,
                            points_m: tuple[tuple[float, float], tuple[float, float]]) -> Any:
    points = [f.createIfcCartesianPoint(point) for point in points_m]
    return f.createIfcShapeRepresentation(
        body_ctx, "Axis", "Curve2D", [f.createIfcPolyline(points)]
    )


def set_storey_elevation(f: Any, storey: Any, elevation_m: float) -> None:
    """State a storey's datum both ways an importer may read it.

    The placement is what elements are measured from and what the semantic extractor
    trusts; the ``Elevation`` attribute is the label scheduling tools read without
    resolving placements. Element geometry stays authored in the world frame (identity
    placements with no ``PlacementRelTo``), so a storey placement re-bases nothing.
    """
    storey.Elevation = float(elevation_m)
    origin = f.createIfcCartesianPoint((0.0, 0.0, float(elevation_m)))
    axis = f.createIfcAxis2Placement3D(origin, None, None)
    storey.ObjectPlacement = f.createIfcLocalPlacement(None, axis)


def ensure_local_placement(f: Any, element: Any) -> None:
    """Give a represented product an explicit identity placement in the project frame."""
    if getattr(element, "ObjectPlacement", None) is not None:
        return
    origin = f.createIfcCartesianPoint((0.0, 0.0, 0.0))
    axis = f.createIfcAxis2Placement3D(origin, None, None)
    element.ObjectPlacement = f.createIfcLocalPlacement(None, axis)


def assign_representation(f: Any, element: Any, rep: Any) -> None:
    assign_representations(f, element, [rep])


def assign_representations(f: Any, element: Any, representations: list[Any]) -> None:
    element.Representation = f.createIfcProductDefinitionShape(
        None, None, representations
    )
    # Geometry is authored in the shared project frame inside its swept solid. IFC still
    # requires every represented product to carry an ObjectPlacement; an identity placement
    # expresses that frame explicitly and satisfies both schema validation and BIM importers.
    ensure_local_placement(f, element)


def ensure_pset(f: Any, element: Any, name: str, props: dict[str, Any]) -> None:
    """Attach a property set to an element (ported ensure_pset)."""
    import ifcopenshell.api

    pset = ifcopenshell.api.run("pset.add_pset", f, product=element, name=name)
    ifcopenshell.api.run("pset.edit_pset", f, pset=pset, properties=props)


def assign_container(f: Any, element: Any, container: Any) -> None:
    import ifcopenshell.api

    ifcopenshell.api.run(
        "spatial.assign_container", f, products=[element], relating_structure=container
    )


def assign_type(f: Any, occurrence: Any, type_object: Any) -> None:
    """Keep occurrence/type semantics explicit for BIM consumers and schedules."""
    import ifcopenshell.api

    ifcopenshell.api.run("type.assign_type", f, related_objects=[occurrence], relating_type=type_object)


def create_system(f: Any, name: str, predefined_type: str | None = None) -> Any:
    """An ``IfcDistributionSystem`` — the entity a BIM tool reads as a *system*.

    Loose pipe elements sharing a category are only a naming convention; a system is the
    grouping Revit and Bonsai surface in their browsers, filter on, and schedule against.
    ``predefined_type`` is the IFC4 enum (``STORMWATER``, ``SANITARY``, ``VENT``…), which is
    what makes the group mean drainage rather than merely being called it.
    """
    system = create_entity(f, "IfcDistributionSystem", name=name)
    if predefined_type is not None:
        system.PredefinedType = predefined_type
    return system


def assign_to_group(f: Any, group: Any, elements: list[Any]) -> Any:
    """``IfcRelAssignsToGroup`` group ← elements, membership for systems and zones."""
    import ifcopenshell.api

    return ifcopenshell.api.run("group.assign_group", f, products=list(elements),
                                group=group)


def serves_building(f: Any, system: Any, building: Any) -> Any:
    """``IfcRelServicesBuildings`` — which spatial structure a system serves.

    Without it the system floats unattached to the building, and importers that walk the
    spatial tree to find services never reach it.
    """
    return f.create_entity(
        "IfcRelServicesBuildings", GlobalId=new_guid(), RelatingSystem=system,
        RelatedBuildings=[building])


def aggregate(f: Any, parent: Any, children: list[Any]) -> None:
    """IfcRelAggregates parent ← children (framed-LOD member aggregation)."""
    import ifcopenshell.api

    ifcopenshell.api.run("aggregate.assign_object", f, products=children,
                         relating_object=parent)


def assign_material_layer_set(f: Any, element: Any, layers: list[dict[str, Any]],
                              name: str) -> Any:
    """Attach an ``IfcMaterialLayerSet`` to a wall — how Revit reads a wall type's layers.

    ``layers`` is interior→exterior; each entry is
    ``{"name", "material_ref", "thickness_m", "category"}``. The set's thicknesses must sum
    to the element's real depth, so cavity fill (which lives inside a structure layer) must
    already be excluded by the caller — an over-thick layer set is the classic import
    artifact where a Revit wall type ends up thicker than its geometry.
    """
    materials: dict[str, Any] = {}
    ifc_layers = []
    for spec in layers:
        ref = spec["material_ref"]
        material = materials.get(ref)
        if material is None:
            # IfcMaterial is not a rooted entity — no GlobalId/OwnerHistory, so it must
            # bypass ``create_entity`` (which stamps both).
            material = f.create_entity("IfcMaterial", Name=ref)
            materials[ref] = material
        ifc_layer = f.create_entity(
            "IfcMaterialLayer",
            Material=material,
            LayerThickness=float(spec["thickness_m"]),
            Name=spec["name"],
            Category=spec.get("category"),
        )
        ifc_layers.append(ifc_layer)
    if not ifc_layers:
        return None
    layer_set = f.create_entity("IfcMaterialLayerSet", MaterialLayers=ifc_layers,
                                LayerSetName=name)
    f.create_entity("IfcRelAssociatesMaterial", GlobalId=new_guid(),
                    RelatedObjects=[element], RelatingMaterial=layer_set)
    return layer_set


def assign_material_layer_usage(f: Any, element: Any, layer_set: Any,
                                offset_from_reference_line_m: float) -> Any:
    # IfcOpenShell's type assignment creates a default occurrence usage when the wall
    # type already owns a layer set. Update that relationship instead of creating an
    # EXPRESS-invalid second material association.
    for relation in f.by_type("IfcRelAssociatesMaterial"):
        if element not in relation.RelatedObjects:
            continue
        related_material = relation.RelatingMaterial
        if related_material.is_a("IfcMaterialLayerSetUsage"):
            related_material.OffsetFromReferenceLine = float(offset_from_reference_line_m)
            return related_material
    usage = f.create_entity(
        "IfcMaterialLayerSetUsage",
        ForLayerSet=layer_set,
        LayerSetDirection="AXIS2",
        DirectionSense="POSITIVE",
        OffsetFromReferenceLine=float(offset_from_reference_line_m),
    )
    f.create_entity(
        "IfcRelAssociatesMaterial", GlobalId=new_guid(),
        RelatedObjects=[element], RelatingMaterial=usage,
    )
    return usage


def new_guid() -> str:
    import ifcopenshell.guid

    return ifcopenshell.guid.new()


def add_opening(f: Any, wall: Any, opening: Any) -> None:
    """IfcRelVoidsElement — the opening element voids its host wall (ported add_opening).

    ifcopenshell 0.8 exposes voiding under the ``feature`` api (``add_feature``)."""
    import ifcopenshell.api.feature

    ifcopenshell.api.feature.add_feature(f, feature=opening, element=wall)


def add_filling(f: Any, opening: Any, filling: Any) -> None:
    """IfcRelFillsElement — a window/door fills its opening (ported add_filling)."""
    import ifcopenshell.api.feature

    ifcopenshell.api.feature.add_filling(f, opening=opening, element=filling)

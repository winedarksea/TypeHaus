"""Typed low-level IfcOpenShell 0.8 adapter (ported from ifcplot/ifc_utils.py, → 12).

Risk 5 mitigation: *all* IfcOpenShell calls are confined to this ~one-file adapter, so a
0.8→0.9 reshape touches one place and golden IFC snapshots detect drift. Length unit is
standardized to meters project-wide and scaling is centralized here (avoiding the
mm-units gotcha documented at ifc_utils.py:395-406).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

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
    """Extrude a rectangular-jamb, semicircular-head opening through a wall.

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
    radius = half_width
    left_bottom = f.createIfcCartesianPoint((-half_width, 0.0))
    right_bottom = f.createIfcCartesianPoint((half_width, 0.0))
    right_spring = f.createIfcCartesianPoint((half_width, springline))
    left_spring = f.createIfcCartesianPoint((-half_width, springline))
    bottom = f.createIfcPolyline((left_bottom, right_bottom))
    right_jamb = f.createIfcPolyline((right_bottom, right_spring))
    circle = f.createIfcCircle(
        f.createIfcAxis2Placement2D(f.createIfcCartesianPoint((0.0, springline)), None), radius,
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


def add_axis_representation(f: Any, body_ctx: Any,
                            points_m: tuple[tuple[float, float], tuple[float, float]]) -> Any:
    points = [f.createIfcCartesianPoint(point) for point in points_m]
    return f.createIfcShapeRepresentation(
        body_ctx, "Axis", "Curve2D", [f.createIfcPolyline(points)]
    )


def ensure_local_placement(f: Any, element: Any) -> None:
    """Give a represented product an explicit identity placement in the project frame."""
    if getattr(element, "ObjectPlacement", None) is not None:
        return
    origin = f.createIfcCartesianPoint((0.0, 0.0, 0.0))
    axis = f.createIfcAxis2Placement3D(origin, None, None)
    element.ObjectPlacement = f.createIfcLocalPlacement(None, axis)


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

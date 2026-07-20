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
                           height_m: float, z0_m: float = 0.0) -> Any:
    """Extrude a closed polygon profile to a solid (ported add_prism_from_profile)."""
    pts = [f.createIfcCartesianPoint((x, y)) for (x, y) in points_m]
    polyline = f.createIfcPolyline(pts + [pts[0]])
    profile = f.createIfcArbitraryClosedProfileDef("AREA", None, polyline)
    origin = f.createIfcCartesianPoint((0.0, 0.0, z0_m))
    placement = f.createIfcAxis2Placement3D(origin, None, None)
    direction = f.createIfcDirection((0.0, 0.0, 1.0))
    solid = f.createIfcExtrudedAreaSolid(profile, placement, direction, height_m)
    return f.createIfcShapeRepresentation(body_ctx, "Body", "SweptSolid", [solid])


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


def aggregate(f: Any, parent: Any, children: list[Any]) -> None:
    """IfcRelAggregates parent ← children (framed-LOD member aggregation)."""
    import ifcopenshell.api

    ifcopenshell.api.run("aggregate.assign_object", f, products=children,
                         relating_object=parent)


def add_opening(f: Any, wall: Any, opening: Any) -> None:
    """IfcRelVoidsElement — the opening element voids its host wall (ported add_opening).

    ifcopenshell 0.8 exposes voiding under the ``feature`` api (``add_feature``)."""
    import ifcopenshell.api.feature

    ifcopenshell.api.feature.add_feature(f, feature=opening, element=wall)


def add_filling(f: Any, opening: Any, filling: Any) -> None:
    """IfcRelFillsElement — a window/door fills its opening (ported add_filling)."""
    import ifcopenshell.api.feature

    ifcopenshell.api.feature.add_filling(f, opening=opening, element=filling)

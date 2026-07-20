"""Joint resolution — per-layer terminations + treatment geometry at a transition (→ 11b).

A junction detail is a live section cut whose per-layer laps are *derived*, never authored:
a ``JointPlan`` maps each participating layer to a termination plane (Revit "layer extension
distance") and carries the treatment fills (spray-foam wedge, sealant, tape) computed from the
same interface planes. Default joins come from layer function/control; authored ``LayerJoin``
entries on the matched ``Transition`` override by fnmatch glob.

Engine-internal IR (plain dataclasses, never serialized as source), consumed by the cutter.
Section coordinates: ``u`` = world x (cut_direction "x") or world y ("y"); ``z`` = world z.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from typehaus.emit.draw.scene import Hatch, IRNode, Polyline
from typehaus.model.patterns import matches
from typehaus.resolve.model import ResolvedModel, ResolvedRoof, ResolvedWall

M_TO_IN = 39.37007874015748


@dataclass(frozen=True)
class TerminationPlane:
    """A layer's termination (top) elevation in section (u, z): ``z0 + slope*(u - u0)``."""

    u0: float
    z0: float
    slope: float = 0.0

    def z(self, u: float) -> float:
        return self.z0 + self.slope * (u - self.u0)


@dataclass
class JointPlan:
    """Per (element uid, layer name) termination planes + treatment scene nodes."""

    terminations: dict[tuple[str, str], TerminationPlane] = field(default_factory=dict)
    treatments: list[IRNode] = field(default_factory=list)

    def termination(self, uid: str, layer: str) -> TerminationPlane | None:
        return self.terminations.get((uid, layer))


def _roof_underside_line(roof: ResolvedRoof, direction: str, junction_u: float,
                         thickness_m: float) -> TerminationPlane:
    """The roof deck underside as a section (u, z) line at the junction, minus its thickness.

    ``u`` is the in-section coordinate (world x for a "x" cut, world y for a "y" cut). The
    roof slopes perpendicular to its ridge; the plane is anchored at ``junction_u`` so the
    derived wedge stays local to the junction instead of extrapolating across the roof.
    """
    xs = [p[0] for p in roof.footprint]
    ys = [p[1] for p in roof.footprint]
    # The coordinate the roof slope runs along (perpendicular to the ridge).
    slope_axis_is_u = (
        (roof.ridge_direction == "y" and direction == "x")
        or (roof.ridge_direction == "x" and direction == "y")
    )
    lo, hi = (min(xs), max(xs)) if roof.ridge_direction == "y" else (min(ys), max(ys))
    mid = (lo + hi) / 2.0
    span = (hi - lo) / 2.0 or 1e-9
    rise = roof.ridge_z_m - roof.eave_z_m

    def z_top(u: float) -> float:
        if roof.form == "shed":
            return roof.eave_z_m + (u - lo) / (hi - lo or 1e-9) * rise
        return roof.eave_z_m + rise * (1.0 - abs(u - mid) / span)

    if not slope_axis_is_u:
        slope = 0.0
        z_here = roof.eave_z_m  # flat in u; nearest eave elevation
    elif roof.form == "shed":
        slope = rise / (hi - lo or 1e-9)
        z_here = z_top(junction_u)
    else:
        slope = -rise / span if junction_u >= mid else rise / span
        z_here = z_top(junction_u)
    return TerminationPlane(u0=junction_u, z0=z_here - thickness_m, slope=slope)


def _layer_control(layer) -> frozenset:
    return getattr(layer, "control", frozenset())


def build_joint_plan(model: ResolvedModel, condition, transition,
                     direction: str, station: float) -> JointPlan:
    """Derive the joint plan for one bound (condition, transition) at a section cut.

    Default joins by layer function/control at a wall↔roof junction; authored ``LayerJoin``
    entries override by glob. Other junction kinds currently contribute authored joins only.
    """
    plan = JointPlan()
    wall = _representative_wall(model, condition)
    roof = _representative_roof(model, condition)

    if wall is not None and roof is not None:
        _default_roof_joins(plan, model, wall, roof, direction, station)

    # Authored overrides (LayerJoin) — glob over layer name/function on the wall's side.
    if wall is not None and transition is not None:
        for join in getattr(transition, "joins", ()):
            _apply_authored_join(plan, wall, join, direction, station)
    return plan


def _representative_wall(model, condition) -> ResolvedWall | None:
    for tag in getattr(condition, "element_tags", ()):
        w = model.wall(tag)
        if w is not None:
            return w
    return None


def _representative_roof(model, condition) -> ResolvedRoof | None:
    tags = set(getattr(condition, "element_tags", ()))
    return next((r for r in model.roofs if r.tag in tags), None)


_WEDGE_GAP_M = 0.05  # CI stops ~2" short of the deck underside; wedge fills the gap.
_DRIP_M = 0.04       # cladding/furring run long past the interface.


def _default_roof_joins(plan: JointPlan, model, wall: ResolvedWall, roof: ResolvedRoof,
                        direction: str, station: float) -> None:
    asm = model.plan.library.resolve_assembly(roof.assembly)
    roof_thickness = sum(l.thickness.meters for l in asm.layers) if asm is not None else 0.3
    # Junction u = the wall's in-section position (world x for "x" cut, world y for "y").
    (x0, y0), (x1, y1) = wall.axis
    junction_u = (x0 + x1) / 2.0 if direction == "x" else (y0 + y1) / 2.0
    underside = _roof_underside_line(roof, direction, junction_u, roof_thickness)
    wall_top = wall.top_z1_m if wall.top_z1_m is not None else wall.z1_m

    ci_top_u: tuple[float, float] | None = None
    sheath_face_u: tuple[float, float] | None = None
    for layer in wall.layers:
        key = (wall.uid, layer.name)
        control = _layer_control(layer)
        func = layer.function
        if "air" in control:
            # Air barrier runs to the far structure plane (roof underside).
            plan.terminations[key] = underside
        elif func == "insulation":
            # Continuous exterior insulation stops short of the deck; wedge fills the gap.
            plan.terminations[key] = TerminationPlane(
                u0=underside.u0, z0=underside.z0 - _WEDGE_GAP_M, slope=underside.slope)
            u_iv = _layer_u_interval(layer, direction, station)
            if u_iv is not None:
                ci_top_u = (max(u_iv), underside.z0 - _WEDGE_GAP_M)
        elif func in ("cladding", "furring"):
            # Cladding/furring run long past the interface (drip gap).
            plan.terminations[key] = TerminationPlane(
                u0=underside.u0, z0=underside.z0 + _DRIP_M, slope=underside.slope)
        elif func in ("sheathing", "structure"):
            u_iv = _layer_u_interval(layer, direction, station)
            if u_iv is not None and func == "sheathing":
                sheath_face_u = (max(u_iv), wall_top)

    # Spray-foam wedge = quad bounded by CI top, roof underside, wall sheathing face.
    if ci_top_u is not None and sheath_face_u is not None:
        u_ci, z_ci = ci_top_u
        u_sh, _ = sheath_face_u
        poly = (
            (u_ci * M_TO_IN, z_ci * M_TO_IN),
            (u_ci * M_TO_IN, underside.z(u_ci) * M_TO_IN),
            (u_sh * M_TO_IN, underside.z(u_sh) * M_TO_IN),
            (u_sh * M_TO_IN, wall_top * M_TO_IN),
        )
        plan.treatments.append(
            Hatch(boundary=poly, pattern="spray-foam", layer="A-DETL-TRMT",
                  uid=f"trmt:{wall.uid}:wedge"))
        plan.treatments.append(
            Polyline(points=poly, layer="A-DETL-TRMT", closed=True, lineweight=0.18,
                     tag="spray-foam-wedge"))


def _apply_authored_join(plan: JointPlan, wall: ResolvedWall, join, direction, station) -> None:
    interface_z = wall.top_z1_m if wall.top_z1_m is not None else wall.z1_m
    term = interface_z + join.termination.meters
    for layer in wall.layers:
        if matches(join.layer, layer.name) or matches(join.layer, layer.function):
            u_iv = _layer_u_interval(layer, direction, station)
            u0 = station if u_iv is None else sum(u_iv) / 2.0
            plan.terminations[(wall.uid, layer.name)] = TerminationPlane(u0=u0, z0=term)


def _layer_u_interval(layer, direction: str, station: float) -> tuple[float, float] | None:
    from typehaus.emit.draw.section import _ring_cut_intervals

    ivs = _ring_cut_intervals(layer.polygon, direction, station)
    return ivs[0] if ivs else None

"""Whether a turn has room for its fitting: the nipple before it, and the heel behind it.

Two plumber's rules the lattice cannot see on its own:

* **Minimum nipple.** Two fittings cannot sit closer, centre to centre, than their bodies
  allow. The catalog's ``center_to_face_in`` gives that where a submittal publishes it;
  where none does (``library/fittings.py`` publishes no DWV elbow body) the floor is the
  hub OD — two hubs cannot overlap — which never refuses a pair that could be built.
* **Heel room.** A bend's outside corner carries the hub past the pipe, and the joint needs
  a tool's swing round it (``RouteCost.*_tool_in``). The test is in the TURN'S OWN PLANE:
  the two points behind the corner, along the incoming leg carried on and the outgoing leg
  carried back. Out of plane a fitting needs only its hub, which ``cavity_radius_m``
  already holds, so a bend in a stud bay is not refused by the bay's own faces.

Hard prisms are inflated by the run's radius and clearance, so a heel point is blocked
exactly when the hub plus the tool, beyond the pipe, would meet one.
"""

from __future__ import annotations

from typehaus.hardware.fittings import fitting_catalog
from typehaus.quantities import M_PER_IN
from typehaus.routing.cost import RouteCost
from typehaus.routing.graph import Graph
from typehaus.routing.space import RoutingSpace

#: Solvent weld unless the material says otherwise.
_PRESS = ("copper", "cu", "type_l", "type_m", "propress")
_PEX = ("pex", "pex_a", "pex-a", "pex_b", "pex-b")


def tool_in(cost: RouteCost, material: str | None) -> float:
    """The joint's tool allowance, by joining method read off the material."""
    name = (material or "").strip().lower()
    if any(name.startswith(p) for p in _PRESS):
        return cost.propress_tool_in
    if any(name.startswith(p) for p in _PEX):
        return cost.pex_expansion_tool_in
    return cost.solvent_weld_tool_in


def nipple_m(service: str, nominal_m: float, hub_od_m: float) -> float:
    """Least centre-to-centre between two turns: two published bodies, else the hub OD."""
    size = round(nominal_m / M_PER_IN * 16) / 16
    faces = [f.center_to_face_in for f in fitting_catalog()
             if f.service == service and f.kind == "elbow" and f.nominal_in == size
             and f.center_to_face_in is not None]
    return max(2.0 * min(faces) * M_PER_IN if faces else 0.0, hub_od_m)


def heel_m(cost: RouteCost, material: str | None, hub_radius_m: float,
           radius_m: float) -> float:
    """How far behind a corner the fitting and its tool reach beyond the pipe itself."""
    return max(0.0, hub_radius_m - radius_m) + tool_in(cost, material) * M_PER_IN


def heel_clear(graph: Graph, space: RoutingSpace, prev: int, here: int, nxt: int,
               reach_m: float) -> bool:
    """Whether both heel points of the turn ``prev -> here -> nxt`` are clear."""
    if reach_m <= 0.0:
        return True
    a, b, c = graph.nodes[prev], graph.nodes[here], graph.nodes[nxt]
    for (fx, fy, fz), sign in (((b.x - a.x, b.y - a.y, b.z - a.z), 1.0),
                               ((c.x - b.x, c.y - b.y, c.z - b.z), -1.0)):
        length = (fx * fx + fy * fy + fz * fz) ** 0.5
        if length <= 0.0:
            continue
        k = sign * reach_m / length
        if space.blocked((b.x + fx * k, b.y + fy * k), b.z + fz * k) is not None:
            return False
    return True


def fitting_terms(cost: RouteCost, service: str, nominal_m: float, material: str | None,
                  radius_m: float) -> tuple[float, float]:
    """``(nipple_m, heel_m)`` for a run of this size and material."""
    from typehaus.resolve.pipe_sections import hub_outside_diameter_m

    hub_od = hub_outside_diameter_m(nominal_m, material)
    return (nipple_m(service, nominal_m, hub_od),
            heel_m(cost, material, hub_od / 2.0, radius_m))

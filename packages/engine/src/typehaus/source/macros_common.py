"""What every macro module shares: the error type, the snap/collinearity tolerances, and the
lookup + coordinate helpers that turn authored plan source into meters and back.

Split out of :mod:`typehaus.source.macros` (→ 21b §Room macros). The seam is dependency
direction, not topic: this module imports no sibling macro module, so wall, opening, and
placeable macros can all lean on it without a cycle. Coordinates are emitted as
:class:`RawExpr` ``pt(...)`` here and nowhere else, which is what keeps a mutation from
re-encoding an authored dimension through a lossy meters round-trip.
"""

from __future__ import annotations

from typehaus.model.elements import Node, Wall
from typehaus.model.mep import ElectricalDevice, Equipment, Register
from typehaus.model.plan import PlanModel
from typehaus.model.spatial import Appliance, Fixture, Furniture
from typehaus.quantities import Length
from typehaus.quantities.length import ft, m
from typehaus.source.ops import RawExpr

# Node coincidence tolerance — nodes closer than this fuse (T-junction heal), in meters.
SNAP_M = 0.02
# Product rotations default to the same 15° increment in every canvas adapter. The explicit
# macro flag keeps free rotation intentional rather than an accidental floating-point drift.
ROTATION_SNAP_DEGREES = 15.0
# Room faces resolve at finish surfaces while authored nodes lie on wall axes.  This is the
# maximum practical finish/half-wall offset for identifying a room's boundary graph.
ROOM_BOUNDARY_NODE_TOLERANCE_M = 0.35

XY = tuple[float | str, float | str]


class MacroError(ValueError):
    """A macro could not be built (degenerate geometry, missing element, ambiguous heal)."""


# --- coordinate helpers ------------------------------------------------------

def _as_length(v: float | str) -> Length:
    return Length.parse(v) if isinstance(v, str) else m(float(v))


def _point_expr(x: float | str, y: float | str) -> RawExpr:
    return RawExpr(f"pt({_as_length(x).to_source()}, {_as_length(y).to_source()})")


def _meters(v: float | str) -> float:
    return _as_length(v).meters


def _nodes(plan: PlanModel, storey: str) -> list[Node]:
    return [e for e in plan.storey_elements(storey) if isinstance(e, Node)]


def _walls(plan: PlanModel, storey: str) -> list[Wall]:
    return [e for e in plan.storey_elements(storey) if isinstance(e, Wall)]


def _next_tag(existing: list, prefix: str) -> str:
    used = set()
    for el in existing:
        t = el.tag
        if t.startswith(prefix) and t[len(prefix):].isdigit():
            used.add(int(t[len(prefix):]))
    n = 1
    while n in used:
        n += 1
    return f"{prefix}{n}"


def _copy_tag(plan: PlanModel, source_tag: str) -> str:
    """Return a readable unused duplicate tag without changing the original identity."""
    used = {item.tag for storey in plan.storeys for item in plan.storey_elements(storey.tag)}
    candidate = f"{source_tag}-COPY"
    index = 2
    while candidate in used:
        candidate = f"{source_tag}-COPY-{index}"
        index += 1
    return candidate


def _find_node_near(plan: PlanModel, storey: str, xy_m: tuple[float, float]) -> Node | None:
    for nd in _nodes(plan, storey):
        px, py = nd.position.xy_m
        if (px - xy_m[0]) ** 2 + (py - xy_m[1]) ** 2 <= SNAP_M ** 2:
            return nd
    return None


def _point_expr_m(x_m: float, y_m: float) -> RawExpr:
    """Emit a point from meters, snapping near-round inch values to authored ft-in."""
    return RawExpr(f"pt({_round_len(x_m).to_source()}, {_round_len(y_m).to_source()})")


def _round_len(x_m: float) -> Length:
    """Meters -> an authored ``ft(f, i)``, snapped to the 1/16" grid when it lands on it.

    The sign goes on *both* arguments for a negative length. ``divmod`` floors, so
    ``divmod(-27, 12)`` is ``(-3, 9)`` — arithmetically right (``-3*12 + 9 == -27``) and
    unreadable: the source it writes says ``ft(-3, 9)``, which every human reads as minus
    three-foot-nine and is off by 18". Splitting the magnitude and negating both parts emits
    ``ft(-2, -3)``, which reads as what it is. ``quantities.length.ft`` now rejects the
    mixed-sign form outright, so this is also the only spelling it will accept.
    """
    inches = x_m / 0.0254
    nearest = round(inches * 16) / 16  # 1/16" grid
    if abs(nearest - inches) < 1e-6:
        feet, rem = divmod(abs(nearest), 12)
        sign = -1.0 if nearest < 0 else 1.0
        return ft(sign * feet, sign * rem)
    return m(x_m)


# --- element lookups ---------------------------------------------------------

def _openings(plan: PlanModel, storey: str) -> list:
    kinds = {"Window", "Door", "RoughOpening"}
    return [e for e in plan.storey_elements(storey) if e.element_kind in kinds]


def _rooms(plan: PlanModel, storey: str) -> list:
    return [e for e in plan.storey_elements(storey) if e.element_kind == "Room"]


_PLACEABLE_KINDS = (Furniture, Fixture, Appliance, Equipment, Register, ElectricalDevice)


def _placeable(plan: PlanModel, storey: str, tag: str):
    return next((item for item in plan.storey_elements(storey)
                 if isinstance(item, _PLACEABLE_KINDS) and item.tag == tag), None)

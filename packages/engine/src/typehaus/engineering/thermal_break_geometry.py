"""What one insulating break IS, read off the resolved model — for ``thermal_break``.

A ``Board`` is a break's facts in inches along its thickness axis (``ax``): its thickness, faces
and extent, the court pour on one side, the house element on the other, and the clear gap
between the two concretes. Two kinds carry one: an ``IsolationBoard``, and a cast wall or
beam in a retaining loop whose assembly carries an INSULATION layer (catlin's veneer beam).
Free body §11, "The five boards".
"""

from __future__ import annotations

from dataclasses import dataclass, field

_IN = 1.0 / 0.0254
#: How far past its own face a board may look for the house element it bears on, in.
FACING_REACH_IN = 12.0


@dataclass
class Board:
    tag: str
    element: object | None      # the IsolationBoard, or None for a layer board
    ax: int                       # 0 = x, 1 = y: the axis the board's thickness runs along
    t_in: float
    h_in: float
    length_in: float
    bottom_in: float
    top_in: float
    along: tuple[float, float]    # extent along the joint (the other plan axis), in
    court_face_in: float          # the face cast against the court pour
    house_face_in: float          # the face toward the house
    loop_ref: str | None = None
    structure: set[str] = field(default_factory=set)
    court_tag: str | None = None  # the court element the board is cast against
    house_tag: str | None = None  # the house element named in ``connects``

    @property
    def mid_in(self) -> float:
        return (self.court_face_in + self.house_face_in) / 2.0

    @property
    def toward_house(self) -> float:
        return 1.0 if self.house_face_in > self.court_face_in else -1.0

    @property
    def area_in2(self) -> float:
        return self.h_in * self.length_in


def isolation_boards(ctx) -> list:
    from typehaus.model.structure import IsolationBoard

    return sorted((b for b in ctx.plan.all_elements() if isinstance(b, IsolationBoard)),
                  key=lambda b: b.tag)


def structure_of(ctx, tag: str) -> set[str]:
    """Tags of the cast walls and beams node-connected to ``tag`` (a Footing reads through
    ``under``) — one structure, which is what a break separates."""
    from typehaus.model.structure import Footing, FoundationWall
    from typehaus.resolve.assembly_material import is_cast_beam

    start = ctx.plan.by_tag(tag)
    if isinstance(start, Footing):
        start = ctx.plan.by_tag(start.under)
    if start is None or not getattr(start, "start_node", None):
        return set()
    pool = [e for e in ctx.plan.all_elements()
            if (isinstance(e, FoundationWall) or is_cast_beam(ctx.plan, e))
            and e.start_node and e.end_node]
    seen, nodes, grew = {start.tag}, {start.start_node, start.end_node}, True
    while grew:
        grew = False
        for e in pool:
            if e.tag not in seen and ({e.start_node, e.end_node} & nodes):
                seen.add(e.tag)
                nodes |= {e.start_node, e.end_node}
                grew = True
    return seen


def loop_of(structure: set[str], loops: dict) -> str | None:
    for ref, by_pcf in loops.items():
        members = set(next(iter(by_pcf.values()), {}))
        if structure & (members | {ref}):
            return ref
    return None


def _solid(ctx, tag: str, category: str):
    return next((s for s in ctx.model.solids if s.tag == tag and s.category == category),
                None)


def _extent(outline, ax: int) -> tuple[float, float]:
    vals = [p[ax] * _IN for p in outline]
    return min(vals), max(vals)


def concrete_extent(ctx, tag: str, ax: int) -> tuple[float, float] | None:
    """The element's STRUCTURE extent along ``ax``, in — a footing's solid, a wall's
    STRUCTURE layer."""
    solid = _solid(ctx, tag, "footing")
    if solid is not None:
        return _extent(solid.outline, ax)
    wall = next((w for w in ctx.model.walls if w.tag == tag), None)
    if wall is None:
        return None
    layer = next((ly for ly in wall.depth_layers() if ly.function == "structure"), None)
    return None if layer is None else _extent(layer.polygon, ax)


def z_extent(ctx, tag: str) -> tuple[float, float] | None:
    solid = _solid(ctx, tag, "footing")
    if solid is not None:
        return solid.z0_m * _IN, solid.z1_m * _IN
    wall = next((w for w in ctx.model.walls if w.tag == tag), None)
    return None if wall is None else (wall.z0_m * _IN, wall.z1_m * _IN)


def authored_board(ctx, element, loops: dict) -> Board | None:
    """The resolved solid of an ``IsolationBoard`` as a :class:`Board`, or ``None``."""
    solid = _solid(ctx, element.tag, "thermal_break")
    if solid is None:
        return None
    ax = 1 if element.axis == "y" else 0
    lo, hi = _extent(solid.outline, ax)
    along = _extent(solid.outline, 1 - ax)
    court_tag = house_tag = None
    structure: set[str] = set()
    ref = None
    for tag in element.connects:
        s = structure_of(ctx, tag)
        r = loop_of(s, loops)
        if r is not None and court_tag is None:
            court_tag, structure, ref = tag, s, r
        else:
            house_tag = tag
    board = Board(element.tag, element, ax, hi - lo, (solid.z1_m - solid.z0_m) * _IN,
                  along[1] - along[0], solid.z0_m * _IN, solid.z1_m * _IN, along,
                  court_face_in=lo, house_face_in=hi, loop_ref=ref, structure=structure,
                  court_tag=court_tag, house_tag=house_tag)
    house = concrete_extent(ctx, house_tag, ax) if house_tag else None
    if house is not None and abs(house[0] - lo) < abs(house[0] - hi) and abs(
            house[1] - lo) < abs(house[1] - hi):
        board.court_face_in, board.house_face_in = hi, lo
    return board


def layer_boards(ctx, loops: dict) -> list[Board]:
    """Cast walls and beams in a retaining loop whose assembly carries an INSULATION layer
    that faces a house footing — a board with no bars (catlin's veneer grade beam)."""
    from typehaus.model.structure import FoundationWall
    from typehaus.resolve.assembly_material import is_cast_beam

    out = []
    for element in ctx.plan.all_elements():
        if not (isinstance(element, FoundationWall) or is_cast_beam(ctx.plan, element)):
            continue
        wall = next((w for w in ctx.model.walls if w.tag == element.tag), None)
        if wall is None:
            continue
        structure = structure_of(ctx, element.tag)
        ref = loop_of(structure, loops)
        if ref is None:
            # Cast into a wall's run rather than joined at a node (catlin's veneer beam ends
            # mid-wall on W-SG-W1/E1's axes, monolithic per AN-SG-PLACEMENTS).
            host = _host_at_ends(ctx, wall)
            structure = structure_of(ctx, host) | {element.tag} if host else structure
            ref = loop_of(structure, loops)
        if ref is None:
            continue
        layers = wall.depth_layers()
        board = next((ly for ly in layers if ly.function == "insulation"), None)
        core = next((ly for ly in layers if ly.function == "structure"), None)
        if board is None or core is None:
            continue
        (x0, y0), (x1, y1) = wall.axis
        ax = 1 if abs(x1 - x0) >= abs(y1 - y0) else 0     # thickness runs across the axis
        lo, hi = _extent(board.polygon, ax)
        c_lo, c_hi = _extent(core.polygon, ax)
        court_face, house_face = (hi, lo) if abs(hi - c_hi) < 1e-6 or abs(
            hi - c_lo) < 1e-6 else (lo, hi)
        along = _extent(board.polygon, 1 - ax)
        found = Board(element.tag, None, ax, hi - lo, (wall.z1_m - wall.z0_m) * _IN,
                      along[1] - along[0], wall.z0_m * _IN, wall.z1_m * _IN, along,
                      court_face_in=court_face, house_face_in=house_face, loop_ref=ref,
                      structure=structure, court_tag=element.tag)
        if facing_footings(ctx, found):
            out.append(found)
    return sorted(out, key=lambda b: b.tag)


def _host_at_ends(ctx, wall, tol_in: float = 0.5) -> str | None:
    """A wall whose axis passes through one of ``wall``'s end points."""
    for end in wall.axis:
        for other in ctx.model.walls:
            if other.tag == wall.tag:
                continue
            (x0, y0), (x1, y1) = other.axis
            dx, dy = x1 - x0, y1 - y0
            span = dx * dx + dy * dy
            if not span:
                continue
            u = max(0.0, min(1.0, ((end[0] - x0) * dx + (end[1] - y0) * dy) / span))
            gap = ((x0 + u * dx - end[0]) ** 2 + (y0 + u * dy - end[1]) ** 2) ** 0.5
            if gap * _IN <= tol_in:
                return other.tag
    return None


def facing_footings(ctx, board: Board) -> list[str]:
    """House footings the board bears on: overlapping it along the joint and in z, their
    near face within ``FACING_REACH_IN`` of the board's house face."""
    from typehaus.model.structure import Footing

    out = []
    for f in ctx.plan.all_elements():
        if not isinstance(f, Footing) or f.under in board.structure:
            continue
        solid = _solid(ctx, f.tag, "footing")
        if solid is None:
            continue
        a0, a1 = _extent(solid.outline, 1 - board.ax)
        if min(a1, board.along[1]) - max(a0, board.along[0]) <= 0.5:
            continue
        if min(solid.z1_m * _IN, board.top_in) - max(solid.z0_m * _IN, board.bottom_in) <= 0.5:
            continue
        n0, n1 = _extent(solid.outline, board.ax)
        near = n0 if board.toward_house > 0 else n1
        gap = (near - board.house_face_in) * board.toward_house
        if 0.0 <= gap <= FACING_REACH_IN:
            out.append((gap, f.tag))
    # The FIRST line only: a strip teeing in behind it (FT-B-CS) is not faced.
    first = min((g for g, _t in out), default=0.0)
    return sorted(t for g, t in out if g <= first + 1.0)


def house_concrete_face(ctx, board: Board) -> float | None:
    """The house-side concrete face along the bar axis — what a bar spans to."""
    if board.house_tag is None:
        return None
    ext = concrete_extent(ctx, board.house_tag, board.ax)
    if ext is None:
        return None
    return ext[0] if board.toward_house > 0 else ext[1]


def house_insulation(ctx, board: Board) -> list[tuple[str, str, float]]:
    """``(layer, material, thickness in)`` for the house element's insulation layers lying
    between the board and its concrete — what the board bears on."""
    wall = next((w for w in ctx.model.walls if w.tag == board.house_tag), None)
    face = house_concrete_face(ctx, board)
    if wall is None or face is None:
        return []
    lo, hi = sorted((board.house_face_in, face))
    out = []
    for ly in wall.depth_layers():
        if ly.function != "insulation":
            continue
        a, b = _extent(ly.polygon, board.ax)
        if a >= lo - 1e-3 and b <= hi + 1e-3:
            out.append((ly.name, ly.material_ref or "", b - a))
    return out


def court_centre_along(ctx, board: Board) -> float | None:
    """The court structure's centreline across its walls, along the joint — the point its
    E-W growth moves away from."""
    pts = [p[1 - board.ax] * _IN for w in ctx.model.walls if w.tag in board.structure
           for p in w.axis]
    return (min(pts) + max(pts)) / 2.0 if pts else None


def court_run_in(ctx, board: Board) -> float:
    """The court's run along the bar axis, from the board's mid-plane to its farthest wall
    axis point (free body §11c: it grows toward the break over the full run)."""
    origin = board.mid_in
    return max((abs(p[board.ax] * _IN - origin) for w in ctx.model.walls
                if w.tag in board.structure for p in w.axis), default=0.0)


def stacked_on(ctx, board: Board, others: list[Board]) -> str | None:
    """The break block this board stands on, if any — then no face of it is under the pour."""
    for other in others:
        if other.tag == board.tag or abs(other.top_in - board.bottom_in) > 1e-3:
            continue
        if (min(other.along[1], board.along[1]) - max(other.along[0], board.along[0]) > 0
                and abs(other.mid_in - board.mid_in) < board.t_in):
            return other.tag
    return None

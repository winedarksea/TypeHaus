"""Fabricated countertop and stool pieces, one record per piece, for ``haus countertops``.

Scope is ``takeoff/countertops.py``'s: every ``Countertop`` plus the stools cut from a
countertop material — less a custom-milled material, which goes to the mill
(``haus millwork``), not a slab yard — and the pieces of a stool's fabricated picture frame
(``countertop_returns``). Each piece is laid out in its own inches: the longest
finished edge along +x at the bottom, origin at the bounding-box minimum, counter-clockwise.
Gross area stays square-cornered (a yard quotes the rectangle).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from shapely.geometry import Point, Polygon
from shapely.ops import nearest_points

from typehaus.resolve.countertop_edges import (
    EDGE_FINISHED,
    EDGE_SEAM,
    EDGE_WALL,
    STOOL_EDGE_KINDS,
    stool_edge_kinds,
    stool_ring_radii,
)
from typehaus.resolve.fillet import corner_fillets, filleted_ring, signed_area
from typehaus.resolve.geometry_millwork import window_stool_ring
from typehaus.resolve.model import ResolvedCountertop, ResolvedModel, ResolvedWindowStool
from typehaus.resolve.model_window_returns import ResolvedWindowReturn
from typehaus.takeoff.countertops import countertop_returns, countertop_stools

_M_TO_IN = 39.37007874
_SQIN_TO_SQFT = 1.0 / 144.0
#: Fabricator words for the authored ``profile`` strings.
PROFILE_WORDS = {
    "eased": 'eased edge (standard ~1/8" arris top and bottom), polished',
    "built-up eased": "built-up (laminated) front edge, eased",
}
TEMPLATE_HOLD = "Field template after cabinets are set; dimensions here are design intent."
RETURN_HOLD = ("Field-measure the reveal after the membrane is returned onto the buck; glue "
               "the jambs to the stool and the head over them, back edge to the delivered "
               "window's interior frame face.")
WEB_HOLD = "Verify the fabricator's minimum web; the narrowest webs are dimensioned, not graded."

PointIn = tuple[float, float]


def inches_text(value: float) -> str:
    """``0.375`` -> ``3/8"``, ``1.0`` -> ``1"``; otherwise three decimals."""
    sixteenths = round(value * 16)
    if abs(value * 16 - sixteenths) > 1e-3:
        return f'{value:.3f}"'
    whole, rest = divmod(sixteenths, 16)
    if not rest:
        return f'{whole}"'
    num, den = rest, 16
    while num % 2 == 0:
        num, den = num // 2, den // 2
    return f'{whole} {num}/{den}"' if whole else f'{num}/{den}"'


@dataclass(frozen=True)
class PieceCutout:
    ring: tuple[PointIn, ...]
    label: str
    fixture_ref: str


@dataclass(frozen=True)
class PieceHole:
    center: PointIn
    diameter_in: float
    purpose: str


@dataclass(frozen=True)
class PieceWeb:
    """The narrowest stone between a cutout or hole and the next opening or edge."""

    label: str
    distance_in: float
    start: PointIn
    end: PointIn


@dataclass
class FabricatedPiece:
    tag: str
    uid: str
    kind: str  # "top" | "stool" | "return"
    material_ref: str
    material_name: str
    product: str
    thickness_in: float
    profile: str
    location: str
    outline: tuple[PointIn, ...]
    edge_kinds: tuple[str, ...]
    radii_in: tuple[float, ...]
    length_in: float
    depth_in: float
    area_sqft: float
    cutouts: list[PieceCutout] = field(default_factory=list)
    holes: list[PieceHole] = field(default_factory=list)
    webs: list[PieceWeb] = field(default_factory=list)
    support: str = ""
    holds: list[str] = field(default_factory=list)
    clamped_corners: tuple[int, ...] = ()
    mixed_edges: tuple[int, ...] = ()

    @property
    def profile_words(self) -> str:
        return PROFILE_WORDS.get(self.profile, self.profile)

    @property
    def fillets(self):  # type: ignore[no-untyped-def]
        return corner_fillets(self.outline, self.radii_in)

    def cut_ring(self, segments: int = 12) -> tuple[PointIn, ...]:
        return filleted_ring(self.outline, self.radii_in, segments)

    def edge_runs(self):  # type: ignore[no-untyped-def]
        """``(kind, (start, end))`` per edge: its straight run between fillet tangents."""
        fillets = {fillet.index: fillet for fillet in self.fillets}
        count = len(self.outline)
        for index, kind in enumerate(self.edge_kinds):
            nxt = (index + 1) % count
            start = fillets[index].end if index in fillets else self.outline[index]
            end = fillets[nxt].start if nxt in fillets else self.outline[nxt]
            yield kind, (start, end)

    def edge_length_in(self, kind: str) -> float:
        return sum(math.dist(self.outline[i], self.outline[(i + 1) % len(self.outline)])
                   for i, edge in enumerate(self.edge_kinds) if edge == kind)


def fabricated_pieces(model: ResolvedModel, material: str | None = None
                      ) -> list[FabricatedPiece]:
    """Every fabricated piece, tops then stools then returns, each sorted by tag."""
    materials = {item.tag: item for item in model.plan.library.materials}

    def wanted(ref: str) -> bool:
        stock = materials.get(ref)
        return ((material is None or ref == material)
                and not getattr(stock, "requires_custom_milling", False))

    pieces = [_top_piece(model, top, materials)
              for top in sorted(model.countertops, key=lambda item: item.tag)
              if wanted(top.material_ref)]
    for stool in sorted(countertop_stools(model), key=lambda item: item.tag):
        if wanted(stool.material_ref):
            piece = _stool_piece(model, stool, materials)
            if piece is not None:
                pieces.append(piece)
    for reveal, ref, thickness in sorted(countertop_returns(model), key=lambda r: r[0].tag):
        if wanted(ref):
            pieces.extend(_return_pieces(model, reveal, ref, thickness, materials))
    return pieces


def _products(model: ResolvedModel) -> dict[str, str]:
    return {product.tag: f"{product.brand} {product.model}".strip()
            for product in getattr(model.plan.library, "products", ())}


def _top_piece(model: ResolvedModel, top: ResolvedCountertop, materials
               ) -> FabricatedPiece:
    objects = {obj.tag: obj for obj in model.canvas_objects}
    types = {typ.tag: typ for typ in model.plan.library.fixture_types}
    products = _products(model)
    to_local, ring, kinds, radii = _local_frame(top.outline, top.edge_kinds,
                                                top.corner_radii_m)
    cutouts: list[PieceCutout] = []
    holds = [TEMPLATE_HOLD]
    for ring_m, ref in zip(top.cutouts, top.cutout_refs or ("",) * len(top.cutouts),
                           strict=True):
        obj = objects.get(ref)
        typ = types.get(obj.type_ref or "") if obj is not None else None
        basin = next((part.product_ref for part in getattr(typ, "parts", ())
                      if part.role == "basin"), None)
        product = products.get(basin or getattr(typ, "product_ref", None) or "", ref)
        cutouts.append(PieceCutout(tuple(to_local(p) for p in ring_m),
                                   f"CUT TO DELIVERED SINK TEMPLATE ({product})", ref))
        holds.append(f"{ref}: cut to the delivered {product} template — radii, reveal and "
                     "clip positions; the drawn opening is schematic.")
        holds.extend(_under_sink_holds(model, obj, top))
    holes = [PieceHole(to_local(hole.center), hole.diameter_m * _M_TO_IN, hole.purpose)
             for hole in top.holes]
    material = materials.get(top.material_ref)
    piece = FabricatedPiece(
        tag=top.tag, uid=top.uid, kind="top", material_ref=top.material_ref,
        material_name=getattr(material, "name", top.material_ref),
        product=products.get(getattr(material, "product_ref", None) or "", ""),
        thickness_in=top.thickness_m * _M_TO_IN, profile=top.profile,
        location=f"{top.room or top.storey}: over {', '.join(top.hosts)}",
        outline=ring, edge_kinds=kinds, radii_in=radii,
        length_in=0.0, depth_in=0.0, area_sqft=round(top.area_m2 * 10.7639104, 2),
        cutouts=cutouts, holes=holes, support=_support_note(model, top), holds=holds,
        mixed_edges=top.mixed_edges)  # the outline is already CCW: indices hold
    return _finish(piece)


def _stool_piece(model: ResolvedModel, stool: ResolvedWindowStool, materials
                 ) -> FabricatedPiece | None:
    wall = model.wall(stool.wall_tag)
    opening = next((item for item in model.openings if item.tag == stool.window_ref), None)
    ring_m = window_stool_ring(wall, opening, stool) if wall and opening else None
    if ring_m is None or stool.depth_m is None:
        return None
    radii_m = stool_ring_radii(stool.corner_radii_m, len(ring_m)) or (0.0,) * len(ring_m)
    to_local, ring, kinds, radii = _local_frame(ring_m, stool_edge_kinds(len(ring_m)),
                                                radii_m)
    material = materials.get(stool.material_ref)
    piece = FabricatedPiece(
        tag=stool.tag, uid=stool.uid, kind="stool", material_ref=stool.material_ref,
        material_name=getattr(material, "name", stool.material_ref),
        product=_products(model).get(getattr(material, "product_ref", None) or "", ""),
        thickness_in=stool.thickness_m * _M_TO_IN, profile=stool.profile,
        location=f"{stool.storey}: window {stool.window_ref} in {stool.wall_tag}",
        outline=ring, edge_kinds=kinds, radii_in=radii, length_in=0.0, depth_in=0.0,
        area_sqft=round(stool.length_m * stool.depth_m * 10.7639104, 2),
        holds=[TEMPLATE_HOLD, "Horns stop at the finished wall face; set the back edge to "
               "the delivered window's interior frame face.", *_notch_holds(model, stool),
               *(["The back tongue steps in at the sheathing face to clear the lined buck."]
                 if len(ring_m) == len(STOOL_EDGE_KINDS) else [])])
    return _finish(piece)


def _notch_holds(model: ResolvedModel, stool: ResolvedWindowStool) -> list[str]:
    if stool.notch_inset_m <= 0.0:
        return []
    if any(r.fabricated and r.window_ref == stool.window_ref for r in model.window_returns):
        return ["Shoulder notches take the frame's jambs, glued square: template with them."]
    return ["Shoulder notches wrap the finished drywall return, their inside radius matching "
            "its bullnose bead: template after the returns are beaded."]


def _return_pieces(model: ResolvedModel, reveal: ResolvedWindowReturn, ref: str,
                   thickness_m: float, materials) -> list[FabricatedPiece]:
    """A picture frame's head and jambs, front edge finished; each is a plain rectangle."""
    stool = next((s for s in model.window_stools if s.window_ref == reveal.window_ref), None)
    material = materials.get(ref)
    product = _products(model).get(getattr(material, "product_ref", None) or "", "")
    pieces = []
    for part in reveal.pieces:
        length, depth = part.length_m * _M_TO_IN, part.depth_m * _M_TO_IN
        holds = [RETURN_HOLD]
        if part.strip_width_m > 0.0:
            holds.append(f"Front edge built up with a {inches_text(thickness_m * _M_TO_IN)} x "
                         f"{inches_text(part.strip_width_m * _M_TO_IN)} x "
                         f"{part.strip_length_m * _M_TO_IN:.3f}\" strip over the buck lining.")
        area_m2 = part.length_m * part.depth_m + part.strip_length_m * part.strip_width_m
        pieces.append(_finish(FabricatedPiece(
            tag=f"{reveal.tag}-{part.edge}", uid=f"{reveal.uid}-{part.edge.upper()}",
            kind="return", material_ref=ref, material_name=getattr(material, "name", ref),
            product=product, thickness_in=thickness_m * _M_TO_IN,
            profile=stool.profile if stool is not None else "eased",
            location=f"{reveal.storey}: window {reveal.window_ref} reveal in {reveal.wall_tag}",
            outline=((0.0, 0.0), (length, 0.0), (length, depth), (0.0, depth)),
            edge_kinds=(EDGE_FINISHED, EDGE_SEAM, EDGE_WALL, EDGE_SEAM), radii_in=(0.0,) * 4,
            length_in=0.0, depth_in=0.0, area_sqft=round(area_m2 * 10.7639104, 2),
            holds=holds)))
    return pieces


def _finish(piece: FabricatedPiece) -> FabricatedPiece:
    """Overall size, clamped radii and narrowest webs, from the local outline."""
    xs = [x for x, _ in piece.outline]
    ys = [y for _, y in piece.outline]
    piece.length_in, piece.depth_in = max(xs) - min(xs), max(ys) - min(ys)
    piece.clamped_corners = tuple(f.index for f in piece.fillets if f.clamped)
    piece.webs = _webs(piece)
    if piece.webs:
        piece.holds.append(WEB_HOLD)
    return piece


def _local_frame(ring_m, kinds, radii_m):
    """(to_local, ring_in, kinds, radii_in): counter-clockwise, longest finished edge at +x."""
    ring = list(ring_m)
    kinds, radii = list(kinds), list(radii_m)
    if signed_area(ring) < 0.0:
        count = len(ring)
        ring = ring[::-1]
        radii = radii[::-1]
        kinds = [kinds[(count - 2 - j) % count] for j in range(count)]
    edges = [(math.dist(ring[i], ring[(i + 1) % len(ring)]), i) for i in range(len(ring))]
    finished = [edge for edge in edges if kinds[edge[1]] == EDGE_FINISHED]
    _, base = max(finished or edges)
    a, b = ring[base], ring[(base + 1) % len(ring)]
    angle = math.atan2(b[1] - a[1], b[0] - a[0])
    cos, sin = math.cos(-angle), math.sin(-angle)

    def rotate(point):  # type: ignore[no-untyped-def]
        x, y = point[0] - a[0], point[1] - a[1]
        return (x * cos - y * sin) * _M_TO_IN, (x * sin + y * cos) * _M_TO_IN

    turned = [rotate(point) for point in ring]
    min_x = min(x for x, _ in turned)
    min_y = min(y for _, y in turned)

    def to_local(point) -> PointIn:  # type: ignore[no-untyped-def]
        x, y = rotate(point)
        return (round(x - min_x, 6) + 0.0, round(y - min_y, 6) + 0.0)

    return (to_local, tuple(to_local(point) for point in ring), tuple(kinds),
            tuple(radius * _M_TO_IN for radius in radii))


def _webs(piece: FabricatedPiece) -> list[PieceWeb]:
    """For each cutout and hole, the narrowest stone to an edge or another opening."""
    slab = Polygon(piece.cut_ring())
    openings = [(f"cutout {cut.fixture_ref}", Polygon(cut.ring)) for cut in piece.cutouts]
    openings += [(f"{hole.purpose} hole", Point(hole.center).buffer(hole.diameter_in / 2.0))
                 for hole in piece.holes]
    webs: list[PieceWeb] = []
    for index, (label, shape) in enumerate(openings):
        candidates = [("slab edge", slab.exterior)]
        candidates += [(other, geom) for j, (other, geom) in enumerate(openings) if j != index]
        other, geom = min(candidates, key=lambda item: shape.distance(item[1]))
        a, b = nearest_points(shape, geom)
        webs.append(PieceWeb(f"{label} to {other}", shape.distance(geom),
                             (a.x, a.y), (b.x, b.y)))
    return webs


def _under_sink_holds(model: ResolvedModel, sink, top: ResolvedCountertop) -> list[str]:
    """An appliance hung under a cutout (a disposer) may want a deck pushbutton."""
    if sink is None:
        return []
    footprint = Polygon(sink.footprint)
    underside = None if sink.body_z1_m is None else sink.body_z1_m
    return [f"{obj.tag} ({obj.type_ref}) hangs under {sink.tag}: locate any deck pushbutton "
            "or air switch from its delivered template, not from this drawing."
            for obj in model.canvas_objects
            if obj.kind == "Appliance" and obj.storey == top.storey
            and len(obj.footprint) >= 3 and footprint.contains(Polygon(obj.footprint))
            and underside is not None and obj.body_z1_m is not None
            and obj.body_z1_m <= underside + 1e-6]


def _support_note(model: ResolvedModel, top: ResolvedCountertop) -> str:
    """What carries a cantilever: the authored support and the members under the slab."""
    if top.unsupported_overhang_m <= top.overhang_m + 1e-6 and top.support == "none":
        return ""  # the ordinary oversail past the doors, not a cantilever
    overhang = top.unsupported_overhang_m * _M_TO_IN
    authored = model.plan.by_tag(top.tag)
    band = getattr(authored, "cantilever_length", None)
    where = (f" along the first {band.meters * _M_TO_IN:g}\" of the run" if band is not None
             else "")
    if top.support == "none":
        return f'{overhang:.2f}" cantilever{where}, unsupported.'
    slab = Polygon(top.outline)
    underside = max((obj.body_z1_m for obj in model.canvas_objects
                     if obj.tag in top.hosts and obj.body_z1_m is not None),
                    default=None)
    members: dict[str, int] = {}
    if underside is not None:
        underside -= top.thickness_m
        for obj in model.canvas_objects:
            if (obj.tag not in top.hosts and obj.storey == top.storey
                    and obj.body_z1_m is not None and len(obj.footprint) >= 3
                    and abs(obj.body_z1_m - underside) <= 0.0127
                    and slab.intersects(Polygon(obj.footprint))):
                members[obj.type_ref or obj.tag] = members.get(obj.type_ref or obj.tag, 0) + 1
    carried = ", ".join(f"{count} x {ref}" for ref, count in sorted(members.items()))
    return (f'{overhang:.2f}" cantilever{where}, carried on {top.support}'
            + (f" ({carried}, under the slab)" if carried else "") + ".")

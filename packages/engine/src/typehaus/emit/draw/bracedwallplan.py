"""S-1xx — the braced wall plan, per floor (→ 30 §Structural).

MNSPECT's most-cited residential omission, and this set had none. A braced wall plan states
four things per floor: where the braced wall **lines** are, where the **panels** on each
line are, how **wide** each panel is, and which IRC R602.10.4 **method** it is built to
(CS-WSP, WSP, PFH...). A discrete braced-wall inspection is run against it.

**What this sheet can honestly draw, and what it cannot.** A spike over catlin's resolved
model answered that, and the answer shaped this module:

*Lines are derivable.* ``resolve/layout_lines.py`` already builds the collinear, stacked
chains a braced wall line is — 63 of them here — and every wall names its assembly, so the
sheathing that would qualify a line for a method is known.

*Panels and methods are NOT derivable, and no amount of care makes them so.* A panel is a
designer's decision about where to spend bracing, and its method carries hold-down,
fastening and hold-down-free-corner requirements that no field in this model expresses. So
this sheet draws the LINES and states, per line, the method its construction could support
and the length available — and says plainly that the panels are not modelled. That is a
useful drawing and an honest one; a sheet that invented panel positions would be neither.

**``structural_role`` is not the input, and the plan for this work assumed it was.** Every
one of catlin's 174 walls carries ``structural_role=None`` — the field exists and the house
authors it nowhere. Lines are identified here by what is actually known: a chain that
carries a wall on the building's exterior envelope, which is where R602.10 requires bracing
first and where every line on this house's perimeter is.
"""

from __future__ import annotations

from dataclasses import dataclass

from typehaus.emit.draw._shared import emit_ghost_walls, to_in
from typehaus.emit.draw.lineweights import CUT_HEAVY
from typehaus.emit.draw.scene import Polyline, Scene, SceneBuilder, Text
from typehaus.emit.draw.typography import DIM_TEXT_PT
from typehaus.quantities import M_PER_IN

BWL_LAYER = "S-WALL-BRCE"

#: Wood structural panel sheathing, by the material refs a house actually uses. A method is
#: a property of what is fastened to the studs, so this is the one lookup that decides which
#: R602.10.4 row a line could be built to.
#:
#: ``siding-303-mdo`` joined on 2026-09-11 and is the one entry that is not a sheathing grade:
#: APA Rated Siding 303 is a wood structural panel with published shear values (SDPWS Table
#: 4.3B), sold as a finished face. `ENTRY_SCREEN_WALL` carries it on its sheltered east face
#: opposite 5/8" CDX, and without this row the union below saw two materials, one unknown, and
#: called the whole line "not rated" — a false statement about a line whose west face alone is
#: ordinary CDX. What this row does NOT do is count that face: bracing LENGTH still comes from
#: panels, which are not modelled, so the line stays UNKNOWN either way.
_WSP_MATERIALS = frozenset({
    "struct-1-plywood", "cdx-plywood", "cdx", "osb", "zip-sheathing", "plywood",
    "siding-303-mdo",
})

#: IRC R602.10.4 method names, as a plan reviewer reads them.
METHOD_WSP = "WSP"
METHOD_CS_WSP = "CS-WSP"
METHOD_UNRATED = "not rated"


@dataclass(frozen=True)
class BracedWallLine:
    """One derived line: where it runs, how long, and what method its build could support.

    ``method`` is deliberately "could support", not "is". Whether a line is CS-WSP rather
    than WSP turns on continuous sheathing over the WHOLE line including above and below
    openings, which is a construction decision this model does not record; whether it meets
    R602.10.3's required length turns on panels, which are not modelled at all.
    """

    tag: str
    storey: str
    direction: str                     #: "x" or "y"
    p0: tuple[float, float]            #: metres
    p1: tuple[float, float]
    length_m: float
    method: str
    wall_tags: tuple[str, ...]

    @property
    def length_ft(self) -> float:
        return self.length_m / M_PER_IN / 12.0


def braced_wall_lines(model, storey: str) -> list[BracedWallLine]:
    """Derived braced wall lines for one storey, longest first.

    A line is a layout-line chain whose walls stand on the building's exterior envelope.
    Interior partitions are excluded not because they never brace — they can — but because
    identifying WHICH interior line is a braced wall line is exactly the designer's decision
    this module refuses to invent.
    """
    walls = {wall.tag: wall for wall in model.walls if wall.storey == storey}
    lines: list[BracedWallLine] = []
    for line in model.layout_lines:
        tags = tuple(sorted({m.wall_tag for m in line.members
                             if m.wall_tag in walls}))
        if not tags:
            continue
        members = [walls[tag] for tag in tags]
        if not any(_is_envelope(wall) and _is_light_frame(wall) for wall in members):
            continue
        span = _span(members)
        if span is None:
            continue
        p0, p1, length = span
        lines.append(BracedWallLine(
            tag=f"BWL-{line.tag.removeprefix('LL-')}", storey=storey,
            direction="x" if abs(p1[0] - p0[0]) >= abs(p1[1] - p0[1]) else "y",
            p0=p0, p1=p1, length_m=length, method=_method(members), wall_tags=tags))
    return sorted(lines, key=lambda item: (-item.length_m, item.tag))


def _is_envelope(wall) -> bool:
    """On the building's weather envelope — the walls R602.10 braces first.

    Tested on the assembly tag's ``INT`` token, which is how this house already takes an
    interior assembly out of the envelope everywhere else (``mn_energy``, and the ENVELOPE
    block on G-002). One rule, not a third spelling of it.
    """
    assembly = getattr(wall, "assembly", "") or ""
    return bool(assembly) and "INT" not in assembly and "PARTITION" not in assembly


def _is_light_frame(wall) -> bool:
    """R602 is the LIGHT-FRAME chapter, and a poured wall is not in it.

    Without this the basement reported 23 lines, most of them foundation walls and the
    sunken garden's retaining walls: a concrete wall braces by being concrete, and a braced
    wall panel is a thing you fasten to studs. Tested on whether the wall resolved framing
    members, which is the model's own answer to "is this stick-built" — an assembly whose
    structure layer carries no FramingSpec frames monolithically and resolves none.
    """
    return bool(getattr(wall, "members", ()))


def _method(walls) -> str:
    """The R602.10.4 method these walls' sheathing could support.

    Only the two panel methods, and only where every wall on the line carries a wood
    structural panel: a line whose sheathing changes part-way is not one method, and saying
    which of the two it is would need the continuity this model does not record.
    """
    materials = {layer.material_ref for wall in walls for layer in wall.layers
                 if layer.function == "sheathing"}
    if materials and materials <= _WSP_MATERIALS:
        return METHOD_WSP
    return METHOD_UNRATED


def _span(walls):
    """``(p0, p1, length)`` of the chain's outermost endpoints, or ``None``."""
    points = [point for wall in walls for point in (wall.axis[0], wall.axis[1])]
    if len(points) < 2:
        return None
    p0 = min(points, key=lambda p: (p[0], p[1]))
    p1 = max(points, key=lambda p: (p[0], p[1]))
    length = ((p1[0] - p0[0]) ** 2 + (p1[1] - p0[1]) ** 2) ** 0.5
    return (p0, p1, length) if length > 0.0 else None


def has_braced_wall_content(model, storey: str) -> bool:
    return bool(braced_wall_lines(model, storey))


def build_braced_wall_plan(model, storey: str) -> Scene:
    """The sheet: ghosted walls, the lines drawn heavy, each tagged with its length."""
    b = SceneBuilder(name=f"braced-wall-{storey}", units="in")
    emit_ghost_walls(b, model, storey)
    lines = braced_wall_lines(model, storey)
    for line in lines:
        b.add(Polyline(points=(to_in(line.p0), to_in(line.p1)),
                       layer=BWL_LAYER, lineweight=CUT_HEAVY, tag=line.tag))
        mid = ((line.p0[0] + line.p1[0]) / 2.0, (line.p0[1] + line.p1[1]) / 2.0)
        b.add(Text(anchor=to_in(mid),
                   content=f"{line.tag}  {line.length_ft:.1f}'  {line.method}",
                   height_pt=DIM_TEXT_PT, layer=BWL_LAYER, align="center"))
    # The sheet says what it does not know, on the sheet. A braced wall plan with no panels
    # on it that does not say so would read as a plan with no bracing required.
    if lines:
        b.add(Text(anchor=(0.0, -48.0), content=_DISCLAIMER, height_pt=DIM_TEXT_PT,
                   layer=BWL_LAYER, align="left"))
    return b.build()


#: Printed on every braced wall sheet, and it is the whole honesty of this drawing.
_DISCLAIMER = (
    "BRACED WALL LINES SHOWN. PANELS ARE NOT MODELLED: panel positions, widths and "
    "R602.10.4 methods are the designer's, and this set does not carry them. "
    "structural.braced_wall_panels reports UNKNOWN until they are authored."
)

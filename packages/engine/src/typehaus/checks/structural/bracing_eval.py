"""One reading of R602.10 for one braced wall line — required, provided, and every row read.

The check (``braced_wall.py``, ``braced_wall_panels.py``) and the S-103 sheet
(``emit/draw/bracedwallplan.py``) both read this, so the drawing and the verdict cannot
disagree about what the line needs.

**Where the numbers come from, measured, never authored.** The story location is derived
(how many braced stories stand above this one in the same building); the wall height is the
line's own plates; the eave-to-ridge height is the ridge above the TOP OF THE TOPMOST
BRACED STORY'S WALL, not the roof's own eave, because everything between that plate and the
ridge is wind area the top story's bracing carries (decision #79 — catlin's habitable attic
is not a story, and its gable walls ride this factor); the line spacing is the distance to
the parallel lines beside it; the number of lines is counted per plan direction.

**A factor not taken is printed with its reason.** The 0.80 hold-down credit is an
intermittent-method credit and a continuously sheathed line cannot have it; the 1.40 gypsum
penalty IS taken where the panels on a line carry no gypsum inside (catlin's plant room);
the 2.00 no-blocking penalty applies only where the sheathing has a horizontal joint to
block, which a 9'-0" wall sheathed in one 9'-0" sheet does not.
"""

from __future__ import annotations

from dataclasses import dataclass

from typehaus.checks.structural.bracing_tables import (
    GYPSUM_OMITTED_FACTOR,
    GYPSUM_OMITTED_METHODS,
    HOLD_DOWN_FACTOR,
    HOLD_DOWN_FACTOR_METHODS,
    NO_BLOCKING_FACTOR,
    NO_BLOCKING_METHODS,
    STORY_FIRST_OF_THREE,
    STORY_FIRST_OF_TWO,
    STORY_TOP,
    TableRead,
    eave_to_ridge_factor,
    exposure_factor,
    line_count_factor,
    min_panel_length_in,
    required_bracing_length_ft,
    wall_height_factor,
)
from typehaus.quantities import M_PER_IN
from typehaus.resolve.braced_walls import (
    KIND_BRACED,
    BracedWallLine,
    ResolvedPanel,
    braced_wall_lines,
    resolved_braced_wall_panels,
)
from typehaus.wind import wind_basis

#: A sheet reaches the plate without a horizontal joint up to this wall height (10'-0"
#: sheathing is a stocked length). Above it, R602.10.3(2) item 8's blocking question is
#: real; at or below it there is no horizontal joint to block. Not a code number — the
#: code says "where horizontal blocking is omitted" and says nothing about sheet stock.
SINGLE_SHEET_WALL_HEIGHT_IN = 120.0

_GYPSUM_MATERIALS = frozenset({"gwb", "gypsum", "gypsum-board", "type-x-gwb", "gwb-type-x"})


@dataclass(frozen=True)
class PanelGrade:
    """One merged panel, against R602.10.5's minimum length."""

    panel: ResolvedPanel
    minimum: TableRead | None
    contributes_in: float
    reason: str = ""


@dataclass(frozen=True)
class LineEvaluation:
    """What R602.10.3 asks of one line, what stands on it, and every row read."""

    line: BracedWallLine
    story_location: str
    base: TableRead | None
    factors: tuple[TableRead, ...]
    not_taken: tuple[str, ...]
    panels: tuple[PanelGrade, ...]
    gaps: tuple[str, ...]

    @property
    def required_ft(self) -> float | None:
        if self.base is None or self.gaps:
            return None
        value = self.base.value
        for factor in self.factors:
            value *= factor.value
        return value

    @property
    def provided_ft(self) -> float:
        return sum(g.contributes_in for g in self.panels) / 12.0

    @property
    def ok(self) -> bool:
        required = self.required_ft
        return required is not None and self.provided_ft >= required - 1e-6

    def describe(self) -> str:
        required = self.required_ft
        if required is None:
            return "required length not determined: " + "; ".join(self.gaps)
        return (f"{self.provided_ft:.2f} ft provided against {required:.2f} ft required "
                f"({len(self.panels)} panel(s))")


# --- story location ---------------------------------------------------------------------

def braced_storeys(model, building: str) -> list[str]:
    """The storeys of one building that owe R602.10 a braced wall length, low to high.

    This is the STORY COUNT the tables are indexed on, and it is derived: a concrete
    basement box, a rafter-plate attic and a habitable attic (IRC R325.6: "shall not be
    considered a story") all drop out of it because none of them carries a ``braced`` line.
    """
    storeys = [s for s in model.plan.storeys if s.building == building]
    out = []
    for storey in sorted(storeys, key=lambda s: s.elevation.meters):
        if any(line.kind == KIND_BRACED for line in braced_wall_lines(model, storey.tag)):
            out.append(storey.tag)
    return out


def story_location(model, storey: str) -> tuple[str | None, str]:
    """``(the R602.10.3(1) row, the sentence that derives it)`` for one storey."""
    here = model.plan.storey(storey)
    if here is None:
        return None, f"{storey} is not a storey of this plan"
    stack = braced_storeys(model, here.building)
    if storey not in stack:
        return None, f"{storey} carries no braced wall line"
    above = len(stack) - stack.index(storey) - 1
    row = {0: STORY_TOP, 1: STORY_FIRST_OF_TWO, 2: STORY_FIRST_OF_THREE}.get(above)
    words = (f"building '{here.building}' is {len(stack)} story/stories for R602.10 "
             f"({', '.join(stack)}); {storey} carries {above} braced story/stories above it")
    if row is None:
        return None, words + " — past Table R602.10.3(1)'s three story rows"
    return row, words


_SUPPORTS = {STORY_TOP: "roof_only", STORY_FIRST_OF_TWO: "roof_plus_1_floor",
             STORY_FIRST_OF_THREE: "roof_plus_2_floors"}


# --- the evaluation ---------------------------------------------------------------------

def evaluate_storey(model, storey: str) -> list[LineEvaluation]:
    lines = braced_wall_lines(model, storey)
    panels, _unplaced = resolved_braced_wall_panels(model, storey, lines)
    return [evaluate_line(model, line, lines, panels) for line in lines
            if line.kind == KIND_BRACED]


def evaluate_line(model, line: BracedWallLine, lines: list[BracedWallLine],
                  panels: list[ResolvedPanel]) -> LineEvaluation:
    mine = [p for p in panels if p.line_tag == line.tag]
    row, story_words = story_location(model, line.storey)
    gaps: list[str] = []
    basis = wind_basis(model.plan.project.site)
    if basis is None:
        gaps.append("the site carries no design wind speed and exposure")
    if row is None:
        gaps.append(story_words)
    method = mine[0].method if mine else "CS-WSP"
    wall_height_in = _wall_height_in(model, line)
    spacing = _line_spacing_ft(line, lines)
    if spacing is None:
        gaps.append(f"{line.tag} has no parallel braced wall line to be spaced from")
    count = len([o for o in lines if o.direction == line.direction
                 and o.kind == KIND_BRACED])
    eave = _eave_to_ridge_ft(model, line.storey)
    if eave is None:
        gaps.append("no roof over this storey's building, so the eave-to-ridge height "
                    "cannot be measured")
    base = None
    factors: list[TableRead] = []
    not_taken: list[str] = []
    if not gaps:
        assert basis is not None and row is not None and spacing is not None
        base = required_bracing_length_ft(row, spacing, basis.speed_mph, method)
        if base is None:
            gaps.append(f"Table R602.10.3(1) publishes no cell for {method} at "
                        f"{basis.speed_mph:.0f} mph and {spacing:.1f} ft spacing")
        else:
            factors = _factors(model, line, mine, basis, row, eave or 0.0, wall_height_in,
                               count, method, not_taken, gaps)
    graded = tuple(_grade_panel(p, wall_height_in) for p in mine)
    return LineEvaluation(line=line, story_location=row or "", base=base,
                          factors=tuple(factors), not_taken=tuple(not_taken),
                          panels=graded, gaps=tuple(gaps))


def _factors(model, line, panels, basis, row, eave_ft, wall_height_in, count, method,
             not_taken: list[str], gaps: list[str]) -> list[TableRead]:
    factors: list[TableRead] = []
    stories = len(braced_storeys(model, model.plan.storey(line.storey).building))
    for read, what in (
        (exposure_factor(basis.exposure, stories), f"exposure {basis.exposure}"),
        (eave_to_ridge_factor(eave_ft, _SUPPORTS[row]), "eave-to-ridge height"),
        (wall_height_factor(wall_height_in / 12.0), "wall height"),
        (line_count_factor(count), "braced wall line count"),
    ):
        if read is None:
            gaps.append(f"Table R602.10.3(2) has no {what} row for this line")
        else:
            factors.append(read)
    if method in GYPSUM_OMITTED_METHODS:
        bare = _panels_without_gypsum(model, line, panels)
        if bare:
            factors.append(TableRead(GYPSUM_OMITTED_FACTOR, (
                f"Table R602.10.3(2) item 6, interior gypsum board omitted from the inside "
                f"face of {', '.join(bare)}: x{GYPSUM_OMITTED_FACTOR:.2f}")))
        else:
            not_taken.append("item 6 (x1.40, gypsum omitted) is NOT taken: every panel on "
                             "this line carries gypsum board on its inside face")
    if method in NO_BLOCKING_METHODS:
        if wall_height_in <= SINGLE_SHEET_WALL_HEIGHT_IN:
            not_taken.append(
                f"item 8 (x2.00, horizontal blocking omitted) is NOT taken: the wall is "
                f"{wall_height_in:.1f} in and a single sheet reaches the plate, so there is "
                f"no horizontal sheathing joint to block")
        else:
            factors.append(TableRead(NO_BLOCKING_FACTOR, (
                f"Table R602.10.3(2) item 8, horizontal blocking at the sheathing joint in "
                f"a {wall_height_in:.1f} in wall is not modelled: "
                f"x{NO_BLOCKING_FACTOR:.2f}")))
    if method in HOLD_DOWN_FACTOR_METHODS:
        not_taken.append(f"item 5 (x{HOLD_DOWN_FACTOR:.2f}, an additional 800-lb hold-down "
                         f"at each panel end) is NOT taken: it is a top-story credit and "
                         f"this model does not claim a device at every panel end")
    else:
        not_taken.append(f"item 5 (x{HOLD_DOWN_FACTOR:.2f}, an additional 800-lb hold-down "
                         f"at each panel end) does not reach method {method}: it is "
                         f"published for the intermittent methods only")
    return factors


def _panels_without_gypsum(model, line, panels) -> list[str]:
    walls = {w.tag: w for w in model.walls if w.storey == line.storey}
    bare = []
    for panel in panels:
        for tag in panel.wall_tags:
            wall = walls.get(tag)
            if wall is None:
                continue
            if not any(layer.material_ref in _GYPSUM_MATERIALS for layer in wall.layers
                       if layer.function == "finish"):
                bare.append(tag)
    return sorted(set(bare))


def _grade_panel(panel: ResolvedPanel, wall_height_in: float) -> PanelGrade:
    minimum = min_panel_length_in(panel.method, wall_height_in / 12.0,
                                  panel.adjacent_opening_height_in)
    if minimum is None:
        return PanelGrade(panel, None, 0.0,
                          f"Table R602.10.5 publishes no minimum length for "
                          f"{panel.method} at this wall height and opening height")
    if panel.length_in + 1e-6 < minimum.value:
        return PanelGrade(panel, minimum, 0.0,
                          f"{panel.length_in:.1f} in is under the {minimum.value:.0f} in "
                          f"minimum, so it contributes 0 ft")
    return PanelGrade(panel, minimum, panel.length_in)


def _wall_height_in(model, line: BracedWallLine) -> float:
    """The line's wall height: top of top plate to bottom of bottom plate, tallest wall."""
    heights = []
    for wall in model.walls:
        if wall.tag not in line.wall_tags:
            continue
        plates = [m for m in wall.members if m.category == "plate"]
        if plates:
            heights.append(max(m.z1_m for m in plates) - min(m.z0_m for m in plates))
        else:
            heights.append(wall.z1_m - wall.z0_m)
    return (max(heights) if heights else 0.0) / M_PER_IN


def _line_spacing_ft(line: BracedWallLine, lines: list[BracedWallLine]) -> float | None:
    """The larger of the distances to the parallel braced wall lines either side of it."""
    parallel = [o for o in lines if o.direction == line.direction
                and o.kind == KIND_BRACED and o.tag != line.tag]
    if not parallel:
        return None
    here = _offset(line)
    gaps = [abs(_offset(o) - here) for o in parallel]
    before = [g for g, o in zip(gaps, parallel, strict=True) if _offset(o) < here]
    after = [g for g, o in zip(gaps, parallel, strict=True) if _offset(o) > here]
    neighbours = [min(side) for side in (before, after) if side]
    return max(neighbours) / M_PER_IN / 12.0 if neighbours else None


def _offset(line: BracedWallLine) -> float:
    """Where the line sits ACROSS its own direction — a line running in x is located by y."""
    return line.p0[1] if line.direction == "x" else line.p0[0]


def _eave_to_ridge_ft(model, storey: str) -> float | None:
    """Ridge above the top of the topmost braced storey's wall, for this building.

    Measured from the WALL, not from the roof's own eave: at catlin the habitable attic
    stands 10 ft of gable wall and 9 ft of roof above the second storey's top plate, and all
    of it is wind area that the second storey's bracing carries.
    """
    here = model.plan.storey(storey)
    if here is None:
        return None
    building = here.building
    storey_tags = {s.tag for s in model.plan.storeys if s.building == building}
    ridges = [roof.ridge_z_m for roof in model.roofs if roof.storey in storey_tags]
    if not ridges:
        return None
    stack = braced_storeys(model, building)
    tops = []
    for wall in model.walls:
        if wall.storey != (stack[-1] if stack else storey):
            continue
        plates = [m for m in wall.members if m.category == "plate"]
        if plates:
            tops.append(max(m.z1_m for m in plates))
    if not tops:
        return None
    return (max(ridges) - max(tops)) / M_PER_IN / 12.0

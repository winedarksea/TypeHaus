"""S-101 content derivation: the framed level's load path, its schedules, and its gaps.

Reads one ``ResolvedFloor`` and the authored elements around it — the deck's joists, the
walls that carry it, the beams and posts under those, the headers in the walls below — and
returns keyed schedule rows plus :class:`Finding` records for the datums a framing permit
sheet needs that the model does not carry (braced-wall lines above all). Drawing lives in
``framingplan``; nothing here touches the IR.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace

from typehaus.emit.draw.schedule_block import ScheduleTable
from typehaus.emit.draw.structural_common import feet_inches, wall_center
from typehaus.findings import Finding, Result, Severity
from typehaus.model.enums import StructuralRole
from typehaus.model.floors import FloorSystem
from typehaus.resolve.framing.tables import DEFAULT_SPACING
from typehaus.resolve.geometry import opening_center
from typehaus.resolve.model import ResolvedFloor, ResolvedModel, ResolvedWall

# JoistSpec leaves spacing unset when the solver's residential default applies; read that
# default from the framing tables rather than restating it, so the sheet cannot drift from
# the joists the resolver actually generated (→ resolve.framing.tables).
DEFAULT_JOIST_SPACING_IN = DEFAULT_SPACING.inches
# A header's midpoint and its opening's centre coincide to well within a jack stud.
HEADER_TO_OPENING_TOLERANCE_M = 0.2
# Plan-view member categories, in the order a schedule reads them.
MEMBER_CATEGORY_TITLES = (
    ("joist", "J", "FLOOR JOIST"),
    ("trimmer", "TR", "TRIMMER JOIST"),
    ("header", "FH", "FLOOR OPENING HEADER"),
    ("rim", "R", "RIM BOARD"),
    ("blocking", "BL", "BLOCKING"),
)


@dataclass(frozen=True)
class FramedLevel:
    """Everything S-101 draws and schedules for one framed deck."""

    floor: ResolvedFloor
    system: FloorSystem
    bearing_storey: str | None
    declared_bearing_walls: tuple[ResolvedWall, ...] = ()
    role_bearing_walls: tuple[ResolvedWall, ...] = ()
    beams: tuple = ()   # (authored Beam, span_m)
    posts: tuple = ()   # authored Post
    headers: tuple = ()  # (ResolvedWall, FramedMember, opening tag or "")
    connectors: tuple = ()  # authored Connector
    marks: dict = field(default_factory=dict)  # element/child tag -> mark


def framed_level(model: ResolvedModel, floor_tag: str) -> FramedLevel | None:
    """Assemble the level's framing content, or ``None`` when the tag is not a framed deck."""
    floor = next((item for item in model.floors if item.tag == floor_tag), None)
    if floor is None:
        return None
    system = model.plan.by_tag(floor_tag)
    if not isinstance(system, FloorSystem):
        return None  # defensive; every ResolvedFloor is sourced from a FloorSystem

    declared = tuple(wall for tag in system.joists.bearing_refs
                     if (wall := model.wall(tag)) is not None)
    bearing_storey = declared[0].storey if declared else None
    role_walls = tuple(wall for wall in model.walls
                       if wall.storey == bearing_storey and _is_bearing_role(model, wall)
                       and wall not in declared)
    beams = _load_path_beams(model, system)
    posts = _load_path_posts(model, beams)
    headers = _wall_headers(model, (*declared, *role_walls))
    connectors = tuple(element for element in model.plan.all_elements()
                       if element.element_kind == "Connector"
                       and _connects_any(element, declared, beams, posts))
    level = FramedLevel(floor=floor, system=system, bearing_storey=bearing_storey,
                        declared_bearing_walls=declared, role_bearing_walls=role_walls,
                        beams=beams, posts=posts, headers=headers, connectors=connectors)
    return replace(level, marks=_assign_marks(level))


def _is_bearing_role(model: ResolvedModel, wall: ResolvedWall) -> bool:
    authored = model.plan.by_tag(wall.tag)
    return getattr(authored, "structural_role", None) is StructuralRole.BEARING


def _load_path_beams(model: ResolvedModel, system: FloorSystem) -> tuple:
    """Beams the deck declares it bears on, with their measured span."""
    out = []
    for tag in system.joists.bearing_refs:
        element = model.plan.by_tag(tag)
        if element is None or element.element_kind != "Beam":
            continue
        out.append((element, _beam_span_m(model, element)))
    return tuple(sorted(out, key=lambda item: item[0].tag))


def _beam_span_m(model: ResolvedModel, beam) -> float:
    start, end = model.plan.by_tag(beam.start_node), model.plan.by_tag(beam.end_node)
    if start is None or end is None:
        return 0.0
    (x0, y0), (x1, y1) = start.position.xy_m, end.position.xy_m
    return ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5


def _load_path_posts(model: ResolvedModel, beams: tuple) -> tuple:
    """The posts those beams bear on — the next link down the load path."""
    tags = {ref for beam, _span in beams for ref in beam.bearing_refs}
    posts = [model.plan.by_tag(tag) for tag in sorted(tags)]
    return tuple(post for post in posts if post is not None and post.element_kind == "Post")


def _wall_headers(model: ResolvedModel, walls: tuple) -> tuple:
    out = []
    for wall in walls:
        for member in wall.members:
            if member.category != "header":
                continue
            out.append((wall, member, _opening_for_header(model, wall, member)))
    return tuple(out)


def _opening_for_header(model: ResolvedModel, wall: ResolvedWall, member) -> str:
    """Name the opening a header spans by matching midpoints along the wall axis."""
    midpoint = ((member.p0[0] + member.p1[0]) / 2.0, (member.p0[1] + member.p1[1]) / 2.0)
    for opening in model.openings:
        if opening.host_wall != wall.tag:
            continue
        center = opening_center(wall, opening)
        if center is None:
            continue
        if (abs(center[0] - midpoint[0]) + abs(center[1] - midpoint[1])
                < HEADER_TO_OPENING_TOLERANCE_M):
            return opening.tag
    return ""


def _connects_any(connector, walls: tuple, beams: tuple, posts: tuple) -> bool:
    known = {wall.tag for wall in walls} | {beam.tag for beam, _ in beams} | {p.tag for p in posts}
    return bool(set(connector.connects) & known)


def _assign_marks(level: FramedLevel) -> dict:
    marks: dict = {}
    for category, prefix, _title in MEMBER_CATEGORY_TITLES:
        if any(member.category == category for member in level.floor.members):
            marks[f"category:{category}"] = f"{prefix}1"
    for index, (beam, _span) in enumerate(level.beams, start=1):
        marks[beam.tag] = f"B{index}"
    for index, post in enumerate(level.posts, start=1):
        marks[post.tag] = f"P{index}"
    header_keys: dict[tuple, str] = {}
    for wall, member, _opening in level.headers:
        key = (member.profile, round(member.length_m, 2))
        mark = header_keys.setdefault(key, f"H{len(header_keys) + 1}")
        marks[f"{wall.tag}/{member.child_key}"] = mark
    return marks


def joist_spacing_in(system: FloorSystem) -> float:
    return (system.joists.spacing.inches if system.joists.spacing is not None
            else DEFAULT_JOIST_SPACING_IN)


def joist_label(system: FloorSystem) -> str:
    return f'{system.joists.member.upper()} @ {joist_spacing_in(system):.0f}" O.C.'


def build_framing_schedules(level: FramedLevel) -> list[ScheduleTable]:
    """The keyed S-101 schedules: deck members, beams/posts, headers, connectors."""
    tables = [_member_schedule(level), _beam_post_schedule(level), _header_schedule(level),
              _connector_schedule(level)]
    return [table for table in tables if table.rows]


def _member_schedule(level: FramedLevel) -> ScheduleTable:
    spacing = f'{joist_spacing_in(level.system):.0f}" O.C.'
    rows: list[tuple[str, ...]] = []
    for category, _prefix, title in MEMBER_CATEGORY_TITLES:
        members = [m for m in level.floor.members if m.category == category]
        if not members:
            continue
        rows.append((
            level.marks[f"category:{category}"], title, members[0].profile,
            spacing if category in ("joist", "trimmer") else "—",
            str(len(members)),
            feet_inches(max(member.length_m for member in members)),
        ))
    return ScheduleTable(title=f"{level.floor.tag} MEMBER SCHEDULE",
                         columns=("MARK", "MEMBER", "SIZE", "SPACING", "QTY", "MAX SPAN"),
                         rows=tuple(rows))


def _beam_post_schedule(level: FramedLevel) -> ScheduleTable:
    rows: list[tuple[str, ...]] = []
    for beam, span in level.beams:
        rows.append((level.marks[beam.tag], beam.tag, "BEAM", beam.size, feet_inches(span),
                     ", ".join(beam.bearing_refs) or "—"))
    for post in level.posts:
        height = feet_inches(post.height.meters) if post.height is not None else "—"
        rows.append((level.marks[post.tag], post.tag, "POST", post.size, height,
                     post.supported_by or "—"))
    return ScheduleTable(title="BEAM / POST SCHEDULE (LOAD PATH)",
                         columns=("MARK", "TAG", "TYPE", "SIZE", "SPAN/HT", "BEARS ON"),
                         rows=tuple(rows))


def _header_schedule(level: FramedLevel) -> ScheduleTable:
    grouped: dict[str, list[tuple]] = {}
    for wall, member, opening in level.headers:
        grouped.setdefault(level.marks[f"{wall.tag}/{member.child_key}"], []).append(
            (wall, member, opening))
    rows: list[tuple[str, ...]] = []
    for mark, items in sorted(grouped.items(), key=lambda item: int(item[0][1:])):
        _wall, member, _opening = items[0]
        over = ", ".join(sorted({opening or wall.tag for wall, _m, opening in items}))
        rows.append((mark, member.profile, feet_inches(member.length_m), str(len(items)),
                     _abbreviate(over)))
    return ScheduleTable(title="HEADER SCHEDULE — BEARING WALLS BELOW",
                         columns=("MARK", "SIZE", "SPAN", "QTY", "OVER"),
                         rows=tuple(rows))


def _connector_schedule(level: FramedLevel) -> ScheduleTable:
    rows = [(connector.tag, connector.kind.value.replace("_", " ").upper(),
             connector.size or "—", ", ".join(connector.connects) or "—")
            for connector in sorted(level.connectors, key=lambda item: item.tag)]
    return ScheduleTable(title="CONNECTOR SCHEDULE",
                         columns=("TAG", "KIND", "PRODUCT", "JOINS"), rows=tuple(rows))


def _abbreviate(text: str, limit: int = 44) -> str:
    return text if len(text) <= limit else text[: limit - 1] + "…"


def framing_general_notes(model: ResolvedModel, level: FramedLevel) -> list[str]:
    """Sheet notes derived from the deck spec, the declared bearing, and the subfloor."""
    notes = [f"{level.floor.tag}: {joist_label(level.system)}, SPANNING "
             f"{level.floor.direction.upper()} — ARROWS SHOW SPAN DIRECTION."]
    if level.system.subfloor is not None:
        deck = level.system.subfloor
        notes.append(f"SUBFLOOR: {deck.thickness.inches:.2f}\" {deck.material_ref.upper()} "
                     "GLUED AND FASTENED TO JOISTS.")
    if level.declared_bearing_walls or level.beams:
        carried = ", ".join(sorted([wall.tag for wall in level.declared_bearing_walls]
                                   + [beam.tag for beam, _ in level.beams]))
        notes.append(f"DECK BEARS ON: {carried}.")
    if level.role_bearing_walls:
        notes.append("ADDITIONAL WALLS BELOW DECLARED BEARING (DO NOT REMOVE): "
                     + ", ".join(sorted(wall.tag for wall in level.role_bearing_walls)) + ".")
    notes.append("MEMBER SIZES ARE THE AUTHORED / SOLVER-GENERATED FRAMING; SPANS ARE "
                 "MEASURED FROM THE RESOLVED MODEL AND ARE NOT AN ENGINEERED DESIGN.")
    return notes


def framing_sheet_findings(model: ResolvedModel, level: FramedLevel) -> list[Finding]:
    """Permit-set datums S-101 must show that the model does not carry."""
    findings = [Finding(
        severity=Severity.WARN, check_id="sheet.framing.braced_wall_lines",
        message="braced-wall / shear lines are not modelled — Wall.structural_role carries "
                "bearing intent only, with no bracing method, line spacing, or panel length",
        element_tags=(level.floor.tag,), result=Result.UNKNOWN,
        fix_hint="add a BracedWallLine element (method, length, holdowns) so S-101 can key "
                 "the lines and their panels",
    )]
    if not level.declared_bearing_walls and not level.beams:
        findings.append(Finding(
            severity=Severity.WARN, check_id="sheet.framing.bearing_undeclared",
            message="floor system declares no bearing refs, so the sheet cannot show what "
                    "carries this deck", element_tags=(level.floor.tag,),
            result=Result.UNKNOWN,
            fix_hint="set JoistSpec.bearing_refs on the FloorSystem"))
    unmatched = [f"{wall.tag}/{member.child_key}"
                 for wall, member, opening in level.headers if not opening]
    if unmatched:
        findings.append(Finding(
            severity=Severity.WARN, check_id="sheet.framing.header_opening_unmatched",
            message="header could not be keyed to an opening, so the schedule names its wall "
                    "instead", element_tags=tuple(unmatched), result=Result.UNKNOWN))
    if not any(member.category == "blocking" for member in level.floor.members):
        findings.append(Finding(
            severity=Severity.WARN, check_id="sheet.framing.joist_blocking",
            message="no blocking/bridging is generated for this deck, so the sheet shows "
                    "none at bearing lines", element_tags=(level.floor.tag,),
            result=Result.UNKNOWN))
    return findings


def bearing_wall_labels(level: FramedLevel) -> list[tuple[tuple[float, float], str]]:
    """Plan-frame label anchors for the walls that carry the deck (drawn by framingplan)."""
    labels = [(wall_center(wall), f"BRG: {wall.tag}") for wall in level.declared_bearing_walls]
    labels.extend((wall_center(wall), "BEARING") for wall in level.role_bearing_walls)
    return labels

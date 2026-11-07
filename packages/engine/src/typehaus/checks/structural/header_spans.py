"""Wall headers against IRC 2018 R602.7, and the wall roles that decide which rule applies.

* ``structural.header_span`` — a sawn header in a BEARING wall up to 8' with no published
  row, read off Table R602.7(1)/(2) at the load ``resolve/header_loads.py`` derives: span
  (x 0.70 where cripples bear on it, note f) and NJ against what is framed.
* ``structural.wall_role_load`` — a NONBEARING wall nothing may bear on; a header host whose
  role is UNKNOWN; a BEARING host nothing derivable bears on.
* ``structural.flat_2x4_nonbearing_header`` — the R602.7.4 flat nailer's limits, windows
  included, measured to the plate underside at the span's ends (a raked top's worst).

Past 8', or with a ``published_span``, a header is ``structural.header_prescriptive``'s.
"""

from __future__ import annotations

import math
import re
from types import SimpleNamespace

from typehaus.checks._authoring import structural_advisory as _advisory
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result
from typehaus.model.enums import StructuralRole
from typehaus.model.framing_standards import built_up_size
from typehaus.resolve.framing.header_choice import (
    FLAT_HEADER_GAP_MAX_IN,
    PRESCRIPTIVE_SPAN_MAX_IN,
    host_table,
    plate_underside_at,
    span_stations,
)
from typehaus.resolve.framing.header_tables import TableCondition, row_for
from typehaus.resolve.header_loads import LoadIndex

_IN = 0.0254
_FLAT = re.compile(r"^2x\d+$")
_SPAN_CID = "structural.header_span"
_ROLE_CID = "structural.wall_role_load"
_FLAT_CID = "structural.flat_2x4_nonbearing_header"
_R602_7 = "IRC R602.7"
_TRIAGE = ("author header_spec + published_span from a manufacturer's header guide, move "
           "the opening off the load, or carry it as an engineered item")


def _role(ctx: CheckContext, tag: str) -> StructuralRole:
    return getattr(ctx.plan.by_tag(tag), "structural_role", StructuralRole.UNKNOWN)


def _headers(ctx: CheckContext):
    """(wall, header member, its opening, the opening as the solver saw it)."""
    operations = {item.tag: item.operation for item in ctx.plan.library.door_types}
    openings = {op.tag: op for op in ctx.model.openings}
    for wall in ctx.model.walls:
        for header in wall.members:
            op = openings.get(header.opening_tag) if header.category == "header" else None
            if op is None:
                continue
            seen = SimpleNamespace(
                center_m=op.center_along_m, width_m=op.width_m,
                operation=operations.get(op.type_ref) if op.is_door else None,
                pocket_run_m=op.pocket_run_m, pocket_sign=op.pocket_sign)
            yield wall, header, op, seen


def published_read(ctx: CheckContext, op, index: LoadIndex) -> tuple[float, tuple[str, ...]]:
    """(the span a published header row must cover, in feet — a pocket's cavity included —
    and the point loads bearing inside it). A header guide's rows are uniform-load only."""
    operations = {item.tag: item.operation for item in ctx.plan.library.door_types}
    seen = SimpleNamespace(
        center_m=op.center_along_m, width_m=op.width_m,
        operation=operations.get(op.type_ref) if op.is_door else None,
        pocket_run_m=op.pocket_run_m, pocket_sign=op.pocket_sign)
    lo, hi = span_stations(seen)
    wall = ctx.model.wall(op.host_wall)
    points = index.condition(wall, lo, hi).point_loads if wall is not None else ()
    return (hi - lo) / 0.3048, points


def _pack(wall, header) -> tuple[int, bool]:
    """(jacks per carried end, head cripples bear on it)."""
    index = header.child_key.split("-", 1)[1]
    sides = [sum(1 for m in wall.members if m.category == "jack"
                 and m.child_key.startswith(f"jack-{index}-{side}")) for side in "lr"]
    cripples = any(m.child_key.startswith(f"cripple-head-{index}-") for m in wall.members)
    carried = [count for count in sides if count]
    return (min(carried) if carried else 0), cripples


@check(Tier.STRUCTURAL, _SPAN_CID)
def header_span(ctx: CheckContext) -> list[Finding]:
    """Grade each sawn bearing header up to 8' against R602.7 at its derived load."""
    if ctx.plan is None:
        return []
    site = getattr(ctx.plan.project, "site", None)
    snow = getattr(site, "ground_snow_load_psf", None)
    index = LoadIndex.of(ctx.plan, ctx.model)
    out: list[Finding] = []
    for wall, header, op, seen in _headers(ctx):
        lo, hi = span_stations(seen)
        span_in = (hi - lo) / _IN
        if (getattr(ctx.plan.by_tag(op.tag), "published_span", None) is not None
                or span_in > PRESCRIPTIVE_SPAN_MAX_IN + 1e-6 or _FLAT.match(header.profile)):
            continue
        tags = (op.tag, wall.tag)
        what = f"{op.tag}'s {header.profile} header in {wall.tag} ({span_in:.1f}\" clear)"
        role = _role(ctx, wall.tag)
        if role is StructuralRole.NONBEARING:
            out.append(_advisory(_SPAN_CID, f"N/A — {what}: a NONBEARING host gives R602.7 "
                                 "nothing to carry", tags, Result.NOT_APPLICABLE, code=_R602_7))
            continue
        if role is not StructuralRole.BEARING:
            out.append(_advisory(_SPAN_CID, f"{what}: host role is UNKNOWN", tags,
                                 Result.UNKNOWN, "author Wall.structural_role", code=_R602_7))
            continue
        table = host_table(index, snow, wall, seen)
        if not isinstance(table, TableCondition):
            out.append(_advisory(_SPAN_CID, f"{what}: no R602.7 row — {table}", tags,
                                 Result.UNKNOWN, _TRIAGE, code=_R602_7))
            continue
        size = built_up_size(header.profile)
        jacks, cripples = _pack(wall, header)
        row = row_for(table, size, cripples) if size else None
        if row is None:
            out.append(_advisory(_SPAN_CID, f"{what}: {table.describe()} has no row for it",
                                 tags, Result.UNKNOWN, _TRIAGE, code=_R602_7))
            continue
        short = []
        if row.allowable_in + 1e-6 < span_in:
            short.append(f"allowable {row.allowable_in:.1f}\" < {span_in:.1f}\"")
        if jacks < row.jacks:
            short.append(f"{jacks} jack(s) framed < NJ {row.jacks}")
        verdict = Result.FAIL if short else Result.PASS
        note = "; ".join(short) if short else f"{jacks} jack(s) framed"
        out.append(_advisory(_SPAN_CID, f"{what}: {row.describe()} — {note}", tags, verdict,
                             None if not short else "a deeper or wider header, or more jacks",
                             code=_R602_7))
    return out


@check(Tier.STRUCTURAL, _ROLE_CID)
def wall_role_load(ctx: CheckContext) -> list[Finding]:
    """A wall's authored role against what the bearing graph puts on it."""
    if ctx.plan is None:
        return []
    index = LoadIndex.of(ctx.plan, ctx.model)
    hosts = {wall.tag for wall, *_rest in _headers(ctx)}
    out: list[Finding] = []
    for wall in ctx.model.walls:
        role = _role(ctx, wall.tag)
        if role is StructuralRole.UNKNOWN:
            if wall.tag in hosts:
                out.append(_advisory(_ROLE_CID, f"{wall.tag} hosts a header and its role is "
                                     "UNKNOWN", (wall.tag,), Result.UNKNOWN,
                                     "author Wall.structural_role", code=_R602_7))
            continue
        carried = index.condition(wall, 0.0, math.dist(*wall.axis))
        if role is StructuralRole.NONBEARING and carried.carries:
            out.append(_advisory(_ROLE_CID, f"{wall.tag} is NONBEARING and carries "
                                 f"{carried.describe()}", (wall.tag,), Result.FAIL,
                                 "author it BEARING, or move what bears on it", code=_R602_7))
        elif role is StructuralRole.BEARING and wall.tag in hosts and not carried.carries:
            out.append(_advisory(_ROLE_CID, f"{wall.tag} is BEARING and nothing derivable "
                                 "bears on it (no roof, floor, beam, opening or stair names it "
                                 "or a wall above it)", (wall.tag,), Result.UNKNOWN,
                                 "name it in what bears on it, or author it NONBEARING",
                                 code=_R602_7))
    return out


@check(Tier.STRUCTURAL, _FLAT_CID)
def flat_2x4_nonbearing_header(ctx: CheckContext) -> list[Finding]:
    """Validate the deliberately narrow R602.7.4 flat-nailer exception.

    A flat 2x4 is not a small bearing header. It is permitted only in a nonbearing wall, over
    an opening up to 8', and where the plate is within 24" to nail the wall above together.
    ``flat 2xN`` (a flat 2x6 in a 2x6 wall, so both faces have a nailer) is this engine's
    reading of that rule, not its text: a wider flat member of the same thickness is
    conservative, not code-named.
    """
    if ctx.plan is None:
        return []
    out: list[Finding] = []
    for wall, header, op, seen in _headers(ctx):
        if not _FLAT.match(header.profile):
            continue
        lo, hi = span_stations(seen)
        violations: list[str] = []
        if _role(ctx, wall.tag) is not StructuralRole.NONBEARING:
            violations.append("host wall is not explicitly NONBEARING")
        if hi - lo > PRESCRIPTIVE_SPAN_MAX_IN * _IN + 1e-9:
            violations.append(f"clear span is {(hi - lo) / _IN:.1f}\" (> 96\")")
        underside = plate_underside_at(ctx.plan, wall)
        if underside is not None:
            gap = max(underside(lo), underside(hi)) - header.z1_m
            if gap < -1e-9 or gap > FLAT_HEADER_GAP_MAX_IN * _IN + 1e-9:
                violations.append(f"header-to-plate nailing surface is {gap / _IN:.1f}\" "
                                  "(must be 0–24\")")
        if violations:
            out.append(_advisory(
                _FLAT_CID, f"opening {op.tag} cannot use a flat {header.profile} nonbearing "
                "header: " + "; ".join(violations), (op.tag,), Result.FAIL,
                code="IRC R602.7.4",
                fix_hint="use a table-sized header or explicitly correct the nonbearing "
                         "wall, RO, and plate clearance"))
    return out

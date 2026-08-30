"""Foundation-wall screens the framing solver does not do: unbalanced backfill height.

A basement wall's governing load case is usually not what it carries from above — it is the
soil pushing sideways on it. IRC Table R404.1.2(8) publishes the vertical reinforcement a
flat concrete wall needs, by nominal thickness, by how heavy the soil is, by unsupported
wall height and by how much unbalanced backfill it retains. Many of its cells read "NR" —
no vertical reinforcement required, i.e. plain concrete is enough. Past the table the wall
is an engineered element, and the code says so.

This check used to screen against a table it called "IRC Table R404.1.2(1)", capping a 12"
wall at 7' of unbalanced fill at 45 psf/ft. That was wrong twice over. R404.1.2(1) is
"MINIMUM HORIZONTAL REINFORCEMENT FOR CONCRETE BASEMENT WALLS" — two rows about where to
put horizontal bars, carrying no backfill limits at all — and no IRC edition from 2009
through 2021 publishes any maximum-unbalanced-fill table for plain *concrete* walls. The
limits it used matched nothing: not R404.1.2(8), not the plain *masonry* table R404.1.1(1),
not IBC 1807.1.6.3(1). They were also wrong in the unsafe direction — not conservative, but
rejecting walls the code plainly permits. A 12" wall at 45 psf/ft retaining 9' of fill on a
9' storey needs no vertical steel at all.

Same contract as the sibling structural checks: this is a table lookup, labeled advisory,
and it never claims to be a design. It also never guesses an input — no soil class means
UNKNOWN, because the three lateral-pressure columns are two wall thicknesses apart and
picking one silently would be choosing the answer. For the same reason an unbraced or
unstated wall is not quietly run through a table that presumes bracing.
"""

from __future__ import annotations

from functools import partial

from typehaus.checks._authoring import engineered as _engineered
from typehaus.checks._authoring import structural_advisory as _advisory
from typehaus.checks._authoring import unknown as _unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.checks.soil import site_soil_class
from typehaus.checks.structural._r404_table import (
    BACKFILL_HEIGHTS_FT,
    DESIGN_REQUIRED,
    NOMINAL_THICKNESSES_IN,
    NOT_REQUIRED,
    SOIL_LATERAL_PSF_PER_FT,
    VERTICAL_REINFORCEMENT,
    WALL_HEIGHTS_FT,
)
from typehaus.engineering import item_id
from typehaus.findings import Finding, Result
from typehaus.model.enums import LayerFunction

_M_PER_FT = 0.3048

# R404.1.1 and R404.4 both hinge on this number: below it a wall's backfill is not a
# structural question at all, and Table R404.1.2(8) publishes no row under it either.
_SCREEN_THRESHOLD_FT = 4.0


def _structural_thickness_in(ctx: CheckContext, assembly_tag: str) -> float | None:
    """The nominal thickness of the assembly's concrete STRUCTURE layer, in inches.

    The wall's *total* thickness is the wrong number: CATLIN_BASEMENT_12 is 12" of concrete
    plus damp-proofing plus 4" of XPS, and the foam retains nothing.
    """
    assembly = next((a for a in ctx.plan.library.assemblies if a.tag == assembly_tag), None)
    if assembly is None:
        return None
    for layer in assembly.layers:
        if layer.function is LayerFunction.STRUCTURE:
            # Rounded to the nominal 1/2": `.inches` comes back off a metres round-trip, so a
            # 12" layer arrives as 12.000000000000002 and misses the table key exactly.
            return round(layer.thickness.inches * 2.0) / 2.0
    return None


def _unbalanced_fill_ft(wall, grade_m: float) -> float | None:
    """How much backfill this wall retains, authored or derived.

    Derived, when not authored: from grade down to the bottom of the wall, clamped at zero.
    That is a *conservative proxy*, and deliberately so — the real unbalanced height depends
    on the finished grade at each face and on whether a slab braces the inside, neither of
    which the model carries. It over-reports a walkout wall whose exterior grade falls away,
    which is the safe direction to be wrong in; author ``unbalanced_fill`` where it matters.
    """
    if wall.unbalanced_fill is not None:
        return wall.unbalanced_fill.meters / _M_PER_FT
    if wall.top_elevation is None or wall.bottom_elevation is None:
        return None
    top = min(grade_m, wall.top_elevation.meters)
    return max(0.0, top - wall.bottom_elevation.meters) / _M_PER_FT


def _wall_height_ft(wall: object) -> float | None:
    """Unsupported wall height — the table's other row index, not the same as the backfill.

    A 10'-tall wall retaining 9' and a 9'-tall wall retaining 9' are different rows, and at
    12"/45 psf they are literally the difference between #4 @ 48 and no steel at all.
    """
    top = getattr(wall, "top_elevation", None)
    bottom = getattr(wall, "bottom_elevation", None)
    if top is None or bottom is None:
        return None
    return max(0.0, float(top.meters) - float(bottom.meters)) / _M_PER_FT


def _round_up(value: float, published: tuple[int, ...]) -> int | None:
    """The next published row at or above ``value`` — footnote f, interpolation is not
    permitted, so a 9.8' wall is graded on the 10' row rather than between two."""
    return next((row for row in published if row >= value - 1e-6), None)


@check(Tier.STRUCTURAL, "structural.foundation_unbalanced_fill")
def foundation_unbalanced_fill(ctx: CheckContext) -> list[Finding]:
    """Flat concrete foundation walls against IRC Table R404.1.2(8).

    Findings are aggregated by the whole lookup key rather than emitted per wall: sixteen
    identical 12" walls retaining 9' of the same soil are one condition and one decision,
    and sixteen copies of it would bury the two that differ.
    """
    from typehaus.model.structure import FoundationWall

    cid = "structural.foundation_unbalanced_fill"
    profile = ctx.profile
    # The SITE's own soil first, the profile's presumption second. A profile is shared by
    # every house that names it, so the class it carries can only ever be a presumptive
    # regional value; a parcel with a soils report states its own and that has to win.
    soil_class = site_soil_class(ctx.plan, profile)
    if soil_class is None:
        return [_unknown(cid, "neither the site nor the jurisdiction profile declares a "
                              "soil_class, so no equivalent-fluid pressure column of IRC "
                              "Table R404.1.2(8) applies")]
    lateral = SOIL_LATERAL_PSF_PER_FT.get(soil_class.upper())
    if lateral is None:
        return [_unknown(cid, f"soil class {soil_class!r} is not one of the IRC Table R405.1 "
                              "groups this table is indexed on, and footnote o prohibits "
                              "using it for a classification it does not show")]

    grade = ctx.plan.project.site.grade
    if grade is None:
        return [_unknown(cid, "the site declares no grade datum to measure backfill against")]
    grade_m = grade.meters

    walls = [w for w in ctx.plan.all_elements() if isinstance(w, FoundationWall)]
    if not walls:
        return []

    groups: dict[tuple, list[str]] = {}
    unknowns: dict[str, list[str]] = {}
    for wall in walls:
        thickness = _structural_thickness_in(ctx, wall.assembly)
        fill_ft = _unbalanced_fill_ft(wall, grade_m)
        if thickness is None or fill_ft is None:
            reason = ("the assembly declares no concrete STRUCTURE layer to read a thickness "
                      "from" if thickness is None else
                      "neither unbalanced_fill nor top/bottom elevations are authored")
            unknowns.setdefault(reason, []).append(wall.tag)
            continue
        if round(fill_ft, 1) <= 0.0:
            continue  # retains nothing — an interior cross wall, or a wall entirely above grade
        key = (wall.assembly, thickness, round(fill_ft, 1), round(_wall_height_ft(wall) or 0.0, 1),
               wall.lateral_support, wall.vertical_reinforcement, wall.engineering_spec)
        groups.setdefault(key, []).append(wall.tag)

    out: list[Finding] = []
    for reason, tags in sorted(unknowns.items()):
        out.append(_unknown(cid, f"{len(tags)} foundation wall(s) — {reason}",
                            tuple(sorted(tags))))

    for key, tags in sorted(groups.items(), key=lambda item: (item[0][0], -item[0][2])):
        assembly, thickness, fill_ft, height_ft, support, rebar, spec = key
        tags = sorted(tags)
        # Two phrasings of one condition. The grouped rows are per-*condition* and say how
        # many walls share it; an engineered handoff is per-*element*, because that is what
        # gets sealed, so it needs the same sentence in the singular.
        condition = (f"{assembly} wall at {thickness:.0f}\" concrete retaining "
                     f"{fill_ft:.1f}' of unbalanced fill ({soil_class}, {lateral} psf/ft)")
        where = f"{len(tags)} {condition.replace(' wall at ', ' wall(s) at ', 1)}"
        out.extend(_grade_one(ctx, cid, where, tuple(tags), thickness, lateral, fill_ft,
                              height_ft, support, rebar, spec, condition=condition))
    return out


#: One item id per wall, ``retaining_wall/<tag>``. The identity is deliberately
#: per-element even though the *grading* is per-condition: a group of three identical walls
#: is one row in this check's output and three things an engineer seals, and keeping the
#: item per-element is what lets moving one of them stale that one alone.
_KIND = "retaining_wall"


def _handoff(ctx, cid: str, reason: str, tags: tuple[str, ...], *,
             spec: str | None = None) -> list[Finding]:
    """This condition is outside the prescriptive path — delegate it, one item per wall.

    Every branch below that used to hard-code ``Result.UNKNOWN`` and end its sentence with
    the word "engineered" now comes here. Nothing about the gate moves: with no calculation
    registered for ``retaining_wall`` the finding is still UNKNOWN and still blocks. What it
    gains is a *name* — ``retaining_wall/W-SG-E2`` — that ``engineering.toml`` can seal and
    that ``structural.frost_depth`` can point at too, so one engineer's design over these
    walls answers both checks instead of each carrying its own untraceable paragraph.
    """
    return [_engineered(ctx, cid, item_id(_KIND, tag), f"{tag}: {reason}", (tag,),
                        code="IRC R404.4", authored=spec)
            for tag in tags]


def _grade_one(ctx, cid: str, where: str, tags: tuple[str, ...], thickness: float,
               lateral: int, fill_ft: float, height_ft: float, support: str | None,
               rebar: str | None, spec: str | None, *,
               condition: str = "") -> list[Finding]:
    """One condition, graded. Split out to keep the aggregation loop readable.

    ``condition`` is ``where`` in the singular, for the per-element engineered handoffs.
    """
    _handoff_here = partial(_handoff, ctx, cid, tags=tags)
    # Every engineered branch below reads `single` where the prescriptive ones read `where`:
    # a handoff is per-element and its sentence must be singular, since the finding it
    # becomes names one wall and one sealable item.
    single = condition or where
    # An authored engineer's design IS the design — the table stops applying, exactly as
    # Door.header_spec stops the header tables. It routes through the register now so that
    # the PASS says *authored*, not computed, and so the wall is a nameable item either way.
    if spec:
        return _handoff_here(single, spec=spec)

    # Below 4' of fill neither R404.1.1 nor R404.4 engages and the table publishes no row.
    if fill_ft < _SCREEN_THRESHOLD_FT:
        return [_advisory(
            cid, f"{where} — under the 4' at which IRC R404.1.1 and Table R404.1.2(8) "
                 f"engage at all", tags, Result.PASS)]

    if int(thickness) not in NOMINAL_THICKNESSES_IN or thickness != int(thickness):
        thickest = max(NOMINAL_THICKNESSES_IN)
        beyond = (f"thicker than the table's {thickest}\" maximum" if thickness > thickest
                  else "not a tabulated nominal section")
        return _handoff_here(f"{single}: {beyond}, so IRC Table R404.1.2(8) does not "
                             f"answer it")

    # The table presumes a wall braced top and bottom (footnote g). Without that, R404.1.1
    # (>48" of fill, no permanent lateral support) and R404.4 (a retaining wall unsupported
    # at the top) both send the wall to an engineered design instead.
    if support == "unsupported":
        return _handoff_here(
            f"{single} is not laterally supported top and bottom, so IRC R404.1.1 and "
            f"R404.4 require an engineered design (safety factor 1.5 against sliding and "
            f"overturning) rather than Table R404.1.2(8)")
    if support is None:
        return [_unknown(
            cid, f"{where}: the wall does not declare whether it is permanently braced top "
                 "and bottom, which is what Table R404.1.2(8) presumes (footnote g) and "
                 "what IRC R404.1.1 turns on above 48\" of fill — author "
                 "FoundationWall.lateral_support", tags)]

    row_h = _round_up(height_ft, WALL_HEIGHTS_FT)
    row_f = _round_up(fill_ft, BACKFILL_HEIGHTS_FT)
    if row_h is None or row_f is None or row_f > row_h:
        beyond = ("retains more fill than its own height" if row_h is not None
                  and row_f is not None and row_f > row_h else
                  f"is outside the table's {max(WALL_HEIGHTS_FT)}' maximum")
        return _handoff_here(f"{single}, {height_ft:.1f}' tall, {beyond}, so IRC Table "
                             f"R404.1.2(8) does not answer it")

    cell, notes = VERTICAL_REINFORCEMENT[(int(thickness), lateral, row_h, row_f)]
    cited = (f"IRC Table R404.1.2(8) at {thickness:.0f}\"/{lateral} psf/ft, the {row_h}' wall "
             f"x {row_f}' backfill row")

    if cell == DESIGN_REQUIRED:
        return _handoff_here(f"{single}, {height_ft:.1f}' tall — {cited} reads DR, "
                             f"design required per ACI 318")

    if cell == NOT_REQUIRED:
        # Footnote d: a 6" nominal wall in a stay-in-place form (an ICF) is the one NR that
        # is not actually bare — it still takes #4 @ 48.
        icf_note = ("; note footnote d — a 6\" wall formed with a stay-in-place system still "
                    "takes #4 @ 48\" o.c." if int(thickness) == 6 else "")
        plain = f" (plain concrete, f'c >= 2,500 psi{_note_suffix(notes)})"
        return [_advisory(cid, f"{where}, {height_ft:.1f}' tall, needs no vertical "
                               f"reinforcement{plain} — {cited}{icf_note}", tags,
                          Result.PASS)]

    required = f"{cell}\" o.c."
    if rebar:
        return [_advisory(cid, f"{where}, {height_ft:.1f}' tall, is reinforced {rebar} "
                               f"against the {required} {cited} requires", tags,
                          Result.PASS)]
    return [_advisory(
        cid, f"{where}, {height_ft:.1f}' tall, needs {required} vertical reinforcement "
             f"({cited}{_note_suffix(notes)}) and the wall declares none", tags, Result.FAIL,
        fix_hint=f"author FoundationWall.vertical_reinforcement='{cell}\" o.c.' — bars at "
                 "1 1/4\" cover from the inside face per footnote h, Grade 60 per "
                 "footnote b")]


def _note_suffix(notes: str) -> str:
    """The cell-attached footnotes, spelled out — they change the concrete, not the steel."""
    if "m" in notes:
        return "; footnote m allows plain 12\" concrete instead, at f'c 3,500 psi"
    if "l" in notes:
        return "; footnote l allows 2\" less thickness, at f'c 4,000 psi"
    return ""

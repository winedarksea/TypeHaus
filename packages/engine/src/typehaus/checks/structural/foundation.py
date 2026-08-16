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

from typehaus.checks._authoring import structural_advisory as _advisory, unknown as _unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.checks.structural._r404_table import (
    BACKFILL_HEIGHTS_FT,
    DESIGN_REQUIRED,
    NOMINAL_THICKNESSES_IN,
    NOT_REQUIRED,
    SOIL_LATERAL_PSF_PER_FT,
    VERTICAL_REINFORCEMENT,
    WALL_HEIGHTS_FT,
)
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
    soil_class = getattr(profile, "soil_class", None) if profile is not None else None
    if soil_class is None:
        return [_unknown(cid, "the jurisdiction profile declares no soil_class, so no "
                              "equivalent-fluid pressure column of IRC Table R404.1.2(8) "
                              "applies")]
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
        where = (f"{len(tags)} {assembly} wall(s) at {thickness:.0f}\" concrete retaining "
                 f"{fill_ft:.1f}' of unbalanced fill ({soil_class}, {lateral} psf/ft)")
        out.append(_grade_one(cid, where, tuple(tags), thickness, lateral, fill_ft,
                              height_ft, support, rebar, spec))
    return out


def _grade_one(cid: str, where: str, tags: tuple[str, ...], thickness: float, lateral: int,
               fill_ft: float, height_ft: float, support: str | None, rebar: str | None,
               spec: str | None) -> Finding:
    """One condition, graded. Split out to keep the aggregation loop readable."""
    # An authored engineer's design IS the design — the table stops applying, exactly as
    # Door.header_spec stops the header tables.
    if spec:
        return _advisory(cid, f"{where} — engineered design authored: {spec}", tags,
                         Result.PASS)

    # Below 4' of fill neither R404.1.1 nor R404.4 engages and the table publishes no row.
    if fill_ft < _SCREEN_THRESHOLD_FT:
        return _advisory(
            cid, f"{where} — under the 4' at which IRC R404.1.1 and Table R404.1.2(8) "
                 f"engage at all", tags, Result.PASS)

    if int(thickness) not in NOMINAL_THICKNESSES_IN or thickness != int(thickness):
        thickest = max(NOMINAL_THICKNESSES_IN)
        beyond = (f"thicker than the table's {thickest}\" maximum" if thickness > thickest
                  else "not a tabulated nominal section")
        return _unknown(cid, f"{where}: {beyond}, so IRC Table R404.1.2(8) does not answer "
                             "it — engineered", tags)

    # The table presumes a wall braced top and bottom (footnote g). Without that, R404.1.1
    # (>48" of fill, no permanent lateral support) and R404.4 (a retaining wall unsupported
    # at the top) both send the wall to an engineered design instead.
    if support == "unsupported":
        return _unknown(
            cid, f"{where} is not laterally supported top and bottom, so IRC R404.1.1 and "
                 "R404.4 require an engineered design (safety factor 1.5 against sliding "
                 "and overturning) rather than Table R404.1.2(8) — engineered", tags)
    if support is None:
        return _unknown(
            cid, f"{where}: the wall does not declare whether it is permanently braced top "
                 "and bottom, which is what Table R404.1.2(8) presumes (footnote g) and "
                 "what IRC R404.1.1 turns on above 48\" of fill — author "
                 "FoundationWall.lateral_support", tags)

    row_h = _round_up(height_ft, WALL_HEIGHTS_FT)
    row_f = _round_up(fill_ft, BACKFILL_HEIGHTS_FT)
    if row_h is None or row_f is None or row_f > row_h:
        beyond = ("retains more fill than its own height" if row_h is not None
                  and row_f is not None and row_f > row_h else
                  f"is outside the table's {max(WALL_HEIGHTS_FT)}' maximum")
        return _unknown(cid, f"{where}, {height_ft:.1f}' tall, {beyond}, so IRC Table "
                             "R404.1.2(8) does not answer it — engineered", tags)

    cell, notes = VERTICAL_REINFORCEMENT[(int(thickness), lateral, row_h, row_f)]
    cited = (f"IRC Table R404.1.2(8) at {thickness:.0f}\"/{lateral} psf/ft, the {row_h}' wall "
             f"x {row_f}' backfill row")

    if cell == DESIGN_REQUIRED:
        return _unknown(cid, f"{where}, {height_ft:.1f}' tall — {cited} reads DR, design "
                             "required per ACI 318 — engineered", tags)

    if cell == NOT_REQUIRED:
        # Footnote d: a 6" nominal wall in a stay-in-place form (an ICF) is the one NR that
        # is not actually bare — it still takes #4 @ 48.
        icf_note = ("; note footnote d — a 6\" wall formed with a stay-in-place system still "
                    "takes #4 @ 48\" o.c." if int(thickness) == 6 else "")
        plain = f" (plain concrete, f'c >= 2,500 psi{_note_suffix(notes)})"
        return _advisory(cid, f"{where}, {height_ft:.1f}' tall, needs no vertical "
                              f"reinforcement{plain} — {cited}{icf_note}", tags, Result.PASS)

    required = f"{cell}\" o.c."
    if rebar:
        return _advisory(cid, f"{where}, {height_ft:.1f}' tall, is reinforced {rebar} against "
                              f"the {required} {cited} requires", tags, Result.PASS)
    return _advisory(
        cid, f"{where}, {height_ft:.1f}' tall, needs {required} vertical reinforcement "
             f"({cited}{_note_suffix(notes)}) and the wall declares none", tags, Result.FAIL,
        fix_hint=f"author FoundationWall.vertical_reinforcement='{cell}\" o.c.' — bars at "
                 "1 1/4\" cover from the inside face per footnote h, Grade 60 per footnote b")


def _note_suffix(notes: str) -> str:
    """The cell-attached footnotes, spelled out — they change the concrete, not the steel."""
    if "m" in notes:
        return "; footnote m allows plain 12\" concrete instead, at f'c 3,500 psi"
    if "l" in notes:
        return "; footnote l allows 2\" less thickness, at f'c 4,000 psi"
    return ""

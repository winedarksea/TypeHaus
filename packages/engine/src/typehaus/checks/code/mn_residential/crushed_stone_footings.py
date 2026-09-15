"""2024 IRC R403.5 — crushed stone footings under cast-in-place concrete foundations.

R403.5 permits a consolidated crushed-stone footing in place of a cast strip, but only for a
**nonretaining** cast-in-place foundation complying with R404.1.3, and only in Seismic Design
Categories A, B and C (A and B for townhouses). The stone itself is R403.4.1's — angular,
ASTM C33, 1/2" maximum and 1/16" minimum, free of organic, clayey or silty soils, and
consolidated with a vibratory plate in lifts not greater than 8". Its size comes from Table
R403.4, which R403.4.1 points at.

**Why this is worth encoding at all**, given catlin's own profile is still MN_2020: because
without it the nine garage footings would simply stop being concrete and nothing anywhere
would ask whether that was allowed. A retype that no rule can see is the failure mode this
whole repo is aimed at — geometry that is silently wrong at 0 FAIL. Minnesota takes the 2024
edition in 2027 and this house is built after it, so the rule is written against the edition
the building will be inspected under and the profile gate below says so out loud.

**Four things can be wrong and each is reported separately**, because they are answered by
different people: the stone (a supplier's ticket), the consolidation (the excavator's
method), the scope (the designer's, via ``unbalanced_fill``), and the size (Table R403.4,
against the wall it carries).

**N/A is earned from positive absence**, per decision #32: a house with footings but none of
them crushed stone returns NOT_APPLICABLE naming that, rather than an empty list.
"""

from __future__ import annotations

from typehaus.checks._authoring import passed
from typehaus.checks.code.mn_residential._common import _fail, _na, _unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.model.structure import Footing, FoundationWall
from typehaus.quantities import inch

_CID = "code.R403_5_crushed_stone_footings"
_CODE = "IRC R403.5"

#: R403.5's own scope sentence. A townhouse is A and B only; this engine models no townhouse
#: and grades the dwelling row, so C is included and the difference is stated rather than
#: silently applied.
_ALLOWED_SDC = frozenset({"A", "B", "C"})

#: R403.4.1's gradation bounds, as lengths so a house that authors its own are compared in
#: the units it wrote them in.
_MAX_STONE = inch(0.5)
_MIN_STONE = inch(1.0 / 16.0)
#: R403.4.1: "consolidated using a vibratory plate in not greater than 8-inch lifts".
_MAX_LIFT = inch(8)

#: Table R403.4, the row this engine can actually reach: CONVENTIONAL LIGHT-FRAME, 1 STOREY,
#: 1,100 plf. Minimum depth D is 4" at every one of the table's six soil bearing values, so
#: the depth requirement does not need the soil to be known. Minimum width W is 13", 15" and
#: 17" for an 8", 10" and 12" wall respectively.
#:
#: **The table starts at an 8" wall and a 6" stem has no column.** Footnote a permits linear
#: interpolation of DEPTH between wall widths; it says nothing about extrapolating WIDTH
#: below the table's own range, and inventing a number under a published table is exactly
#: what this repo refuses elsewhere. So a wall narrower than 8" is held to the WIDEST
#: published W — the conservative reading, and one a plan reviewer can follow.
_TABLE_R403_4_MIN_DEPTH = inch(4)
_TABLE_R403_4_MIN_WIDTH = {8: inch(13), 10: inch(15), 12: inch(17)}
_WIDEST_W = inch(17)


def _structure_width_in(ctx: CheckContext, wall_tag: str) -> float | None:
    """The width of the concrete WALL this footing carries, in inches.

    Table R403.4 is indexed on the wall's own width, which for an ICF stem is the poured
    CORE and not the assembly: catlin's GARAGE_ICF_6 resolves 11" overall (a 6" core between
    two 2 1/2" EPS faces) and 6" of it is concrete. Reading the assembly would put the wall
    in a column it does not belong to and, here, would have made a 6" wall look like a 12"
    one. Read off the resolved STRUCTURE layer, which is the concrete.

    ``None`` where the wall resolves no structure layer — the check then requires the widest
    W the table publishes rather than picking a row on a guess.
    """
    for resolved in ctx.model.walls:
        if resolved.tag != wall_tag:
            continue
        for layer in resolved.layers:
            if str(getattr(layer, "function", "")).endswith("structure"):
                return layer.thickness_m / 0.0254
    return None


def _stone_faults(stone) -> list[str]:
    """Every way this stone fails R403.4.1, in the section's own order."""
    faults = []
    if not stone.gradation or "C33" not in stone.gradation.upper().replace(" ", ""):
        faults.append(f"gradation is {stone.gradation!r}, and R403.4.1 requires ASTM C33")
    if stone.max_size.meters > _MAX_STONE.meters + 1e-9:
        faults.append(f'maximum stone size {stone.max_size.inches:g}" exceeds the 1/2" '
                      "R403.4.1 allows")
    if stone.min_size.meters < _MIN_STONE.meters - 1e-9:
        faults.append(f'minimum stone size {stone.min_size.inches:g}" is finer than the '
                      '1/16" R403.4.1 allows')
    if not stone.angular:
        faults.append("the stone is not stated angular, and R403.4.1 requires it "
                      "(a rounded pit gravel does not lock up under load)")
    if not stone.free_of_fines:
        faults.append("the stone is not stated free of organic, clayey or silty soils")
    if stone.lift_thickness.meters > _MAX_LIFT.meters + 1e-9:
        faults.append(f'lifts of {stone.lift_thickness.inches:g}" exceed the 8" R403.4.1 '
                      "allows")
    if "vibratory" not in (stone.consolidation or "").lower():
        faults.append(f"consolidation is {stone.consolidation!r}, and R403.4.1 requires a "
                      "vibratory plate")
    return faults


@check(Tier.CODE, _CID)
def crushed_stone_footings(ctx: CheckContext) -> list[Finding]:
    """Every crushed-stone footing against R403.5's scope and R403.4.1's specification."""
    stone_footings = [el for el in ctx.plan.all_elements()
                      if isinstance(el, Footing) and el.material == "crushed_stone"]
    if not stone_footings:
        concrete = [el for el in ctx.plan.all_elements() if isinstance(el, Footing)]
        return [_na(_CID,
                    f"none of this building's {len(concrete)} footings is built of crushed "
                    "stone — every one is cast concrete, so R403.5's alternative is not the "
                    "condition here" if concrete else
                    "this building resolves no Footing at all, so there is no footing for "
                    "R403.5 to describe",
                    tuple(el.tag for el in concrete), _CODE)]

    profile = ctx.profile
    sdc = getattr(profile, "seismic_design_category", None)
    tags = tuple(el.tag for el in stone_footings)
    if sdc is None:
        return [_unknown(_CID,
                         "the jurisdiction profile declares no seismic_design_category, and "
                         "R403.5 is limited to Categories A, B and C — so whether a crushed "
                         "stone footing is permitted here cannot be answered. IRC Table "
                         "R301.2.2.1 is where a jurisdiction reads it",
                         tags, _CODE)]
    if sdc.upper() not in _ALLOWED_SDC:
        return [_fail(_CID,
                      f"{len(stone_footings)} crushed stone footing(s) in Seismic Design "
                      f"Category {sdc}: R403.5 permits them in Categories A, B and C only "
                      "(A and B for a townhouse)",
                      tags, _CODE)]

    walls = {el.tag: el for el in ctx.plan.all_elements()
             if isinstance(el, FoundationWall)}
    out: list[Finding] = []
    for footing in sorted(stone_footings, key=lambda el: el.tag):
        tag = footing.tag
        one = (tag,)

        if footing.stone is None:
            out.append(_unknown(_CID,
                                f"{tag} is built of crushed stone but names no stone: "
                                "R403.4.1 is a specification (ASTM C33, 1/2\" max, 1/16\" "
                                "min, angular, no fines, vibratory plate in 8\" lifts) and "
                                "an unstated stone meets none of it. Author "
                                "`stone=CrushedStoneSpec(...)`",
                                one, _CODE))
            continue
        faults = _stone_faults(footing.stone)
        if faults:
            out.append(_fail(_CID, f"{tag}'s stone does not meet IRC R403.4.1: "
                                   + "; ".join(faults), one, _CODE))
            continue

        wall = walls.get(footing.under)
        if wall is None:
            out.append(_unknown(_CID,
                                f"{tag} is a crushed stone footing but {footing.under!r} is "
                                "not a FoundationWall this model carries, so R403.5's "
                                "\"nonretaining cast-in-place foundation complying with "
                                "R404.1.3\" cannot be tested against anything",
                                one, _CODE))
            continue
        fill = getattr(wall, "unbalanced_fill", None)
        if fill is None:
            out.append(_unknown(_CID,
                                f"{wall.tag} does not author `unbalanced_fill`, so this "
                                f"engine cannot say {tag} carries a NONRETAINING foundation "
                                "— which is R403.5's first condition. "
                                "`structural.foundation_unbalanced_fill`'s derived figure is "
                                "an explicitly conservative proxy (grade to the wall's "
                                "underside) and is not evidence of the real height",
                                one, _CODE))
            continue
        if fill.meters > 1e-9:
            out.append(_fail(_CID,
                             f"{wall.tag} retains {fill.inches:g}\" of unbalanced fill, and "
                             f"R403.5 permits a crushed stone footing under a NONRETAINING "
                             f"foundation only — {tag} has to be cast concrete",
                             (tag, wall.tag), _CODE))
            continue

        if footing.depth.meters < _TABLE_R403_4_MIN_DEPTH.meters - 1e-9:
            out.append(_fail(_CID,
                             f"{tag} is {footing.depth.inches:g}\" deep against Table "
                             f"R403.4's minimum D of {_TABLE_R403_4_MIN_DEPTH.inches:g}\" "
                             "for one-storey conventional light-frame construction, which "
                             "is the table's floor at every soil bearing value it publishes",
                             one, _CODE))
            continue

        wall_in = _structure_width_in(ctx, wall.tag)
        if wall_in is None:
            required = _WIDEST_W
            why = ("the wall states no thickness, so the widest W the table publishes is "
                   "required rather than a narrower row being assumed")
        elif wall_in < 8.0:
            required = _WIDEST_W
            why = (f"a {wall_in:g}\" wall is NARROWER than Table R403.4's first column (8\"), "
                   "so there is no row to read and the widest published W is required — "
                   "footnote a permits interpolating DEPTH between wall widths, not "
                   "extrapolating WIDTH below the table")
        else:
            key = min(_TABLE_R403_4_MIN_WIDTH, key=lambda w: abs(w - wall_in))
            required = _TABLE_R403_4_MIN_WIDTH[key]
            why = f'Table R403.4\'s W for a {key}" wall'
        if footing.width.meters < required.meters - 1e-9:
            out.append(_fail(_CID,
                             f"{tag} is {footing.width.inches:g}\" wide against "
                             f"{required.inches:g}\" required: {why}",
                             one, _CODE))
            continue

        # ``passed`` rather than ``_common._pass``: that adapter drops tags, and a PASS with
        # no element on it cannot be linked back to the footing it is about.
        out.append(passed(_CID,
                         f"{tag}: {footing.width.inches:g}\" x {footing.depth.inches:g}\" of "
                         f"angular ASTM C33 crushed stone, 1/16\"-1/2\", consolidated by "
                         f"vibratory plate in {footing.stone.lift_thickness.inches:g}\" "
                         f"lifts, under {wall.tag} which retains nothing — IRC R403.5 in "
                         f"Seismic Design Category {sdc}, sized against Table R403.4 "
                         f"({required.inches:g}\" W / "
                         f"{_TABLE_R403_4_MIN_DEPTH.inches:g}\" D required)",
                         one, _CODE))
    return out

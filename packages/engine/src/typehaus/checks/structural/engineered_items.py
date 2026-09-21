"""One permit line per engineering kind that no other check names.

``haus engineering`` listed 26 items — base rotation, column heads, the veneer beam, the
thermal breaks and the tiered apron — that no ``@check`` delegated to, so none of them
produced a finding and none reached the permit checklist. A deferral nobody can see on the
checklist reads exactly like a design with nothing outstanding. These checks close that:
each walks its kind's keys through ``registry.keys_of`` (the register's own list, never a
re-walked predicate) and reports each item through ``engineered()``.

**One check id per kind**, never a catch-all. ``_item_from_findings`` folds by check id, so
a shared id would send one kind's UNKNOWN red on another kind's line (the 2026-09-20
``structural.column_base`` incident, ``profile.py``).
"""

from __future__ import annotations

from typehaus.checks._authoring import engineered as _engineered
from typehaus.checks._authoring import structural_advisory as _advisory
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.checks.structural._engineering import engineering_context
from typehaus.engineering import item_id, keys_of
from typehaus.findings import Finding, Result


def _items(ctx: CheckContext, cid: str, kind: str, subject: str, code: str,
           absent: str) -> list[Finding]:
    keys = keys_of(kind, engineering_context(ctx))
    if not keys:
        # Earned: the kind's own enumeration ran and found nothing in this plan.
        return [_advisory(cid, absent, (), Result.NOT_APPLICABLE)]
    return [_engineered(ctx, cid, item_id(kind, key), f"{key}: {subject}", (key,),
                        code=code, fix=f"seal `{item_id(kind, key)}` in engineering.toml")
            for key in keys]


@check(Tier.STRUCTURAL, "structural.base_rotation")
def base_rotation(ctx: CheckContext) -> list[Finding]:
    """Base STIFFNESS of a fixed cast column — the sway its rotating footing adds."""
    return _items(ctx, "structural.base_rotation", "base_rotation",
                  "the fixed column base's rotational stiffness and the sway it adds",
                  "ACI 318-19 §6.6.4; IBC 2018 §1806.3.4",
                  "no cast column in this plan is fixed at its base")


@check(Tier.STRUCTURAL, "structural.column_head_joint")
def column_head_joint(ctx: CheckContext) -> list[Finding]:
    """The joint at a lateral-system column's head: connector, shear, torsion, seat."""
    return _items(ctx, "structural.column_head_joint", "column_head_joint",
                  "the column head joint — connector capacity, column shear and torsion, "
                  "and bearing at the beam seat",
                  "ACI 318-19 §22.5, §22.7, §22.8",
                  "no cast column in this plan is a lateral system")


@check(Tier.STRUCTURAL, "structural.veneer_beam")
def veneer_beam(ctx: CheckContext) -> list[Finding]:
    """A cast beam carrying a masonry wythe between two walls."""
    return _items(ctx, "structural.veneer_beam", "veneer_beam",
                  "a cast beam carrying a masonry wythe — flexure, shear, torsion and "
                  "end restraint",
                  "ACI 318-19 §9, §22.7",
                  "no footingless wall in this plan carries another wall on its top")


@check(Tier.STRUCTURAL, "structural.thermal_break")
def thermal_break(ctx: CheckContext) -> list[Finding]:
    """Bars tying two pours across an insulating break."""
    return _items(ctx, "structural.thermal_break", "thermal_break_transfer",
                  "the dowel row across a thermal break — shear reserve, movement and "
                  "the board's integrity during the pour",
                  "ACI 318-19 §22.9; ACI 347R-14 §2.2",
                  "no dowel in this plan crosses an insulating break")


@check(Tier.STRUCTURAL, "structural.tiered_retaining")
def tiered_retaining(ctx: CheckContext) -> list[Finding]:
    """A footingless gravity wall retaining fill above a taller cut."""
    return _items(ctx, "structural.tiered_retaining", "tiered_retaining",
                  "a segmental gravity wall retaining fill — sliding, overturning, "
                  "bearing, and its interaction with the wall below",
                  "IRC R404.4; IBC 2018 §1807.2",
                  "no footingless wall in this plan retains fill")

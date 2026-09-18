"""Can this heat pump turn DOWN to the load — not just up to it?

``mep.heating_capacity`` asks whether a unit can make enough heat at the design hour, which
is one hour of the year. This asks the other question, and it is the one that decides whether
a house is comfortable in October: **an inverter's minimum output rises as it gets colder
while the zone load falls**, and where those two cross is where the machine stops modulating
and starts short-cycling.

The defect that produced this module. catlin's System 1 PASSes ``mep.heating_capacity``
with a +6,743 Btu/h margin while short-cycling through essentially the whole heating season:
the FLEXX Ultra's published minimum runs 10,800 Btu/h at 47 °F and 14,000 at 5 °F against a
zone load of 4,170 Btu/h at 47 °F, and it modulates down to the load only below **−5.9 °F**.
A single ``heating_capacity_at_design_btuh`` scalar structurally cannot express that — it is
one number at one temperature, and turndown is a relation between two curves.

Split out of ``checks/mep/hvac.py`` (341 lines) because +180 crosses the 500-line guideline,
and because the question is genuinely a different one: ``hvac.py`` grades a zone against a
capacity, this grades a zone against a *table*.

Oracled by ``houses/catlin/notes/heat_pump_turndown.md``; reproduced by
``tests/test_heat_pump_turndown.py``.
"""

from __future__ import annotations

from typehaus.checks._authoring import advisory
from typehaus.checks._authoring import not_applicable as _na
from typehaus.checks._authoring import passed as _pass
from typehaus.checks._authoring import unknown as _unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result

# Manual S §2: the minimum-compressor heating sizing factor. A modulating heat pump's
# MINIMUM output may be up to 0.80 of the design heating load — above that it cannot settle
# at the load through most of the season and cycles instead. This is the one figure in the
# module and it is a published limit, not a comfort preference.
_MAX_MINIMUM_SIZING_FACTOR = 0.80


def _advisory_fail(cid: str, msg: str, tags: tuple[str, ...]) -> Finding:
    """WARN severity + FAIL result, the idiom ``checks/mep/hvac.py`` sets: the permit
    integrity gate blocks on ERROR severity only, and this finding is advisory."""
    return advisory(cid, msg, tags, Result.FAIL)


def _crossover_temp_f(zone, rows) -> float | None:
    """The outdoor temperature at which the unit's MINIMUM output meets the zone load.

    Below it the unit modulates down to the load and runs continuously; above it the load is
    under the unit's floor and the compressor cycles. This is the sentence the audit is
    really making — "it cycles above −5.9 °F" is a fact an owner can act on, where "minimum
    sizing factor 0.91" is one they cannot.

    Solved on the first sign-flip bracket in the published rows: ``minimum(T) − load(T)``
    changes sign exactly once in practice (the minimum rises with cold, the load falls), and
    a secant on a bracket is honest where a root-find over an extrapolated curve is not.
    ``None`` where no bracket exists inside the table — the unit either never turns down far
    enough, or always does.
    """
    points = [(row.outdoor_db_f, row.minimum_btuh - zone.heating_load_at_outdoor_f(
        row.outdoor_db_f)) for row in rows if row.minimum_btuh is not None]
    if len(points) < 2:
        return None
    for (t0, d0), (t1, d1) in zip(points, points[1:], strict=False):
        if d0 == 0:
            return t0
        if (d0 < 0) != (d1 < 0):
            # Linear between the two rows, which is the same reading ``capacity_at`` takes
            # between them — so the crossover and the capacity cannot disagree about the
            # shape of the table.
            return t0 + (t1 - t0) * (-d0) / (d1 - d0)
    return None


@check(Tier.ADVISORY, "mep.heat_pump_turndown")
def heat_pump_turndown(ctx: CheckContext) -> list[Finding]:
    """Manual S: a modulating unit's MINIMUM output against the zone load it must settle at.

    The verdict is Manual S's own: the unit's **largest published minimum** against the
    **design** load, capped at 0.80. Walking the whole table is what finds that largest
    minimum — an inverter's floor moves with outdoor temperature and is rarely highest at
    the design row — but the denominator stays the design load, because that is what a
    sizing factor is and inventing a stricter ratio would be a rule this engine made up.

    **The crossover temperature is reported either way, including on a PASS**, and it is
    often the more useful sentence. catlin's System 2 passes the Manual S cap at 0.60 and
    still cycles above 27 °F, because its load falls faster than its floor does. The rule
    catches gross over-size; the crossover describes the year.

    Tri-state, and the third state is earned rather than assumed:

    * **UNKNOWN** — no ratings table, or a table with no ``minimum_btuh`` column at all
      (which is most manufacturer documents: NEEP's ccASHP database is the one public source
      that publishes one). An assumed turndown ratio would be exactly the invented input this
      package refuses.
    * **NOT_APPLICABLE** — every row states ``minimum == maximum``. That is positive evidence
      of a single-stage machine, which has no turndown to grade: it is on or off by design,
      and Manual S's minimum-compressor factor does not reach it. Per the fourth-verdict rule,
      N/A must be *earned*, and a table saying so is earning it.
    """
    from typehaus.takeoff.hvac import heating_zones

    cid = "mep.heat_pump_turndown"
    zones, _ = heating_zones(ctx.model, ctx.preferences)
    out: list[Finding] = []
    if not zones:
        return [_unknown(cid, "no Equipment carries a heating_ratings table")]
    for zone in zones:
        if not zone.rooms:
            continue
        tags = (zone.equipment_tag,)
        rows = zone.heating_ratings
        name = zone.type_tag or zone.equipment_tag
        if not rows:
            out.append(_unknown(
                cid, f"{zone.name}: {name} publishes no heating_ratings table, so there is "
                     "no minimum output to compare the load against", tags))
            continue
        # NOT_APPLICABLE is earned from positive evidence: every row says min == max.
        stated = [row for row in rows
                  if row.minimum_btuh is not None and row.maximum_btuh is not None]
        if stated and all(row.minimum_btuh == row.maximum_btuh for row in stated):
            out.append(_na(
                cid, f"{zone.name}: {name} is single-stage — every published row states the "
                     "same minimum and maximum output — so it has no turndown to grade. "
                     "Manual S's minimum-compressor sizing factor governs modulating "
                     "equipment; this unit is on or off by design", tags))
            continue
        with_minimum = [row for row in rows if row.minimum_btuh is not None]
        if not with_minimum:
            out.append(_unknown(
                cid, f"{zone.name}: {name}'s table states no minimum_btuh at any "
                     "temperature. Most manufacturer documents do not; NEEP's ccASHP "
                     "database (ashp.neep.org) is the one public source that does. A "
                     "turndown ratio assumed from the maximum would be an invented input",
                tags))
            continue
        if zone.design_temp_f is None:
            out.append(_unknown(cid, f"{zone.name}: Site.design_temp_heating is not "
                                     "authored, so there is no load curve to solve against",
                                tags))
            continue
        design_f = zone.design_temp_f
        if not (rows[0].outdoor_db_f <= design_f <= rows[-1].outdoor_db_f):
            out.append(_unknown(
                cid, f"{zone.name}: the site designs at {design_f:g} °F and {name}'s table "
                     f"spans {rows[0].outdoor_db_f:g} to {rows[-1].outdoor_db_f:g} °F, so "
                     "the design point is outside it and nothing is read by extrapolation",
                tags))
            continue
        load_at_design = zone.heating_load_btu_per_hour
        # **Manual S's sizing factor is against the DESIGN load**, which is the load the
        # equipment was selected for — not against the load at whatever temperature the row
        # happens to be. What walking the rows changes is the numerator: the minimum column
        # moves with temperature, so the binding figure is the HIGHEST minimum the unit will
        # ever be asked to sit at, and that is rarely the design row. catlin's System 1 has
        # its largest minimum at 5 °F (14,000 Btu/h), not at the −15 °F it designs for
        # (13,556 interpolated).
        worst = max(with_minimum, key=lambda row: row.minimum_btuh)
        factor = worst.minimum_btuh / load_at_design if load_at_design > 0 else float("inf")
        allowed = _MAX_MINIMUM_SIZING_FACTOR * load_at_design
        crossover = _crossover_temp_f(zone, with_minimum)
        where = (f"; it modulates down to the load only below {crossover:.1f} °F, and "
                 "cycles above it" if crossover is not None
                 else "; its minimum never meets the load anywhere in the published rows")
        detail = (
            f"{zone.name}: largest published minimum output {worst.minimum_btuh:,.0f} Btu/h "
            f"(at {worst.outdoor_db_f:g} °F) against a {load_at_design:,.0f} Btu/h design "
            f"load — a minimum-compressor sizing factor of {factor:.2f}, where Manual S "
            f"caps it at {_MAX_MINIMUM_SIZING_FACTOR:.2f} "
            f"({allowed:,.0f} Btu/h){where}")
        if factor > _MAX_MINIMUM_SIZING_FACTOR:
            out.append(_advisory_fail(
                cid, detail + ". SHORT-CYCLING: the unit cannot settle at the load, so it "
                              "runs in bursts — which costs efficiency, comfort and "
                              "compressor life, and no amount of capacity fixes it",
                tags))
        else:
            out.append(_pass(cid, detail, tags))
    return out

"""Grading a span against a published manufacturer table — the prescriptive read.

**Why this is a check and not an engineering item.** A published table is a document a
reviewer opens: they find the row, confirm the conditions, and the question is closed. That
is the same act as reading IRC Table R602.7(1), and it is not something a professional seal
adds anything to. The cladding set the precedent — PBR stays out of the engineering register
because three manufacturers publish a wall span table for it — and this module generalises
it: a ``PublishedSpan`` authored on the element turns what used to be an UNKNOWN waiting for
a seal into a PASS a reviewer can check.

``checks/_authoring.engineered()`` stays for what no table publishes.

**The refusals are the substance.** A quoted row is true for the row, not for the building
forever, so everything the row is indexed by is compared before the span is:

* the **member** the row is for, against the member the model now has;
* the **spacing** and the **carried span** the row is indexed by, where it has them;
* the row's own **load basis**, against the demand this check computed;
* and, since 2026-09-18, the conditions that used to be prose inside ``condition`` — the
  **service condition**, the **species and grade**, the **treatment**, the **minimum
  bearing**, the **deflection limit**, and whether the row is for load from **both sides**.

Any mismatch is UNKNOWN naming it — never a PASS off a stale quotation, and never a FAIL,
because a row that does not describe this building is silent about it rather than damning.
And a house that authors nothing gets UNKNOWN with the authoring hint, which is what
``engineered()``'s NO_CALC used to provide.

** AND A GUARD THE CALLER PASSES NOTHING FOR IS A MISMATCH TOO. ** Every comparison used to
require both sides to be present, so a row stating a condition the check had no value for
fell straight through to PASS — identical, from the outside, to a row that had been checked.
The glulam call omitted ``demand_psf`` entirely, which meant the load-basis guard never ran
on a single deck beam in the reference house.
"""

from __future__ import annotations

import re

from typehaus.checks._authoring import structural_advisory
from typehaus.findings import Finding, Result
from typehaus.model.published_cladding import PublishedCladdingLoad
from typehaus.model.refs import PublishedCapacity, PublishedSpan

#: How far a span may exceed the published row before it is a FAIL, in feet. Zero — a table
#: is a maximum and the whole value of reading one is that it does not get rounded.
_TOLERANCE_FT = 1e-6
#: The same zero, in pounds. A published allowable is a maximum and the whole value of
#: reading one is that it does not get rounded; this exists only to keep float noise out of
#: an equality.
_CAPACITY_TOLERANCE_LB = 1e-6


def graded_against_published(
    cid: str,
    subject: str,
    tags: tuple[str, ...],
    span_ft: float,
    published: PublishedSpan | None,
    member: str | None,
    *,
    spacing_in: float | None = None,
    carried_span_ft: float | None = None,
    demand_psf: float | None = None,
    service_condition: str | None = None,
    species_grade: str | None = None,
    treatment: str | None = None,
    bearing_in: float | None = None,
    deflection_limit: str | None = None,
    loads_both_sides: bool | None = None,
    fix: str | None = None,
) -> Finding:
    """One member, graded against the row authored on it. Always returns exactly one finding."""
    if published is None:
        return structural_advisory(
            cid, f"{subject} spans {span_ft:.1f}' and no published table row is authored "
                 f"for it", tags, Result.UNKNOWN,
            fix_hint=fix or "author a PublishedSpan naming the document, the row read, the "
                            "member it is for and the conditions it assumes")

    drift = _drift(published, member, spacing_in, carried_span_ft, demand_psf,
                   service_condition=service_condition, species_grade=species_grade,
                   treatment=treatment, bearing_in=bearing_in,
                   deflection_limit=deflection_limit, loads_both_sides=loads_both_sides)
    if drift is not None:
        return structural_advisory(
            cid, f"{subject}: the authored published row no longer describes this "
                 f"member — {drift}", tags, Result.UNKNOWN,
            fix_hint="re-read the table at the model's own condition and re-author the "
                     "PublishedSpan, or delegate the member to an engineered design")

    allowable_ft = published.span.feet
    if span_ft > allowable_ft + _TOLERANCE_FT:
        return structural_advisory(
            cid, f"{subject} spans {span_ft:.2f}', past the {allowable_ft:.2f}' its own "
                 f"published row allows ({published.table}; {published.source})",
            tags, Result.FAIL, code=published.source,
            fix_hint="shorten the span, read a heavier row, or have the member designed")

    return structural_advisory(
        cid, f"{subject} spans {span_ft:.2f}' — a prescriptive read of a published table: "
             f"{published.table}; {span_ft:.2f}' <= {allowable_ft:.2f}'; conditions the "
             f"engine does not check: {published.condition} ({published.source})",
        tags, Result.PASS, code=published.source)


def graded_against_published_capacity(
    cid: str,
    subject: str,
    tags: tuple[str, ...],
    demand_lb: float,
    published: PublishedCapacity | None,
    member: str | None,
    *,
    spacing_in: float | None = None,
    wind_speed_mph: float | None = None,
    exposure: str | None = None,
    fix: str | None = None,
) -> Finding:
    """One uplift joint, graded against the row authored on it. Always exactly one finding.

    The same four outcomes as :func:`graded_against_published`, in the same order and for the
    same reasons — nothing authored is UNKNOWN with the hint, a row that has drifted is
    UNKNOWN naming the drift, an exceeded row is a FAIL, and a covered one is a PASS quoting
    the conditions the engine does not check.

    **What is deliberately absent is an ``engineering_item``, and that absence is the whole
    mechanism.** This function is what takes a roof's uplift capacity out of the seal register:
    a demand this engine computes, against an allowable a reviewer can look up, is a
    prescriptive read and not something a stamp adds to. ``_authoring.engineered()`` remains
    for what no table publishes.

    ** THE COMPARISON IS DEMAND vs CAPACITY, NOT SPAN vs SPAN, AND THE FAIL IS REAL. ** A
    roof whose computed uplift exceeds the part somebody quoted gets a FAIL naming both
    numbers. That is the check working: an under-sized tie is a finding, not a reason to stop
    reading the table.
    """
    if published is None:
        return structural_advisory(
            cid, f"{subject} takes {demand_lb:,.0f} lb of uplift and no published capacity "
                 f"is authored for it", tags, Result.UNKNOWN,
            fix_hint=fix or "author a PublishedCapacity naming the document, the row read, "
                            "the part it is for and the conditions it assumes")

    drift = _capacity_drift(published, member, spacing_in, wind_speed_mph, exposure, demand_lb)
    if drift is not None:
        return structural_advisory(
            cid, f"{subject}: the authored published row no longer describes this joint — "
                 f"{drift}", tags, Result.UNKNOWN,
            fix_hint="re-read the table at the model's own condition and re-author the "
                     "PublishedCapacity, or delegate the joint to an engineered design")

    if demand_lb > published.capacity_lb + _CAPACITY_TOLERANCE_LB:
        return structural_advisory(
            cid, f"{subject} takes {demand_lb:,.0f} lb of uplift, past the "
                 f"{published.capacity_lb:,.0f} lb its own published row allows "
                 f"({published.table}; {published.source})",
            tags, Result.FAIL, code=published.source,
            fix_hint="upsize the connector, read a heavier row, or have the joint designed")

    return structural_advisory(
        cid, f"{subject} takes {demand_lb:,.0f} lb of uplift — a prescriptive read of a "
             f"published table: {published.table}; {demand_lb:,.0f} lb <= "
             f"{published.capacity_lb:,.0f} lb; conditions the engine does not check: "
             f"{published.condition} ({published.source})",
        tags, Result.PASS, code=published.source)


def _capacity_drift(published: PublishedCapacity, member: str | None,
                    spacing_in: float | None, wind_speed_mph: float | None,
                    exposure: str | None, demand_lb: float) -> str | None:
    """What stops this row from describing the joint, or ``None`` when nothing does."""
    if member is not None and _normalise(member) != _normalise(published.member):
        return f"the row is for {published.member!r} and the model now has {member!r}"
    if (spacing_in is not None and published.spacing is not None
            and abs(spacing_in - published.spacing.inches) > 0.01):
        return (f"the row is indexed at {published.spacing.inches:g}\" o.c. and the model is "
                f"framed at {spacing_in:g}\"")
    # ** INCREASE-ONLY, on the same reasoning as a carried span. ** A required force read at
    # 115 mph covers a building the site later derates to 105; the reverse is the error. The
    # exposure is not ordered that way and cannot be — B, C and D are categories, not a
    # ladder this check may walk — so ANY change to it drifts.
    if (wind_speed_mph is not None and published.wind_speed_mph is not None
            and wind_speed_mph > published.wind_speed_mph + 0.01):
        return (f"the row was read at {published.wind_speed_mph:g} mph and the site now "
                f"declares {wind_speed_mph:g} mph")
    if (exposure is not None and published.exposure is not None
            and str(exposure).strip().upper() != str(published.exposure).strip().upper()):
        return (f"the row was read at Exposure {published.exposure} and the site now "
                f"declares Exposure {exposure}")
    if published.demand_lb is not None and demand_lb > published.demand_lb + 0.01:
        return (f"the row was judged against {published.demand_lb:,.0f} lb and this check "
                f"computes {demand_lb:,.0f} lb")
    return None


def graded_against_published_cladding(
    cid: str,
    subject: str,
    tags: tuple[str, ...],
    demand_psf: float,
    direction: str,
    published: PublishedCladdingLoad | None,
    *,
    material_name: str,
    fastener_spacing_in: float,
    coverage_in: float | None,
    panel_fastener: str | None,
    support_is_wood: bool,
    support_thickness_in: float,
    governing_demand_psf: float,
    wind_speed_mph: float | None,
    exposure: str | None,
    fix: str | None = None,
) -> Finding:
    """One panel design, one wind direction, graded against the row on its Material.

    The four outcomes of :func:`graded_against_published_capacity`. ``direction`` is
    ``"outward"`` (suction) or ``"inward"``; the two allowables differ and either may
    govern. The PASS ends with the row's ``condition`` and then, always, its ``excludes``:
    the row covers the PANEL. The fastener is the maker's named screw at the maker's
    spacing — a CONDITION this read checks, not a capacity it computes;
    ``structural.cladding_fastener`` carries that arithmetic as an advisory.
    """
    if published is None:
        return structural_advisory(
            cid, f"{subject} takes {demand_psf:.1f} psf ASD {direction} and no published "
                 f"cladding load row is authored for it", tags, Result.UNKNOWN,
            fix_hint=fix or "author Material.published_cladding: the maker's allowable "
                            "uniform load table row, its fastener spacing and conditions")

    drift = _cladding_drift(
        published, material_name, fastener_spacing_in, coverage_in, panel_fastener,
        support_is_wood, support_thickness_in, governing_demand_psf, wind_speed_mph,
        exposure)
    excludes = f" Not covered by the row — {published.excludes}." if published.excludes else ""
    if drift is not None:
        return structural_advisory(
            cid, f"{subject}: the authored cladding row no longer describes this wall — "
                 f"{drift}.{excludes}", tags, Result.UNKNOWN,
            fix_hint="re-read the maker's table at the model's own condition and re-author "
                     "Material.published_cladding")

    allowable = (published.allowable_outward_psf if direction == "outward"
                 else published.allowable_inward_psf)
    if demand_psf > allowable + 1e-6:
        return structural_advisory(
            cid, f"{subject} takes {demand_psf:.1f} psf ASD {direction}, past the "
                 f"{allowable:g} psf its published row allows ({published.table}; "
                 f"{published.source}).{excludes}",
            tags, Result.FAIL, code=published.source,
            fix_hint="tighten the girt spacing to a heavier row, or change the panel")

    return structural_advisory(
        cid, f"{subject} takes {demand_psf:.1f} psf ASD {direction} — a prescriptive read of "
             f"a published table: {published.table}; {demand_psf:.1f} <= {allowable:g} psf "
             f"(d/c {demand_psf / allowable:.3f}); conditions the engine does not check: "
             f"{published.condition} ({published.source}).{excludes} The fastener is the "
             f"maker's named screw at the maker's spacing, graded here as a condition and "
             f"not a computed capacity; structural.cladding_fastener carries the NDS/AISI "
             f"arithmetic as an advisory.",
        tags, Result.PASS, code=published.source)


def _cladding_drift(published: PublishedCladdingLoad, material_name: str,
                    spacing_in: float, coverage_in: float | None,
                    panel_fastener: str | None, support_is_wood: bool,
                    support_thickness_in: float, demand_psf: float,
                    wind_speed_mph: float | None, exposure: str | None) -> str | None:
    """What stops a cladding row from describing the wall, or ``None``.

    The row lives on the Material, so a retype to another panel reaches no row at all; the
    ``member``/``gauge`` guards catch the Material itself being re-specified under it.
    """
    name = _normalise(material_name)
    if _normalise(published.member) not in name:
        return f"the row is for {published.member!r} and the material is {material_name!r}"
    if published.gauge is not None and _normalise(f"{published.gauge} ga") not in name:
        return (f"the row is for {published.gauge} ga and the material's name does not say "
                f"{published.gauge} ga")
    if published.coverage is not None:
        if coverage_in is None:
            return _unanswered("a panel coverage", f"{published.coverage.inches:g}\"")
        if abs(coverage_in - published.coverage.inches) > 0.01:
            return (f"the row is for {published.coverage.inches:g}\" coverage and the "
                    f"material declares {coverage_in:g}\"")
    # ** INCREASE-ONLY. ** A spacing-indexed table publishes MORE at TIGHTER spacing (this
    # panel: 58 psf at 2', 13 at 6'), so a wall girted at 18" is covered by the 2' row and
    # one girted at 3' is not.
    if spacing_in > published.fastener_spacing.inches + 0.01:
        return (f"the row is indexed at {published.fastener_spacing.inches:g}\" fastener "
                f"spacing and the girts here are {spacing_in:g}\" apart")
    if published.panel_fastener is not None:
        if panel_fastener is None:
            return _unanswered("a panel fastener", published.panel_fastener)
        screw = _fastener_drift(published.panel_fastener, panel_fastener)
        if screw is not None:
            return screw
    if published.min_support_thickness is not None:
        least = published.min_support_thickness.inches
        if not support_is_wood:
            return (f"the row accepts {published.support_material or 'wood'} and the "
                    f"support here is not wood")
        if support_thickness_in + 0.01 < least:
            return (f"the row needs {least:g}\" of support and the girt here is "
                    f"{support_thickness_in:g}\"")
    if published.demand_psf is not None and demand_psf > published.demand_psf + 0.01:
        return (f"the row was judged against {published.demand_psf:.2f} psf and this check "
                f"computes {demand_psf:.2f} psf")
    if (wind_speed_mph is not None and published.wind_speed_mph is not None
            and wind_speed_mph > published.wind_speed_mph + 0.01):
        return (f"the row was read at {published.wind_speed_mph:g} mph and the site now "
                f"declares {wind_speed_mph:g} mph")
    if (exposure is not None and published.exposure is not None
            and str(exposure).strip().upper() != str(published.exposure).strip().upper()):
        return (f"the row was read at Exposure {published.exposure} and the site now "
                f"declares Exposure {exposure}")
    return None


def drift_reason(published: PublishedSpan, member: str | None, *,
                 spacing_in: float | None = None, carried_span_ft: float | None = None,
                 demand_psf: float | None = None, service_condition: str | None = None,
                 species_grade: str | None = None, treatment: str | None = None,
                 bearing_in: float | None = None, deflection_limit: str | None = None,
                 loads_both_sides: bool | None = None) -> str | None:
    """:func:`_drift` by its public name, for a caller that is not minting the finding.

    ``checks/structural/deck.py`` needs the reason a supplier's row does not cover a glulam
    so its ENGINEERED record can say so — the row is real, the engine did read it, and a
    record that stayed silent about it would look like one that never looked.
    """
    return _drift(published, member, spacing_in, carried_span_ft, demand_psf,
                  service_condition=service_condition, species_grade=species_grade,
                  treatment=treatment, bearing_in=bearing_in,
                  deflection_limit=deflection_limit, loads_both_sides=loads_both_sides)


def _drift(published: PublishedSpan, member: str | None, spacing_in: float | None,
           carried_span_ft: float | None, demand_psf: float | None, *,
           service_condition: str | None = None, species_grade: str | None = None,
           treatment: str | None = None, bearing_in: float | None = None,
           deflection_limit: str | None = None,
           loads_both_sides: bool | None = None) -> str | None:
    """What stops this row from describing the model, or ``None`` when nothing does.

    ** A GUARD THE CALLER CANNOT ANSWER IS A MISMATCH, NOT AGREEMENT — AND THAT IS THE
    CHANGE OF 2026-09-18. ** Every clause below used to read ``if model_value is not None
    and row_value is not None``, so a row stating a condition the check passed nothing for
    fell through to PASS, indistinguishable from a row the check had actually compared. The
    glulam call in ``checks/structural/deck.py`` is what made it concrete: it omitted
    ``demand_psf`` entirely, so the load-basis comparison — the single most important guard
    on a span table — never ran on any deck beam in the house, and nothing said so.

    An author who states a guard is asking for it to be checked. Where the check has no
    value to check it with, the honest verdict is UNKNOWN naming the gap.
    """
    if published.member and member is None:
        return _unanswered("member", published.member)
    if member is not None and _normalise(member) != _normalise(published.member):
        return (f"the row is for {published.member!r} and the model now has "
                f"{member!r}")
    if published.spacing is not None and spacing_in is None:
        return _unanswered("an o.c. spacing", f"{published.spacing.inches:g}\"")
    if (spacing_in is not None and published.spacing is not None
            and abs(spacing_in - published.spacing.inches) > 0.01):
        return (f"the row is indexed at {published.spacing.inches:g}\" o.c. and the "
                f"model is framed at {spacing_in:g}\"")
    if published.carried_span is not None and carried_span_ft is None:
        return _unanswered("a carried span", f"{published.carried_span.feet:g}'")
    # Only an INCREASE drifts. A row read at a 10' joist span covers a beam picking up 7'
    # of joist; reading it the other way round would be the error.
    if (carried_span_ft is not None and published.carried_span is not None
            and carried_span_ft > published.carried_span.feet + 0.01):
        return (f"the row is indexed at a {published.carried_span.feet:g}' carried "
                f"span and this member picks up {carried_span_ft:.2f}'")
    if published.load_psf is not None and demand_psf is None:
        return _unanswered("a load basis", f"{published.load_psf:g} psf")
    if (demand_psf is not None and published.load_psf is not None
            and demand_psf > published.load_psf + 0.01):
        return (f"the row is published at {published.load_psf:g} psf and this check "
                f"computes {demand_psf:.1f} psf")

    # --- the conditions that used to be prose inside ``condition`` ----------------------
    for label, row_value, model_value in (
            ("a service condition", published.service_condition, service_condition),
            ("a species and grade", published.species_grade, species_grade),
            ("a treatment", published.treatment, treatment),
            ("a deflection limit", published.deflection_limit, deflection_limit)):
        if row_value is None:
            continue
        if model_value is None:
            return _unanswered(label, row_value)
        if _normalise(str(model_value)) != _normalise(str(row_value)):
            return (f"the row is for {label.split(' ', 1)[-1]} of {row_value!r} and this "
                    f"member is {model_value!r}")
    if published.min_bearing_in is not None:
        if bearing_in is None:
            return _unanswered("a minimum bearing",
                               f"{published.min_bearing_in:g}\"")
        if bearing_in + 0.01 < published.min_bearing_in:
            return (f"the row needs {published.min_bearing_in:g}\" of bearing and this "
                    f"member has {bearing_in:g}\"")
    if published.loads_both_sides is not None:
        if loads_both_sides is None:
            return _unanswered("load from both sides"
                               if published.loads_both_sides else "load from one side",
                               "yes" if published.loads_both_sides else "no")
        if bool(loads_both_sides) and not published.loads_both_sides:
            return ("the row is published for load from ONE side and this member picks up "
                    "load from both")
    return None


def _unanswered(what: str, row_value: str) -> str:
    """The row states a guard and the check had nothing to compare it with."""
    return (f"the row states {what} ({row_value}) and this check passes nothing for it, so "
            f"the condition is unverified — which is not the same as met")


#: ``#10-12 x 1-1/2" Pancake Head ...`` -> designation, length, the rest.
_SCREW = re.compile(r'^(#\s*\d+\s*-\s*\d+\s*x\s*)(\d+-\d+/\d+|\d+/\d+|\d*\.?\d+)\s*"(.*)$',
                    re.IGNORECASE)


def _fastener_drift(named: str, specified: str) -> str | None:
    """The maker's named screw must lead the material's — except in LENGTH, increase-only.

    The row excludes fasteners by its own footnote, so the named screw is a floor on thread
    in the support, not a panel condition: the same gauge, head and point made longer is
    still that screw (catlin's #10-12 x 1-1/2", D3). Shorter, or anything else, drifts.
    """
    if _normalise(specified).startswith(_normalise(named)):
        return None
    n, s = _SCREW.match(named.strip()), _SCREW.match(specified.strip())
    if (n and s and _normalise(n[1]) == _normalise(s[1])
            and _normalise(s[3]).startswith(_normalise(n[3]))):
        if _inches(s[2]) + 1e-6 >= _inches(n[2]):
            return None
        return (f"the maker names {named!r} and the material specifies a shorter "
                f"{s[2]}\" screw")
    return f"the maker names {named!r} and the material specifies {specified!r}"


def _inches(token: str) -> float:
    """``1``, ``1.5``, ``3/4`` or ``1-1/2``."""
    whole, _, frac = token.rpartition("-")
    if "/" not in frac:
        return float(frac)
    num, den = frac.split("/")
    return float(whole or 0) + float(num) / float(den)


def _normalise(member: str) -> str:
    """Member spellings differ in punctuation and case, never in substance.

    ``'2-ply 14" LVL'`` and ``'2-PLY 14" LVL'`` are the same member; ``'2-ply 14" LVL'`` and
    ``'11.875 TJI 230'`` are not, and no normalisation should make them look alike.
    """
    return "".join(ch for ch in member.lower() if ch.isalnum())

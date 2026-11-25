"""Grading a cladding panel's wind demand against its maker's published load row.

The cladding sibling of ``published.py``: one row on the panel's Material
(``PublishedCladdingLoad``), the same drift-guard discipline (a row that does not describe
the wall is UNKNOWN naming why, never a PASS), graded in both wind directions. The row is an
ASD allowable (Metal Sales) or an ULTIMATE pressure (ESR-1301 Table 3A): each is compared
against the demand at its own level, and the finding prints which.

An ``off_label`` row is a known, owner-accepted departure the engine cannot see (LP over
strapping): it keeps the finding UNKNOWN even when every guard agrees.
"""

from __future__ import annotations

from typehaus.checks._authoring import structural_advisory
from typehaus.checks.structural.published import _fastener_drift, _normalise, _unanswered
from typehaus.findings import Finding, Result
from typehaus.model.published_cladding import PublishedCladdingLoad


def _unit(published: PublishedCladdingLoad) -> str:
    return "psf ultimate" if published.basis == "ultimate" else "psf ASD"


def _estimate(published: PublishedCladdingLoad, allowable: float, demand_psf: float,
              spacing_in: float) -> str:
    """The row scaled to a wider support spacing, labelled an estimate, or ``""``.

    Only for a row authored as fastener-governed: each field fastener then carries a
    tributary load proportional to the spacing, so the row falls by ``row / model``.
    """
    row = published.fastener_spacing.inches
    if not published.fastener_governed or spacing_in <= row + 0.01:
        return ""
    scaled = allowable * row / spacing_in
    return (f" Estimate, not a code read: the row is fastener-governed, so at "
            f"{spacing_in:g}\" supports it scales by {row:g}/{spacing_in:g} to "
            f"{scaled:.1f} {_unit(published)}, and {demand_psf:.1f} against that is d/c "
            f"{demand_psf / scaled:.2f}.")


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

    ``demand_psf`` is at the row's own level (``published.basis``: ASD or ultimate);
    ``governing_demand_psf`` stays ASD, for the increase-only guard. The four outcomes of
    :func:`published.graded_against_published_capacity`. ``direction`` is ``"outward"``
    (suction) or ``"inward"``; the two allowables differ and either may govern. The PASS ends
    with the row's ``condition`` and then, always, its ``excludes``:
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
    unit = _unit(published)
    allowable = (published.allowable_outward_psf if direction == "outward"
                 else published.allowable_inward_psf)
    if published.off_label:
        drift = f"{drift}; {published.off_label}" if drift else published.off_label
    excludes = f" Not covered by the row — {published.excludes}." if published.excludes else ""
    if drift is not None:
        estimate = _estimate(published, allowable, demand_psf, fastener_spacing_in)
        note = f" {published.off_label_note}" if published.off_label_note else ""
        return structural_advisory(
            cid, f"{subject} takes {demand_psf:.1f} {unit} {direction}: the authored "
                 f"cladding row ({published.source}) does not describe "
                 f"this wall — {drift}.{estimate}{note}{excludes}", tags, Result.UNKNOWN,
            fix_hint="re-read the maker's table at the model's own condition and re-author "
                     "Material.published_cladding")

    if demand_psf > allowable + 1e-6:
        return structural_advisory(
            cid, f"{subject} takes {demand_psf:.1f} {unit} {direction}, past the "
                 f"{allowable:g} psf its published row allows ({published.table}; "
                 f"{published.source}).{excludes}",
            tags, Result.FAIL, code=published.source,
            fix_hint="tighten the girt spacing to a heavier row, or change the panel")

    return structural_advisory(
        cid, f"{subject} takes {demand_psf:.1f} {unit} {direction} — a prescriptive read of "
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


"""Every exposed eave rib is closed exactly once, against what the roof's pans actually do.

The expected set comes from the resolved pan ends (a rib sits between two neighbouring pans),
not from the seam register the records were derived from, so drift between them is caught.
Catalog eave coverage says nothing about this: a covered eave can still have open ribs.
"""

from __future__ import annotations

from collections import Counter

from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import failed, not_applicable, passed, unknown
from typehaus.library.trim.image_ii_eave_sealing import EAVE_RIB_SEALING_BY_KIT
from typehaus.quantities import M_PER_IN
from typehaus.resolve.model_eave_sealing import EAVE_PAN_CONNECTIONS
from typehaus.resolve.roof_edge_geometry import abutted_run_keys, roof_edge_runs
from typehaus.resolve.roof_image_ii import roof_edge_kit

COVERAGE = "integrity.eave_rib_sealing"
SPEC_STATUS = "advisory.eave_rib_sealing_spec"
_MATCH_TOLERANCE_M = 0.125 * M_PER_IN
#: Neighbouring pans closer than this share a rib; further apart, something is missing.
_MAX_RIB_GAP_M = 2 * M_PER_IN


def expected_rib_stations(model, roof) -> dict[str, list[float]]:
    """Run key -> stations of the ribs between neighbouring resolved pan ends."""
    along = 0 if roof.ridge_direction == "x" else 1
    xs, ys = zip(*roof.footprint, strict=True)
    middle = ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2)
    abutted = abutted_run_keys(model, roof)
    expected = {}
    for run in roof_edge_runs(roof):
        if not run.is_eave or run.key in abutted:
            continue
        spans = sorted(
            sorted((member.p0[along], member.p1[along])) for member in roof.members
            if member.connection in EAVE_PAN_CONNECTIONS
            and (member.p0[0] - middle[0]) * run.normal[0]
            + (member.p0[1] - middle[1]) * run.normal[1] > 0)
        expected[run.key] = [(a[1] + b[0]) / 2 for a, b in zip(spans, spans[1:], strict=False)
                             if b[0] - a[1] <= _MAX_RIB_GAP_M]
    return expected


def _unmatched(want: list[float], have: list[float]) -> tuple[list[float], list[float]]:
    missing, spare = [], list(have)
    for station in want:
        near = [s for s in spare if abs(s - station) <= _MATCH_TOLERANCE_M]
        if near:
            spare.remove(near[0])
        else:
            missing.append(station)
    return missing, spare


@check(Tier.INTEGRITY, COVERAGE)
def eave_rib_sealing(ctx: CheckContext) -> list:
    model = ctx.model
    roofs = [roof for roof in model.roofs if roof_edge_kit(model, roof)]
    if not roofs:
        return [not_applicable(COVERAGE, "no roof declares a panel edge-trim kit")]
    runs = {(run.roof_tag, run.run_key): run for run in model.eave_sealing_runs}
    findings, closed = [], 0
    for roof in roofs:
        for run_key, want in expected_rib_stations(model, roof).items():
            run = runs.get((roof.tag, run_key))
            ends = run.rib_ends if run is not None else ()
            tag = f"{roof.tag}:{run_key}"
            for key, count in Counter(end.key for end in ends).items():
                if count > 1:
                    findings.append(failed(COVERAGE, f"{key} is recorded {count} times",
                                           (roof.tag,)))
            for end in ends:
                if end.treatment is None:
                    findings.append(unknown(
                        COVERAGE, f"{end.key} ({end.cavity}) has no resolved treatment",
                        (roof.tag,), fix="inspect the actual cavity and specify its closure"))
            treated = [end.station_m for end in ends if end.treatment is not None]
            unresolved = [end.station_m for end in ends if end.treatment is None]
            missing, spare = _unmatched(want, treated + unresolved)
            for station in missing:
                findings.append(failed(
                    COVERAGE, f"{tag}: exposed rib at {station:.3f} m has no treatment record",
                    (roof.tag,)))
            for station in spare:
                findings.append(failed(
                    COVERAGE, f"{tag}: treatment at {station:.3f} m matches no exposed rib",
                    (roof.tag,)))
            closed += len(treated)
    if not findings:
        findings.append(passed(COVERAGE, f"{closed} exposed eave rib ends each close once"))
    return findings


@check(Tier.ADVISORY, SPEC_STATUS)
def eave_rib_sealing_spec(ctx: CheckContext) -> list:
    """Open product and dimension data, kept visible and outside the permit gate."""
    kits = {run.kit for run in ctx.model.eave_sealing_runs if run.rib_ends}
    if not kits:
        return [not_applicable(SPEC_STATUS, "no eave has exposed panel rib ends")]
    findings = []
    for kit in sorted(kits):
        spec = EAVE_RIB_SEALING_BY_KIT.get(kit)
        if spec is None:
            findings.append(unknown(SPEC_STATUS, f"no eave sealing specification for kit {kit}"))
            continue
        for item in spec.open_items():
            findings.append(unknown(
                SPEC_STATUS, f"{kit}: {item}",
                fix="confirm from current manufacturer data; see "
                    "notes/roof_eave_rib_end_sealing.md"))
        if not spec.open_items():
            findings.append(passed(SPEC_STATUS, f"{kit}: sealing data is fully sourced"))
    return findings

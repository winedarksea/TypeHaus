"""What the print came out as: the scale, the pieces, and everything left out and why."""

from __future__ import annotations

from collections import Counter

from typehaus.print3d.build import PrintRun
from typehaus.print3d.pieces import scale_name

_WORST = 5


def report_lines(run: PrintRun, settings, files: list[str]) -> list[str]:
    lines = [f"# print3d — 1:{run.scale} ({scale_name(run.scale)})", "",
             f"Bed {_mm(settings.bed_mm)}, margin {settings.margin_mm:g} mm; min feature "
             f"{settings.feature_mm:g} mm, min wall {settings.wall_mm:g} mm, max thicken "
             f"{settings.max_thicken:g}x.", "", "## Pieces", "",
             "| piece | size (mm) | shells | support (mm²) | orientation | islands dropped |",
             "|---|---|---|---|---|---|"]
    for piece in run.pieces:
        lines.append(f"| {piece.name} | {_mm(piece.dims_mm)} | {piece.shells} | "
                     f"{piece.support_mm2:.0f} | "
                     f"{piece.orientation} | {_islands(piece.islands_mm3)} |")
    lines += ["", "Cuts: " + ", ".join(f"{band.name} {band.z0:+.2f}..{band.z1:+.2f} m"
                                       for band in run.bands), "", "## Kept, thickened, dropped",
              "", "| kind | kept | thickened | too thin | dropped by policy |",
              "|---|---|---|---|---|"]
    thickened = Counter(result.item.kind for result in run.thickened)
    thin = Counter(result.item.kind for result in run.too_thin)
    for kind in sorted(set(run.kept) | set(thin) | set(run.dropped)):
        lines.append(f"| {kind} | {run.kept.get(kind, 0)} | {thickened.get(kind, 0)} | "
                     f"{thin.get(kind, 0)} | {run.dropped.get(kind, 0)} |")
    if run.thickened:
        lines += ["", "Most thickened: " + ", ".join(
            f"{result.item.tag} {result.thin_mm:.2f} mm x{result.factor:.2f}" for result in
            sorted(run.thickened, key=lambda result: -result.factor)[:_WORST])]
    dropped_bodies = [result for result in run.too_thin if result.item.treatment.value != "trim"]
    if dropped_bodies:
        lines += ["", f"Dropped past {settings.max_thicken:g}x: " + ", ".join(
            f"{result.item.tag} ({result.item.kind}, {result.thin_mm:.2f} mm)" for result in
            sorted(dropped_bodies, key=lambda result: result.thin_mm)[:_WORST * 4])]
    lines += ["", f"## Furniture: {len(run.furniture)} printable, {len(run.rejected)} rejected", ""]
    for piece in run.furniture:
        lines.append(f"- {piece.name}: {_mm(piece.dims_mm)}")
    reasons = Counter(rejection.reason.split(" ")[0] for rejection in run.rejected)
    if run.rejected:
        lines.append("")
        lines += [f"- {rejection.tag}: {rejection.reason}" for rejection in run.rejected]
        lines += ["", "Rejected by first failing test: " + ", ".join(
            f"{reason} {count}" for reason, count in reasons.most_common())]
    lines += ["", "## Files", "", *(f"- {name}" for name in files), "", "## Timings", "",
              ", ".join(f"{stage} {seconds:.2f} s" for stage, seconds in run.timings.items())]
    return lines


def _mm(dims) -> str:
    return " x ".join(f"{value:.1f}" for value in dims)


def _islands(volumes: list[float]) -> str:
    return f"{len(volumes)} ({sum(volumes):.1f} mm³)" if volumes else "0"

"""``mep.run_in_slab`` — a run may not lie INSIDE a pour that nobody cast a void for.

The hole ``houses/catlin/preferences.toml`` has named since the supply bands moved: east of
the centre line the basement ceiling is ``SL-M-DECK``, a cast deck with its soffit at
-1'-1.4", and a pipe on the new cold band there is **4.6" inside concrete**. Nothing graded
it. ``mep.run_in_finished_volume`` measures hang below a ceiling, ``mep.run_member_crossing``
reads framed members, and ``mep.sleeve_coverage`` asks about a run passing THROUGH a pour —
none of the three has a question whose answer is "this run is buried in it".

**What another check already reports is not reported again.** Every contact within
:data:`CROSSING_TOL_M` of a crossing ``concrete_crossings`` found is dropped here, and that
dedupe is **mandatory** rather than a nicety: without it every through-crossing reports
twice, once as a missing sleeve and once as embedment, and a reader cannot tell which one to
act on.

What survives the dedupe is therefore two shapes, and the finding states the measurement
rather than guessing which: a run lying ALONG a band (nothing else in the engine sees it),
and a run passing THROUGH one that ``concrete_crossings`` never walked. The second was how
``DU-B-ERV-R-PLAY`` was found through catlin's 12" centre wall, back when that walk covered
pipe and raceway only; it walks ducts too now, so the case is a residue, not a gap.

Three more things are not this defect:

* **under-slab is not in-slab.** A drain below a slab-on-grade is where a drain belongs, and
  its prism's top lying at or below the band's bottom says so. So is a run laid on top of it.
* **a void somebody authored.** A ``RoughOpening`` whose ``penetration_for`` names the run,
  on the host it is in, is a hole cast on purpose.
* **a clip.** Under :data:`MIN_EMBEDDED_M` of a run inside a band is a vertex landing on a
  face, not a length of pipe in a pour.

The measure is the CENTRELINE's length inside the host's footprint, not the envelope's area:
a prism is the run plus its lagging, and what a reader needs is how many feet of pipe to
move. **The elevation is read over the CLIPPED length, never over the whole leg** — the
banding error ``mep.run_interference`` shed on 2026-09-19, and it is just as wrong here: a
drain that leaves a wall at -10.8" and falls to -12.9" eight feet later is not inside the
wall because its far end drops below the wall's top.

``Tier.STRUCTURAL`` and **no ``PermitItemSpec``**, the footing ``mep.run_interference`` and
``mep.run_member_crossing`` share: no IRC section says "do not draw a pipe inside a slab"
and a CODE tier would trip the coverage test and the ``code_ref`` requirement dishonestly.
``CheckReport.counts()`` counts any ``Result.FAIL`` regardless of severity, so the weight is
the same where it matters.
"""

from __future__ import annotations

from typehaus.checks._authoring import failed as _fail
from typehaus.checks._authoring import not_applicable as _na
from typehaus.checks._authoring import passed as _pass
from typehaus.checks.mep._format import feet_inches
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.quantities import M_PER_IN

_CID = "mep.run_in_slab"

#: A contact this close to a crossing ``mep.sleeve_coverage`` already reports is that
#: crossing seen from the other side. 4" is the tolerance the sleeve matcher itself uses
#: (``mep_concrete._SLEEVE_MATCH_TOL_M``), so the two readings agree by construction.
CROSSING_TOL_M = 0.1

#: Below this there is no length of pipe in the pour — a vertex landing on a face, or a
#: corner clipped by a turn. Half a foot.
MIN_EMBEDDED_M = 0.1524


def _clipped_band(line, inside, za: float, zb: float, grow: float) -> tuple[float, float]:
    """The run's surface z band over the part of the leg that is inside the host.

    ``line.project`` gives the arc-length of each end of the clipped piece, and the
    centreline z is affine in it. Reading the whole leg's range instead is how a run that
    merely STARTS at a wall reads as buried in it.
    """
    total = max(line.length, 1e-12)
    ends = [line.project(inside.interpolate(t, normalized=True)) / total for t in (0.0, 1.0)]
    zs = [za + (zb - za) * t for t in ends]
    return min(zs) - grow, max(zs) + grow


@check(Tier.STRUCTURAL, _CID)
def run_in_slab(ctx: CheckContext) -> list[Finding]:
    """Every run segment against every cast band, with the through-crossings taken out."""
    from shapely.geometry import LineString, Point

    from typehaus.resolve.mep_concrete import concrete_crossings, concrete_hosts
    from typehaus.resolve.mep_envelopes import (
        insulation_thickness_m,
        opening_prisms,
        run_polylines,
        run_sections,
    )

    hosts = concrete_hosts(ctx.model)
    if not hosts:
        # Earned from positive evidence of absence: this model resolves no concrete solid,
        # cast beam or foundation wall, so there is no pour for a run to be inside.
        return [_na(_CID, "no concrete solid, cast beam or foundation wall resolves in this "
                          "model, so no run can be embedded in one", ())]

    crossings = [(row["run"], row["host"], Point(row["point"]))
                 for row in concrete_crossings(ctx.model)]
    authorised = {(name, host) for _tag, _door, host, _prism, _low, _high, names
                  in opening_prisms(ctx.model) for name in names}
    sections = run_sections(ctx.model)

    worst: dict[tuple[str, str], tuple[float, float, tuple[float, float], int]] = {}
    for _kind, tag, path, z in run_polylines(ctx.model):
        if len(path) < 2 or len(z) != len(path):
            continue
        _half_w, half_d, insulation = sections.get(tag, (0.0, 0.0, None))
        grow = half_d + (insulation_thickness_m(insulation) or 0.0)
        for leg in range(len(path) - 1):
            a, b = path[leg], path[leg + 1]
            if a == b:
                continue  # a riser has no plan length to lie ALONG a band
            line = LineString((a, b))
            for host_tag, _category, footprint, band_low, band_high in hosts:
                if (tag, host_tag) in authorised:
                    continue
                inside = line.intersection(footprint)
                length_m = getattr(inside, "length", 0.0)
                if length_m < MIN_EMBEDDED_M:
                    continue
                low, high = _clipped_band(line, inside, z[leg], z[leg + 1], grow)
                if high <= band_low + 1e-9 or low >= band_high - 1e-9:
                    continue
                middle = inside.interpolate(0.5, normalized=True)
                if any(run == tag and host == host_tag
                       and where.distance(middle) <= CROSSING_TOL_M
                       for run, host, where in crossings):
                    continue
                cover = min(band_high - high, low - band_low)
                key = (tag, host_tag)
                if key not in worst or length_m > worst[key][0]:
                    worst[key] = (length_m, cover, (middle.x, middle.y), leg)

    out: list[Finding] = [
        _fail(_CID,
              f"{run} is inside {host}: {length / M_PER_IN / 12:.1f} ft of leg "
              f"{segment + 1} is within the pour at "
              f"({feet_inches(point[0])}, {feet_inches(point[1])}), with "
              + (f"{cover / M_PER_IN:.1f}\" of concrete between it and the nearer face"
                 if cover > 0 else "its own envelope breaking a face of the band")
              + ". Nothing casts a void for it: no rough opening names the run and this "
                "host, and `mep.sleeve_coverage` reports no crossing of this run here",
              (run, host),
              fix="move the run out of the pour — `haus route --run <tag> --avoid "
                  f"{host}` proposes a lane — or author the void: a SleevePenetration where "
                  "it passes through, a RoughOpening naming it where it does not")
        for (run, host), (length, cover, point, segment) in sorted(worst.items())]

    if not out:
        out.append(_pass(_CID, f"no run lies along any of the {len(hosts)} cast bands in "
                               "this model", ()))
    return out

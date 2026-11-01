"""Every metal panel's top end has a girt behind it, for the screw through its top.

BBD75 p. 40 puts a panel fastener through the nail strip at the lower panel's top, under the
Transition Trim, and a panel's top end anywhere else is screwed the same way. A panel top is
backed when a course of the wall's girt band overlaps its top inch along the whole run:
under a BBD75 band, under a window sill, and at a level wall's head where no panel runs on
above. A raked head is backed by its rake nailer (``furring._rake_nailers``).
"""

from __future__ import annotations

from typehaus.checks.integrity.cladding_trim_runs import spans_cover
from typehaus.findings import failed, passed
from typehaus.quantities import M_PER_IN
from typehaus.resolve.cladding_trim.bands import band_spans
from typehaus.resolve.cladding_trim.runs import covered_below, metal_faces
from typehaus.resolve.framing.truss_girts import truss_girt_bands
from typehaus.resolve.rainscreen_strips import BAND_PANEL_BACKING_IN, band_panel_top

_CITE = "BBD75 Install Guide 10/2025 p. 40"
_METAL = {"board-and-batten", "ribbed-panel", "corrugated"}
#: A course is held back half a board from a corner or a post it butts.
_END_ALLOWANCE_M = 1.0 * M_PER_IN
_TOL = 1e-6


def _station(point, d) -> float:
    return point[0] * d[0] + point[1] * d[1]


def _tops(model, face, faces, band_name):
    """``(z, s0, s1, what)`` for each panel top on one cladding face.

    An opening the girts are drilled through rather than framed around (a hose bibb) leaves
    the panel whole, with a hole in it, not a top."""
    from typehaus.resolve.framing.openings import framed_around

    wall = face.wall
    tops = [(band_panel_top(joint), s0, s1, f"band at {joint / M_PER_IN:.0f} in")
            for joint, s0, s1 in band_spans(model, wall)]
    tops += [(wall.base_ref_z_m + opening.sill_m, a, b, f"{opening.tag} sill")
             for opening, a, b in face.openings(model)
             if opening.kind in ("window", "rough_opening")
             and framed_around(opening, wall, band_name)]
    raked = (wall.top_z0_m is not None and wall.top_z1_m is not None
             and abs(wall.top_z0_m - wall.top_z1_m) > _TOL)
    if not raked and not any(covered_below(other, [face]) for other in faces
                             if other is not face):
        tops.append((face.z1, face.lo, face.hi, "head"))
    return tops


def panel_top_girts(ctx, rule: str) -> list:
    model = ctx.model
    faces = list(metal_faces(model, _METAL))
    backing = BAND_PANEL_BACKING_IN * M_PER_IN
    bare, checked = {}, 0
    for face in faces:
        bands = truss_girt_bands(model.plan, face.wall.assembly)
        if bands is None:
            continue
        girts = [(*sorted((_station(m.p0, face.d), _station(m.p1, face.d))), m.z0_m, m.z1_m)
                 for m in face.wall.members
                 if f"-{bands[1].name}-" in m.child_key and m.p0 != m.p1]
        if not girts:
            continue
        # Past the band's own run, at a corner, the panel is on the return wall's girts.
        run_lo, run_hi = min(g[0] for g in girts), max(g[1] for g in girts)
        for z, s0, s1, what in _tops(model, face, faces, bands[1].name):
            spans = [(a, b) for a, b, z0, z1 in girts if z0 < z - _TOL and z1 > z - backing]
            lo, hi = max(s0, run_lo) + _END_ALLOWANCE_M, min(s1, run_hi) - _END_ALLOWANCE_M
            checked += 1
            if hi > lo and not spans_cover(spans, lo, hi):
                bare.setdefault(what, []).append(face.wall.tag)
    if bare:
        return [failed(rule, f"no girt behind the panel top's last "
                             f"{BAND_PANEL_BACKING_IN:g} in at the {what} on "
                             f"{len(tags)} wall(s)", tuple(sorted(tags)), code=_CITE)
                for what, tags in sorted(bare.items())]
    if checked:
        return [passed(rule, f"{checked} metal panel tops (bands, sills, level heads) have a "
                             "girt behind their top inch", code=_CITE)]
    return []

"""The gutter girt: a flat girt in the closure's girt layer, screwed back into the eave blocking.

Only where a roof has eave blocking (``Roof.eave_blocking``) — the girt's screws need
something to land in. Per side of blocks, and per closure furring band on that side:

* one flat girt on the band's centreline, as tall as the blocking and spanning the rafter
  field (the gable girts own the corner square beyond it);
* one multi-ply standoff at each bay centre, filling sheathing face to girt — never on a
  rafter line, where it would land on a flange instead of a block;
* the band's own bottom raised to the girt's top, so the two do not share volume.

Sizing (a 2x6 girt, two screws per standoff) is ``notes/eave_gutter_girt.md`` in catlin.
"""

from __future__ import annotations

from dataclasses import replace

from typehaus.resolve.framing.furring import STRAPPING_CATEGORY
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.framing.roof_eave import EAVE_BLOCKING_CONNECTION
from typehaus.resolve.framing.truss_common import BLOCK_CATEGORY
from typehaus.resolve.model import FramedMember, ResolvedRoof

EAVE_GIRT_CONNECTION = "eave:gutter-girt"
#: The girt and its standoff plies. 2x6, not the wall's 2x4: the gutter's couple needs the
#: 5-1/2" lever between two screws (notes/eave_gutter_girt.md §3).
EAVE_GIRT_MEMBER = "2x6"
_PLY_M = cross_section(EAVE_GIRT_MEMBER).width_m
_BAND_REACH_M = 0.3
_TOL_M = 1e-6


def eave_girts(
    roof: ResolvedRoof, closure: tuple[FramedMember, ...]
) -> tuple[tuple[FramedMember, ...], tuple[FramedMember, ...]]:
    """``(closure with trimmed girt bands, the girts and standoffs)``."""
    blocks = [m for m in roof.members if m.connection == EAVE_BLOCKING_CONNECTION]
    if not blocks:
        return closure, ()
    span_ax = 1 if roof.ridge_direction == "x" else 0
    ridge_ax = 1 - span_ax
    rafters = [m for m in roof.members if m.category == "rafter"]
    trimmed = {id(m): m for m in closure}
    added: list[FramedMember] = []
    for side, out in (("lo", -1.0), ("hi", 1.0)):
        side_blocks = [b for b in blocks if b.child_key.startswith(f"eave-block-{side}-")]
        if not side_blocks:
            continue
        block = side_blocks[0]
        outer = block.p0[span_ax] + out * cross_section(block.profile).width_m / 2.0
        z0, z1 = block.z0_m, block.z1_m
        on_cut = [r for r in rafters if abs(r.p0[span_ax] - outer) < 1e-4]
        lo = min(r.p0[ridge_ax] - cross_section(r.profile).width_m / 2.0 for r in on_cut)
        hi = max(r.p0[ridge_ax] + cross_section(r.profile).width_m / 2.0 for r in on_cut)
        centres = sorted((b.p0[ridge_ax] + b.p1[ridge_ax]) / 2.0 for b in side_blocks)
        for band in closure:
            if not _eave_band(band, span_ax, outer, out, z1):
                continue
            wall_tag = band.child_key.split("-closure-")[0]
            a = max(lo, min(band.p0[ridge_ax], band.p1[ridge_ax]))
            b = min(hi, max(band.p0[ridge_ax], band.p1[ridge_ax]))
            if b - a <= _TOL_M:
                continue
            axis = band.p0[span_ax]
            girt_inner = axis - out * _PLY_M / 2.0
            sheathing = _sheathing_face(closure, band, span_ax, out)
            standoff_m = out * (girt_inner - (outer if sheathing is None else sheathing))
            plies = max(1, round(standoff_m / _PLY_M))
            profile = EAVE_GIRT_MEMBER if plies == 1 else f"{plies}-{EAVE_GIRT_MEMBER}"
            added.append(FramedMember(
                roof.uid, f"{wall_tag}-eave-girt", STRAPPING_CATEGORY, EAVE_GIRT_MEMBER,
                _pt(span_ax, axis, a), _pt(span_ax, axis, b), z0, z1, b - a,
                connection=EAVE_GIRT_CONNECTION, material=band.material,
            ))
            ply_axis = girt_inner - out * standoff_m / 2.0
            orient = _pt(span_ax, out, 0.0)
            for index, station in enumerate(c for c in centres if a - _TOL_M <= c < b - _TOL_M):
                point = _pt(span_ax, ply_axis, station)
                added.append(FramedMember(
                    roof.uid, f"{wall_tag}-eave-girt-block-{index:03d}", BLOCK_CATEGORY,
                    profile, point, point, z0, z1, z1 - z0, orient=orient,
                    connection=EAVE_GIRT_CONNECTION, material=band.material,
                ))
            if band.z1_m > z1 and band.z0_m < z1:
                trimmed[id(band)] = replace(band, z0_m=z1, z0_end_m=z1)
    return tuple(trimmed[id(m)] for m in closure), tuple(added)


def _eave_band(band: FramedMember, span_ax: int, outer: float, out: float, z1: float) -> bool:
    """A furring closure band parallel to the eave, just outboard of the blocks' cut plane."""
    if band.category != "furring" or "-closure-" not in band.child_key:
        return False
    if abs(band.p0[span_ax] - band.p1[span_ax]) > _TOL_M:
        return False
    reach = out * (band.p0[span_ax] - outer)
    return 0.0 < reach < _BAND_REACH_M and band.z0_m < z1


def _sheathing_face(closure: tuple[FramedMember, ...], band: FramedMember, span_ax: int,
                    out: float) -> float | None:
    """The outer face of the same wall's sheathing closure band, when it has one."""
    wall_tag, rest = band.child_key.split("-closure-", 1)
    prefix = f"{wall_tag}-closure-{rest.split('-', 1)[0]}-"
    for m in closure:
        if m.category == "sheathing" and m.child_key.startswith(prefix):
            half = cross_section(m.profile).width_m / 2.0
            return m.p0[span_ax] + out * half
    return None


def _pt(span_ax: int, span: float, along: float) -> tuple[float, float]:
    return (span, along) if span_ax == 0 else (along, span)

"""``integrity.wall_penetration_closure``: every metal-wall crossing and mount is closed (#142).

Reads ``model.wall_penetrations`` / ``mount_blocks`` (``resolve/wall_penetrations.py``):

* each crossing has a sleeve row and a closure (boot, inlet, escutcheon or block);
* a boot, inlet or escutcheon lies within one flat (``panel_flats``); a boot whose row
  ``conforms_to_ribs`` laps features up to ``bridgeable_rib_height``; one trimmed to a batten
  face passes only with at least its row's ``min_trimmed_seal`` left between pipe and cut;
* a sleeve clears the girts (``STRAPPING_CATEGORY`` members);
* a strap block sits within one flat, ``batten_clearance`` off its edges, no wider than its
  row;
* a block or strut clears the base, band, corner and opening trim.
"""

from __future__ import annotations

from typing import Any

from typehaus.checks._authoring import failed, not_applicable, passed
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.quantities import M_PER_IN

_CID = "integrity.wall_penetration_closure"
_TOL_M = 1e-3


def _in(m: float) -> str:
    return f'{m / M_PER_IN:.2f}"'


@check(Tier.INTEGRITY, _CID)
def wall_penetration_closure(ctx: CheckContext) -> list[Finding]:
    from typehaus.resolve.mount_blocks import penetration_standard

    model = ctx.model
    pens, mounts = model.wall_penetrations, model.mount_blocks
    standard = penetration_standard(ctx.plan)
    if standard is None or not (pens or mounts):
        return [not_applicable(_CID, "no metal-wall crossing or exterior mount")]
    out: list[Finding] = []
    flats = _FlatCache(model, standard.bridgeable_rib_height.meters)
    for pen in pens:
        out.extend(_pen_findings(model, pen, flats))
    for mount in mounts:
        out.extend(_mount_findings(model, standard, mount, flats))
    if out:
        return out
    return [passed(_CID, f"{len(pens)} crossings and {len(mounts)} mounts closed, each on "
                         "its flat, sleeves clear of the girts, blocks clear of the trim")]


class _FlatCache:
    def __init__(self, model: Any, bridge_m: float) -> None:
        from typehaus.resolve.panel_flats import layout_datums

        self.model, self.bridge, self.datums, self.cache = model, bridge_m, layout_datums(
            model), {}

    def get(self, wall_tag: str, bridged: bool) -> list[tuple[float, float]]:
        from typehaus.resolve.panel_flats import panel_flats

        key = (wall_tag, bridged)
        if key not in self.cache:
            wall = self.model.wall(wall_tag)
            self.cache[key] = (panel_flats(self.model, wall, datums=self.datums,
                                           bridge_m=self.bridge if bridged else 0.0)
                               if wall is not None else [])
        return self.cache[key]


def _pen_findings(model: Any, pen: Any, flats: _FlatCache) -> list[Finding]:
    from typehaus.resolve.panel_flats import flat_at, flat_holding

    tags = (pen.tag, pen.run_tag, pen.wall_tag)
    if pen.sleeve_d_m is None and pen.sleeve_ref is None:
        return [failed(_CID, f"{pen.tag}: no sleeve row passes {_in(pen.outside_d_m)} OD",
                       tags=tags, fix="add a PenetrationSleeveRow / BondSleeveRow")]
    if pen.closure is None:
        return [failed(_CID, f"{pen.tag}: no closure fits ({pen.kind}, "
                             f"{_in(pen.outside_d_m)} OD)", tags=tags,
                       fix="add a BootRow (or the lineset inlet) that fits this run")]
    out = []
    half = _closure_half_width(model, pen)
    if half is not None:
        s = pen.station_m
        fl = flats.get(pen.wall_tag, pen.closure == "boot" and pen.boot_conforms)
        if fl and flat_holding(fl, s - half, s + half) is None:
            home = flat_at(fl, s)
            seal = _trimmed_seal(home, s, half, pen.outside_d_m / 2)
            if not (seal is not None and pen.min_trimmed_seal_m is not None
                    and seal >= pen.min_trimmed_seal_m - _TOL_M):
                out.append(failed(_CID, (
                    f"{pen.tag}: its {pen.closure} ({_in(2 * half)}) leaves its flat"
                    + (f"; trimmed to the batten it keeps {_in(seal)} of seal"
                       f" (min {_in(pen.min_trimmed_seal_m or 0.0)})" if seal is not None
                       else "")), tags=tags, fix="move the run onto a flat's centre"))
    wall = model.wall(pen.wall_tag)
    if wall is not None and pen.sleeve_d_m and pen.sleeve_ref is None:
        girt = _girt_hit(wall, pen.station_m, pen.z_m, pen.sleeve_d_m / 2)
        if girt is not None:
            out.append(failed(_CID, f"{pen.tag}: its {_in(pen.sleeve_d_m)} sleeve cuts girt "
                                    f"{girt}", tags=tags,
                              fix="move the crossing between girt courses"))
    return out


def _closure_half_width(model: Any, pen: Any) -> float | None:
    from typehaus.resolve.mount_blocks import penetration_standard, station_of

    if pen.closure in ("boot", "strut_boot") and pen.boot_base_m:
        return pen.boot_base_m[0] / 2
    if pen.closure == "inlet":
        row = penetration_standard(model.plan).lineset_inlet
        return row.flange_width.meters / 2 if row is not None else None
    if pen.closure == "escutcheon" and pen.device_ref:
        obj = next((o for o in model.canvas_objects if o.tag == pen.device_ref), None)
        wall = model.wall(pen.wall_tag)
        if obj is not None and wall is not None:
            stations = [station_of(wall, p) for p in obj.footprint]
            return (max(stations) - min(stations)) / 2
    return None


def _trimmed_seal(home: tuple[float, float] | None, s: float, half: float,
                  r_pipe: float) -> float | None:
    """Seal left between the pipe and a batten face the base is cut to, when the base
    overhangs one edge of its flat only."""
    if home is None:
        return None
    lo_over, hi_over = home[0] > s - half + _TOL_M, home[1] < s + half - _TOL_M
    if lo_over == hi_over:
        return None
    return (s - r_pipe) - home[0] if lo_over else home[1] - (s + r_pipe)


def _girt_hit(wall: Any, station: float, z: float, r: float) -> str | None:
    from typehaus.resolve.framing.furring import STRAPPING_CATEGORY
    from typehaus.resolve.mount_blocks import station_of

    for m in wall.members:
        if m.category != STRAPPING_CATEGORY:
            continue
        a, b = sorted((station_of(wall, m.p0), station_of(wall, m.p1)))
        if (a - _TOL_M < station < b + _TOL_M
                and m.z0_m < z + r - _TOL_M and z - r + _TOL_M < m.z1_m):
            return m.child_key
    return None


def _mount_findings(model: Any, standard: Any, mount: Any,
                    flats: _FlatCache) -> list[Finding]:
    from typehaus.resolve.panel_flats import flat_holding

    out = []
    tags = (mount.tag, *mount.holds, mount.wall_tag)
    if mount.kind == "strap_block":
        row = standard.strap_block
        clear = row.batten_clearance.meters
        fl = flats.get(mount.wall_tag, True)
        if mount.width_m > row.max_width.meters + _TOL_M:
            out.append(failed(_CID, f"{mount.tag}: {_in(mount.width_m)} wide, over the "
                                    f"{_in(row.max_width.meters)} row", tags=tags))
        if fl and flat_holding(fl, mount.station_lo_m - clear,
                               mount.station_hi_m + clear) is None:
            out.append(failed(_CID, f"{mount.tag}: not on one flat {_in(clear)} off its "
                                    "battens", tags=tags,
                              fix="narrow the block or move the strap onto a flat"))
    trim = _trim_hit(model, mount)
    if trim is not None:
        out.append(failed(_CID, f"{mount.tag}: its {mount.kind} runs into trim {trim}",
                          tags=(*tags, trim), fix="move the device clear of the trim"))
    return out


def _trim_hit(model: Any, mount: Any) -> str | None:
    """The first trim piece whose body meets the mount's, tested in plan and then in the
    wall's elevation plane (a raked trim's bounding box spans the whole gable)."""
    from shapely.geometry import Polygon

    from typehaus.resolve.overlay import union_all

    s0, s1 = mount.station_lo_m, mount.station_hi_m
    b, n = mount.back_n_m, mount.back_n_m + mount.depth_m
    ring = [mount.point(s, o, 0.0)[:2] for s, o in ((s0, b), (s1, b), (s1, n), (s0, n))]
    body = Polygon(ring).buffer(-_TOL_M)
    top = mount.top_z or (mount.z1_m, mount.z1_m)
    face = Polygon([(s0, mount.z0_m), (s1, mount.z0_m), (s1, top[1]), (s0, top[0])]).buffer(
        -_TOL_M)
    for solid in model.solids:
        if (solid.category != "cladding_trim" or solid.z1_m <= mount.z0_m + _TOL_M
                or solid.z0_m >= mount.z1_m - _TOL_M or len(solid.outline) < 3
                or not Polygon(solid.outline).intersects(body)):
            continue
        mesh = solid.body_mesh
        if mesh is None:
            return solid.tag
        tris = []
        for tri in mesh.triangles:
            pts = [_local(mount, mesh.positions[k]) for k in tri]
            if max(p[1] for p in pts) < b or min(p[1] for p in pts) > n:
                continue  # wholly behind or before the block
            poly = Polygon([(p[0], p[2]) for p in pts])
            if poly.area > 0:
                tris.append(poly)
        if tris and union_all(tris).intersects(face):
            return solid.tag
    return None


def _local(mount: Any, p: tuple[float, float, float]) -> tuple[float, float, float]:
    dx, dy = p[0] - mount.origin[0], p[1] - mount.origin[1]
    return (dx * mount.tangent[0] + dy * mount.tangent[1],
            dx * mount.normal[0] + dy * mount.normal[1], p[2])

"""BBD75 horizontal joint trim: one Transition Trim along each authored panel joint."""

from __future__ import annotations

import math

from typehaus.library.trim.metal_sales import BBD_TRANSITION
from typehaus.quantities import M_PER_IN
from typehaus.resolve.cladding_trim.members import split_stock_run
from typehaus.resolve.cladding_trim.section import folded_section_mesh
from typehaus.resolve.metal_skin_profiles import SHEET_24_GA_M
from typehaus.resolve.model import ResolvedSolid

_PRODUCT = "BBD_TRANSITION"


def resolve_band_trim(model) -> None:
    """Sweep the Transition Trim at every joint of a board-and-batten cladding layer."""
    assemblies = model.plan.library
    finishes = {m.tag: m.finish for m in assemblies.materials}
    profile = BBD_TRANSITION
    section = tuple((x * M_PER_IN, y * M_PER_IN) for x, y in profile.section_in)
    for wall in model.walls:
        if not wall.assembly:
            continue
        assembly = assemblies.resolve_assembly(wall.assembly)
        authored = {layer.name: layer for layer in assembly.layers}
        for layer in wall.layers:
            spec = authored.get(layer.name)
            if (layer.function != "cladding" or spec is None
                    or finishes.get(layer.material_ref) != "board-and-batten"):
                continue
            z0, z1 = layer.band(wall)
            (ax, ay), (bx, by) = wall.axis[0], wall.axis[-1]
            length = math.hypot(bx - ax, by - ay)
            if length < 1e-6:
                continue
            d = ((bx - ax) / length, (by - ay) / length)
            n = (-d[1], d[0])
            mid = [sum(p[i] for p in layer.polygon) / len(layer.polygon) for i in (0, 1)]
            inner = [sum(p[i] for p in wall.layers[0].polygon) / len(wall.layers[0].polygon)
                     for i in (0, 1)]
            if sum((mid[i] - inner[i]) * n[i] for i in (0, 1)) < 0:
                n = (-n[0], -n[1])
            back = min(x * n[0] + y * n[1] for x, y in layer.polygon)
            along = [x * d[0] + y * d[1] for x, y in layer.polygon]
            lo, hi = min(along), max(along)
            for joint in sorted({j.meters for j in spec.panel_joint_elevations}):
                if not z0 < joint < z1:
                    continue
                for index, (start, end, stock) in enumerate(split_stock_run(
                        hi - lo, tuple(v * M_PER_IN for v in profile.stock_lengths_in),
                        profile.min_lap_in * M_PER_IN)):
                    origin = tuple(
                        (lo + start) * d[i] + back * n[i] for i in (0, 1)) + (joint,)
                    mesh = folded_section_mesh(
                        section, origin, (*n, 0.0), (0.0, 0.0, 1.0),
                        (d[0] * (end - start), d[1] * (end - start), 0.0), SHEET_24_GA_M)
                    xs, ys, zs = zip(*mesh.positions, strict=True)
                    tag = f"TRIM-{wall.tag}-BAND-{round(joint / M_PER_IN)}-{index + 1}"
                    model.solids.append(ResolvedSolid(
                        uid=f"{wall.uid}-band-{round(joint / M_PER_IN)}-{index}", tag=tag,
                        storey=wall.storey, category="cladding_trim",
                        outline=((min(xs), min(ys)), (max(xs), min(ys)),
                                 (max(xs), max(ys)), (min(xs), max(ys))),
                        z0_m=min(zs), z1_m=max(zs), material=layer.material_ref,
                        product=_PRODUCT, body_mesh=mesh, host_ref=wall.tag,
                        trim_length_m=end - start,
                        trim_stock_length_in=round(stock / M_PER_IN, 6)))

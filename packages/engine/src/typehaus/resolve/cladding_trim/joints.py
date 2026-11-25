"""Battens over a sheet-laid panel's vertical joints (``TrimCondition.VERTICAL_JOINT``).

Read off ``ResolvedModel.sheet_layouts``: every vertical break of a cladding run whose
material's kit names a joint profile takes a board centred on it, standing on the panel
face, from the panel's foot to its top. It stops at an opening it crosses or touches, and at
the trim and flashing hosted on that opening (a head drip, a door head), so a joint over a
door is battened only above the door's head trim. Material is the layer's
``joint_trim_material_ref``, else the panel's own.
"""

from __future__ import annotations

from typehaus.library.trim.catalog import PROFILES
from typehaus.model.cladding_trim import TrimCondition
from typehaus.quantities import M_PER_IN
from typehaus.resolve.cladding_trim.members import split_stock_run
from typehaus.resolve.cladding_trim.runs import cladding_face, subtract_spans
from typehaus.resolve.model import ResolvedSolid
from typehaus.resolve.sheet_layout_runs import direction

_MIN_PIECE_M = 1.0 * M_PER_IN  # a remnant under this between two cuts is not cut


def joint_profile(model, layout) -> str | None:
    """The kit's joint batten for a cladding layout's material, or None."""
    if layout.function != "cladding":
        return None
    material = model.plan.library.material(layout.material_ref)
    return material.trim_kit.get(TrimCondition.VERTICAL_JOINT) if material else None


def _station_span(solid, d) -> tuple[float, float]:
    stations = [x * d[0] + y * d[1] for x, y in solid.outline]
    return min(stations), max(stations)


def batten_spans(model, layout, brk, half: float, base: float, d) -> list[tuple[float, float]]:
    """``(z0, z1)`` pieces of one joint's batten, less what its openings take."""
    x = base + brk.at
    cuts = []
    trims = [s for s in model.solids if s.host_ref and (
        s.category == "cladding_trim" or "flashing" in s.category)]
    for opening in model.openings:
        if opening.host_wall not in layout.wall_tags:
            continue
        wall = model.wall(opening.host_wall)
        wd = direction(wall)
        sign = 1.0 if wd[0] * d[0] + wd[1] * d[1] > 0 else -1.0
        mid = wall.axis[0][0] * d[0] + wall.axis[0][1] * d[1] + sign * opening.center_along_m
        lo, hi = mid - opening.width_m / 2.0, mid + opening.width_m / 2.0
        z0 = wall.base_ref_z_m + opening.sill_m
        z1 = z0 + opening.height_m
        hosted = [s for s in trims if s.host_ref == opening.tag]
        reach = [(lo, hi, z0, z1)] + [(*_station_span(s, d), s.z0_m, s.z1_m) for s in hosted]
        if any(a < x + half and b > x - half for a, b, _z0, _z1 in reach):
            cuts.append((min(r[2] for r in reach), max(r[3] for r in reach)))
    return [(a, b) for a, b in subtract_spans(brk.lo, brk.hi, cuts) if b - a > _MIN_PIECE_M]


def resolve_joint_battens(model) -> None:
    """One batten per joint span, cut from the profile's stock."""
    for layout in model.sheet_layouts:
        key = joint_profile(model, layout)
        profile = PROFILES.get(key or "")
        if profile is None:
            continue
        first = model.wall(layout.wall_tag)
        d = direction(first)
        base = first.axis[0][0] * d[0] + first.axis[0][1] * d[1]
        width = max(x for x, _y in profile.section_in) * M_PER_IN
        thick = max(y for _x, y in profile.section_in) * M_PER_IN
        stock = tuple(v * M_PER_IN for v in profile.stock_lengths_in)
        for brk in layout.vertical_breaks:
            wall = model.wall(layout.wall_at(brk.at))
            layer = next((ly for ly in wall.layers if ly.name == layout.layer_name), None)
            face = cladding_face(wall, layer) if layer is not None else None
            if face is None:
                continue
            spec = next((ly for ly in model.plan.library.resolve_assembly(wall.assembly).layers
                         if ly.name == (layer.source_layer_name or layer.name)), None)
            material = (spec.joint_trim_material_ref if spec else None) or layer.material_ref
            x = base + brk.at
            if face.d[0] * d[0] + face.d[1] * d[1] < 0:  # a wall laid against the run
                x = -x
            s_in = round(abs(x) / M_PER_IN)
            pieces = [(z0 + a, z0 + b, length) for z0, z1 in batten_spans(
                model, layout, brk, width / 2.0, base, d)
                for a, b, length in split_stock_run(z1 - z0, stock, profile.min_lap_in)]
            for index, (z0, z1, length) in enumerate(pieces):
                ring = [face.xy(x + ds, layer.thickness_m + dn)
                        for ds, dn in ((-width / 2, 0.0), (width / 2, 0.0),
                                       (width / 2, thick), (-width / 2, thick))]
                model.solids.append(ResolvedSolid(
                    uid=f"{wall.uid}-batten-{s_in}-{index}",
                    tag=f"TRIM-{wall.tag}-JOINT-{s_in}-{chr(ord('A') + index)}",
                    storey=wall.storey, category="cladding_trim", material=material,
                    product=key, host_ref=wall.tag, derived=True, outline=tuple(ring),
                    z0_m=z0, z1_m=z1, trim_length_m=z1 - z0,
                    trim_stock_length_in=round(length / M_PER_IN, 6)))

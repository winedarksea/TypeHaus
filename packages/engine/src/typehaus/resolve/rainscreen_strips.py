"""Perforated strips under the cladding's panel ends: base, window and door heads, the band.

A panel end over a rainscreen opens its rib (PBR) or batten (BBD75) voids into the cavity.
Instead of a foam or polyethylene closure (chewable, and it holds water against the panel
end) the end sits on a flat perforated aluminium strip, itself set on 1/16" EPDM pads so no
steel bears on aluminium and water runs off between them. At the BBD75 band the lower
panel stops 1" under the Transition Trim's seat and a strip across that slot is the cavity's
vented outlet (``notes/metal_trim_kit.md``). Derived from the trim each one lands on.
"""

from __future__ import annotations

import math

from typehaus.model.enums import TrimKind
from typehaus.quantities import M_PER_IN
from typehaus.resolve.cladding_trim.members import split_stock_run
from typehaus.resolve.cladding_trim.section import folded_section_mesh
from typehaus.resolve.model import ResolvedSolid
from typehaus.resolve.rainscreen_closures import (
    BUG_SCREEN_MATERIAL,
    BUG_SCREEN_SHEET_IN,
    BUG_SCREEN_STOCK_IN,
    opening_head_spans,
    rainscreen_band,
    screens_rainscreen_base,
)
from typehaus.resolve.sheet_geometry import combine_sheets

STRIP_PRODUCT = "PANEL_END_STRIP"
BAND_OUTLET_PRODUCT = "BAND_OUTLET_STRIP"
PAD_PRODUCT = "EPDM_PAD"
PAD_MATERIAL = "rubber"
PAD_THICKNESS_IN = 0.0625
PAD_LENGTH_IN = 2.0
PAD_SPACING_IN = 12.0
#: The lower panel stops this far under the Transition Trim's seat: the band's outlet slot.
BAND_PANEL_GAP_IN = 1.0
#: A strip is cut this short of each edge of its seat, so its aluminium edge stands off the
#: steel legs (and the band girt's KDAT) it lies between; the gap is under the 1/8" hole.
STRIP_EDGE_CLEAR_IN = 1.0 / 32.0


def _sheet(seat, origin, outward, along, length, lift, thickness):
    """``seat`` = (dx, dz) from ``origin`` in (outward, up); the sheet's underside ``lift``
    above it. ``folded_section_mesh`` thickens below a line run outward."""
    top = lift + thickness
    return folded_section_mesh(((0.0, top), (seat[0], seat[1] + top)), origin,
                               (*outward, 0.0), (0.0, 0.0, 1.0),
                               (along[0] * length, along[1] * length, 0.0), thickness)


def _solid(model, uid, tag, storey, host, product, category, material, mesh, length, stock):
    xs, ys, zs = zip(*mesh.positions, strict=True)
    model.solids.append(ResolvedSolid(
        uid=uid, tag=tag, storey=storey, category=category, material=material,
        product=product, host_ref=host, body_mesh=mesh, derived=True,
        outline=((min(xs), min(ys)), (max(xs), min(ys)), (max(xs), max(ys)), (min(xs), max(ys))),
        z0_m=min(zs), z1_m=max(zs), trim_length_m=length,
        trim_stock_length_in=round(stock / M_PER_IN, 6) if stock else None))


def add_strip_run(model, *, uid, tag, storey, host, product, origin, outward, along, seat,
                  length) -> None:
    """A strip on pads along ``length``, cut from stock and butted, each piece with its pads.

    ``seat`` is the full (outward, up) run between the legs; the strip and its pads are held
    ``STRIP_EDGE_CLEAR_IN`` off each end of it."""
    pad = PAD_THICKNESS_IN * M_PER_IN
    sheet = BUG_SCREEN_SHEET_IN * M_PER_IN
    run = math.hypot(*seat)
    clear = STRIP_EDGE_CLEAR_IN * M_PER_IN
    unit = (seat[0] / run, seat[1] / run)
    origin = (origin[0] + outward[0] * unit[0] * clear, origin[1] + outward[1] * unit[0] * clear,
              origin[2] + unit[1] * clear)
    seat = (unit[0] * (run - 2 * clear), unit[1] * (run - 2 * clear))
    for index, (start, end, stock) in enumerate(split_stock_run(
            length, (BUG_SCREEN_STOCK_IN * M_PER_IN,), 0.0)):
        point = (origin[0] + along[0] * start, origin[1] + along[1] * start, origin[2])
        piece = end - start
        _solid(model, f"{uid}-{index}", f"{tag}-{index + 1}", storey, host, product,
               TrimKind.BUG_SCREEN.value, BUG_SCREEN_MATERIAL,
               _sheet(seat, point, outward, along, piece, pad, sheet), piece, stock)
        pad_length = min(PAD_LENGTH_IN * M_PER_IN, piece)
        count = max(2, math.ceil(piece / (PAD_SPACING_IN * M_PER_IN)) + 1)
        step = (piece - pad_length) / (count - 1)
        pads = [_sheet(seat, (point[0] + along[0] * step * k, point[1] + along[1] * step * k,
                              point[2]), outward, along, pad_length, 0.0, pad)
                for k in range(count)]
        _solid(model, f"{uid}-{index}-pads", f"{tag}-{index + 1}-PADS", storey, host,
               PAD_PRODUCT, "cladding_trim", PAD_MATERIAL, combine_sheets(pads),
               pad_length * count, 0.0)


def resolve_panel_end_strips(model) -> None:
    _base_strips(model)
    _head_strips(model)
    _band_strips(model)


def _base_strips(model) -> None:
    from typehaus.library.trim.metal_sales import PROFILES
    from typehaus.resolve.cladding_trim.base import base_trim_spans

    for face, key, span, lo, hi, z, depth in base_trim_spans(model):
        if not screens_rainscreen_base(model, face.wall):
            continue
        section = PROFILES[key].section_in
        seat = tuple((b - a) * M_PER_IN for a, b in zip(section[1], section[2], strict=True))
        x, y = face.xy(lo, depth)
        add_strip_run(model, uid=f"{face.wall.uid}-basestrip-{span}",
                      tag=f"{face.wall.tag}-BASESTRIP-S{span}", storey=face.wall.storey,
                      host=face.wall.tag, product=STRIP_PRODUCT, origin=(x, y, z),
                      outward=face.n, along=face.d, seat=seat, length=hi - lo)


def _head_strips(model) -> None:
    from typehaus.resolve.flashing_config import FLASHING
    from typehaus.resolve.opening_flashing import head_flashing_section, opening_flashing_frame

    heads = {s.host_ref: s.product for s in model.solids if s.category == "cladding_trim"
             and s.product in ("OPENING_HEAD", "DOOR_HEAD_CUSTOM")}
    for wall in model.walls:
        for opening, _s0, _s1, _z in opening_head_spans(model, wall):
            product = heads.get(opening.tag)
            frame = opening_flashing_frame(model, wall, opening) if product else None
            if frame is None:
                continue
            if product == "OPENING_HEAD":
                lo = opening.center_along_m - opening.width_m / 2 - M_PER_IN
                z = (wall.base_ref_z_m + opening.sill_m + opening.height_m
                     - opening.window_seat.head_drop_m)
                start, length, seat = lo, opening.width_m + 2 * M_PER_IN, (1.5 * M_PER_IN, 0.0)
                origin = frame.point(lo, frame.mount, z)
            else:
                head = head_flashing_section(wall, opening, frame, FLASHING)
                (water, bend), (front, seat_z) = head.points[1], head.points[2]

                def line(depth, water=water, bend=bend, front=front, seat_z=seat_z):
                    return bend + (seat_z - bend) * (depth - water) / (front - water)

                start, length = head.start, head.span
                origin = frame.point(start, frame.mount, line(frame.mount))
                seat = (frame.clad - frame.mount, line(frame.clad) - line(frame.mount))
            add_strip_run(model, uid=f"{opening.uid}-headstrip", tag=f"{opening.tag}-HEADSTRIP",
                          storey=wall.storey, host=opening.tag, product=STRIP_PRODUCT,
                          origin=origin, outward=frame.outward, along=frame.along, seat=seat,
                          length=length)


def band_screen_spans(model, wall) -> list[tuple[float, float, float]]:
    """``(joint z, s0, s1)`` along a BBD75 band, in the cladding face's stations.

    Read off the assembly's authored ``panel_joint_elevations``. An opening framed through the
    Transition Trim's height is left out: its own head detail governs there.
    """
    from typehaus.library.trim.metal_sales import BBD_TRANSITION
    from typehaus.resolve.cladding_trim.runs import cladding_face, subtract_spans

    if rainscreen_band(wall.layers) is None or not wall.assembly:
        return []
    assembly = model.plan.library.resolve_assembly(wall.assembly)
    finishes = {m.tag: m.finish for m in model.plan.library.materials}
    authored = {layer.name: layer for layer in assembly.layers} if assembly else {}
    legs = [z * M_PER_IN for _, z in BBD_TRANSITION.section_in]
    course = _course_face(model, wall)
    spans = []
    for layer in wall.layers:
        spec = authored.get(layer.name)
        if (layer.function != "cladding" or spec is None
                or finishes.get(layer.material_ref) != "board-and-batten"):
            continue
        face = cladding_face(wall, layer)
        if face is None:
            continue
        z0, z1 = layer.band(wall)
        for joint in sorted({j.meters for j in spec.panel_joint_elevations}):
            if not z0 < joint < z1:
                continue
            low, high = joint + min(legs), joint + max(legs)
            cuts = [(a - course, b + course) for opening, a, b in face.openings(model)
                    if wall.base_ref_z_m + opening.sill_m - course < high
                    and wall.base_ref_z_m + opening.sill_m + opening.height_m + course > low]
            spans += [(joint, a, b) for a, b in subtract_spans(face.lo, face.hi, cuts)]
    return spans


def _course_face(model, wall) -> float:
    from typehaus.resolve.framing.profiles import cross_section
    from typehaus.resolve.framing.truss_girts import truss_girt_bands

    bands = truss_girt_bands(model.plan, wall.assembly)
    spec = bands[1].framing if bands is not None else None
    return cross_section(spec.member).depth_m if spec is not None else 0.0


def _band_strips(model) -> None:
    from typehaus.library.trim.metal_sales import BBD_TRANSITION
    from typehaus.resolve.cladding_trim.runs import cladding_face

    section = BBD_TRANSITION.section_in
    width = section[2][0] * M_PER_IN
    seat = tuple((b - a) * M_PER_IN for a, b in zip(section[1], section[2], strict=True))
    for wall in model.walls:
        spans = band_screen_spans(model, wall)
        if not spans:
            continue
        layer = next(ly for ly in wall.layers if ly.function == "cladding")
        face = cladding_face(wall, layer)
        for index, (joint, lo, hi) in enumerate(spans, 1):
            x, y = face.xy(lo)
            gap = BAND_PANEL_GAP_IN * M_PER_IN
            add_strip_run(model, uid=f"{wall.uid}-bandstrip-lower-{index}",
                          tag=f"{wall.tag}-BANDSTRIP-LOWER-{index}", storey=wall.storey,
                          host=wall.tag, product=BAND_OUTLET_PRODUCT,
                          origin=(x, y, joint - gap), outward=face.n, along=face.d,
                          seat=(width, 0.0), length=hi - lo)
            add_strip_run(model, uid=f"{wall.uid}-bandstrip-upper-{index}",
                          tag=f"{wall.tag}-BANDSTRIP-UPPER-{index}", storey=wall.storey,
                          host=wall.tag, product=STRIP_PRODUCT, origin=(x, y, joint),
                          outward=face.n, along=face.d, seat=seat, length=hi - lo)

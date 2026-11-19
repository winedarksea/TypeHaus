"""BBD75 horizontal joint trim: one Transition Trim along each authored panel joint."""

from __future__ import annotations

from typehaus.library.trim.metal_sales import BBD_TRANSITION
from typehaus.quantities import M_PER_IN
from typehaus.resolve.cladding_trim.corner_closures import closures_for
from typehaus.resolve.cladding_trim.members import split_stock_run
from typehaus.resolve.cladding_trim.runs import cladding_face, subtract_spans
from typehaus.resolve.cladding_trim.section import folded_section_mesh
from typehaus.resolve.metal_skin_profiles import SHEET_24_GA_M
from typehaus.resolve.model import ResolvedSolid

_PRODUCT = "BBD_TRANSITION"
#: A band's end short of a corner C-Closure's return: under the 1/8" insect limit.
CLOSURE_GAP_M = M_PER_IN / 16
#: How near a joint an authored wall flashing's back leg must sit to stand in for the trim.
FLASHING_JOINT_TOL_M = M_PER_IN / 2


def band_spans(model, wall) -> list[tuple[float, float, float]]:
    """``(joint z, s0, s1)`` along a BBD75 band, in the cladding face's stations.

    Read off the assembly's authored ``panel_joint_elevations``. An opening framed through the
    Transition Trim's height is left out: its own head detail governs there. At a corner
    C-Closure the band stops 1/16" short of its return, the end under the corner's leg.
    """
    if not wall.assembly:
        return []
    assembly = model.plan.library.resolve_assembly(wall.assembly)
    finishes = {m.tag: m.finish for m in model.plan.library.materials}
    authored = {layer.name: layer for layer in assembly.layers} if assembly else {}
    legs = [z * M_PER_IN for _, z in BBD_TRANSITION.section_in]
    course = _course_depth(model, wall)
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
            cuts += [(min(face.lo, c.web_station), c.lip_station + CLOSURE_GAP_M) if c.inward > 0
                     else (c.lip_station - CLOSURE_GAP_M, max(face.hi, c.web_station))
                     for c in closures_for(model, wall, layer.name)]
            spans += [(joint, a, b) for a, b in subtract_spans(face.lo, face.hi, cuts)]
    return spans


def stand_ins(model, wall, joint) -> list[tuple[object, float, float]]:
    """``(Flashing, s0, s1)``: authored wall flashings standing in for the trim at ``joint``.

    The flashing names a wall as ``host_ref``, tops out at the joint and lies on this face's
    back plane, so a run spilling past a wall break stands in on both faces.
    """
    walls = {w.tag for w in model.walls}
    face = cladding_face(wall, next(ly for ly in wall.layers if ly.function == "cladding"))
    found = []
    for run in model.plan.elements_of_kind("Flashing"):
        if (run.host_ref not in walls or run.vertical
                or abs(run.top_elevation.meters - joint) > FLASHING_JOINT_TOL_M):
            continue
        centre = face.back + run.thickness.meters / 2
        points = [p.xy_m for p in run.path]
        if all(abs(x * face.n[0] + y * face.n[1] - centre) < FLASHING_JOINT_TOL_M
               for x, y in points):
            stations = [x * face.d[0] + y * face.d[1] for x, y in points]
            found.append((run, min(stations), max(stations)))
    return found


def trim_spans(model, wall) -> list[tuple[float, float, float]]:
    """``band_spans`` less the stations a ``stand_ins`` flashing takes at the joint.

    Only the trim yields: the outlet strip and band girt follow the joint and stay
    continuous. The trim runs one stock lap under a stand-in's end, as two sticks lap; a
    remnant no longer than that lap (a stand-in ending shy of an opening's cut) is dropped,
    the stand-in closing it.
    """
    spans = band_spans(model, wall)
    if not spans:
        return spans
    lap = BBD_TRANSITION.min_lap_in * M_PER_IN
    out = []
    for joint, lo, hi in spans:
        cuts = [(a, b) for _run, a, b in stand_ins(model, wall, joint)]
        for a, b in subtract_spans(lo, hi, cuts):
            under_a = a > lo + 1e-6 and any(abs(a - c1) < 1e-6 for _c0, c1 in cuts)
            under_b = b < hi - 1e-6 and any(abs(b - c0) < 1e-6 for c0, _c1 in cuts)
            if (under_a or under_b) and b - a <= lap:
                continue
            out.append((joint, a - lap * under_a, b + lap * under_b))
    return out


def _course_depth(model, wall) -> float:
    from typehaus.resolve.framing.profiles import cross_section
    from typehaus.resolve.framing.truss_girts import truss_girt_bands

    bands = truss_girt_bands(model.plan, wall.assembly)
    spec = bands[1].framing if bands is not None else None
    return cross_section(spec.member).depth_m if spec is not None else 0.0


def resolve_band_trim(model) -> None:
    """Sweep the Transition Trim along every band span of a board-and-batten cladding layer."""
    profile = BBD_TRANSITION
    section = tuple((x * M_PER_IN, y * M_PER_IN) for x, y in profile.section_in)
    stock = tuple(v * M_PER_IN for v in profile.stock_lengths_in)
    for wall in model.walls:
        spans = trim_spans(model, wall)
        if not spans:
            continue
        layer = next(ly for ly in wall.layers if ly.function == "cladding")
        face = cladding_face(wall, layer)
        spec = next(ly for ly in model.plan.library.resolve_assembly(wall.assembly).layers
                    if ly.name == layer.name)
        index = 0
        for joint, lo, hi in spans:
            for start, end, length in split_stock_run(hi - lo, stock,
                                                      profile.min_lap_in * M_PER_IN):
                origin = (*face.xy(lo + start), joint)
                mesh = folded_section_mesh(
                    section, origin, (*face.n, 0.0), (0.0, 0.0, 1.0),
                    (face.d[0] * (end - start), face.d[1] * (end - start), 0.0), SHEET_24_GA_M)
                xs, ys, zs = zip(*mesh.positions, strict=True)
                z_in = round(joint / M_PER_IN)
                model.solids.append(ResolvedSolid(
                    uid=f"{wall.uid}-band-{z_in}-{index}",
                    tag=f"TRIM-{wall.tag}-BAND-{z_in}-{index + 1}",
                    storey=wall.storey, category="cladding_trim",
                    outline=((min(xs), min(ys)), (max(xs), min(ys)),
                             (max(xs), max(ys)), (min(xs), max(ys))),
                    # The trim's own finish: the panel's ref would paint it the panel's.
                    z0_m=min(zs), z1_m=max(zs),
                    material=spec.joint_trim_material_ref or layer.material_ref,
                    product=_PRODUCT, body_mesh=mesh, host_ref=wall.tag,
                    trim_length_m=end - start,
                    trim_stock_length_in=round(length / M_PER_IN, 6)))
                index += 1

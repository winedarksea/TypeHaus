"""Build declared diaphragm blocking against the final deck and truss faces."""

from dataclasses import replace

from typehaus.model import Roof
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.geometry_members import member_box
from typehaus.resolve.model import FramedMember, ResolvedModel
from typehaus.resolve.roof_geometry import roof_height_at, roof_ridge_coordinate

DIAPHRAGM_BLOCK_CONNECTION = "diaphragm:collector-block"
PANEL_EDGE_BLOCK_CONNECTION = "diaphragm:panel-edge-block"
JOINT_NAILER_CONNECTION = "diaphragm:joint-nailer"
GEOMETRY_TOLERANCE_M = 1e-4


def deck_block(roof, key, stock, material, p0, p1, *, base=None, flat=False,
               connection=None):
    """A bevelled rectangular blank; its real top follows the deck across its width."""
    section = cross_section(stock)
    width = section.depth_m if flat else section.width_m
    depth = section.width_m if flat else section.depth_m
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    length = (dx * dx + dy * dy) ** 0.5
    if length <= GEOMETRY_TOLERANCE_M:
        return None
    nx, ny = -dy / length, dx / length
    offsets = [-width / 2, 0.0, width / 2]
    tops = [roof_height_at(roof, (p0[0] + nx * s, p0[1] + ny * s)) for s in offsets]
    base = max(tops) - depth if base is None else base
    if min(tops) <= base or max(tops) - base > depth + GEOMETRY_TOLERANCE_M:
        return None
    ring = ((-width / 2, 0.0), (width / 2, 0.0),
            *((s, z - base) for s, z in reversed(list(zip(offsets, tops, strict=True)))))
    return FramedMember(
        roof.uid, key, "blocking", stock, p0, p1, base, max(tops), length,
        material=material, plan_width_m=width, section_ring=ring, connection=connection)


def truss_faces(roof):
    axis = 0 if roof.ridge_direction == "x" else 1
    faces = []
    for member in roof.members:
        if member.category != "roof_truss":
            continue
        box = member_box(member)
        if box is not None:
            values = [p[axis] for p in box.corners_bottom]
            faces.append((min(values), max(values)))
    return sorted(faces)


def _run(axis, station, lo, hi):
    """Plan end points of a member at ``station`` across the trusses, from lo to hi."""
    p0, p1 = [0.0, 0.0], [0.0, 0.0]
    p0[1 - axis] = p1[1 - axis] = station
    p0[axis], p1[axis] = lo, hi
    return tuple(p0), tuple(p1)


def _collector_blocks(model, roof, spec, axis, bays, additions):
    """Blocks on each declared collector; returns their (centre, half width) stations."""
    span_axis = 1 - axis
    beams = []
    for recipe in spec.collector_blocking:
        solid = next((s for s in model.solids if s.tag == recipe.collector), None)
        beam = model.plan.by_tag(recipe.collector)
        if solid is None or beam is None:
            continue
        points = [model.plan.by_tag(getattr(beam, name)).position.xy_m
                  for name in ("start_node", "end_node")]
        across = [p[span_axis] for p in solid.outline]
        beams.append((recipe, solid, sorted(p[axis] for p in points), min(across),
                      max(across)))
    if not beams:
        return []
    middle = sum((lo + hi) / 2 for *_rest, lo, hi in beams) / len(beams)
    extents = []
    for recipe, solid, limits, face_lo, face_hi in beams:
        half = cross_section(recipe.stock).width_m / 2
        station = (face_lo + face_hi) / 2
        if recipe.flush == "inboard":
            station = face_hi - half if station < middle else face_lo + half
        extents.append((station, half))
        for i, (lo, hi) in enumerate(bays):
            lo, hi = max(lo, limits[0]), min(hi, limits[1])
            if hi - lo <= GEOMETRY_TOLERANCE_M:
                continue
            member = deck_block(
                roof, f"collector-block-{recipe.collector}-{i:03d}", recipe.stock,
                recipe.material, *_run(axis, station, lo, hi), base=solid.z1_m,
                connection=DIAPHRAGM_BLOCK_CONNECTION)
            if member:
                additions[roof.uid].append(member)
    return extents


def _within(station, extents):
    return any(abs(station - centre) <= half + GEOMETRY_TOLERANCE_M
               for centre, half in extents)


def frame_diaphragm_attachments(model: ResolvedModel) -> None:
    """A second pass: the receiving roof's trusses must already be framed."""
    additions = {roof.uid: [] for roof in model.roofs}
    for roof in model.roofs:
        element = model.plan.by_tag(roof.tag)
        if not isinstance(element, Roof) or element.diaphragm is None:
            continue
        spec = element.diaphragm
        axis = 0 if roof.ridge_direction == "x" else 1
        span_axis = 1 - axis
        faces = truss_faces(roof)
        if not faces:
            continue
        delivery = spec.delivers_to
        receiver = next((r for r in model.roofs if delivery and r.tag == delivery.roof), None)
        receiving_faces = truss_faces(receiver) if receiver else []
        bays = [(roof, a[1], b[0]) for a, b in zip(faces, faces[1:], strict=False)]
        if delivery and receiving_faces and receiving_faces[0][0] > faces[-1][1]:
            bays.append((roof, faces[-1][1], receiving_faces[0][0]))
        recipe = delivery.joint_nailing if delivery else None
        # A continuous deck runs its first sheet course into the receiver's first bay, so
        # those sheet edges need the same backing there.
        receiver_bay = ((receiver, receiving_faces[0][1], receiving_faces[1][0])
                        if recipe and recipe.continuous_deck and len(receiving_faces) >= 2
                        else None)
        extents = _collector_blocks(model, roof, spec, axis,
                                    [(lo, hi) for _host, lo, hi in bays], additions)
        joints = ([(tag, connector.position.xy_m[span_axis])
                   for tag in delivery.joint_refs
                   if (connector := model.plan.by_tag(tag)) is not None]
                  if recipe else [])
        joint_stations = [station for _tag, station in joints]
        panel = spec.panel_edge_blocking
        if panel and len(extents) >= 2:
            # Panels stop at the ridge fold. The module is a plan projection, chosen to fit
            # the sheet's physical width after allowing for the roof pitch.
            low = min(c for c, _h in extents)
            high = max(c for c, _h in extents)
            ridge = roof_ridge_coordinate(roof)
            anchor = ridge if ridge is not None else low
            stations = [anchor] if low < anchor < high else []
            for direction in (-1, 1):
                station = anchor + direction * panel.module.meters
                while low + GEOMETRY_TOLERANCE_M < station < high - GEOMETRY_TOLERANCE_M:
                    stations.append(station)
                    station += direction * panel.module.meters
            joint_bays = {len(bays) - 1} if recipe else set()
            for station in sorted(stations):
                for i, (host, lo, hi) in enumerate([*bays, *([receiver_bay]
                                                            if receiver_bay else [])]):
                    # Only a coincident panel edge may reuse a joint nailer.
                    if ((i in joint_bays or host is receiver)
                            and any(abs(station - s) < GEOMETRY_TOLERANCE_M
                                    for s in joint_stations)):
                        continue
                    member = deck_block(
                        host, f"panel-block-{roof.tag}-{station:.6f}-{i:03d}", panel.stock,
                        panel.material, *_run(axis, station, lo, hi),
                        connection=PANEL_EDGE_BLOCK_CONNECTION)
                    if member:
                        additions[host.uid].append(member)
        if not (recipe and receiver and len(receiving_faces) >= 2):
            continue
        for tag, station in joints:
            for host, lo, hi, side in (
                (roof, faces[-1][1], receiving_faces[0][0], "south"),
                (receiver, receiving_faces[0][1], receiving_faces[1][0], "north"),
            ):
                # The end straps nail into the collector blocks they land on.
                if side == "south" and _within(station, extents):
                    continue
                member = deck_block(host, f"joint-nailer-{tag}-{side}", recipe.stock,
                                    recipe.material, *_run(axis, station, lo, hi),
                                    connection=JOINT_NAILER_CONNECTION)
                if member:
                    additions[host.uid].append(member)
    model.roofs = [replace(r, members=(*r.members, *additions[r.uid])) for r in model.roofs]

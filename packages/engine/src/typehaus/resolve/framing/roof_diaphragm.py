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
        bays = [(a[1], b[0]) for a, b in zip(faces, faces[1:], strict=False)]
        if delivery and receiving_faces and receiving_faces[0][0] > faces[-1][1]:
            bays.append((faces[-1][1], receiving_faces[0][0]))
        collectors = []
        for recipe in spec.collector_blocking:
            solid = next((s for s in model.solids if s.tag == recipe.collector), None)
            beam = model.plan.by_tag(recipe.collector)
            if solid is None or beam is None:
                continue
            points = [model.plan.by_tag(getattr(beam, name)).position.xy_m
                      for name in ("start_node", "end_node")]
            station = sum(p[span_axis] for p in points) / 2
            collectors.append(station)
            limits = sorted(p[axis] for p in points)
            for i, (lo, hi) in enumerate(bays):
                p0, p1 = [0.0, 0.0], [0.0, 0.0]
                p0[span_axis] = p1[span_axis] = station
                p0[axis], p1[axis] = max(lo, limits[0]), min(hi, limits[1])
                member = deck_block(
                    roof, f"collector-block-{recipe.collector}-{i:03d}", recipe.stock,
                    recipe.material, tuple(p0), tuple(p1), base=solid.z1_m,
                    connection=DIAPHRAGM_BLOCK_CONNECTION)
                if member:
                    additions[roof.uid].append(member)
        if spec.panel_edge_blocking and spec.panel_width and len(collectors) >= 2:
            # Panels stop at the ridge fold. The declared module is a plan projection,
            # chosen to fit the sheet's physical width after allowing for the roof pitch.
            ridge = roof_ridge_coordinate(roof)
            anchor = ridge if ridge is not None else min(collectors)
            stations = [anchor] if min(collectors) < anchor < max(collectors) else []
            for direction in (-1, 1):
                station = anchor + direction * spec.panel_width.meters
                while (min(collectors) + GEOMETRY_TOLERANCE_M < station
                       < max(collectors) - GEOMETRY_TOLERANCE_M):
                    stations.append(station)
                    station += direction * spec.panel_width.meters
            joint_stations = ([connector.position.xy_m[span_axis]
                               for tag in delivery.joint_refs
                               if (connector := model.plan.by_tag(tag)) is not None]
                              if delivery and delivery.joint_nailing else [])
            for station in sorted(stations):
                for i, (lo, hi) in enumerate(bays):
                    # Only coincident panel edges may reuse a joint nailer.
                    if (i == len(bays) - 1
                            and any(abs(station - s) < GEOMETRY_TOLERANCE_M
                                    for s in joint_stations)):
                        continue
                    p0, p1 = [0.0, 0.0], [0.0, 0.0]
                    p0[span_axis] = p1[span_axis] = station
                    p0[axis], p1[axis] = lo, hi
                    member = deck_block(
                        roof, f"panel-block-{station:.6f}-{i:03d}", spec.panel_edge_blocking,
                        spec.collector_blocking[0].material, tuple(p0), tuple(p1),
                        connection=PANEL_EDGE_BLOCK_CONNECTION)
                    if member:
                        additions[roof.uid].append(member)
        if not (delivery and delivery.joint_nailing and receiver and len(receiving_faces) >= 2):
            continue
        recipe = delivery.joint_nailing
        for tag in delivery.joint_refs:
            connector = model.plan.by_tag(tag)
            if connector is None:
                continue
            station = connector.position.xy_m[span_axis]
            for host, lo, hi, side in (
                (roof, faces[-1][1], receiving_faces[0][0], "south"),
                (receiver, receiving_faces[0][1], receiving_faces[1][0], "north"),
            ):
                if side == "south" and any(abs(station - s) < GEOMETRY_TOLERANCE_M
                                            for s in collectors):
                    continue
                p0, p1 = [0.0, 0.0], [0.0, 0.0]
                p0[span_axis] = p1[span_axis] = station
                p0[axis], p1[axis] = lo, hi
                member = deck_block(host, f"joint-nailer-{tag}-{side}", recipe.stock,
                                    recipe.material, tuple(p0), tuple(p1),
                                    connection=JOINT_NAILER_CONNECTION)
                if member:
                    additions[host.uid].append(member)
    model.roofs = [replace(r, members=(*r.members, *additions[r.uid])) for r in model.roofs]

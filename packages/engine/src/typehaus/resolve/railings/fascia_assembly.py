"""Resolve purchased fascia mounts into shared export/viewer bodies."""

import math

from typehaus.quantities import M_PER_IN
from typehaus.resolve.connector_geometry.mesh import box_mesh, combine_meshes, transform_mesh
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.geometry import square
from typehaus.resolve.model import ResolvedSolid
from typehaus.resolve.railings.fascia_backing import band_behind, check_screw
from typehaus.resolve.railings.fascia_layout import fascia_deck, fascia_stations
from typehaus.resolve.railings.fascia_mesh import (
    bolt_mesh,
    outside_corner_mesh,
    pierced_plate,
    place,
    pocket_mesh,
    post_screw_mesh,
)
from typehaus.resolve.railings.mounting_solids import mounting_solid


def mounting_layout(library, railing):
    product = next(t for t in library.railing_types if t.tag == railing.type_ref)
    return fascia_stations([p.xy_m for p in railing.path], railing.post_spacing.meters,
                          railing.fascia_face_offset.meters,
                          product.fascia_post_offset.meters)



def emit_fascia_assembly(model, railing, storey, surface, parts, spec, shared):
    stations = mounting_layout(model.plan.library, railing)
    thickness = spec.wall_thickness.inches
    half = spec.pocket_width.inches / 2
    post_half = parts.post_section_m / 2
    drop = railing.fascia_bracket_drop.meters
    fascia = model.plan.by_tag(railing.fascia_ref) if railing.fascia_ref else None
    deck = fascia_deck(model, railing)
    for index, station in enumerate(stations):
        if index in shared:
            continue
        walking_z = surface.height_at(station.post)
        top = walking_z - drop
        bottom = top - spec.overall_height.meters
        first = station.faces[0]
        origin = (*station.post, top)
        jog = 0.0
        if station.variant == "outside_corner":
            second = station.faces[1]
            jog = spec.display_corner_jog.inches
            offsets = [sum((face.origin[i]-station.post[i])*face.outward[i] for i in range(2))
                       / M_PER_IN for face in station.faces]
            side = 1 if sum(second.outward[i]*first.tangent[i] for i in range(2)) > 0 else -1
            body = outside_corner_mesh(spec, *offsets, side)
        else:
            body = pocket_mesh(spec, station.variant != "straight")
        shell = place(body, origin, first.tangent, first.outward)
        leaves, bolts, screws = [shell], [], []
        for face_index, face in enumerate(station.faces):
            grip = thickness + (fascia.thickness.inches if fascia else 0)
            band = None
            if deck is not None:
                distance, band = band_behind(deck, face, railing.tag)
                grip = thickness + (distance + cross_section(band.profile).width_m/2) / M_PER_IN
            if (spec.fastener == "through_bolt"
                    and grip + spec.display_head_height.inches >= spec.bolt_length.inches):
                raise ValueError(f"{railing.tag}: fascia bolt too short for mounting stack")
            if station.variant == "straight":
                width = spec.flange_width.inches
                along = (-spec.mounting_hole_spacing[0].inches / 2,
                         spec.mounting_hole_spacing[0].inches / 2)
                leaf_origin = face.origin
            else:
                # Outside leaves run away from the corner along each fascia; inside leaves
                # reverse that handedness. The post pocket remains one physical part.
                direction = (-1 if face_index == 0 else 1)
                if station.variant == "inside_corner":
                    direction *= -1
                envelope = (spec.corner_wing_length.inches if station.variant == "outside_corner"
                            else spec.inside_corner_envelope.inches)
                width = envelope - 2*half - thickness - jog
                shift = direction * (half + jog + width / 2) * M_PER_IN
                leaf_origin = tuple(face.origin[i] + face.tangent[i] * shift for i in range(2))
                along = (direction * (width/2-spec.display_corner_hole_inset.inches),)
            holes = [(x, -spec.mounting_hole_top_drop.inches - z,
                      spec.bolt_diameter.inches / 2 + 0.005)
                     for x in along for z in (0, spec.mounting_hole_spacing[1].inches)]
            leaf = pierced_plate(width, -spec.flange_height.inches, 0, thickness, holes)
            leaves.append(place(leaf, (*leaf_origin, top), face.tangent, face.outward))
            for x, z, _radius in holes:
                bolt_origin = (leaf_origin[0] + face.tangent[0] * x * M_PER_IN
                               + face.outward[0] * thickness * M_PER_IN,
                               leaf_origin[1] + face.tangent[1] * x * M_PER_IN
                               + face.outward[1] * thickness * M_PER_IN, top + z * M_PER_IN)
                if spec.fastener == "wood_screw":
                    if band is not None:
                        check_screw(deck, band, face, bolt_origin[:2], bolt_origin[2],
                                    spec, railing.tag, corner=station.variant != "straight")
                    bolts.append(place(bolt_mesh(spec), bolt_origin, face.tangent,
                                       face.outward))
                else:
                    bolts.append(place(bolt_mesh(spec, grip), bolt_origin,
                                       face.tangent, face.outward))
        # Two screws on each side of the pocket, through the shell into the post tube.
        for side in (-1, 1):
            for fraction in (0.25, 0.75):
                u = side * (half + thickness) * M_PER_IN
                screw_origin = (station.post[0] + first.tangent[0] * u,
                                station.post[1] + first.tangent[1] * u,
                                top - spec.overall_height.meters * fraction)
                screws.append(place(post_screw_mesh(spec), screw_origin, first.outward,
                                    tuple(side * v for v in first.tangent)))
        mounting_solid(model, railing, storey, f"FASCIA-BRACKET{index + 1}",
               combine_meshes(*leaves), parts.post_material,
               getattr(spec, f"{station.variant}_product"))
        mounting_solid(model, railing, storey, f"FASCIA-BOLTS{index + 1}",
               combine_meshes(*bolts), parts.post_material)
        mounting_solid(model, railing, storey, f"FASCIA-SCREWS{index + 1}",
               combine_meshes(*screws), parts.post_material)
        insert = box_mesh((-half, -half, -spec.overall_height.inches),
                          (half, half, -spec.overall_height.inches + spec.insert_thickness.inches))
        mounting_solid(model, railing, storey, f"FASCIA-INSERT{index + 1}",
               place(insert, origin, first.tangent, first.outward), parts.post_material)
        corners = [(station.post[0] + first.tangent[0]*x + first.outward[0]*y,
                    station.post[1] + first.tangent[1]*x + first.outward[1]*y)
                   for x, y in square(0, 0, post_half, post_half)]
        corners.sort(key=lambda p: math.atan2(p[1]-station.post[1], p[0]-station.post[0]))
        z0, z1 = bottom + spec.insert_thickness.meters, walking_z + railing.height.meters
        # Height stays authored: a post the stock tube cannot cut to is refused, not shortened.
        if z1 - z0 > spec.post_tube_length.meters + 1e-6:
            raise ValueError(f"{railing.tag}: post longer than stock tube")
        model.solids.append(ResolvedSolid(
            uid=f"{railing.uid}-p{index:02d}", tag=f"{railing.tag}-POST{index + 1}",
            storey=storey, category="railing", outline=corners, z0_m=z0, z1_m=z1,
            assembly=railing.assembly, material=parts.post_material,
        ))
    _emit_foot_blocks(model, railing, storey, stations, surface, parts, spec)


def _emit_foot_blocks(model, railing, storey, stations, surface, parts, spec):
    width = spec.display_foot_block_width.inches
    thickness = spec.display_foot_block_thickness.inches
    for index, (a, b) in enumerate(zip(stations[:-1], stations[1:], strict=True)):
        point = tuple((a.post[i] + b.post[i]) / 2 for i in range(2))
        run = tuple(b.post[i] - a.post[i] for i in range(2))
        length = sum(v*v for v in run)**0.5
        tangent = tuple(v / length for v in run)
        outward = (tangent[1], -tangent[0])
        post_offset = spec.pocket_width.inches / 2
        origin = (*point, surface.height_at(point))
        clearance = spec.bottom_clearance.inches
        mounting_drop = railing.fascia_bracket_drop.inches
        bracket = combine_meshes(
            box_mesh((-width/2, -post_offset, -mounting_drop-1),
                     (width/2, -post_offset+thickness, clearance)),
            box_mesh((-width/2, -post_offset, clearance-thickness),
                     (width/2, thickness, clearance)),
            place(post_screw_mesh(spec, length_in=spec.foot_block_fascia_screw_length.inches),
                  (0, -post_offset*M_PER_IN, (-mounting_drop-0.5)*M_PER_IN),
                  (1, 0), (0, 1)),
            transform_mesh(post_screw_mesh(spec),
                           origin_m=(0, 0, (clearance-thickness)*M_PER_IN),
                           y_axis=(0, 0, -1), z_axis=(0, 1, 0)),
        )
        mounting_solid(model, railing, storey, f"FASCIA-FOOTBLOCK{index + 1}",
               place(bracket, origin, tangent, outward), parts.post_material,
               spec.foot_block_product)

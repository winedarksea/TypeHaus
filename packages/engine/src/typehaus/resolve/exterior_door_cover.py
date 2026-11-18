"""A removable cover over a door's walking joint (``ApproachBearing.landing="cover"``).

Fixed on the landing member's inner part, beside the plank ends' bearing, its top flush
with the deck; at the house end it slides on a ledge on the sill beam's face, below the
pan's drip. It bears at both ends and slides at one. Graded across the joint's full range,
the catalog's movement plus ``cover_tolerance`` each way: bearing on the ledge at the widest
opening, and the ledge clear of the landing member and the cover clear of the beam (and the
pan's drip leg on its face, ``skin``) at the narrowest (``notes/exterior_door_sill_beam.md``
§4). Depths are the bridge's layout frame; ``drip_foot`` is the drip leg's bottom.
"""

_IN = 0.0254
_TOL = _IN / 64


def add_cover(model, builder, bearing, support, house_face, movement, skin, drip_foot, span):
    """``(report fields, conflicts, unknown)``; draws the cover and its ledge, ``span`` long."""
    conflicts, unknown = [], []
    if None in (support.member_inner, support.member_outer, support.member_top,
                support.deck_top, support.girt_top):
        return {}, ["a joint cover needs a landing member, its deck and a sill beam"], []
    swing = movement + bearing.cover_tolerance.meters
    seat = bearing.cover_seat.meters
    fixed_outer = support.member_outer - bearing.plank_bearing.meters
    inner = house_face + skin + swing
    bottom, top = support.member_top, support.deck_top
    fixed = fixed_outer - support.member_inner
    sliding = house_face + seat - inner - swing
    ledge_clear = support.member_inner - swing - (house_face + seat)
    report = dict(cover_thickness_in=(top - bottom) / _IN,
                  cover_width_in=(fixed_outer - inner) / _IN,
                  cover_fixed_bearing_in=fixed / _IN, cover_min_seat_bearing_in=sliding / _IN,
                  cover_min_ledge_clearance_in=ledge_clear / _IN,
                  cover_range_in=swing / _IN)
    if top - bottom <= _TOL:
        conflicts.append("the joint cover has no depth between its member and the deck top")
    if support.deck_edge is not None and support.deck_edge < fixed_outer - _TOL:
        conflicts.append("the landing's planks cover the member where the joint cover is fixed")
    if fixed < bearing.cover_min_bearing.meters - _TOL:
        conflicts.append("the joint cover's fixed end bears on less of the landing member "
                         "than its minimum")
    if sliding < bearing.cover_min_bearing.meters - _TOL:
        conflicts.append(f"at the widest joint the cover bears {sliding / _IN:.3f}\" on its "
                         "seat, under its minimum")
    if ledge_clear < -_TOL:
        conflicts.append("at the narrowest joint the cover seat meets the landing member")
    if bottom > drip_foot + _TOL:
        conflicts.append("the cover seat stands above the pan's drip on the sill beam")
    if not any(getattr(e, "tag", None) == bearing.cover_discharge_ref
               for items in model.plan.elements.values() for e in items):
        conflicts.append(f"cover discharge {bearing.cover_discharge_ref} does not resolve")
    if conflicts:
        return report, conflicts, unknown
    builder.rectangle("approach-joint-cover", inner, fixed_outer, bottom, top,
                      bearing.cover_material_ref, "rigid", span=span)
    builder.rectangle("approach-cover-seat", house_face, house_face + seat,
                      bottom - bearing.cover_seat_thickness.meters, bottom,
                      bearing.cover_seat_material_ref, "lumber", span=span)
    unknown.append("joint cover: the product, its slip rating and its seat's fastening are "
                   f"a supplier hold; water drops through to {bearing.cover_discharge_ref}")
    return report, conflicts, unknown

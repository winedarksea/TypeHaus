"""A door's sill pan sloped across its RO only, level from the RO's outer face out.

``ExteriorDoorSillDesign.pan_across_ro``: the shim tapers at the flashing slope from the back
dam to the frame's outer face and stops; the pan runs level over the outboard layers to its
drip. The threshold then seats at ``seat_height`` over the RO base instead of on a pan that
rises the whole way from the outlet (R311.3.1's 1.5" interior rise on the egress door).
"""

from __future__ import annotations

from typehaus.resolve.sheet_geometry import combine_sheets


def sill_pan_across_ro(frame, outlet: float, lo: float, width: float, seat: float, cfg,
                       profile, end_dam_stop: float | None, outlet_lip: float, drip):
    """The ``_sill_pan`` meshes for a ``pan_rise_profile`` with an RO-face breakpoint."""
    (dam, fall), (ro_face, _), _ = profile
    shim = ((dam, seat), (ro_face, seat), (dam, seat + fall))
    support_meshes = [
        frame.section(lo, ((frame.back, seat), (dam, seat), (dam, seat + cfg.back_dam_m),
                           (frame.back, seat + cfg.back_dam_m)), width, 1.0),
        frame.section(lo, shim, width, 1.0),
    ]
    down = drip[0] if drip else seat - cfg.pan_drop_m
    pan_meshes = [frame.leg(lo, width, a, b, cfg.sill_membrane_m)
                  for a, b in (((dam, seat + cfg.back_dam_m), (dam, seat + fall)),
                               ((dam, seat + fall), (ro_face, seat)),
                               ((ro_face, seat), (outlet, seat)),
                               ((outlet, seat), (outlet, down)))]
    pan_meshes += drip[1] if drip else []
    for station, sign in ((lo, 1.0), (lo + width, -1.0)):
        stop = outlet if end_dam_stop is None else max(end_dam_stop, ro_face)
        if end_dam_stop is not None:
            # Beyond the buried upstands a low lip stays under the walking plate.
            pan_meshes.append(frame.section(station, (
                (stop, seat), (outlet, seat), (outlet, seat + outlet_lip),
                (stop, seat + outlet_lip)), cfg.sill_membrane_m, sign))
        profile_2d = ((dam, seat + fall), (ro_face, seat), (stop, seat),
                      (stop, seat + cfg.end_dam_m), (dam, seat + cfg.end_dam_m))
        pan_meshes.append(frame.section(station, profile_2d, cfg.sill_membrane_m, sign))
    return [("sill", "opening_sill_pan", cfg.membrane_material, combine_sheets(pan_meshes)),
            ("sill-support", "opening_sill_pan", cfg.sill_shim_material,
             combine_sheets(support_meshes))]

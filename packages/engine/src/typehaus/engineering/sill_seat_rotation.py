"""A door sill seat's rotation: each screw in combined lateral and withdrawal (NDS 12.4.1).

The beam's reaction stands ``eccentricity`` off the rim face, so each seat rolls outward about
a compression resultant ``inset`` above its bearing edge (its bottom; its top where the seat
is lifted). The couple ``|R| e`` is shared by the seat's screws in proportion to their lever
from that resultant, as tension; each screw's lateral share is the spring beam's for the same
load station. ESR-1078 §4.1.6 sends the pair to NDS 12.4.1:
``Z'α = W' Z' / (W' cos²α + Z' sin²α)``, ``tan α = T / Z``, graded on the resultant.
One grade per axial column (``notes/exterior_door_sill_beam.md`` §3).
"""

from __future__ import annotations

import math


def seat_rotation_report(forces, nodes, screws, seats, eccentricity_in, inset_in, lateral_lb,
                         axial_columns):
    """Report fields for the worst screw under every load station, per axial column.

    ``forces[screw, load]`` and ``nodes`` come from ``screw_force_matrix``; ``screws`` is
    ``(station, z)`` per row of ``forces``; ``seats`` is ``(screw indices, bottom z, top z)``
    per seat; ``axial_columns`` is ``(label, W' lb)``. Inches and pounds throughout.
    """
    worst = {label: (0.0, None) for label, _ in axial_columns}
    max_reaction = 0.0
    for load in range(forces.shape[1]):
        for indices, bottom, top in seats:
            reaction = float(sum(forces[i, load] for i in indices))
            max_reaction = max(max_reaction, abs(reaction))
            pivot = bottom + inset_in if reaction >= 0 else top - inset_in
            levers = {i: (screws[i][1] - pivot) * (1 if reaction >= 0 else -1) for i in indices}
            levers = {i: d for i, d in levers.items() if d > 0}
            if not levers:
                continue
            sum_sq = sum(d * d for d in levers.values())
            moment = abs(reaction) * eccentricity_in
            for i in indices:
                tension = moment * levers.get(i, 0.0) / sum_sq
                shear = abs(float(forces[i, load]))
                angle = math.atan2(tension, shear)
                for label, axial in axial_columns:
                    allowed = axial * lateral_lb / (axial * math.cos(angle) ** 2
                                                    + lateral_lb * math.sin(angle) ** 2)
                    ratio = math.hypot(shear, tension) / allowed if allowed > 0 else math.inf
                    if ratio > worst[label][0]:
                        worst[label] = (ratio, dict(
                            load_at_in=nodes[load], screw_at_in=screws[i][0],
                            screw_z_in=screws[i][1], lateral_lb=shear, tension_lb=tension,
                            seat_reaction_lb=reaction, allowed_lb=allowed, axial_lb=axial))
    dcr = max(ratio for ratio, _ in worst.values())
    return dict(
        seat_rotation_status="PASS" if dcr <= 1 else "FAIL",
        seat_rotation_dcr=dcr,
        seat_rotation_columns={label: dict(dcr=ratio, **(case or {}))
                               for label, (ratio, case) in worst.items()},
        seat_reaction_max_lb=max_reaction,
        seat_eccentricity_in=eccentricity_in)

"""A soakaway bed, a plain bed abutting it and a lateral into it, spliced onto catlin.

Shared by the soakaway tests. Two 4'x4' pads side by side in open yard east of the house:
PD-TEST-SOAK carries a 24" drained section over a 12" flood course; PD-TEST-PLAIN's bed
abuts it and drains into it; FD-TEST-SOAK lets go inside the soakaway bed's stone.
"""

from __future__ import annotations

from typehaus.model.structure import DrainTile, FootingBedding, FrenchDrain, Pad
from typehaus.quantities import ft, inch, pt

PAD_BOTTOM_FT = -8.0
X0_FT = 70.0


def _pad(tag: str, uid: str, x_ft: float) -> Pad:
    return Pad(uid=uid, tag=tag, thickness=inch(12), bottom_elevation=ft(PAD_BOTTOM_FT),
               outline=(pt(ft(x_ft), ft(10)), pt(ft(x_ft + 4), ft(10)),
                        pt(ft(x_ft + 4), ft(14)), pt(ft(x_ft), ft(14))))


def soak_bed(**update) -> FootingBedding:
    bed = FootingBedding(
        uid="TSTSOAK001", tag="FB-TEST-SOAK", host_ref="PD-TEST-SOAK", undercut=inch(24),
        non_frost_susceptible=True, soakaway_depth=inch(12), void_ratio=0.40,
        infiltration_in_per_hr=0.06,
        drain_tile_spec=DrainTile(diameter=inch(4), discharge="soakaway"),
        inlet_refs=("FB-TEST-PLAIN", "FD-TEST-SOAK"),
        overflow_ref="daylight", overflow_invert=ft(PAD_BOTTOM_FT) - inch(6))
    return bed.model_copy(update=update)


def plain_bed(**update) -> FootingBedding:
    bed = FootingBedding(
        uid="TSTSOAK002", tag="FB-TEST-PLAIN", host_ref="PD-TEST-PLAIN", undercut=inch(24),
        non_frost_susceptible=True,
        drain_tile_spec=DrainTile(diameter=inch(4), discharge="FB-TEST-SOAK"))
    return bed.model_copy(update=update)


def lateral(**update) -> FrenchDrain:
    """Starts 6' south of the pads and ends mid-soakaway, 30" under the pad (in the course)."""
    run = FrenchDrain(
        uid="TSTSOAK003", tag="FD-TEST-SOAK",
        path=(pt(ft(X0_FT + 2), ft(4)), pt(ft(X0_FT + 2), ft(12))),
        invert=ft(PAD_BOTTOM_FT) - inch(28), end_invert=ft(PAD_BOTTOM_FT) - inch(30),
        trench_width=inch(6), trench_depth=inch(8),
        tile=DrainTile(diameter=inch(4), sock=False, discharge="FB-TEST-SOAK"),
        discharge_ref="FB-TEST-SOAK")
    return run.model_copy(update=update)


def soak_plan(catlin_plan, *, soak=None, plain=None, run=None, extra=()):
    elements = (_pad("PD-TEST-SOAK", "TSTSOAKP01", X0_FT),
                _pad("PD-TEST-PLAIN", "TSTSOAKP02", X0_FT + 4),
                soak if soak is not None else soak_bed(),
                plain if plain is not None else plain_bed(),
                run if run is not None else lateral(), *extra)
    return catlin_plan.with_elements(
        "basement", (*catlin_plan.storey_elements("basement"), *elements))

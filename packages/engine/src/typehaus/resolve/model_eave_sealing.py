"""Records for a panel eave's rib-end sealing; drawings, takeoff and checks all read these."""

from __future__ import annotations

from dataclasses import dataclass

WRAPPED_EAVE = "wrapped-extended-eave"
CLEAT_EAVE = "fascia-offset-cleat"
#: Both rib legs inside the roofing, so the end is one closed cavity.
FULL_CAVITY = "full"
#: Cut by a rake: the opening's shape is not the profile's, so no plug is assumed.
RIPPED_CAVITY = "ripped-at-rake"
#: Straddles a boundary another roof continues across; one roof owns it.
SHARED_CAVITY = "shared-boundary"
#: The members that end a pan at an eave, whichever way it is held.
EAVE_PAN_CONNECTIONS = frozenset({"roof:pan-end", "roof:pan-hem"})


@dataclass(frozen=True)
class ResolvedEaveRibEnd:
    key: str
    roof_tag: str
    run_key: str
    edge_name: str
    station_m: float
    point_m: tuple[float, float, float]
    outward_normal: tuple[float, float]
    eave_condition: str
    cavity: str
    profile_key: str
    #: ``None`` when no specification covers this kit or cavity: unresolved, never assumed.
    treatment: str | None
    sealant_part: str | None
    source: str | None


@dataclass(frozen=True)
class ResolvedEaveSealingRun:
    roof_tag: str
    run_key: str
    edge_name: str
    kit: str
    eave_condition: str
    rib_ends: tuple[ResolvedEaveRibEnd, ...]
    hem_length_m: float
    tape_length_m: float
    rib_cavity_area_m2: float

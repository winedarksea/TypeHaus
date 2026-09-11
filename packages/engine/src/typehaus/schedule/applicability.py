"""Does this inspection's condition exist in this building, and how do we know?

N/A must be **earned** (→ ``findings.Result``). "No gas piping is modelled" in a house
whose mechanical plan is complete is positive evidence of absence; the same sentence about
a house with no MEP authored at all is a gap, and dropping the gas test on the strength of
it would send an owner to a fuel-gas line nobody inspected.

So every probe returns a tri-state :class:`~typehaus.schedule.model.Applicability` and
carries the sentence it rests on. ``None`` leaves the inspection listed as "applicability
unknown" — visible, never dropped.
"""

from __future__ import annotations

from typing import Any

from typehaus.schedule.model import Applicability

#: Cladding material substrings that mean a lath inspection. Matched against the resolved
#: wall layers' material keys, which is where a finish actually lives.
_STUCCO_TOKENS = ("stucco", "portland_cement_plaster", "eifs")

#: What a gas system looks like in the model: a ``PipeSystem`` value, and the appliance
#: fuel strings the equipment catalogue uses.
_GAS_TOKENS = ("gas", "propane", "lp")


def _system_of(run: Any) -> str:
    """A run's system as the plain string the enum carries, never ``PipeSystem.GAS``."""
    system = getattr(run, "system", "")
    return str(getattr(system, "value", system)).lower()


def _seen(model: Any, attribute: str) -> bool:
    """Has anything at all been authored in this family? The guard on every N/A below."""
    return bool(getattr(model, attribute, None))


def gas(model: Any) -> Applicability:
    """Fuel-gas piping — the MN mechanical gas test."""
    runs = [run for run in getattr(model, "pipe_runs", []) if _system_of(run) in _GAS_TOKENS]
    if runs:
        return Applicability("gas", True,
                             f"{len(runs)} gas pipe run(s): "
                             + ", ".join(sorted(str(r.tag) for r in runs)[:4]))
    if not _seen(model, "pipe_runs"):
        # No plumbing authored at all is not evidence that the house burns no gas.
        return Applicability("gas", None,
                             "no pipe runs are modelled at all, so the absence of a gas "
                             "system is not established")
    fuelled = [str(getattr(item, "tag", "")) for item in getattr(model, "solids", [])
               if any(token in str(getattr(item, "category", "")).lower()
                      for token in ("pipe_gas",))]
    if fuelled:
        return Applicability("gas", True, f"gas solids: {', '.join(sorted(fuelled)[:4])}")
    return Applicability("gas", False,
                         f"{len(model.pipe_runs)} pipe run(s) modelled, none on a gas "
                         f"system — this house is all-electric")


def stucco(model: Any) -> Applicability:
    """Cement plaster or EIFS anywhere on the exterior — the lath inspection."""
    walls = getattr(model, "walls", [])
    if not walls:
        return Applicability("stucco", None, "no walls are modelled")
    hits: list[str] = []
    for wall in walls:
        for layer in getattr(wall, "layers", ()) or ():
            material = str(getattr(layer, "material", "") or "").lower()
            if any(token in material for token in _STUCCO_TOKENS):
                hits.append(str(getattr(wall, "tag", "")))
                break
    if hits:
        return Applicability("stucco", True,
                             f"{len(hits)} wall(s) carry a cement-plaster layer: "
                             + ", ".join(sorted(hits)[:4]))
    return Applicability("stucco", False,
                         f"no layer on any of {len(walls)} modelled walls names cement "
                         f"plaster or EIFS")


def radiant_slab(model: Any) -> Applicability:
    """In-floor tube cast into a slab — what the slab inspection has to see pressurised."""
    heat = getattr(model, "floor_heat", [])
    if heat:
        return Applicability("radiant_slab", True,
                             f"{len(heat)} floor-heat zone(s): "
                             + ", ".join(sorted(str(z.tag) for z in heat)[:4]))
    if not getattr(model, "floors", None) and not getattr(model, "solids", None):
        return Applicability("radiant_slab", None, "no floors or slabs are modelled")
    return Applicability("radiant_slab", False, "no floor-heat zone is modelled")


def fireplace(model: Any) -> Applicability:
    """A solid-fuel or gas fireplace and its chimney.

    Always ``None`` when nothing names one, and that is the honest answer rather than a
    convenient one: the model has no fireplace element kind, so absence here is absence of
    a *field*, not absence of a hearth. R1001-R1004 is outside the profile's coverage
    statement for exactly the same reason.
    """
    named = [str(getattr(item, "tag", "")) for item in getattr(model, "solids", [])
             if "fireplace" in str(getattr(item, "category", "")).lower()
             or "chimney" in str(getattr(item, "tag", "")).lower()]
    if named:
        return Applicability("fireplace", True, f"named: {', '.join(sorted(named)[:4])}")
    return Applicability("fireplace", None,
                         "the model has no fireplace element kind, so nothing in it can "
                         "establish that this house has none — confirm with the AHJ")


def garage_separation(model: Any) -> Applicability:
    """A garage sharing a separation with the dwelling — what subp. 6.H's penetration
    inspection is about on a house of this kind.

    N/A is earned from rooms, not from walls: an attached garage is a *room* fact, and a
    house with no rooms modelled establishes nothing either way.
    """
    rooms = getattr(model, "rooms", [])
    if not rooms:
        return Applicability("garage_separation", None, "no rooms are modelled")
    named = [str(getattr(room, "tag", "") or getattr(room, "name", ""))
             for room in rooms
             if "garage" in f"{getattr(room, 'name', '')} {getattr(room, 'tag', '')}".lower()]
    if named:
        return Applicability("garage_separation", True,
                             f"{len(named)} garage room(s): {', '.join(sorted(named)[:4])}")
    return Applicability("garage_separation", False,
                         f"none of {len(rooms)} modelled rooms is a garage, so there is no "
                         "dwelling-to-garage separation to penetrate")


#: key -> probe. ``InspectionSpec.applies_when`` is linted against exactly this mapping.
PROBES = {
    "gas": gas,
    "stucco": stucco,
    "radiant_slab": radiant_slab,
    "fireplace": fireplace,
    "garage_separation": garage_separation,
}


def applicability(model: Any, key: str | None) -> Applicability | None:
    """The evidence for one key, or ``None`` when the inspection always applies."""
    if key is None:
        return None
    probe = PROBES.get(key)
    if probe is None:
        raise KeyError(f"unknown applicability key {key!r}; known: {sorted(PROBES)}")
    return probe(model)

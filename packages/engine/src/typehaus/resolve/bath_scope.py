"""Is a BATHROOM-occupancy room a code bathroom? IRC R202 needs a bathing fixture or a WC.

Out of scope only on positive evidence: the room holds fixtures and every one is a
declared lavatory basin (``FixtureType.basin``). No fixtures, or any other fixture, keeps it in.
"""

from __future__ import annotations


def lavatory_only_rooms(plan) -> frozenset[str]:
    """Tags of rooms whose fixtures are all lavatory basins (and there is at least one)."""
    types = {t.tag: t for t in getattr(getattr(plan, "library", None), "fixture_types", ())}
    basins: dict[str, bool] = {}
    for element in plan.all_elements():
        if element.element_kind != "Fixture" or element.room is None:
            continue
        basin = getattr(types.get(element.type_ref), "basin", None) is True
        basins[element.room] = basins.get(element.room, True) and basin
    return frozenset(tag for tag, only in basins.items() if only)


LAVATORY_ONLY_NOTE = "lavatory-only room: not a bathroom or toilet room (IRC R202)"

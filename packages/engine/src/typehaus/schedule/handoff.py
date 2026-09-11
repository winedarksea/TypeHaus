"""What a visit must leave in place, derived from the model where the model knows.

This is the list the owner walks with after the sub packs up, and the reason ``verified``
exists beside ``done``. Every item is derived — a count the takeoff already computes, a set
of tags that already exist — and every item carries the sentence saying where it came from.

That sentence is load-bearing, not decoration. Several of these items exist precisely to
say **"the model knows the count and not the positions"** out loud: the mudsill anchor row
is a number per sill run with no coordinates behind it, and the braced-wall panels are not
modelled at all. A checklist that hid that distinction would be worse than none, because it
would read as a verification of something nobody verified.

Nothing here invents a quantity. A probe that cannot answer returns no item, or returns one
whose ``count`` is ``None`` and whose ``derived`` says why.
"""

from __future__ import annotations

from typing import Any

from typehaus.schedule.model import HandoffItem

#: Which trades a probe's items belong on. A visit only ever shows its own trade's items —
#: handing the concrete crew the window schedule is how a checklist stops being read.
_BY_TRADE: dict[str, tuple[str, ...]] = {
    "concrete": ("sleeves", "dowels", "mudsill_anchors", "holdowns", "post_bases",
                 "radon", "floor_heat", "slab_edge"),
    "earth": ("drain_tile",),
    "drainage": ("drain_tile",),
    "framing": ("braced_walls", "rough_openings", "post_bases"),
    "openings": ("rough_openings", "window_order"),
    "roof": ("roof_penetrations",),
    "walls": ("roof_penetrations",),
    "plumbing": ("sleeves", "radon"),
}


def handoff_items(model: Any, visit: Any) -> list[HandoffItem]:
    """Everything ``visit`` has to leave behind, filtered to the elements it covers."""
    wanted = _BY_TRADE.get(getattr(visit, "trade", ""), ())
    tags = set(getattr(visit, "element_tags", ()) or ())
    out: list[HandoffItem] = []
    for name in wanted:
        probe = _PROBES.get(name)
        if probe is None:
            continue
        for item in probe(model) or []:
            # An item whose elements are all outside this visit's scope belongs to another
            # arrival in the same trade. One with no tags at all (a count with no
            # positions) rides every visit of the trade, which is the honest default.
            if item.scope and tags and not tags.intersection(item.scope):
                continue
            out.append(item)
    return out


def _tags(elements: Any, limit: int | None = None) -> tuple[str, ...]:
    found = tuple(sorted(str(getattr(e, "tag", "") or "") for e in elements
                         if getattr(e, "tag", None)))
    return found[:limit] if limit else found


# --- probes ---------------------------------------------------------------------------

def sleeves(model: Any) -> list[HandoffItem]:
    """Cast-in block-outs, per pour host. The one item that cannot be fixed afterwards."""
    by_host: dict[str, list[Any]] = {}
    for sleeve in getattr(model, "sleeves", []) or []:
        by_host.setdefault(str(getattr(sleeve, "host_slab", "") or "unassigned"),
                           []).append(sleeve)
    if not by_host:
        return []
    return [HandoffItem(
        id=f"sleeves:{host}",
        label=f"{len(found)} cast-in sleeve(s) placed and blocked in {host}",
        count=len(found), element_tags=_tags(found), scope_tags=(host,),
        sheet_ref="S-100",
        derived=("model.sleeves, by host — each one is modelled with a position, so this "
                 "is a list of places and not only a count"))
        for host, found in sorted(by_host.items())]


def dowels(model: Any) -> list[HandoffItem]:
    """Footing-to-wall dowels and the thermal-break solids cast with them."""
    found = [solid for solid in getattr(model, "solids", []) or []
             if "dowel" in str(getattr(solid, "category", "") or "").lower()]
    if not found:
        return []
    return [HandoffItem(
        id="dowels", label=f"{len(found)} dowel set(s) tied before the pour",
        count=len(found), element_tags=_tags(found), sheet_ref="S-100",
        derived="solids whose category names a dowel")]


def mudsill_anchors(model: Any) -> list[HandoffItem]:
    """Anchor count per sill run — **a count, with no positions behind it.**"""
    from typehaus.takeoff.anchors import mudsill_anchor_rows
    from typehaus.takeoff.hardware_config import DEFAULT_HARDWARE_TAKEOFF_CONFIG as CONFIG

    try:
        rows = mudsill_anchor_rows(model, CONFIG.sill_plate_anchors,
                                   CONFIG.sill_plate_takeoff_category)
    except Exception:  # noqa: BLE001 - a house without the config gets no item, not a crash
        return []
    if not rows:
        return []
    row = rows[0]
    return [HandoffItem(
        id="mudsill_anchors",
        label=f"{row.get('count')} sill anchors set to the plate layout",
        count=int(row.get("count") or 0), sheet_ref="S-100",
        derived=("takeoff/anchors.mudsill_anchor_rows — a count at a pitch, NOT a set of "
                 f"positions ({row.get('basis', '')}). Set them off the sill plan on the "
                 "day and mark what you actually placed."))]


def holdowns(model: Any) -> list[HandoffItem]:
    """Embedded strap holdowns — merged run-end locations, which the model does know."""
    from typehaus.takeoff.anchors import strap_holdown_locations
    from typehaus.takeoff.hardware_config import DEFAULT_HARDWARE_TAKEOFF_CONFIG as CONFIG

    try:
        runs, locations = strap_holdown_locations(
            model, CONFIG.sill_plate_anchors, CONFIG.sill_plate_takeoff_category)
    except Exception:  # noqa: BLE001
        return []
    if not locations:
        return []
    per_end = CONFIG.sill_plate_anchors.holdowns_per_run_end
    return [HandoffItem(
        id="holdowns",
        label=f"{len(locations) * per_end} embedded strap holdown(s) at "
              f"{len(locations)} sill-run end(s)",
        count=len(locations) * per_end, sheet_ref="S-100",
        derived=(f"takeoff/anchors.strap_holdown_locations over {len(runs)} sill runs; "
                 "ends that meet at a corner or a butt joint are one location, not two"))]


def post_bases(model: Any) -> list[HandoffItem]:
    """Post base anchors — the bolts that have to be in the wet concrete."""
    from typehaus.takeoff.hardware_config import DEFAULT_HARDWARE_TAKEOFF_CONFIG as CONFIG
    from typehaus.takeoff.uplift_joints import post_base_anchor_rows

    try:
        rows = post_base_anchor_rows(model, CONFIG.uplift)
    except Exception:  # noqa: BLE001
        return []
    total = sum(int(row.get("count") or 0) for row in rows)
    if not total:
        return []
    return [HandoffItem(
        id="post_bases", label=f"{total} post-base anchor(s) cast in",
        count=total, sheet_ref="S-602",
        derived="takeoff/uplift_joints.post_base_anchor_rows — a count per post, set from "
                "the post layout on the day")]


def radon(model: Any) -> list[HandoffItem]:
    """The passive soil-gas system's buried half: collection point, riser and sump."""
    found = [solid for solid in getattr(model, "solids", []) or []
             if "radon" in str(getattr(solid, "category", "") or "").lower()
             or "radon" in str(getattr(solid, "tag", "") or "").lower()]
    if not found:
        return []
    return [HandoffItem(
        id="radon", label="Radon collection point, riser and sealed sump cover in place",
        count=len(found), element_tags=_tags(found), sheet_ref="S-100",
        derived="solids naming radon (MN Rules 1303.2400-.2402); the membrane laps and the "
                "10 ft of perforated pipe are NOT modelled and must be verified by eye")]


def floor_heat(model: Any) -> list[HandoffItem]:
    """In-floor tube, pressurised and marked before anybody pours over it."""
    zones = list(getattr(model, "floor_heat", []) or [])
    if not zones:
        return []
    return [HandoffItem(
        id="floor_heat",
        label=f"{len(zones)} in-floor heat zone(s) pressurised, gauged and marked",
        count=len(zones), element_tags=_tags(zones), sheet_ref="M-101",
        derived="model.floor_heat — the zone outlines are modelled; the tube runs inside "
                "them are a layout the installer sets")]


def slab_edge(model: Any) -> list[HandoffItem]:
    """Under-slab insulation and the vapour retarder, checked before the truck arrives."""
    slabs = [solid for solid in getattr(model, "solids", []) or []
             if str(getattr(solid, "category", "") or "").lower().startswith("slab")]
    if not slabs:
        return []
    return [HandoffItem(
        id="slab_edge",
        label="Under-slab insulation and vapour retarder lapped, sealed and unpunctured",
        count=len(slabs), element_tags=_tags(slabs), sheet_ref="S-100",
        derived="the slab solids' own assembly layers; laps and seals are a field "
                "operation this model cannot grade")]


def drain_tile(model: Any) -> list[HandoffItem]:
    """Perimeter tile and its bedding, which backfill buries for good."""
    beddings = list(getattr(model, "footing_beddings", []) or [])
    if not beddings:
        return []
    return [HandoffItem(
        id="drain_tile",
        label=f"{len(beddings)} drain-tile bed(s) placed, fabric lapped, fall to daylight",
        count=len(beddings), element_tags=_tags(beddings), sheet_ref="S-100",
        derived="model.footing_beddings — the bed is modelled; the tile's fall within it "
                "is set in the field against the discharge invert")]


def rough_openings(model: Any) -> list[HandoffItem]:
    """The RO schedule, per storey. In this house's ladder the opening *is* the RO."""
    by_storey: dict[str, list[Any]] = {}
    for opening in getattr(model, "openings", []) or []:
        by_storey.setdefault(str(getattr(opening, "storey", "") or ""), []).append(opening)
    if not by_storey:
        return []
    return [HandoffItem(
        id=f"rough_openings:{storey or 'building'}",
        label=f"{len(found)} rough opening(s) framed to the schedule on {storey or 'the building'}",
        count=len(found), element_tags=_tags(found), sheet_ref="A-602",
        derived="model.openings — width and height ARE the rough opening in this house's "
                "assembly ladder, so the schedule and the framing are the same numbers")
        for storey, found in sorted(by_storey.items())]


def window_order(model: Any) -> list[HandoffItem]:
    """The order list, checked against the openings before the truck is unloaded."""
    openings = list(getattr(model, "openings", []) or [])
    if not openings:
        return []
    return [HandoffItem(
        id="window_order",
        label=f"{len(openings)} unit(s) checked off the delivery against the RO schedule",
        count=len(openings), element_tags=_tags(openings), sheet_ref="A-602",
        derived="model.openings against A-601/A-602 — a unit that does not match its RO is "
                "a return, and it is cheaper to find on the truck than in the wall")]


def braced_walls(model: Any) -> list[HandoffItem]:
    """Braced wall lines. **The panels themselves are not modelled** and the item says so."""
    from typehaus.emit.draw.bracedwallplan import braced_wall_lines

    out: list[HandoffItem] = []
    for storey in getattr(getattr(model, "plan", None), "storeys", []) or []:
        try:
            lines = braced_wall_lines(model, storey.tag)
        except Exception:  # noqa: BLE001
            continue
        if not lines:
            continue
        out.append(HandoffItem(
            id=f"braced_walls:{storey.tag}",
            label=f"{len(lines)} braced wall line(s) on {storey.tag} sheathed and nailed",
            count=len(lines), sheet_ref="S-201",
            derived="emit/draw/bracedwallplan.braced_wall_lines — the LINES are derived; "
                    "the PANELS on them are not modelled at all, so pick and mark them "
                    "against R602.10 on the drawing before the sheathing goes up"))
    return out


def roof_penetrations_item(model: Any) -> list[HandoffItem]:
    """What goes through the roof — and an empty list is itself the roofer's line."""
    from typehaus.schedule.roof_penetrations import roof_penetrations

    found, evidence = roof_penetrations(model)
    if not getattr(model, "roofs", None):
        return []
    if not found:
        return [HandoffItem(
            id="roof_penetrations",
            label="Nothing penetrates this roof — if something does on the day, stop",
            count=0, sheet_ref="A-201", derived=evidence)]
    return [HandoffItem(
        id="roof_penetrations",
        label=f"{len(found)} roof penetration(s) set and flashed before the membrane",
        count=len(found),
        element_tags=tuple(sorted(item["tag"] for item in found if item["tag"])),
        sheet_ref="A-201", derived=evidence)]


_PROBES = {
    "sleeves": sleeves,
    "dowels": dowels,
    "mudsill_anchors": mudsill_anchors,
    "holdowns": holdowns,
    "post_bases": post_bases,
    "radon": radon,
    "floor_heat": floor_heat,
    "slab_edge": slab_edge,
    "drain_tile": drain_tile,
    "rough_openings": rough_openings,
    "window_order": window_order,
    "braced_walls": braced_walls,
    "roof_penetrations": roof_penetrations_item,
}

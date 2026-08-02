"""R302.5 garage/dwelling separation and R302.13 floor-assembly protection.

Two of the most-written residential corrections, and neither had a rule. The garage rule in
particular fails in a specific way an inspector sees constantly: the gypsum goes up, and
then a supply register or a door into a bedroom undoes it.

Scope matters as much as the measurement here. A *detached* garage is not a deficiency, it
is a different building — so a garage sharing no separating element with the dwelling gets a
PASS naming that fact, not an UNKNOWN. An UNKNOWN would block this house's permit gate
forever over a garage the code does not reach.
"""

from __future__ import annotations

from typehaus.checks.code.mn_residential._common import _fail, _pass, _unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.model.enums import SLEEPING_OCCUPANCIES, DuctSystem, Occupancy
from typehaus.quantities import inch

_MIN_GARAGE_MEMBRANE = inch(0.5)  # R302.6: 1/2" gypsum on the garage side
_MIN_TYPE_X_MEMBRANE = inch(0.625)  # R302.6: 5/8" Type X where habitable space is above
_MIN_DOOR_FIRE_RATING = 20  # R302.5.1: a 20-minute rated door assembly
# How close two room faces must come before the wall between them is a separating element.
# The resolved faces are interior finish faces, so a shared wall leaves its own thickness
# plus lining between them; 18" clears the thickest assembly in this model without reaching
# across a breezeway.
_SEPARATION_REACH_M = inch(18).meters


def _gypsum_grade(ctx: CheckContext, layer) -> str | None:
    """The gypsum grade of this layer's material, or None if it is not gypsum board.

    Read off ``Material.gypsum_type``, which the material states. Matching on substrings in
    the tag and name would work for a library that spells it "gwb" and break silently for
    one that spells it "board-58" — the same class of mistake as the tag-prefix envelope
    list the energy check had to unwind.
    """
    ref = getattr(layer, "material_ref", None)
    material = next((m for m in ctx.plan.library.materials if m.tag == ref), None)
    return getattr(material, "gypsum_type", None)


def _habitable_above(ctx: CheckContext, garage) -> set[str]:
    """Tags of habitable rooms whose plan footprint sits over this garage on a storey above.

    R302.6 upgrades the garage membrane from 1/2" regular to 5/8" Type X exactly when this
    is non-empty: the ceiling stops being a fire separation and starts being the floor
    somebody is standing on.
    """
    from shapely.geometry import Polygon

    storeys = {s.tag: s.elevation.meters for s in ctx.plan.storeys}
    garage_z = storeys.get(garage.storey)
    if garage_z is None:
        return set()
    footprint = Polygon(garage.clear_face)
    out = set()
    for room in ctx.model.rooms:
        z = storeys.get(room.storey)
        if z is None or z <= garage_z + 1e-6 or len(room.clear_face) < 3:
            continue
        if room.occupancy in (Occupancy.GARAGE.value, Occupancy.UNCONDITIONED.value):
            continue
        if Polygon(room.clear_face).intersection(footprint).area > 1e-6:
            out.add(room.tag)
    return out


def _separating_walls(ctx: CheckContext, garage, dwelling_rooms):
    """Walls of the garage storey that border both the garage and a dwelling room."""
    from shapely.geometry import LineString, Polygon

    garage_face = Polygon(garage.clear_face)
    out = []
    for wall in ctx.model.walls:
        if wall.storey != garage.storey:
            continue
        axis = LineString(wall.axis)
        reach = wall.thickness_m / 2.0 + _SEPARATION_REACH_M
        if axis.distance(garage_face) > reach:
            continue
        for room, face in dwelling_rooms:
            if axis.distance(face) <= reach:
                out.append((wall, room))
                break
    return out


@check(Tier.CODE, "code.R302_5_garage_separation")
def garage_separation(ctx: CheckContext) -> list[Finding]:
    """R302.5.1 / R302.6 — the garage is separated from the dwelling.

    Four sub-rules, all measured:

    * the separating wall's garage-side lining includes at least 1/2" of gypsum, upgraded
      to 5/8" Type X wherever habitable space sits over the garage (R302.6);
    * no door opens from the garage into a *sleeping room* — a flat prohibition, and the
      one part of R302.5.1 that needs no fire data at all;
    * the door that does open into the dwelling is solid core or 20-minute rated;
    * no supply or return duct opens into the garage (R302.5.2).

    The two membrane grades and the door rating are read off ``Material.gypsum_type`` and
    ``DoorType.core``/``fire_rating_minutes``. A type that states neither reports UNKNOWN
    rather than being assumed compliant: "we did not ask" and "it is fine" are different
    answers, and the second one is the one that gets built.
    """
    from shapely.geometry import Polygon

    cid, code = "code.R302_5_garage_separation", "R302.5"
    garages = [room for room in ctx.model.rooms
               if room.occupancy == Occupancy.GARAGE.value and len(room.clear_face) >= 3]
    if not garages:
        return [_unknown(cid, "no garage modeled, so no separation requirement applies",
                         (), code)]
    dwelling = [(room, Polygon(room.clear_face)) for room in ctx.model.rooms
                if room.occupancy not in (Occupancy.GARAGE.value,
                                          Occupancy.UNCONDITIONED.value)
                and len(room.clear_face) >= 3]
    assemblies = {a.tag: a for a in ctx.plan.library.assemblies}
    doors = [e for e in ctx.plan.all_elements() if e.element_kind == "Door"]
    sleeping = {room.tag for room in ctx.model.rooms
                if room.occupancy in {o.value for o in SLEEPING_OCCUPANCIES}}

    out: list[Finding] = []
    for garage in garages:
        shared = _separating_walls(ctx, garage, dwelling)
        if not shared:
            out.append(_pass(cid, f"{garage.tag} shares no wall with a dwelling room — a "
                             "detached garage, which R302.5/R302.6 do not reach", code))
            continue

        # 1. the membrane on the garage side
        for wall, neighbour in shared:
            assembly = assemblies.get(wall.assembly)
            if assembly is None:
                out.append(_unknown(cid, f"{wall.tag} separates {garage.tag} from "
                                    f"{neighbour.tag} but resolves no assembly",
                                    (wall.tag,), "R302.6"))
                continue
            layers = tuple(assembly.layers) + tuple(assembly.default_lining)
            grades = [(_gypsum_grade(ctx, layer), layer.thickness) for layer in layers]
            gypsum = sum(thickness.meters for grade, thickness in grades
                         if grade is not None and thickness is not None)
            if gypsum + 1e-9 < _MIN_GARAGE_MEMBRANE.meters:
                out.append(_fail(cid, f"{wall.tag} separates {garage.tag} from "
                                 f"{neighbour.tag} with {gypsum / .0254:.2f}\" of gypsum; "
                                 "R302.6 requires 1/2\" on the garage side",
                                 (wall.tag, garage.tag), "R302.6"))
            else:
                out.append(_pass(cid, f"{wall.tag} carries {gypsum / .0254:.2f}\" gypsum "
                                 f"separating {garage.tag} from {neighbour.tag}", "R302.6"))

        # 2. Type X where habitable space sits over the garage. R302.6 upgrades the
        # membrane from 1/2" regular to 5/8" Type X once the thing above the garage is a
        # room rather than a roof — the ceiling is then holding a floor up while it burns.
        overhead = _habitable_above(ctx, garage)
        if overhead:
            for wall, neighbour in shared:
                assembly = assemblies.get(wall.assembly)
                if assembly is None:
                    continue
                layers = tuple(assembly.layers) + tuple(assembly.default_lining)
                type_x = sum(layer.thickness.meters for layer in layers
                             if _gypsum_grade(ctx, layer) == "type-x"
                             and layer.thickness is not None)
                if type_x + 1e-9 < _MIN_TYPE_X_MEMBRANE.meters:
                    out.append(_fail(cid, f"{wall.tag} separates {garage.tag} from the "
                                     f"dwelling with habitable space above "
                                     f"({', '.join(sorted(overhead))}) and carries "
                                     f"{type_x / .0254:.2f}\" of Type X gypsum; R302.6 "
                                     "requires 5/8\" Type X", (wall.tag, garage.tag),
                                     "R302.6"))
                else:
                    out.append(_pass(cid, f"{wall.tag} carries {type_x / .0254:.2f}\" Type X "
                                     f"gypsum under habitable space above {garage.tag}",
                                     "R302.6"))

        # 3. the door between garage and dwelling: prohibited into a sleeping room, and
        # otherwise 1-3/8" solid core or a 20-minute rated assembly.
        separating_tags = {wall.tag for wall, _ in shared}
        for door in doors:
            opening = next((o for o in ctx.model.openings if o.tag == door.tag), None)
            if opening is None or opening.host_wall not in separating_tags:
                continue
            neighbour = next((room for wall, room in shared
                              if wall.tag == opening.host_wall), None)
            if neighbour is not None and neighbour.tag in sleeping:
                out.append(_fail(cid, f"door {door.tag} opens from {garage.tag} into "
                                 f"sleeping room {neighbour.tag}; R302.5.1 prohibits it "
                                 "outright", (door.tag, garage.tag, neighbour.tag),
                                 "R302.5.1"))
                continue
            door_type = next((t for t in ctx.plan.library.door_types
                              if t.tag == door.type_ref), None)
            if door_type is None:
                out.append(_unknown(cid, f"door {door.tag} separates {garage.tag} from the "
                                    "dwelling but resolves no type", (door.tag,), "R302.5.1"))
                continue
            rating = door_type.fire_rating_minutes
            if rating is not None and rating >= _MIN_DOOR_FIRE_RATING:
                out.append(_pass(cid, f"door {door.tag} into {garage.tag} is "
                                 f"{rating}-minute rated", "R302.5.1"))
            elif door_type.core == "solid":
                # Leaf *thickness* is not modeled, so the 1-3/8" half of R302.5.1 goes
                # unmeasured and the message says so rather than implying it was checked.
                out.append(_pass(cid, f"door {door.tag} into {garage.tag} is solid core "
                                 "(leaf thickness unmodeled)", "R302.5.1"))
            elif door_type.core is None and rating is None:
                out.append(_unknown(cid, f"door {door.tag} separates {garage.tag} from the "
                                    "dwelling but its type states neither a core nor a fire "
                                    "rating", (door.tag,), "R302.5.1"))
            else:
                out.append(_fail(cid, f"door {door.tag} into {garage.tag} is a "
                                 f"{door_type.core or 'unrated'} leaf; R302.5.1 requires "
                                 "1-3/8\" solid wood or steel, or a 20-minute rating",
                                 (door.tag, garage.tag), "R302.5.1"))

        # 3. no supply/return duct opening into the garage
        registers = [r for r in ctx.plan.all_elements()
                     if r.element_kind == "Register" and r.room == garage.tag
                     and r.kind in (DuctSystem.SUPPLY, DuctSystem.RETURN)]
        if registers:
            names = sorted(r.tag for r in registers)
            out.append(_fail(cid, f"{garage.tag} has supply/return register(s) "
                             f"{', '.join(names)}; R302.5.2 forbids a duct opening into a "
                             "garage", (garage.tag, *names), "R302.5.2"))
        else:
            out.append(_pass(cid, f"no supply or return duct opens into {garage.tag}",
                             "R302.5.2"))
    return out


@check(Tier.CODE, "code.R302_13_floor_protection")
def floor_assembly_protection(ctx: CheckContext) -> list[Finding]:
    """R302.13 — engineered floor framing over a basement needs a membrane below it.

    An I-joist or open-web truss floor burns through far faster than sawn lumber, so the
    code asks for 1/2" gypsum or 5/8" wood structural panel on the underside unless the
    space below is sprinklered or is itself unusable.

    Reports UNKNOWN where no floor system resolves over the below-grade storey — which is
    this house today. Failing it would be asserting a deficiency in an assembly that is not
    modeled, and the whole point of the tri-state is that those are different answers.
    """
    from typehaus.model.floors import FloorSystem

    cid, code = "code.R302_13_floor_protection", "R302.13"
    from typehaus.checks.code.mn_residential._common import _storey_is_below_grade

    below = [storey for storey in ctx.plan.storeys
             if _storey_is_below_grade(ctx, storey) is True]
    if not below:
        if any(_storey_is_below_grade(ctx, s) is None for s in ctx.plan.storeys):
            return [_unknown(cid, "the site states no average-grade datum, so no storey can "
                             "be classified as a basement", (), code)]
        return [_pass(cid, "no below-grade storey — R302.13 has no floor over a basement to "
                      "protect", code)]
    # The floor *over* a basement is the floor system of the storey above it — a
    # FloorSystem belongs to the storey it decks, and carries no storey field of its own, so
    # the storey comes from the resolved floor.
    ordered = sorted(ctx.plan.storeys, key=lambda s: s.elevation.meters)
    above_tags = set()
    for storey in below:
        higher = [s for s in ordered if s.elevation.meters > storey.elevation.meters]
        if higher:
            above_tags.add(higher[0].tag)
    floor_storeys = {floor.tag: floor.storey for floor in ctx.model.floors}
    systems = [fs for fs in ctx.plan.all_elements()
               if isinstance(fs, FloorSystem) and fs.service == "floor"]
    over = [fs for fs in systems if floor_storeys.get(fs.tag) in above_tags]
    if not over:
        return [_unknown(cid, f"no floor system resolves over below-grade storey(s) "
                         f"{', '.join(sorted(s.tag for s in below))}, so the assembly "
                         "R302.13 protects is not modeled",
                         tuple(sorted(s.tag for s in below)), code)]
    out: list[Finding] = []
    for fs in over:
        member = str(getattr(fs.joists, "member", "") or "").lower()
        engineered = any(hint in member for hint in ("i-joist", "ijoist", "tji", "truss",
                                                     "open-web", "lvl"))
        if not engineered:
            out.append(_pass(cid, f"{fs.tag} frames with {member or 'sawn lumber'} — "
                             "R302.13 applies to engineered floor framing", code))
            continue
        ceiling = getattr(fs, "ceiling_below", None)
        if ceiling is None:
            out.append(_fail(cid, f"{fs.tag} uses engineered framing ({member}) over a "
                             "basement with no ceiling membrane below; R302.13 requires "
                             "1/2\" gypsum or 5/8\" wood structural panel",
                             (fs.tag,), code))
        else:
            out.append(_pass(cid, f"{fs.tag} carries a ceiling membrane below its "
                             f"{member} framing", code))
    return out

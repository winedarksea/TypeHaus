"""Uplift hardware along the continuous load path — the ROWS, grouped from the joints.

Where the joints *are* is :mod:`typehaus.joints`' business; this module is what a framer
buys. The split is not tidiness: a derived tie used to be locatable only from inside a bill
of materials, which is upstream of nothing, so three hundred ties could be specified, billed
and graded and never drawn. The locator moved out; the grouping stayed here.

The rest of the load path was already derived — MASA anchors and STHD holdowns off the sill
runs, SP ties off the studs, CS16 coil strap across the stacked wall lines (all
``takeoff/anchors.py``), and LUS/LSSR/HUCQ hangers off the *hung* member ends
(``takeoff/hangers.py``). This module bills the joints none of those can see: the ends that
**bear** rather than hang, and the post/beam connections.

Four rules, one condition each:

* **Bearing ties.** A rafter, truss heel or floor joist whose underside lands on the top of a
  support its own element names as a ``bearing_ref``. This is the exact complement of
  ``hangers.hung_connections`` — a hung end develops its depth *inside* a carrier, a bearing
  end sits *on* one — and the two rules cannot both fire on the same end because the
  elevation test that separates them is one-sided (see ``_bears_on``).
* **Post bases.** Every wood post whose section the catalog stocks a base for.
* **Post/beam straps.** Every beam end that lands on such a post.
* **Lateral tie plates.** The bottom plate of every framed wall standing on a floor band.

Two disciplines the whole module keeps:

* **Supports come from the element's own ``bearing_refs``**, never from a proximity search
  over every wall. A floor crosses walls it does not bear on; the model already states which
  ones carry it, so a tie is billed against a declared bearing and nothing else.
* **An authored ``Connector`` wins.** Every rule skips a joint a plan already modelled by
  hand — the same double-billing guard ``Material.exposed_fastener`` is for. The sunken
  garden and the breezeway author twenty connectors between them, and without this each of
  them would be bought twice.

A joint this module cannot bill is not silently dropped: ``checks/structural/uplift_path.py``
reports every link of the path that no hardware covers, which is where a concrete column, a
post with no declared bearing, or an unstocked section shows up.
"""

from __future__ import annotations

from collections import Counter

from typehaus.hardware.catalog import (
    EXPOSURE_DRY,
    EXPOSURE_TREATED,
    ROLE_GABLE_END_TIE,
    ROLE_HURRICANE_TIE,
    ROLE_LATERAL_TIE_PLATE,
    hardware_for_role,
)
from typehaus.hardware.config import FT_TO_M, GableEndTieRules, UpliftTieRules
from typehaus.joints.bearing import bearing_connections, continuous_bearing_members
from typehaus.joints.gable import gable_end_ties
from typehaus.joints.sills import tie_plate_walls
from typehaus.resolve.model import ResolvedModel
from typehaus.takeoff.hardware_row import hardware_row
from typehaus.takeoff.uplift_joints import (
    post_base_anchor_rows,
    post_base_rows,
    post_beam_strap_rows,
)

_M_TO_FT = 3.280839895013123


def _exposure(connection) -> str:
    """The wood-contact condition one bearing joint puts a tie in.

    One question, asked of the support: is the wood this tie screws into carrying a chemical
    preservative? IRC R317.3.1 answers what coating follows. It is deliberately NOT
    "indoors or out" — the thirty-eight rafter heels on W-A-* face a weather wall and sit on
    dry SPF plates under a roof, and sweeping those onto a ZMAX part would be a house-wide
    price rise bought with no code requirement behind it.
    """
    return EXPOSURE_TREATED if connection.support_treated else EXPOSURE_DRY


def bearing_uplift_tie_rows(model: ResolvedModel, rules: UpliftTieRules) -> list:
    """One tie per bearing joint, grouped by what bears where.

    Grouped on ``(member category, profile)`` rather than per support: a framer buys a box of
    H2.5A, and the support tag belongs in the basis where it can be audited rather than in a
    row that splits one order across thirty walls.
    """
    connections = bearing_connections(model, rules)
    if not connections:
        return []
    groups: dict = {}
    for connection in connections:
        key = (connection.member_category, connection.member_profile,
               _exposure(connection))
        entry = groups.setdefault(key, {"by_storey": Counter(), "supports": Counter()})
        entry["by_storey"][connection.storey] += rules.ties_per_bearing
        entry["supports"][connection.support_tag] += 1

    rows = []
    for (category, profile, exposure), entry in sorted(groups.items()):
        by_storey, supports = entry["by_storey"], entry["supports"]
        item = hardware_for_role(ROLE_HURRICANE_TIE, exposure=exposure)
        note = ("" if exposure == EXPOSURE_DRY else
                " — preservative-treated bearings, so a G185/ZMAX tie under IRC R317.3.1")
        rows.append(hardware_row(
            item, scope=f"{category.replace('_', ' ')} bearing", size=profile,
            count=int(sum(by_storey.values())), by_storey=dict(sorted(by_storey.items())),
            basis=(f"{rules.ties_per_bearing} per bearing joint x {sum(supports.values())} "
                   f"{profile} {category} ends seated on the declared bearings "
                   + ", ".join(f"{tag} x{n}" for tag, n in sorted(supports.items()))
                   + note)))
    return rows


# --- rule 3b: a beam that bears everywhere -------------------------------------------


def continuous_bearing_tie_rows(model: ResolvedModel, rules: UpliftTieRules) -> list:
    """Ties along a beam whose bearing runs its whole length.

    ``bearing_connections`` above ties member ENDS, which is the right rule for every rafter,
    truss heel and joist in the house and the wrong one for a beam that never leaves its wall
    — catlin's ridge is the case, and nothing else in the load path covers it.

    An H2.5A is what the rest of this schedule buys and what a 3-1/2" beam on a 5-1/2" plate
    takes; the pitch is the house's own 4'. Both are commodity choices recorded in
    ``houses/catlin/notes/ridge_beam_detail.md``, not an engineered uplift design: this
    function derives a *schedule* — how many ties, at what pitch — and no part of it reads a
    wind field, computes a tributary uplift, or compares one against the tie's allowable.
    Turning ``Site.design_wind_speed_mph`` into a per-tie demand is ``checks/structural/``
    work (``lateral_racking.py`` today, for the balcony's braced bays only).
    """
    groups: dict = {}
    for run in continuous_bearing_members(model, rules):
        entry = groups.setdefault((run.category, run.profile),
                                  {"count": 0, "runs": Counter()})
        entry["count"] += len(run.stations_m)
        entry["runs"][f"{run.length_m * _M_TO_FT:.4g}'"] += 1
    if not groups:
        return []

    # DRY: ``FramedMember.continuously_supported`` is set on a beam bedded along a wall for
    # its whole length, which in this house is the interior ridge on a dry SPF plate. A
    # treated member has never been continuously supported here, and if one ever is, this is
    # the line that has to start asking — a member carries no material ref of its own, so
    # there is nothing here to ask *with* yet, and an invented answer would be worse than a
    # stated assumption.
    item = hardware_for_role(ROLE_HURRICANE_TIE, exposure=EXPOSURE_DRY)
    rows = []
    for (category, profile), entry in sorted(groups.items()):
        runs = ", ".join(f"{length} x{n}" for length, n in sorted(entry["runs"].items()))
        rows.append(hardware_row(
            item, scope=f"{category.replace('_', ' ')} continuous bearing", size=profile,
            count=entry["count"],
            basis=(f"{rules.continuous_bearing_pitch_ft:g}' o.c. plus both ends along "
                   f"{runs} of {profile} bearing on a wall for its whole length")))
    return rows


# --- rule 4: lateral tie plates ------------------------------------------------------


def lateral_tie_plate_rows(model: ResolvedModel, rules: UpliftTieRules) -> list:
    """LTP4s along the bottom plate of every framed wall that stands on a floor band.

    The sill-on-concrete case is already anchored (MASA, ``anchors.mudsill_anchor_rows``);
    this is the joint above it, where a wall's bottom plate meets the rim and band of the
    floor it stands on and nothing but the nailing holds the two together laterally. The
    walls are exactly the upper halves of the resolved stack edges, so the rule follows the
    model's own account of what stands on what.
    """
    pitch_m = rules.tie_plate_pitch_ft * FT_TO_M
    by_storey: Counter = Counter()
    total_length_m, walls = 0.0, 0
    for wall in tie_plate_walls(model):
        (x0, y0), (x1, y1) = wall.axis
        length_m = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
        by_storey[wall.storey] += max(rules.minimum_tie_plates_per_wall,
                                      int(length_m / pitch_m) + 1)
        total_length_m += length_m
        walls += 1
    if not walls:
        return []
    item = hardware_for_role(ROLE_LATERAL_TIE_PLATE)
    return [hardware_row(
        item, scope="wall on floor band", count=int(sum(by_storey.values())),
        by_storey=dict(sorted(by_storey.items())), length_ft=total_length_m * _M_TO_FT,
        basis=(f"{rules.tie_plate_pitch_ft:g} ft o.c. (min "
               f"{rules.minimum_tie_plates_per_wall} per wall) along the bottom plate of "
               f"{walls} framed walls standing on a framed floor band (a wall on concrete "
               f"is a sill and is anchored by its mudsill anchors instead), "
               f"{total_length_m * _M_TO_FT:.1f} LF"))]


# --- rule 5: the gable end -----------------------------------------------------------


def gable_end_tie_rows(model: ResolvedModel, rules: GableEndTieRules) -> list:
    """H10As along every gable-end wall's top plate.

    The leg that had nothing. ``bearing_connections`` cannot see a gable end because no
    rafter bears on one, so the wall that takes the largest out-of-plane wind pressure in the
    house was the only link in the chain with no hardware against it.

    Grouped into ONE row rather than per wall: a framer buys a box of H10A, and the walls
    belong in the basis where they can be audited. See ``joints/gable.py`` for how a gable end
    is told from an eave wall and from an interior partition that happens to run the same way.
    """
    ends = gable_end_ties(model, rules)
    if not ends:
        return []
    by_storey: Counter = Counter()
    for end in ends:
        by_storey[end.storey] += len(end.stations_m)
    item = hardware_for_role(ROLE_GABLE_END_TIE)
    walls = ", ".join(f"{end.wall_tag} x{len(end.stations_m)}"
                      for end in sorted(ends, key=lambda e: e.wall_tag))
    return [hardware_row(
        item, scope="gable end wall", count=int(sum(by_storey.values())),
        by_storey=dict(sorted(by_storey.items())),
        basis=(f"{rules.tie_pitch_ft:g} ft o.c. plus both ends (min "
               f"{rules.minimum_ties_per_wall} per wall) along the top plate of "
               f"{len(ends)} gable-end walls: {walls}"))]


def uplift_rows(model: ResolvedModel, rules: UpliftTieRules,
                gable_rules: GableEndTieRules | None = None) -> list:
    """Every uplift line, in the order the load path runs: roof down to the band."""
    gable_rules = GableEndTieRules() if gable_rules is None else gable_rules
    return [
        *bearing_uplift_tie_rows(model, rules),
        *continuous_bearing_tie_rows(model, rules),
        *gable_end_tie_rows(model, gable_rules),
        *post_base_rows(model, rules),
        *post_base_anchor_rows(model, rules),
        *post_beam_strap_rows(model, rules),
        *lateral_tie_plate_rows(model, rules),
    ]

"""``thermal_break_transfer``'s calculation sheet: what it does not cover, plain-word symbols
and the joint's free body. Declared here to keep ``thermal_break`` under the line limit; not
hashed."""

from __future__ import annotations

from typehaus.engineering.item import EngineeringRecord, Figure, NotCovered, num
from typehaus.engineering.retaining_sheet import PrefixLabels
from typehaus.engineering.sketch import joint_section

_SEAL = "the sealing engineer"

LABELS = PrefixLabels({
    "board_t": "board thickness",
    "board_h": "board height",
    "board_L": "board length along the joint",
    "foam_psi": "board's rated compressive strength",
    "compliant_t": "compliant (EPDM) layer thickness",
    "compliant_max_psi": "most stress the compliant layer's sheet allows at 25% strain",
    "delta_T": "closing range: service maximum less the set temperature",
    "court_run": "the court's run toward the house",
    "foam_modulus": "board modulus (ESTIMATED where not published)",
    "closure": "joint closure at the stress the board is graded at",
    "board_stress": "stress on the board (the compliant layer's cap)",
    "board_lock_in": "force locked in by the fresh pour",
    "board_thrust": "thrust this board passes to the house",
    "house_thrust": "thrust of every board on the loop",
    "wall_thrust": "thrust on the house wall panel",
    "wall_span": "span of the house wall panel, footing to floor",
    "wall_fc": "house wall concrete strength f'c",
    "wall_steel_area": "steel in the whole house wall panel",
    "wall_effective_depth": "effective depth of the house wall",
    "slab_fc": "house slab concrete strength f'c",
    "near_line_width": "width of the house's near footing line",
    "near_line_fc": "near footing line concrete strength f'c",
    "slab_edge_modulus": "modulus of the slab's perimeter break",
    "winter_tension": "tension in one side line when the court contracts",
    "winter_tension_steel": "steel continuous along the weakest side run",
    "winter_joint_steel": "steel crossing the spliced footing joint",
    "winter_joint_section": "plain footing section at a joint no bar crosses",
    "joint_fit_min_f": "temperature the boards are fitted at, at or above",
    "joint_thermal": "thermal closure of the joint",
    "joint_board_squeeze": "board's own squeeze at the cap (reported, not credited)",
    "joint_slide": "sliding of the court toward the house",
    "pour_head": "head of fresh concrete above the board's bottom",
    "neutral_point": "distance from the far end to the court's neutral point",
    "soil_presumed": "soil class presumed from a code table (not measured)",
})

NOT_COVERED = (
    NotCovered("shear, racking and differential movement across the joint",
               "no structural member crosses it: the court holds its own thrust and the "
               "boards keep the house out of that free body; what does cross (the veneer "
               "ties, the boards' compliance) is named and bounded by the joint row",
               _SEAL, "accepting the isolation joint as drawn"),
    NotCovered("the veneer ties' travel across the joint",
               "the ties go in with the boards and take the same closure as the joint row; "
               "their own capacity is the veneer tie sheet's",
               _SEAL, "the veneer tie calculation"),
    NotCovered("board flotation and fresh-concrete pressure",
               "nothing restrains a board with no bars; a board cast against a stripped "
               "blockout is set after the pour and never meets fresh concrete, a field "
               "sequence the model states and cannot enforce",
               "the contractor at excavation",
               "the placement annotation carried to site, and a schedule hold"),
    NotCovered("the house's own soil",
               "the house's lateral path and far-wall rows read IBC Table 1806.2 "
               "presumptions for a presumed soil class",
               "the owner (soil report)", "a geotechnical report on this parcel"),
)

HOUSE_PATH = ("boards -> house wall panel, floor line (sill anchors)",
              "the rest -> slab edge -> slab strut -> far footing line",
              "held by friction under the whole house and the far wall's soil")


def _val(record: EngineeringRecord, name: str) -> float | None:
    for q in record.inputs:
        if q.name == name or q.name.endswith(":" + name):
            return q.value
    return None


def figure(record: EngineeringRecord) -> Figure | None:
    thermal, slide = _val(record, "joint_thermal"), _val(record, "joint_slide")
    total = _val(record, "house_thrust")
    if thermal is None or slide is None or total is None:
        return None
    closure = next((s for s in record.limit_states if s.name == "court-to-house joint closure"),
                   None)
    allow = (f"the layer takes {num(closure.capacity)} in" if closure
             else "the layer's capacity is not graded")
    return joint_section(
        title=f"{record.key}: the court-to-house isolation joint",
        stack=(f"closure: {num(thermal)} in thermal + {num(slide)} in sliding",
               f"  = {num(thermal + slide)} in; {allow}",
               f"thrust of every board on the loop T = {num(total)} lb"),
        path=HOUSE_PATH,
        caption="Not to scale; section through one board in plan.")

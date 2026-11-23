"""The court's calculation sheets: what they do not cover, plain-word symbols and free bodies.

``retaining_wall`` and ``retaining_system`` declare here, so the calc modules stay under the
line limit. Nothing in this module is hashed (``item.declare_sheet``). Free bodies read the
record's own inputs and the first step of a state's working, never a recomputation.
"""

from __future__ import annotations

from typehaus.engineering.item import EngineeringRecord, Figure, NotCovered, num
from typehaus.engineering.sketch import cantilever_wall, court_loop_plan


class PrefixLabels(dict):
    """A ``labels`` mapping that also answers for inputs named with a tag in them
    (``thrust_W-SG-E2``, ``TB-SG-E1:board_t``, ``surcharge_W-RG-EAST_lateral``)."""

    def __init__(self, exact: dict[str, str], prefixes: dict[str, str] | None = None,
                 suffixes: dict[str, str] | None = None) -> None:
        super().__init__(exact)
        self._prefixes = prefixes or {}
        self._suffixes = suffixes or {}

    def get(self, name, default=""):  # type: ignore[no-untyped-def]
        if ":" in name:
            name = name.split(":", 1)[1]
        if name in self:
            return self[name]
        for prefix, text in self._prefixes.items():
            if name.startswith(prefix):
                return text.format(tag=name[len(prefix):])
        for suffix, text in self._suffixes.items():
            if name.endswith(suffix):
                return text.format(tag=name[:-len(suffix)])
        return default


SOIL_LABELS = {
    "bed_friction": "design friction of concrete on the washed-stone bed",
    "restraint_friction": "upper bed friction for the rows that friction hurts",
    "native_friction": "friction of the native soil at the bed bottom, tan phi'",
    "soil_confirmed": "soil parameters confirmed by a site report",
    "toe_embedment": "soil cover over the toe (passive, not credited)",
}

_WALL_LABELS = PrefixLabels({
    **SOIL_LABELS,
    "system_demand": "resultant thrust on the whole court body",
    "system_capacity": "base friction of the whole court body",
    "column_axial": "service axial of the columns on the wall top, per foot",
    "column_base_moment": "base moment of those columns, per foot",
}, suffixes={
    "_q_net": "net pressure of the apron {tag} over the soil it displaces",
    "_lateral": "lateral thrust of the apron {tag} on this wall",
    "_arm": "height of that thrust above the footing underside",
})

_SYSTEM_LABELS = PrefixLabels({
    **SOIL_LABELS,
    "stone_unit_weight": "unit weight of the washed stone in the beds",
    "body_weight_110": "weight of the sliding body, soil at 110 pcf",
    "body_resultant_110": "resultant thrust on the body, soil at 110 pcf",
    "cross_thickness": "strut thickness",
    "cross_height": "strut depth",
    "cross_fc": "strut concrete strength f'c",
}, prefixes={
    "thrust_": "at-rest thrust per foot of {tag}",
    "weight_": "weight per foot of {tag}'s section",
    "length_": "length of {tag}",
})

_OWNER = "the owner (stated basis)"
_SEAL = "the sealing engineer"

WALL_NOT_COVERED = (
    NotCovered("hydrostatic pressure behind the wall",
               "every number presumes the drained face works; a saturated backfill roughly "
               "doubles the thrust. The court's perched and flooded cases are on the "
               "retaining_system sheet",
               _SEAL, "accepting the drainage as drawn, or a saturated-backfill check"),
    NotCovered("seismic increment",
               "none is applied; this is a screening on presumptive code values",
               _SEAL, "accepting wind and earth as the governing loads"),
    NotCovered("global stability and settlement",
               "not opened: the rows grade the wall's own sliding, overturning, bearing and "
               "sections",
               _SEAL, "a geotechnical report on this parcel"),
    NotCovered("passive resistance on the toe",
               "neglected: the toe is buried 0 in, so there is no soil to mobilise",
               _SEAL, "none needed unless the toe is later buried"),
    NotCovered("bearing of the stone bed on the native soil beneath it",
               "the bearing row grades the stone only, at 3,000 psf",
               _SEAL, "the bearing-on-native row, where it is graded"),
)

SYSTEM_NOT_COVERED = (
    NotCovered("ground snow together with perched water",
               "taken as not concurrent by the owner's stated basis; each is graded alone",
               _OWNER, "the owner re-opening the basis"),
    NotCovered("lateral frost thrust in the top 42 in of retained fill",
               "not covered (owner's stated basis)", _OWNER,
               "the owner re-opening the basis"),
    NotCovered("seasonal thermal ratcheting under the sustained thrust",
               "not covered (owner's stated basis)", _OWNER,
               "the owner re-opening the basis"),
    NotCovered("retained water to the terrace with the court empty",
               "reported in the assumptions and not graded: the court's drain and overflow "
               "are taken to work",
               _SEAL, "accepting the drain and overflow as drawn"),
    NotCovered("bed-bottom acceptance at excavation",
               "the bottom must be granular (GW, GP, SW, SP, GM or SM), firm under the "
               "plate, with no standing water or seepage 48 h after rain, checked by "
               "visual-manual classification",
               "the owner (checks at excavation)",
               "that check; a clay or silt bottom builds the lean-wall fallback"),
    NotCovered("the spliced walls' own thrusts",
               "W-SG-W1 and W-SG-E1 enter the body by their concrete only; their thrusts "
               "are carried by their own braces",
               _SEAL, "the basement-wall check of those walls"),
)


def _step(record: EngineeringRecord, symbol: str) -> float | None:
    for state in record.limit_states:
        for step in state.working:
            if step.symbol == symbol:
                return step.value
    return None


def wall_figure(record: EngineeringRecord) -> Figure | None:
    values = [record.value(n) for n in ("retained_height", "stem_thickness", "toe", "heel",
                                        "footing_width")]
    thrust, weight = _step(record, "T"), _step(record, "W")
    if None in values or thrust is None or weight is None:
        return None
    height, stem, toe, heel, width = values
    restrained = any(s.name == "base restraint" for s in record.limit_states)
    return cantilever_wall(
        title=f"{record.key} in section, per foot of wall", height_ft=height,
        stem_in=stem * 12.0, toe_ft=toe, heel_ft=heel, footing_ft=width,
        thrust=f"T = {num(thrust)} plf", thrust_arm_ft=height / 3.0,
        weight=f"W = {num(weight)} plf",
        base=("held by the court's strut: sliding is graded on the whole court"
              if restrained else "friction on the bed"),
        caption="Moments about the toe; passive resistance on the toe is not credited.")


def system_figure(record: EngineeringRecord) -> Figure | None:
    tags = sorted(q.name[len("thrust_"):] for q in record.inputs if q.name.startswith("thrust_"))
    if len(tags) != 3:
        return None
    sides = [t for t in tags if any(
        s.name.startswith("footing plan bending") and s.name.endswith(t.split("-", 1)[1])
        for s in record.limit_states)]
    if len(sides) != 2:
        return None
    base = next(t for t in tags if t not in sides)

    def leg(tag: str) -> tuple[str, str]:
        return tag, (f"{num(record.value('thrust_' + tag) or 0)} plf x "
                     f"{num(record.value('length_' + tag) or 0)} ft")

    h, f = _step(record, "H"), _step(record, "F")
    summary = (() if h is None or f is None else
               (f"resultant H = {num(h)} lb against base friction F = {num(f)} lb",))
    return court_loop_plan(
        title=f"{record.key}: the court as one body, in plan", left=leg(sides[0]),
        right=leg(sides[1]), base=leg(base), strut=record.key, summary=summary,
        caption="Thrusts per foot of wall and wall length; the two side walls push against "
                "each other through the strut and cancel, the south wall's does not.")


WALL_SHEET = dict(not_covered=WALL_NOT_COVERED, labels=_WALL_LABELS, figure=wall_figure)
SYSTEM_SHEET = dict(not_covered=SYSTEM_NOT_COVERED, labels=_SYSTEM_LABELS, figure=system_figure)

"""HVAC schedules: equipment, zones, duct runs, terminals, and the ventilation summary.

One derivation, three consumers. ``heating_zones`` is imported by
``checks.mep.hvac.heating_capacity`` (the same precedent ``checks.mep.electrical`` sets by
importing the service-load summary) so the check, the ``hvac`` block of ``model.json``, and
the HVAC reader in the UI can never disagree about what a zone is or what its load is.

A zone is a *grouping of rooms*: the authored ``Equipment.zone_rooms``. Nothing here infers
one. An indoor head or ducted air handler names its condenser with ``outdoor_ref``, so a
multi-zone condenser's zone is the union of its heads' rooms, and its capacity is compared
against the load of exactly that union. A conditioned room no unit claims is reported as
such rather than swept into the nearest zone.
"""

from __future__ import annotations

from dataclasses import dataclass

from typehaus.checks.registry import Preferences
from typehaus.quantities import M_PER_IN
from typehaus.resolve.model import ResolvedModel
from typehaus.resolve.room_lookup import axis_polygon

_M_TO_FT = 3.280839895
# Electric resistance heat converts at the physical constant — no efficiency term to apply.
_W_TO_BTUH = 3.412141633
#: Square feet per square metre. Room heat is reported to people who think in feet.
_M2_TO_FT2 = 10.76391041671

# The indoor halves of a split system: both pair back to a condenser and neither carries a
# rating of its own that a zone should be sized against.
_INDOOR_KINDS = frozenset({"indoor_head", "ducted_air_handler"})
_VENTILATION_KINDS = frozenset({"erv"})


@dataclass(frozen=True)
class HeatPumpCapacity:
    """A heat pump's three capacity levels read at ONE outdoor temperature, with provenance.

    ``basis`` is a sentence, not an enum: a finding prints it so a reader sees where the
    number came from — "read at −15 °F (manufacturer)" or "interpolated between −13 °F and
    5 °F (neep)". A capacity with no provenance is the defect the ratings table closed, and
    losing the provenance on the way out would reopen it one layer down.
    """

    outdoor_db_f: float
    minimum_btuh: float | None
    rated_btuh: float | None
    maximum_btuh: float | None
    basis: str


def _interpolate(low_t: float, low: float | None, high_t: float, high: float | None,
                 at: float) -> float | None:
    """Linear between two rows, per column, and ``None`` unless BOTH state that column.

    Per column and not per row, because the published tables are ragged: a manufacturer's
    extended ratings state maximum at every temperature and minimum at three of them, and a
    maximum interpolated across a gap in the minimum column would be fine while a minimum
    interpolated from one endpoint would be invented.
    """
    if low is None or high is None:
        return None
    if high_t == low_t:
        return low
    return low + (high - low) * (at - low_t) / (high_t - low_t)


def capacity_at(rows, odb_f: float) -> HeatPumpCapacity | None:
    """Read a heat pump's capacity table at one outdoor temperature.

    **Refuses to extrapolate at BOTH ends**, which is one more than ``erv_static._delivered``
    does — and the difference is deliberate. A fan curve may be clamped at its low end
    because a fan cannot beat its own free-air flow, so the clamp is a physical bound. There
    is no such bound here: a compressor below the coldest published row is not "at least the
    coldest row's output", it is a machine the manufacturer declined to characterise, and
    quite possibly one that has locked out. Returning the endpoint would turn a gap in the
    document into a number the check then passes on.

    ``None`` where the table is empty, or where ``odb_f`` falls outside its span.
    """
    if not rows:
        return None
    if odb_f < rows[0].outdoor_db_f or odb_f > rows[-1].outdoor_db_f:
        return None
    exact = next((row for row in rows if row.outdoor_db_f == odb_f), None)
    if exact is not None:
        return HeatPumpCapacity(
            odb_f, exact.minimum_btuh, exact.rated_btuh, exact.maximum_btuh,
            f"read at {odb_f:g} °F ({exact.basis.value})")
    low = max((row for row in rows if row.outdoor_db_f < odb_f),
              key=lambda row: row.outdoor_db_f)
    high = min((row for row in rows if row.outdoor_db_f > odb_f),
               key=lambda row: row.outdoor_db_f)
    bases = dict.fromkeys((low.basis.value, high.basis.value))
    return HeatPumpCapacity(
        odb_f,
        _interpolate(low.outdoor_db_f, low.minimum_btuh,
                     high.outdoor_db_f, high.minimum_btuh, odb_f),
        _interpolate(low.outdoor_db_f, low.rated_btuh,
                     high.outdoor_db_f, high.rated_btuh, odb_f),
        _interpolate(low.outdoor_db_f, low.maximum_btuh,
                     high.outdoor_db_f, high.maximum_btuh, odb_f),
        f"interpolated between {low.outdoor_db_f:g} °F and {high.outdoor_db_f:g} °F "
        f"({'/'.join(bases)})")


@dataclass(frozen=True)
class HvacUnit:
    """One authored ``Equipment`` instance joined to its ``EquipmentType``."""

    tag: str
    uid: str
    storey: str
    kind: str
    name: str | None
    type_ref: str | None
    room: str | None
    zone_rooms: tuple[str, ...]
    outdoor_ref: str | None
    circuit: str | None
    #: The type's published heating table (``HeatPumpRating`` rows), ascending in
    #: temperature. The two scalars that were here — ``heating_capacity_btuh`` and
    #: ``heating_capacity_at_design_btuh`` — are gone: *at design* is a question about the
    #: SITE and this record never knew the site (→ decision #76).
    heating_ratings: tuple
    resistance_heating_btuh: float | None
    aux_lockout_above_f: float | None
    cooling_capacity_btuh: float | None
    min_operating_temp_f: float | None
    ventilation_cfm: float | None
    sensible_recovery_effectiveness: float | None
    supplemental_heat: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "tag": self.tag, "uid": self.uid, "storey": self.storey, "kind": self.kind,
            "name": self.name, "type_ref": self.type_ref, "room": self.room,
            "zone_rooms": list(self.zone_rooms), "outdoor_ref": self.outdoor_ref,
            "circuit": self.circuit,
            "heating_ratings": [row.model_dump(mode="json") for row in self.heating_ratings],
            "resistance_heating_btuh": self.resistance_heating_btuh,
            "aux_lockout_above_f": self.aux_lockout_above_f,
            "cooling_capacity_btuh": self.cooling_capacity_btuh,
            "min_operating_temp_f": self.min_operating_temp_f,
            "ventilation_cfm": self.ventilation_cfm,
            "sensible_recovery_effectiveness": self.sensible_recovery_effectiveness,
            "supplemental_heat": self.supplemental_heat,
        }


@dataclass(frozen=True)
class HvacZone:
    """One rated unit and the rooms it serves, with the block load of exactly those rooms."""

    name: str  # human label, e.g. "System 2 (EQ-B-HP-MULTI)"
    equipment_tag: str  # the rated unit — a condenser, or a standalone rated unit
    type_tag: str | None
    rooms: frozenset[str]
    indoor_tags: tuple[str, ...]  # heads/air handlers pointing at this unit
    heating_load_btu_per_hour: float
    heating_capacity_at_design_btuh: float | None
    cooling_load_btu_per_hour: float
    cooling_capacity_btuh: float | None
    min_operating_temp_f: float | None
    # Resistance heat inside this zone's rooms: mats and the electric fireplace. It carries no
    # zone of its own, but at design temp it is heat the outdoor unit does not have to make,
    # so it counts toward the margin.
    supplemental_btuh: float
    supplemental_tags: tuple[str, ...]
    unknown_inputs: tuple[str, ...]
    #: The zone's LATENT load (occupants only — see ``EnergyReport``). Apart from
    #: ``cooling_load_btu_per_hour``, which stays SENSIBLE because a unit's
    #: ``cooling_capacity_btuh`` is a sensible rating.
    latent_btu_per_hour: float = 0.0
    #: Terms the block load knowingly does not carry, as opposed to inputs it is missing.
    #: The sizing checks print these beside the margin so the number never travels without
    #: them — an omitted term is not an UNKNOWN and must not take the verdict with it.
    cooling_caveats: tuple[str, ...] = ()
    #: The site's 99% heating design temperature — the odb ``heating_load_btu_per_hour`` was
    #: computed at, and the one ``heating_load_at_outdoor_f`` reproduces.
    design_temp_f: float | None = None
    #: The zone's heating load DECOMPOSED, so it can be re-evaluated at any outdoor
    #: temperature without a second envelope walk. ``air_coupled_ua`` is the sum of
    #: ``UA × 1`` over every component whose ΔT is the outdoor air, plus the two air-side
    #: terms divided by that same ΔT; ``ground_coupled_btuh`` is everything charged the
    #: ground boundary, which does not move with the weather at all. Read straight off
    #: ``LoadComponent.heating_delta_f`` — no second pass, no perf cost.
    air_coupled_ua: float = 0.0
    ground_coupled_btuh: float = 0.0
    #: The unit's published table, carried through so a check can walk it rather than ask
    #: the model again.
    heating_ratings: tuple = ()
    resistance_at_design_btuh: float | None = None
    capacity_basis: str | None = None

    def heating_load_at_outdoor_f(self, odb_f: float) -> float:
        """This zone's heating load at any outdoor temperature, Btu/h.

        The turndown question is "at what temperature does the unit's MINIMUM output fall to
        the load", and neither side of that is a single number. The load is
        ``ground_coupled_btuh + air_coupled_ua × (setpoint − odb)`` — the decomposition the
        two fields above carry, which is why this costs nothing.

        **Pinned invariant:** ``heating_load_at_outdoor_f(design) == heating_load_btu_per_hour``
        exactly, including in the degenerate case where the house authors no ground boundary
        and every component was charged the air ΔT. The decomposition mirrors what
        ``estimate_block_load`` actually did, not what it ideally would have.
        """
        if self.design_temp_f is None:
            return self.heating_load_btu_per_hour
        setpoint = self.design_temp_f + self._air_delta_at_design
        return self.ground_coupled_btuh + self.air_coupled_ua * (setpoint - odb_f)

    #: The air ΔT the zone's load was computed at. Stored rather than re-derived from a
    #: preference, because the *decomposition* has to be exact against the number
    #: ``estimate_block_load`` produced and the preference is one input to that.
    _air_delta_at_design: float = 0.0

    @property
    def heating_margin_btuh(self) -> float | None:
        if self.heating_capacity_at_design_btuh is None:
            return None
        return (self.heating_capacity_at_design_btuh + self.supplemental_btuh
                - self.heating_load_btu_per_hour)

    @property
    def cooling_margin_btuh(self) -> float | None:
        if self.cooling_capacity_btuh is None:
            return None
        return self.cooling_capacity_btuh - self.cooling_load_btu_per_hour

    def as_dict(self) -> dict[str, object]:
        return {
            "name": self.name, "equipment_tag": self.equipment_tag,
            "type_tag": self.type_tag, "rooms": sorted(self.rooms),
            "indoor_tags": list(self.indoor_tags),
            "heating_load_btu_per_hour": self.heating_load_btu_per_hour,
            "heating_capacity_at_design_btuh": self.heating_capacity_at_design_btuh,
            "supplemental_btuh": self.supplemental_btuh,
            "supplemental_tags": list(self.supplemental_tags),
            "heating_margin_btuh": self.heating_margin_btuh,
            "cooling_load_btu_per_hour": self.cooling_load_btu_per_hour,
            "cooling_capacity_btuh": self.cooling_capacity_btuh,
            "cooling_margin_btuh": self.cooling_margin_btuh,
            "latent_btu_per_hour": self.latent_btu_per_hour,
            "cooling_caveats": list(self.cooling_caveats),
            "design_temp_f": self.design_temp_f,
            "air_coupled_ua": self.air_coupled_ua,
            "ground_coupled_btuh": self.ground_coupled_btuh,
            "capacity_basis": self.capacity_basis,
            "min_operating_temp_f": self.min_operating_temp_f,
            "unknown_inputs": list(self.unknown_inputs),
        }


def hvac_units(model: ResolvedModel) -> list[HvacUnit]:
    """Every authored ``Equipment`` instance, joined to its type's ratings."""
    types = {item.tag: item for item in model.plan.library.equipment_types}
    units: list[HvacUnit] = []
    for storey in model.plan.storeys:
        for element in model.plan.storey_elements(storey.tag):
            if element.element_kind != "Equipment":
                continue
            product = types.get(getattr(element, "type_ref", None))
            units.append(HvacUnit(
                tag=element.tag, uid=element.uid, storey=storey.tag,
                kind=element.kind.value,
                name=getattr(product, "name", None),
                type_ref=getattr(element, "type_ref", None),
                room=getattr(element, "room", None),
                zone_rooms=tuple(getattr(element, "zone_rooms", ())),
                outdoor_ref=getattr(element, "outdoor_ref", None),
                circuit=getattr(element, "circuit", None),
                heating_ratings=tuple(getattr(product, "heating_ratings", ()) or ()),
                resistance_heating_btuh=getattr(
                    product, "resistance_heating_btuh", None),
                aux_lockout_above_f=getattr(product, "aux_lockout_above_f", None),
                cooling_capacity_btuh=getattr(product, "cooling_capacity_btuh", None),
                min_operating_temp_f=getattr(product, "min_operating_temp_f", None),
                ventilation_cfm=getattr(product, "ventilation_cfm", None),
                sensible_recovery_effectiveness=getattr(
                    product, "sensible_recovery_effectiveness", None),
                supplemental_heat=bool(getattr(product, "supplemental_heat", False)),
            ))
    return sorted(units, key=lambda unit: unit.tag)


def equipment_schedule(model: ResolvedModel) -> list[dict[str, object]]:
    return [unit.as_dict() for unit in hvac_units(model)]


def _rated(unit: HvacUnit) -> bool:
    """Does this unit carry a capacity rating a zone can be sized against?

    Supplemental resistance heat — the electric fireplace, radiant mats — never claims a zone
    however it is rated: nothing sizes a house around a fireplace, and letting a rated one
    open a zone of its own would double-count it against the zone it actually sits inside.
    It still counts *toward* that zone through :func:`supplemental_heat_by_room`. The garage
    unit heater carries no rating at all and the garage is unconditioned besides. Indoor heads
    never claim a zone either, even when their type states a nominal capacity: the outdoor
    unit is what has to make the heat at the design temperature.
    """
    if unit.kind in _INDOOR_KINDS or unit.supplemental_heat:
        return False
    return bool(unit.heating_ratings) or unit.resistance_heating_btuh is not None


def _design_temp_f(model: ResolvedModel) -> float | None:
    """The site's 99% heating design temperature, or ``None``. The number *at design* means."""
    design = model.plan.project.site.design_temp_heating
    return None if design is None else design.fahrenheit


def _resistance_at_design(unit: HvacUnit, design_f: float | None) -> float | None:
    """A resistance element's output at the site design temperature, Btu/h.

    **Derived, where it used to be a hand-computed scalar in the catalog.** The heat kit in
    catlin's System 1 cabinet was authored ``heating_capacity_at_design_btuh=0`` with prose
    explaining that its control locks it out above −22 °F and the site designs at −15 °F.
    That is a correct reading and it could go stale in silence the moment the site moved.
    Now ``aux_lockout_above_f`` states the control setting and this does the comparison.

    ``None`` where the unit carries no resistance rating at all.
    """
    if unit.resistance_heating_btuh is None:
        return None
    lockout = unit.aux_lockout_above_f
    if lockout is None or design_f is None:
        return unit.resistance_heating_btuh
    return unit.resistance_heating_btuh if design_f <= lockout else 0.0


def supplemental_heat_by_room(model: ResolvedModel) -> dict[str, list[tuple[str, float]]]:
    """Resistance heat that supplements a zone, gathered onto the room it heats.

    Two authoring shapes feed this, and both are keyed by *room* so the sum partitions across
    zones exactly as the rooms do — a room belongs to at most one zone, so nothing can be
    counted twice however the zones are drawn:

    * ``Equipment`` whose type is ``supplemental_heat`` and carries an at-design rating,
      placed in a room (the electric fireplace);
    * ``FloorHeat`` with authored ``watts`` — by ``room_ref`` when it names one, else by the
      room whose clear face contains the resolved zone. That fallback is what lets a mat sit
      free-standing inside a large room (Catlin's dining zone is 58 ft2 of a 642 ft2 living
      room, deliberately without a ``room_ref``) without forcing an untrue whole-room claim.
    """
    from shapely.geometry import Point, Polygon

    from typehaus.model.floors import FloorHeat

    out: dict[str, list[tuple[str, float]]] = {}

    def add(room: str, tag: str, btuh: float) -> None:
        out.setdefault(room, []).append((tag, btuh))

    design_f = _design_temp_f(model)
    for unit in hvac_units(model):
        if not unit.supplemental_heat or unit.room is None:
            continue
        # Resistance heat is flat with outdoor temperature, so its scalar IS its at-design
        # output — subject to a lockout, which is the one thing that can take it away.
        rated = _resistance_at_design(unit, design_f)
        if rated is None and unit.heating_ratings:
            # A supplemental unit with a real compressor table (nothing in catlin, but the
            # schema allows it): read the table like any other.
            capacity = capacity_at(unit.heating_ratings, design_f) if design_f else None
            rated = capacity.rated_btuh or capacity.maximum_btuh if capacity else None
        if rated is not None:
            add(unit.room, unit.tag, rated)

    # Resolved zones carry the geometry; the authored records carry `watts` and `room_ref`.
    resolved = {item.tag: item for item in model.floor_heat}
    rooms_by_storey: dict[str, list[object]] = {}
    for room in model.rooms:
        rooms_by_storey.setdefault(room.storey, []).append(room)

    for storey in model.plan.storeys:
        for element in model.plan.storey_elements(storey.tag):
            if not isinstance(element, FloorHeat) or element.watts is None:
                continue
            btuh = element.watts * _W_TO_BTUH
            if element.room_ref:
                add(element.room_ref, element.tag, btuh)
                continue
            zone = resolved.get(element.tag)
            if zone is None or not zone.zone:
                continue
            centre = Polygon(zone.zone).representative_point()
            host = next((room for room in rooms_by_storey.get(storey.tag, [])
                         if axis_polygon(room).contains(Point(centre))), None)
            if host is not None:
                add(host.tag, element.tag, btuh)
    return out


@dataclass(frozen=True)
class RoomHeat:
    """What actually heats one conditioned room, gathered from every authoring shape.

    One row per conditioned room, and the point of it is that the *question* differs by
    room. A room with a supply register belongs to a ducted zone and its heat is that zone's
    margin — an arithmetic already done by :func:`heating_zones`. A room with no supply
    register is heated by whatever is physically in it, and nothing was gathering that.

    It lives here rather than in the check because :func:`supplemental_heat_by_room` already
    owns room attribution for radiant and resistance heat, and a second walk of
    ``FloorHeat`` and ``Equipment`` would be a second answer to "which room does this heat".
    """

    room: str
    occupancy: str
    storey: str
    area_ft2: float
    #: What physically reaches this room with conditioned air, by tag: a non-ventilation
    #: SUPPLY register in it, or an indoor head / air handler standing in it. EMPTY is the
    #: interesting case — the room is heated by whatever is inside it and by transfer through
    #: its doorways, and transfer is not something this model can see. Deliberately NOT
    #: ``zone_rooms``: a zone is an authored CLAIM about which rooms a unit serves, and a
    #: head in the basement gym claims the bathroom upstairs behind two doors.
    reached_by: tuple[str, ...]
    #: The rated outdoor unit whose ``zone_rooms`` claim this room, and that zone's margin.
    zone_tag: str | None
    zone_margin_btuh: float | None
    #: ``FloorHeat`` zones attributed to this room, and what they DELIVER at design.
    radiant_tags: tuple[str, ...]
    #: ``min(heated area x delivered_btuh_per_ft2, watts x 3.412)`` summed over the zones —
    #: the floor cannot deliver more than the cable draws, and cannot deliver the cable's
    #: whole draw over more floor than is heated. ``None`` when no zone in the room states
    #: ``delivered_btuh_per_ft2``, which is a gap and never a zero.
    radiant_btuh: float | None
    #: Zones that state ``watts`` but no ``delivered_btuh_per_ft2``, by tag.
    radiant_undeclared: tuple[str, ...]
    #: Resistance heat that is not a floor — a fireplace, a wall unit — from
    #: :func:`supplemental_heat_by_room`, with the radiant entries taken back out.
    supplemental_btuh: float
    supplemental_tags: tuple[str, ...]

    @property
    def delivered_btuh(self) -> float | None:
        """Everything in the room that makes heat, or None when the radiant side is a gap."""
        if self.radiant_btuh is None:
            return None if self.radiant_undeclared else self.supplemental_btuh
        return self.radiant_btuh + self.supplemental_btuh


def room_heat_sources(model: ResolvedModel,
                      preferences: Preferences) -> list[RoomHeat]:
    """One :class:`RoomHeat` per conditioned room, ordered by tag.

    ``preferences`` is taken for symmetry with :func:`heating_zones` and because a caller
    holding one should not have to find another; nothing here reads it today.
    """
    from shapely.geometry import Point, Polygon

    from typehaus.model.floors import FloorHeat

    zones, _unclaimed = heating_zones(model, preferences)
    zone_of: dict[str, HvacZone] = {}
    for zone in zones:
        for room in zone.rooms:
            zone_of[room] = zone

    reach: dict[str, list[str]] = {}
    for row in register_schedule(model):
        if row["kind"] == "supply" and not row["ventilation_terminal"] and row["room"]:
            reach.setdefault(str(row["room"]), []).append(str(row["tag"]))
    for unit in hvac_units(model):
        if unit.kind in _INDOOR_KINDS and unit.room:
            reach.setdefault(unit.room, []).append(unit.tag)

    # Radiant, attributed the same way ``supplemental_heat_by_room`` attributes it: by
    # ``room_ref`` when the zone names one, else by the room whose clear face contains it.
    # One walk, so the two can never disagree about which room a mat heats.
    resolved = {item.tag: item for item in model.floor_heat}
    rooms_by_storey: dict[str, list[object]] = {}
    for room in model.rooms:
        rooms_by_storey.setdefault(room.storey, []).append(room)
    radiant_output: dict[str, list[tuple[str, float | None]]] = {}
    for storey in model.plan.storeys:
        for element in model.plan.storey_elements(storey.tag):
            if not isinstance(element, FloorHeat):
                continue
            zone_geom = resolved.get(element.tag)
            if zone_geom is None or not zone_geom.zone:
                continue
            polygon = Polygon(zone_geom.zone)
            host = element.room_ref
            if host is None:
                centre = polygon.representative_point()
                found = next((room for room in rooms_by_storey.get(storey.tag, [])
                              if axis_polygon(room).contains(Point(centre))), None)
                host = found.tag if found is not None else None
            if host is None:
                continue
            if element.delivered_btuh_per_ft2 is None:
                # A gap, never a zero: a mat whose delivered output nobody stated is not a
                # mat that delivers nothing, and the check must say so rather than sum it.
                radiant_output.setdefault(host, []).append((element.tag, None))
                continue
            # The floor cannot deliver more than the cable draws, and cannot deliver the
            # cable's whole draw over more floor than is actually heated. Both bounds bind.
            delivered = polygon.area * _M2_TO_FT2 * element.delivered_btuh_per_ft2
            if element.watts is not None:
                delivered = min(delivered, element.watts * _W_TO_BTUH)
            radiant_output.setdefault(host, []).append((element.tag, delivered))

    supplemental = supplemental_heat_by_room(model)
    radiant_tags = {tag for entries in radiant_output.values() for tag, _ in entries}

    out: list[RoomHeat] = []
    for room in sorted(model.rooms, key=lambda item: item.tag):
        if not room.conditioned:
            continue
        entries = radiant_output.get(room.tag, [])
        stated = [value for _tag, value in entries if value is not None]
        zone = zone_of.get(room.tag)
        others = [(tag, btuh) for tag, btuh in supplemental.get(room.tag, ())
                  if tag not in radiant_tags]
        out.append(RoomHeat(
            room=room.tag, occupancy=room.occupancy, storey=room.storey,
            area_ft2=room.area_m2 * _M2_TO_FT2,
            reached_by=tuple(sorted(reach.get(room.tag, ()))),
            zone_tag=zone.equipment_tag if zone is not None else None,
            zone_margin_btuh=zone.heating_margin_btuh if zone is not None else None,
            radiant_tags=tuple(tag for tag, _ in entries),
            radiant_btuh=sum(stated) if stated else None,
            radiant_undeclared=tuple(tag for tag, value in entries if value is None),
            supplemental_btuh=sum(btuh for _tag, btuh in others),
            supplemental_tags=tuple(tag for tag, _btuh in others)))
    return out


def heating_zones(
    model: ResolvedModel, preferences: Preferences,
) -> tuple[list[HvacZone], frozenset[str]]:
    """Zones from the authored pairings, plus the conditioned rooms no zone claims.

    The load is ``estimate_block_load(rooms=...)`` over the zone's rooms — approximate by
    design (see that function's docstring), and reported with whatever ``unknown_inputs`` it
    names rather than smoothed over.
    """
    from typehaus.energy import estimate_block_load

    units = hvac_units(model)
    design_f = _design_temp_f(model)
    supplemental = supplemental_heat_by_room(model)
    heads_by_outdoor: dict[str, list[HvacUnit]] = {}
    for unit in units:
        if unit.kind in _INDOOR_KINDS and unit.outdoor_ref is not None:
            heads_by_outdoor.setdefault(unit.outdoor_ref, []).append(unit)

    zones: list[HvacZone] = []
    claimed: set[str] = set()
    for unit in units:
        if not _rated(unit):
            continue
        heads = heads_by_outdoor.get(unit.tag, [])
        rooms = set(unit.zone_rooms)
        for head in heads:
            rooms |= set(head.zone_rooms)
        claimed |= rooms
        # Rooms partition across zones, so summing per-room supplemental heat here can never
        # credit the same mat or fireplace to two zones.
        contributions = [entry for room in sorted(rooms) for entry in supplemental.get(room, ())]
        report = estimate_block_load(model, preferences, rooms=frozenset(rooms)) \
            if rooms else None
        capacity = (capacity_at(unit.heating_ratings, design_f)
                    if unit.heating_ratings and design_f is not None else None)
        # The at-design heating capacity is the RATED column where the table states one and
        # the maximum where it does not: a check asks "can this unit carry the load", and
        # the rated point is the one a manufacturer stands behind for continuous duty.
        at_design = None if capacity is None else (
            capacity.rated_btuh if capacity.rated_btuh is not None else capacity.maximum_btuh)
        resistance = _resistance_at_design(unit, design_f)
        if at_design is None and resistance is not None:
            at_design = resistance  # a resistance-only unit IS its rating
        air_ua, ground_btuh, air_delta = _decompose(report, preferences, design_f)
        zones.append(HvacZone(
            name=f"{unit.tag} zone" if not heads else
                 f"{unit.tag} + {'/'.join(head.tag for head in heads)} zone",
            equipment_tag=unit.tag, type_tag=unit.type_ref, rooms=frozenset(rooms),
            indoor_tags=tuple(head.tag for head in heads),
            heating_load_btu_per_hour=(
                report.heating_load_btu_per_hour if report else 0.0),
            heating_capacity_at_design_btuh=at_design,
            cooling_load_btu_per_hour=(
                report.cooling_load_btu_per_hour if report else 0.0),
            cooling_capacity_btuh=unit.cooling_capacity_btuh,
            min_operating_temp_f=unit.min_operating_temp_f,
            supplemental_btuh=sum(btuh for _tag, btuh in contributions),
            supplemental_tags=tuple(tag for tag, _btuh in contributions),
            unknown_inputs=tuple(report.unknown_inputs) if report else
            (f"{unit.tag} zone_rooms (no rooms authored)",),
            latent_btu_per_hour=report.latent_btu_per_hour if report else 0.0,
            cooling_caveats=tuple(report.cooling_caveats) if report else (),
            design_temp_f=design_f,
            air_coupled_ua=air_ua,
            ground_coupled_btuh=ground_btuh,
            heating_ratings=unit.heating_ratings,
            resistance_at_design_btuh=resistance,
            capacity_basis=None if capacity is None else capacity.basis,
            _air_delta_at_design=air_delta,
        ))
    # A head whose ``outdoor_ref`` names no unit in the model claims nothing — only a rated
    # unit and its own heads add to ``claimed`` — so that authoring error surfaces on its own
    # as unclaimed rooms rather than needing a special case here.
    conditioned = {room.tag for room in model.rooms if room.conditioned}
    return zones, frozenset(conditioned - claimed)


def _decompose(report, preferences, design_f: float | None) -> tuple[float, float, float]:
    """``(air-coupled UA, ground-coupled Btu/h, the air ΔT)`` for one zone's heating load.

    Read straight off the report the zone already has — ``LoadComponent.heating_delta_f``
    says which boundary each component was charged against — so this is a dictionary walk,
    not a second envelope pass.

    The air-side terms (infiltration, ventilation) are divided by the same air ΔT to become
    part of the UA, which is exact: both were computed as ``coefficient × ΔT`` with that ΔT.

    **Where a house authors no ground boundary the decomposition must mirror what
    ``estimate_block_load`` ACTUALLY did, not the ideal.** With no ``monthly_normals`` the
    below-grade components fall back to the air ΔT (and say so in ``unknown_inputs``), so
    they belong in the air-coupled UA here — putting them in the constant would make
    ``heating_load_at_outdoor_f(design)`` disagree with the load it is meant to reproduce.
    Keying on the component's own ``heating_delta_f`` rather than on its ``kind`` is what
    makes that automatic.
    """
    if report is None or design_f is None:
        return 0.0, 0.0, 0.0
    air_delta = preferences.interior_setpoint_f - design_f
    if air_delta <= 0:
        return 0.0, report.heating_load_btu_per_hour, 0.0
    air_ua = 0.0
    ground = 0.0
    for component in report.components:
        delta = component.heating_delta_f
        if delta is None:
            continue
        if abs(delta - air_delta) < 1e-9:
            air_ua += component.ua_btu_per_hour_f
        else:
            ground += component.ua_btu_per_hour_f * delta
    air_ua += (report.infiltration_btu_per_hour + report.ventilation_btu_per_hour) / air_delta
    return air_ua, ground, air_delta


def duct_schedule(model: ResolvedModel) -> list[dict[str, object]]:
    """Every resolved duct run: system, routing, developed length, section, intent.

    ``length_ft`` is the resolver's developed length — plan run plus every rise, not just
    the plan projection. A riser is a leg like any other; a plan-only sum would print zero
    for it.

    ``diameter_in`` and the two host refs are what a reader needs to find a run on site: a
    6" semi-rigid radial and a 6x6 rectangular branch are not the same duct, and "which
    cavity is it in" is answered by the bay or the soffit it names.

    ``terminal`` mirrors ``takeoff/mep.py::duct_takeoff``'s column and is derived the same
    way — some ``Register`` names this run — so the schedule a reader checks and the bill an
    estimator prices cannot disagree about which runs terminate at a room.
    """
    registered = {register.duct_ref for register in model.plan.all_elements()
                  if register.element_kind == "Register" and register.duct_ref is not None}
    rows: list[dict[str, object]] = []
    for duct in model.ducts:
        rows.append({
            "tag": duct.tag, "uid": duct.uid, "storey": duct.storey,
            "system": duct.system, "routing": duct.routing,
            "terminal": duct.tag in registered,
            "length_ft": round(duct.length_m * _M_TO_FT, 1),
            "width_in": round(duct.width_m / M_PER_IN, 2),
            "depth_in": round(duct.depth_m / M_PER_IN, 2),
            "diameter_in": (round(duct.diameter_m / M_PER_IN, 2)
                            if duct.diameter_m is not None else None),
            "design_cfm": duct.design_cfm,
            "floor_ref": duct.floor_ref,
            "soffit_ref": duct.soffit_ref,
            "material": duct.material,
            "insulation": duct.insulation,
        })
    return sorted(rows, key=lambda row: str(row["tag"]))


def register_schedule(model: ResolvedModel) -> list[dict[str, object]]:
    """Every authored ``Register``, with the terminal style its type declares."""
    types = {item.tag: item for item in model.plan.library.register_types}
    rows: list[dict[str, object]] = []
    for storey in model.plan.storeys:
        for element in model.plan.storey_elements(storey.tag):
            if element.element_kind != "Register":
                continue
            product = types.get(element.type_ref)
            rows.append({
                "tag": element.tag, "uid": element.uid, "storey": storey.tag,
                "kind": element.kind.value, "room": element.room,
                "duct_ref": element.duct_ref, "type_ref": element.type_ref,
                "type_name": getattr(product, "name", None),
                "ventilation_terminal": bool(
                    getattr(product, "ventilation_terminal", False)),
            })
    return sorted(rows, key=lambda row: str(row["tag"]))


def ventilation_summary(model: ResolvedModel) -> dict[str, object]:
    """The ERV/HRV side: airflow, recovery, and how many terminals it actually reaches."""
    units = [unit for unit in hvac_units(model) if unit.kind in _VENTILATION_KINDS]
    terminals = [row for row in register_schedule(model) if row["ventilation_terminal"]]
    return {
        "units": [unit.as_dict() for unit in units],
        "total_ventilation_cfm": (
            sum(unit.ventilation_cfm for unit in units
                if unit.ventilation_cfm is not None) or None),
        "terminal_count": len(terminals),
        "supply_terminals": sum(1 for row in terminals if row["kind"] == "supply"),
        "stale_terminals": sum(1 for row in terminals
                               if row["kind"] in ("return", "exhaust")),
    }


def hvac_takeoff(model: ResolvedModel, preferences: Preferences) -> dict[str, object]:
    """The whole ``hvac`` block: schedules plus the per-zone load-vs-capacity rows."""
    zones, unclaimed = heating_zones(model, preferences)
    return {
        "equipment": equipment_schedule(model),
        "zones": [zone.as_dict() for zone in zones],
        "unclaimed_conditioned_rooms": sorted(unclaimed),
        "ducts": duct_schedule(model),
        "registers": register_schedule(model),
        "ventilation": ventilation_summary(model),
    }

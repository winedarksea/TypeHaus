"""The catalog record for a piece of structural connection hardware, plus its lookups.

The *type* lives in the engine and the *items* live in ``library/hardware/`` — the same
split as ``Material`` / ``library/materials/``. A take-off derives a role ("this joint
needs a sloped joist hanger, 10 in of screw"); the catalog is what turns that role into a
manufacturer part number with a citable source.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# The ROLE_* keys live in ``roles``; every caller still imports them from here.
from typehaus.hardware.roles import *  # noqa: F403
from typehaus.hardware.roles import ROLE_POCKET_DOOR_FRAME_KIT


@dataclass(frozen=True)
class AllowableLoads:
    """One connector's published ASD allowable loads, as a vector and with its source.

    **Every field is ``None`` when no public number exists, and that is the point.** A
    connector catalog that carried a scalar "capacity" would have to invent something for the
    parts whose reports do not publish one, and an invented allowable is the single most
    dangerous number a model like this could hold — it looks exactly like a real one in a
    calculation. Absence is a fact here, recorded deliberately, with ``citation`` saying which
    document was read and came back empty.

    It is a **vector** because a connector fails in more than one direction and the numbers
    are wildly different: an H2.5A is published at 700 lbf uplift and 110 lbf lateral, and a
    check that compared a lateral demand against "the H2.5A's 700 lb capacity" would pass a
    joint that is over six times overloaded. ESR-2613 footnote 2 makes the coupling explicit
    (a unity equation across all three), which is only expressible against separate fields.

    ``citation`` and ``fasteners`` are the two invariants ``tests/test_hardware_allowables.py``
    enforces on every record. Without the report, a number cannot be re-checked; without the
    fastener schedule it is not even a number *about* anything, because every one of these
    values is measured through a specific nail, screw or bolt count and drops — often by
    half — when a different one is used.
    """

    #: Tension away from the supporting member, lbf. Simpson publish these already increased
    #: for wind/earthquake (C_D = 1.6) with no further increase allowed.
    uplift_lb: float | None = None
    #: Lateral, F1 direction (as defined by the part's own report figure — for most of these
    #: parallel to the supporting plate or along the brace).
    lateral_f1_lb: float | None = None
    #: F1 at a 30° or 60° brace, where the report tabulates by brace angle and permits
    #: interpolation to the 45° ``lateral_f1_lb`` (KBS1Z: ER-280 Table 7 fn. 3).
    lateral_f1_30_60_lb: float | None = None
    #: Lateral, F2 direction (perpendicular to F1 in the same figure).
    lateral_f2_lb: float | None = None
    #: Bearing/compression, lbf. Published at a *lower* duration factor than uplift, and
    #: Simpson state it may not be increased for short-term loading — so it is not comparable
    #: to the uplift number without saying which C_D each carries, hence the field below.
    download_lb: float | None = None
    #: Rigging working load limit, lbf: in-line tension through the part's two eyes. The
    #: design factor it carries is stated in ``citation``.
    wll_lb: float | None = None
    #: The NDS load-duration factor the tabulated values already include. ``None`` where the
    #: record's values are all ``None`` or where the report tabulates several.
    load_duration_factor: float | None = None
    #: The lowest C_D column the report tabulates the same values at, where it publishes a
    #: range (ESR-3096 Table 5: C_D 1.0 to 1.6). A sustained load reads from here, not 1.6.
    lowest_load_duration_factor: float | None = None
    #: The lumber the values are published against, as the report states it. **Not
    #: decoration**: Simpson tabulate against specific gravity, and a value published for
    #: DF/SP (SG 0.50) does not apply to the SPF (SG 0.42) this house frames in. Where the
    #: report gives both, the SPF/HF column is the one recorded, because that is what is
    #: built here.
    species: str | None = None
    #: The exact fastener schedule the values are measured through, verbatim from the report.
    fasteners: str = ""
    #: The document, table and revision date read. Required, always.
    citation: str = ""

    @property
    def is_empty(self) -> bool:
        """True when the report was read and published no usable number for this part."""
        return all(v is None for v in (self.uplift_lb, self.lateral_f1_lb,
                                       self.lateral_f2_lb, self.download_lb, self.wll_lb))


@dataclass(frozen=True)
class FastenerSpacing:
    """A screw's published placement minima, inches, for load perpendicular to the grain.

    ``row_spacing`` is between STAGGERED rows (adjacent rows offset by half the in-row
    spacing), ``in_line_row_spacing`` between rows that are not; ``loaded_edge`` is the edge
    the screw bears toward in each member. ``min_embedded_thread`` is the report's own floor.
    """

    end_distance: float
    in_row_spacing: float
    row_spacing: float
    in_line_row_spacing: float
    loaded_edge: float
    unloaded_edge: float
    min_embedded_thread: float
    source: str


@dataclass(frozen=True)
class StructuralHardware:
    """One catalog connector/fastener: a stable tag, a role, a part number, and a source."""

    tag: str                      # stable catalog id, e.g. "simpson-masa-mudsill-anchor"
    name: str                     # human name for the BOM line
    role: str                     # one of the ROLE_* keys (``roles``)
    manufacturer: str
    model: str                    # published part/family designation, e.g. "MASA"
    source: str                   # the manufacturer system/product this record describes
    unit: str = "each"            # purchase unit ("each" | "coil")
    # Length-selected fasteners: available lengths mapped to their published part numbers.
    part_number_by_length_in: dict = field(default_factory=dict)
    #: Published THREAD length per overall length, where the report states one. Empty means
    #: nobody has read it, never "fully threaded". It is a different number from the length
    #: and the one the clamped-stack rule turns on: thread standing inside the members being
    #: clamped jacks them apart instead of drawing them together, so a screw is chosen on
    #: ``length - thread >= the stack`` and not on length alone.
    thread_length_in_by_length_in: dict = field(default_factory=dict)
    # Nominal member sizes this part is published for (empty = size-independent).
    fits_nominal: tuple = ()
    #: Which wood-contact condition this coating is for — :data:`EXPOSURE_DRY` or
    #: :data:`EXPOSURE_TREATED`. ``None`` is the default and means "this part answers for
    #: every exposure", which is the honest state for a role served by one product: nobody
    #: has yet had to decide, and pretending otherwise would put a claim on ~40 records that
    #: no catalog page was read for. Set it only where a role holds two coatings of one part
    #: and ``hardware_for_role`` has to choose between them.
    exposure: str | None = None
    # A part that does not fasten to the building on its own, but mounts on another
    # catalogued part — one of those is needed per unit of this one. Without it a BOM reads
    # as orderable while being short every bracket: the CanDuit ring holds the pipe, but it
    # is the S-5! clamp under it that holds the ring to the roof.
    requires_role: str | None = None
    #: The part's published ASD allowables, when a report has been pulled and transcribed for
    #: it. ``None`` means nobody has looked yet — distinct from an ``AllowableLoads`` whose
    #: every value is ``None``, which means somebody looked and the report published nothing.
    #: **Deliberately absent from ``hardware_row``**: a BOM line orders a part, and putting a
    #: capacity on it would invite reading the bill as a connection schedule.
    allowable: AllowableLoads | None = None
    #: How far this part holds the member it carries CLEAR of what it is fastened to, in
    #: inches — a post base's standoff, measured from the bearing surface (the pour, the
    #: slab) to the underside of the wood, so it includes the part's own base-plate steel.
    #:
    #: **It is a length of the building, not a detail of the part.** A 6x6 on an ABU66 is
    #: 1 3/16" shorter than the clear distance between the pour and the beam over it, and
    #: that is the length IRC Table R507.4 caps, the length a mill cuts, and the length the
    #: take-off bills. ``resolve/envelope.py::_resolve_post`` reads it off the POST_BASE
    #: connector a plan authors on the post and starts the wood there.
    #:
    #: ``None`` means nobody has measured it, and the post then runs to its bearing surface
    #: exactly as it did before this field existed — the same "nobody looked" the
    #: ``allowable`` field above means, and for the same reason: a default of 0.0 would be a
    #: claim that the part has no standoff, which for a standoff post base is false.
    bearing_standoff_in: float | None = None
    #: The steel this part puts BETWEEN the member it caps and the member above, in inches —
    #: a column cap's seat. The post top lands one of these below the beam soffit.
    #: ``None`` means unmeasured, exactly as ``bearing_standoff_in``.
    seat_thickness_in: float | None = None
    #: The part is CAST IN and its published uplift is measured through the concrete (a
    #: CBSTQ's cracked/uncracked columns), so it buys no separate anchor bolt and no ACI
    #: Ch. 17 row stands in for its anchorage. ``False`` for a stirrup on a bolt (the ABU).
    anchorage_in_rating: bool = False
    #: Shipping weight, lb, where a load path counts the part's own weight. ``None``: unread.
    weight_lb: float | None = None
    #: A pocket frame's published rough-opening WIDTH per door width, inches. Empty means the
    #: kit follows the 2W + 1" every commodity series publishes (``tables.pocket_run``).
    rough_opening_in_by_length_in: dict = field(default_factory=dict)
    #: Published spacing, end and edge minima (``FastenerSpacing``); ``None``: unread.
    #: ``spacing`` is the SG < 0.50 column, ``spacing_dense`` the SG >= 0.50 one.
    spacing: FastenerSpacing | None = None
    spacing_dense: FastenerSpacing | None = None
    #: A pocket frame's published RO height over the leaf, inches, from the FINISHED floor.
    #: ``None``: the kit publishes none and the generic door equation frames it.
    rough_opening_head_over_leaf_in: float | None = None
    #: A pocket frame whose track screws up into wood gets a flat 2x6 nailer over the header
    #: (the commodity kits). ``False``: the kit's own steel header carries the track (Eclisse).
    pocket_track_nailer: bool = True
    #: A fastener's coating: ``"ss304"``, ``"ss316"``, ``"hdg"``, ``"zmax"``, ``"g90"``,
    #: ``"mech_galv"`` or ``"bright"`` (uncoated, dry wood only).
    #: Read by the connector-schedule lint (never mix stainless and zinc in one joint).
    #: ``None``: not a fastener, or not recorded.
    finish: str | None = None
    #: A bolted angle's holes (HL D1-D3, decision #147): diameter, bolts per leg, and the
    #: hole centre's distance off the heel. ``None``: not a bolted part.
    bolt_diameter_in: float | None = None
    bolts_per_leg: int | None = None
    bolt_from_heel_in: float | None = None

    @property
    def available_lengths_in(self) -> tuple:
        return tuple(sorted(self.part_number_by_length_in))


def structural_hardware_catalog() -> tuple:
    """The shared ``library/hardware/`` catalog.

    Imported lazily: the engine package must import without the repo-root ``library``
    package on ``sys.path`` (the plan loader puts it there when a house is loaded).
    """
    from typehaus.library.hardware import STRUCTURAL_HARDWARE

    return STRUCTURAL_HARDWARE


def hardware_capacity_records() -> tuple:
    """Parts ``library/hardware/`` holds an allowable for but does not bill.

    Kept out of ``structural_hardware_catalog`` on purpose: everything in that tuple is
    orderable and selectable by role, and a capacity record is neither. Only
    ``allowable_for_model`` reads this.
    """
    from typehaus.library.hardware import CAPACITY_ONLY_RECORDS

    return CAPACITY_ONLY_RECORDS


#: The two answers :data:`StructuralHardware.exposure` gives, and the only two a caller may
#: ask for. ``"dry"`` is plain G90 zinc territory: interior framing, and exterior framing
#: that is untreated and stays out of the weather. ``"treated"`` is contact with
#: preservative-treated wood, where IRC R317.3.1 requires hot-dip galvanized (G185 / ZMAX),
#: stainless, silicon bronze or copper — the copper in modern preservatives eats G90.
#:
#: **It is deliberately a wood-contact question and not an indoor/outdoor one.** A roof truss
#: heel on a dry SPF plate is "dry" even though the wall under it faces the weather, and a
#: KDAT deck joist is "treated" even where it is under cover. The coating is decided by what
#: the steel touches, which is the thing the code and the manufacturer both say.
EXPOSURE_DRY = "dry"
EXPOSURE_TREATED = "treated"


def hardware_for_role(role: str, *, exposure: str | None = None) -> StructuralHardware:
    """The single catalog item serving ``role``, or raise — a BOM line without a part is
    not a bill of materials, so an unserved role is a catalog bug, not a silent blank.

    ``exposure`` is the second key, and it exists because one role really can be served by
    two products that are the same part in two coatings: an H2.5A and an H2.5AZ are one tie,
    one published allowable and one price band apart, and a house that lands ties on both
    SPF plates and treated glulam has to buy both. Where a role holds one product the
    argument changes nothing (that product answers for every exposure); where it holds more
    than one, omitting it is a LookupError rather than a silent pick of the cheaper part.
    """
    items = [item for item in structural_hardware_catalog() if item.role == role]
    if len(items) > 1 and exposure is not None:
        items = [item for item in items if item.exposure == exposure]
    if len(items) != 1:
        raise LookupError(f"expected exactly one library hardware item for role {role!r}"
                          + (f" at exposure {exposure!r}" if exposure is not None else "")
                          + f", found {[item.tag for item in items]}")
    return items[0]


def sized_hanger_model(item: StructuralHardware, profile: str) -> str:
    """The orderable size of a face-mount hanger family for one member: LUS + 2x8 -> LUS28,
    and the ZMAX record's trailing ``Z`` kept (LUS28Z). A profile that is not a single
    dimensional-lumber ply (an I-joist, a 3-ply) stays the family name — no guessed size.

    A 2x12 takes the 2x10 part: Simpson C-C-2017 p. 127 lists LUS210 under the 2x12 joist
    size (H 7-13/16", over the 60% of depth a face-mount wants) and there is no LUS212."""
    match = re.fullmatch(r"2x(4|6|8|10|12)", profile.split(":")[0].strip())
    if match is None:
        return item.model
    size = "10" if match.group(1) == "12" else match.group(1)
    family, coated = item.model.removesuffix("Z"), item.model.endswith("Z")
    return f"{family}2{size}{'Z' if coated else ''}"


def hardware_for_role_and_nominal(role: str, nominal: str, *,
                                  exposure: str | None = None) -> StructuralHardware:
    """The catalog item serving ``role`` for a nominal member size (e.g. a 2x6 stud), keyed on
    ``exposure`` the way :func:`hardware_for_role` is where one size comes in two coatings."""
    items = [item for item in structural_hardware_catalog()
             if item.role == role and nominal in item.fits_nominal]
    if len(items) > 1 and exposure is not None:
        items = [item for item in items if item.exposure == exposure]
    if len(items) != 1:
        raise LookupError(f"expected exactly one library hardware item for role {role!r} at "
                          f"{nominal}, found {[item.tag for item in items]}")
    return items[0]


def pocket_frame_kit(family: str | None, width_in: int, deep_wall: bool) -> StructuralHardware:
    """The frame kit a pocket door of ``width_in`` is bought with.

    ``family`` is ``DoorType.pocket_frame``. ``None`` is the commodity ladder, where only the
    36" leaf has a 2x6 kit (Johnson 1560); a named family publishes both depths at every
    width, so its nominal is ``<family>-<width>[-2x6]``.
    """
    base = f"{family}-{width_in}" if family else str(width_in)
    deep = deep_wall and (family is not None or width_in == 36)
    return hardware_for_role_and_nominal(ROLE_POCKET_DOOR_FRAME_KIT,
                                         f"{base}-2x6" if deep else base)


def hardware_by_model(model: str) -> StructuralHardware | None:
    """Look a catalog item up by the part designation a plan authored (``Connector.size``).

    A plan may author a specific size within a family ("LUS210" of the LUS family), so an
    exact match wins and a family-prefix match is the fallback.

    **The exact pass reads the capacity-only records too, and the prefix pass must not.**
    A capacity-only part (ABU66SS, H2.5ASS, APVKB45-6) is still a real part with a real name,
    and this is what the BOM prints. Without the first pass reaching them,
    ``"ABU66SS".startswith("ABU66")`` wins and a line reading "ABU66SS" is captioned "ABU66
    standoff post base" — the exact confusion those records exist to prevent. The prefix pass
    deliberately still does NOT see them: a family fallback is a guess, and a guess onto a
    part that was catalogued separately *because* it is not the family is the wrong one.

    **Note what is no longer the reason.** Two of those three carried ``allowable=None``
    because their published numbers could not be sourced; since 2026-09-11 the ABU66SS and the
    H2.5ASS both carry their carbon twin's values, granted by Simpson letter L-F-SSNAILS. The
    caption argument above is what keeps them here, and it never depended on the capacity.
    """
    catalog = structural_hardware_catalog()
    exact = next((item for item in (*catalog, *hardware_capacity_records())
                  if item.model == model), None)
    if exact is not None:
        return exact
    family = [item for item in catalog if model.startswith(item.model)]
    return max(family, key=lambda item: len(item.model)) if family else None


def allowable_for_model(model: str, *, role: str | None = None) -> AllowableLoads | None:
    """The published allowables for an EXACT part designation, or ``None``.

    ``role`` disambiguates a part catalogued for more than one joint. The KBS1Z is the case:
    ER-280 Table 7 tabulates it by *connection type*, and a beam-to-post cap and a knee brace
    read different rows of the same table — 1,000 lbf uplift for one, 540 lbf F1 for the
    other. Separate catalog roles carry each connection type, so a lookup by model gets whichever
    is listed first, which is a coin flip dressed as an answer. Pass the role of the joint
    being checked and the right row comes back; omit it and the first record wins, which is
    correct for every part catalogued once.

    **Exact, and that is the whole reason this is not ``hardware_by_model(...).allowable``.**
    ``hardware_by_model`` falls back to a family-prefix match so a plan may author "LUS210"
    against a catalogued "LUS" — correct for finding a product, and catastrophic here, because
    ``"ABU66SS".startswith("ABU66")`` is true and the stainless base would silently inherit the
    galvanised ABU66's ESR-1622 numbers. It must not: ESR-1622 §3.2.1 evaluates ASTM A653
    galvanised steel and its Table 2 lists no stainless model at all. A near-miss on a part
    number is exactly how an unevaluated connector acquires a capacity.
    """
    records = [item for item in (*structural_hardware_catalog(), *hardware_capacity_records())
               if item.model == model]
    if role is not None:
        for item in records:
            if item.role == role:
                return item.allowable
    return records[0].allowable if records else None


def screw_for_required_length(role: str, required_length_in: float) -> tuple:
    """Shortest catalogued screw in ``role`` that still reaches ``required_length_in``.

    Returns ``(item, length_in, part_number)``. Raises when no catalogued length is long
    enough — an under-length structural screw is a real failure, not a rounding decision.
    """
    candidates = [(length_in, item)
                  for item in structural_hardware_catalog() if item.role == role
                  for length_in in item.available_lengths_in
                  if length_in + 1e-9 >= required_length_in]
    if not candidates:
        raise LookupError(f"no catalogued {role} reaches {required_length_in:.2f} in")
    length_in, item = min(candidates, key=lambda pair: pair[0])
    return item, length_in, item.part_number_by_length_in[length_in]


def screw_by_part_number(part_number: str) -> tuple:
    """The catalogued screw a house AUTHORED, by part number.

    Returns ``(item, length_in, thread_in)``; ``thread_in`` is ``None`` where the record's
    report was not read for one. Raises when the part is not catalogued — a BOM line naming
    a screw nobody has a source for is the failure this refuses, not a row to guess at.

    Its own function rather than a branch of :func:`screw_for_required_length`: that one
    *derives* a length from a stack and is the right answer when nothing is authored. This
    one is the case where an engineering record already picked the screw, and the takeoff's
    job is to bill exactly that and not re-derive a different one.
    """
    for item in structural_hardware_catalog():
        for length_in, catalogued in item.part_number_by_length_in.items():
            if catalogued == part_number:
                return item, length_in, item.thread_length_in_by_length_in.get(length_in)
    raise LookupError(f"no catalogued structural screw has part number {part_number!r}")

"""The catalog record for a piece of structural connection hardware, plus its lookups.

The *type* lives in the engine and the *items* live in ``library/hardware.py`` — the same
split as ``Material`` / ``library/materials.py``. A take-off derives a role ("this joint
needs a sloped joist hanger, 10 in of screw"); the catalog is what turns that role into a
manufacturer part number with a citable source.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# Stable role keys the take-off selects hardware by. A role is a *condition* in the resolved
# model, never a product: several products may serve one role, and the catalog decides.
ROLE_EXTERIOR_INSULATION_SCREW = "exterior_insulation_screw"
ROLE_SLOPED_JOIST_HANGER = "sloped_joist_hanger"
# The strap that carries a rafter's tension THROUGH the ridge to its opposite number.
# Its own role, not a variant of the sloped hanger: the hanger holds one rafter up in
# the beam's depth and does nothing across the peak, which is why Weyerhaeuser's H5S
# ridge detail adds the strap outright above a 3:12 slope and APA D710 10c calls for it
# from 1/4:12. One per opposing PAIR, so it can never be derived per hung end.
ROLE_RIDGE_TIE_STRAP = "ridge_tie_strap"
ROLE_FACE_MOUNT_JOIST_HANGER = "face_mount_joist_hanger"
ROLE_CONCRETE_FACE_MOUNT_HANGER = "concrete_face_mount_hanger"
ROLE_KNEE_BRACE = "knee_brace"
ROLE_BRACE_THROUGH_BOLT = "brace_through_bolt"
# The bolt a FACE-LAPPED brace foot takes, and its own role for one dimensional reason:
# a lapped foot is bolted through the brace AND the whole post behind it, so the wood it
# crosses is the brace thickness plus the post's full section — 7" for a 2x on a 6x6 —
# where a butting end's bolt only ever crosses the strap and the brace. The 6 in bolt
# ROLE_BRACE_THROUGH_BOLT carries does not reach, and a BOM that lists it for both joints
# is short by the only dimension that decides whether the part fits. See
# ``model/structure.KneeBrace.foot_lap`` and ``takeoff/anchors.brace_bolt_rows``.
ROLE_LAPPED_BRACE_BOLT = "lapped_brace_bolt"
ROLE_MUDSILL_ANCHOR = "mudsill_anchor"
ROLE_EMBEDDED_STRAP_HOLDOWN = "embedded_strap_holdown"
ROLE_STUD_PLATE_TIE = "stud_plate_tie"
ROLE_COIL_STRAP = "coil_strap"
ROLE_POST_BASE = "post_base"
# The cast-in bolt that fastens a post base to the concrete under it. Its own role, and not
# an attribute of the base: an ABU ships as a stirrup with a hole in it and Simpson's tables
# say "anchor bolt by others", so a BOM listing bases and no bolts reads as orderable while
# being short every anchor. Deliberately NOT expressed as ``StructuralHardware.requires_role``
# — that field is a flat property of the *part*, and whether a base needs a cast-in bolt is a
# property of the *joint*: two of catlin's ten ABU66SS land on porch decking, where the base
# is through-bolted into framing and the fixings are inside the framing rate. See
# ``takeoff/uplift.py::post_base_anchor_rows``.
ROLE_POST_BASE_ANCHOR = "post_base_anchor"
#: The one fastener in this catalog that deliberately pierces a waterproof plane: the
#: through-deck anchor holding a mechanical stand down to blocking under a dry-below
#: deck. Its own role rather than a ``post_base`` variant, because what it is selected
#: for is the SEAL and the alloy, not the post section — see library/hardware.py.
ROLE_DECK_EQUIPMENT_ANCHOR = "deck_equipment_anchor"
ROLE_HURRICANE_TIE = "hurricane_tie"
# A wood member held down to CONCRETE or masonry by a gusset angle — one leg screwed into
# the wood, the other anchored with a concrete screw. Its own role and not a second product
# on ROLE_HURRICANE_TIE, which ``hardware_for_role`` would refuse anyway: an H-tie is a
# wood-to-wood part whose published values are nails into lumber on BOTH legs, so at a beam
# landing on a cast column top there is nothing for the second leg to bite. The deciding
# question is the same one that splits the seam clamps above — HOW THE PART REACHES THE
# BUILDING — and a screw into concrete is not a nail into a plate.
ROLE_MASONRY_GUSSET_ANGLE = "masonry_gusset_angle"
# The cap over a post that a beam lands ON (rather than continues past). Its own role, not
# ROLE_BEAM_HOLD_DOWN: the KBS strap ties a beam DOWN to a post whose sides it can reach,
# while a cap seats the beam and takes uplift in one part. Both serve a post/beam joint and
# ``hardware_for_role`` holds exactly one product per role, so they cannot share.
ROLE_POST_CAP = "post_cap"
# Plate-to-plate / plate-to-rim lateral tie. The SP tie and the H tie above both resist
# UPLIFT at a stud or a rafter; this one resists the horizontal shear that walks a plate off
# its band, which is a different joint with a different part and no size ladder.
ROLE_LATERAL_TIE_PLATE = "lateral_tie_plate"
# The cast-in bolt anchoring a sill plate between the mudsill anchors. Distinct from
# ROLE_MUDSILL_ANCHOR: a MASA is a formed strap set in wet concrete and a bolt is a threaded
# rod with a plate washer, priced and installed differently, and the foundation schedule has
# to name a diameter and an embedment the strap does not have.
ROLE_SILL_ANCHOR_BOLT = "sill_anchor_bolt"
ROLE_STANDING_SEAM_CLAMP = "standing_seam_clamp"
# The two profile-specific seam clamps. Their own roles, and keyed on the PANEL PROFILE
# rather than on what they are for, because the profile is what decides the part: an S-5-S
# will not close on a nail-strip bulb and an S-5-N will not close on a snap-lock leg. A house
# clad in more than one profile therefore needs more than one clamp on the shelf, and
# ``hardware_for_role`` holds exactly one product per role — which is the same reason
# ROLE_PV_SEAM_CLAMP exists below.
ROLE_SNAP_LOCK_SEAM_CLAMP = "snap_lock_seam_clamp"
ROLE_NAIL_STRIP_SEAM_CLAMP = "nail_strip_seam_clamp"
# The PV mounting kit is its own role: hardware_for_role demands one product per role,
# and the plain S-5! clamp (vent riser, exterior boxes) must keep serving its own.
ROLE_PV_SEAM_CLAMP = "pv_seam_clamp"
# The ring that secures a round pipe/conduit/leader to a seam clamp. Its own role for the
# same reason: it is a separately purchased part, in fourteen diameters, and a plan that
# says "clamp" without saying which ring is not orderable.
ROLE_PIPE_CLAMP = "pipe_clamp"
# The strap that holds that same round pipe against an *exposed-fastener* panel, by screwing
# through it into the framing behind. Its own role rather than a second product on
# ROLE_PIPE_CLAMP for two reasons: ``hardware_for_role`` holds exactly one product per role,
# and — like the seam-clamp pair above — the deciding question is HOW THE PART REACHES THE
# BUILDING. A ring that mounts on a seam and a strap that penetrates a panel are different
# products for different claddings, and neither one can be substituted for the other on site.
ROLE_THROUGH_PANEL_PIPE_STRAP = "through_panel_pipe_strap"
# A beam strapped down to the post it seats on. Its own role, not ROLE_KNEE_BRACE: a role
# holds exactly one catalogued item (``hardware_for_role`` raises otherwise), and the KBS
# strap and the APVKB knee brace are different products for different joints even though
# the KBS family is marketed for both.
ROLE_BEAM_HOLD_DOWN = "beam_hold_down"
# The gasketed stainless screw that holds a multiwall glazing sheet down to its framing.
ROLE_GLAZING_PANEL_FASTENER = "glazing_panel_fastener"
# The gasketed screw that fixes an exposed-fastener metal wall/roof panel through its face
# into the supports behind. Distinct from the glazing fastener above — that one is sized to
# a sheet that must be free to move in an oversize hole, this one clamps the panel down —
# and it exists at all only because ``Material.exposed_fastener`` panels bill their fixings
# as a counted part instead of inside the $/SF cladding rate.
ROLE_EXPOSED_FASTENER_PANEL_SCREW = "exposed_fastener_panel_screw"
# The frame kit a pocket door slides in: split studs, an aluminium head track, hangers and
# the leaf's guides, bought as one boxed unit per door and selected by door width. It is the
# first door hardware in this catalog — before it, a door's ironmongery could only be carried
# as a ``finish-door-*`` lump-sum allowance, never as a counted part. Width-selected via
# ``fits_nominal``, because the commodity series and the heavy-duty series are different
# products with different tracks and different weight ratings, not two rows of one ladder.
ROLE_POCKET_DOOR_FRAME_KIT = "pocket_door_frame_kit"
# Snow retention on a standing-seam slope: the rail/fence assembly that holds a snow pack on
# the roof instead of letting it release onto whatever is below. Like the CanDuit ring it
# does not reach the panel itself — it mounts on seam clamps (``requires_role``).
ROLE_SNOW_RETENTION = "snow_retention"


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
    #: Lateral, F2 direction (perpendicular to F1 in the same figure).
    lateral_f2_lb: float | None = None
    #: Bearing/compression, lbf. Published at a *lower* duration factor than uplift, and
    #: Simpson state it may not be increased for short-term loading — so it is not comparable
    #: to the uplift number without saying which C_D each carries, hence the field below.
    download_lb: float | None = None
    #: The NDS load-duration factor the tabulated values already include. ``None`` where the
    #: record's values are all ``None`` or where the report tabulates several.
    load_duration_factor: float | None = None
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
                                       self.lateral_f2_lb, self.download_lb))


@dataclass(frozen=True)
class StructuralHardware:
    """One catalog connector/fastener: a stable tag, a role, a part number, and a source."""

    tag: str                      # stable catalog id, e.g. "simpson-masa-mudsill-anchor"
    name: str                     # human name for the BOM line
    role: str                     # one of the ROLE_* keys above
    manufacturer: str
    model: str                    # published part/family designation, e.g. "MASA"
    source: str                   # the manufacturer system/product this record describes
    unit: str = "each"            # purchase unit ("each" | "coil")
    # Length-selected fasteners: available lengths mapped to their published part numbers.
    part_number_by_length_in: dict = field(default_factory=dict)
    # Nominal member sizes this part is published for (empty = size-independent).
    fits_nominal: tuple = ()
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

    @property
    def available_lengths_in(self) -> tuple:
        return tuple(sorted(self.part_number_by_length_in))


def structural_hardware_catalog() -> tuple:
    """The shared ``library/hardware.py`` catalog.

    Imported lazily: the engine package must import without the repo-root ``library``
    package on ``sys.path`` (the plan loader puts it there when a house is loaded).
    """
    from library.hardware import STRUCTURAL_HARDWARE

    return STRUCTURAL_HARDWARE


def hardware_capacity_records() -> tuple:
    """Parts ``library/hardware.py`` holds an allowable for but does not bill.

    Kept out of ``structural_hardware_catalog`` on purpose: everything in that tuple is
    orderable and selectable by role, and a capacity record is neither. Only
    ``allowable_for_model`` reads this.
    """
    from library.hardware import CAPACITY_ONLY_RECORDS

    return CAPACITY_ONLY_RECORDS


def hardware_for_role(role: str) -> StructuralHardware:
    """The single catalog item serving ``role``, or raise — a BOM line without a part is
    not a bill of materials, so an unserved role is a catalog bug, not a silent blank."""
    items = [item for item in structural_hardware_catalog() if item.role == role]
    if len(items) != 1:
        raise LookupError(f"expected exactly one library hardware item for role {role!r}, "
                          f"found {[item.tag for item in items]}")
    return items[0]


def hardware_for_role_and_nominal(role: str, nominal: str) -> StructuralHardware:
    """The catalog item serving ``role`` for a nominal member size (e.g. a 2x6 stud)."""
    items = [item for item in structural_hardware_catalog()
             if item.role == role and nominal in item.fits_nominal]
    if len(items) != 1:
        raise LookupError(f"expected exactly one library hardware item for role {role!r} at "
                          f"{nominal}, found {[item.tag for item in items]}")
    return items[0]


def hardware_by_model(model: str) -> StructuralHardware | None:
    """Look a catalog item up by the part designation a plan authored (``Connector.size``).

    A plan may author a specific size within a family ("LUS210" of the LUS family), so an
    exact match wins and a family-prefix match is the fallback.
    """
    catalog = structural_hardware_catalog()
    exact = next((item for item in catalog if item.model == model), None)
    if exact is not None:
        return exact
    family = [item for item in catalog if model.startswith(item.model)]
    return max(family, key=lambda item: len(item.model)) if family else None


def allowable_for_model(model: str, *, role: str | None = None) -> AllowableLoads | None:
    """The published allowables for an EXACT part designation, or ``None``.

    ``role`` disambiguates a part catalogued for more than one joint. The KBS1Z is the case:
    ER-280 Table 7 tabulates it by *connection type*, and a beam-to-post cap and a knee brace
    read different rows of the same table — 1,000 lbf uplift for one, 540 lbf F1 for the
    other. Two catalog records carry the two rows, so a lookup by model alone gets whichever
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


def hardware_row(item: StructuralHardware | None, *, scope: str, count: int, basis: str,
                 part_number: str | None = None, size: str | None = None,
                 length_ft: float | None = None, coils: int | None = None,
                 by_storey: dict | None = None) -> dict:
    """One BOM line: what it is, how many, and the rule that produced the number.

    ``basis`` is not decoration — a hardware count is only auditable if the line carries
    the spacing/condition it came from, so every row states it.
    """
    return {
        "scope": scope,
        "role": item.role if item else None,
        "hardware_tag": item.tag if item else None,
        "description": item.name if item else scope,
        "manufacturer": item.manufacturer if item else None,
        "part_number": part_number if part_number is not None else (item.model if item else None),
        "size": size,
        "unit": item.unit if item else "each",
        "count": count,
        "length_ft": round(length_ft, 1) if length_ft is not None else None,
        "coils": coils,
        "basis": basis,
        "source": item.source if item else None,
        "by_storey": by_storey,
    }


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

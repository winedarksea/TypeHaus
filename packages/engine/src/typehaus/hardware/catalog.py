"""The catalog record for a piece of structural connection hardware, plus its lookups.

The *type* lives in the engine and the *items* live in ``library/hardware.py`` — the same
split as ``Material`` / ``library/materials.py``. A take-off derives a role ("this joint
needs a sloped joist hanger, 10 in of screw"); the catalog is what turns that role into a
manufacturer part number with a citable source.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# Stable role keys the take-off selects hardware by. A role is a *condition* in the resolved
# model, never a product: several products may serve one role, and the catalog decides.
ROLE_EXTERIOR_INSULATION_SCREW = "exterior_insulation_screw"
# The ONE screw per crossing of a block-standoff girt wall. Its own role, deliberately kept
# off the SDWS/SDWH ladder above: that ladder is length-selected and a girt screw is chosen
# on THREAD length, which the ladder cannot see. A shared role would let
# ``screw_for_required_length`` hand back an 8" SDWS whose 3" thread stands in the clamped
# stack and jacks it apart — the exact failure ``engineering/girt_screw.py`` grades.
ROLE_GIRT_STANDOFF_SCREW = "girt_standoff_screw"
# The screw at an interior partition's top plate, spanning the deflection gap to the
# structure over it. Its own role for the deciding reason, which is the exact INVERSE of
# every other screw in this catalog: **this one must not clamp.** An SDPW carries a polymer
# sleeve that holds the plate a set distance clear of the joist or rafter above, so the
# deck can deflect onto nothing while the wall is still braced laterally. Put it on a shared
# screw role and ``screw_for_required_length`` would grade it through the clamped-stack rule
# that exists to stop a girt jacking off its blocks — a rule whose whole premise is that
# the members are meant to be drawn together, which here they are not.
ROLE_PARTITION_DEFLECTION_SCREW = "partition_deflection_screw"
# The tie from a GABLE-END wall's top plate to the roof framing above it. Its own role, not
# a variant of ROLE_HURRICANE_TIE, for one reason that decides the part: an eave tie resists
# UPLIFT on a rafter that bears on the plate, while a gable-end tie resists the wall's
# OUT-OF-PLANE reaction — a lateral force, in the direction Table 1 calls F2 — at a plate no
# rafter bears on at all. The two are graded against different columns of the same table, and
# a shared role would let ``hardware_for_role`` hand back a tie chosen on its uplift number
# for a joint whose governing load is lateral. The gable end is the classic wind failure in
# a house that has everything else tied, which is exactly why it gets its own leg.
ROLE_GABLE_END_TIE = "gable_end_tie"
# A trussed gable end instead: the gable-end truss is designed for its own out-of-plane load,
# so the joint only holds the truss down on the plate. Its own role so the stud tie is not it.
ROLE_GABLE_TRUSS_ANCHOR = "gable_truss_anchor"
ROLE_SLOPED_JOIST_HANGER = "sloped_joist_hanger"
# The strap that carries a rafter's tension THROUGH the ridge to its opposite number.
# Its own role, not a variant of the sloped hanger: the hanger holds one rafter up in
# the beam's depth and does nothing across the peak, which is why Weyerhaeuser's H5S
# ridge detail adds the strap outright above a 3:12 slope and APA D710 10c calls for it
# from 1/4:12. One per opposing PAIR, so it can never be derived per hung end.
ROLE_RIDGE_TIE_STRAP = "ridge_tie_strap"
ROLE_FACE_MOUNT_JOIST_HANGER = "face_mount_joist_hanger"
# An I-joist into a flush carrier's face: sized by FLANGE width and depth, never by a nominal.
# Never derived on its own — a house authors the part for the joint (a ``Connector`` naming
# the beam and the FloorSystem), and every hung end of that pair takes it.
ROLE_IJOIST_FACE_MOUNT_HANGER = "ijoist_face_mount_hanger"
# A level open-web floor truss into a flush carrier's face: sized for a flat 2x4 (nominal
# "4x2") bottom chord, never derived — same per-joint authoring as the I-joist role above.
ROLE_FLOOR_TRUSS_HANGER = "floor_truss_hanger"
# A multi-ply LVL floor-opening header into its trimmer pack: sized by the pack's width and
# depth (``fits_nominal`` names the profile), derived wherever the header hangs.
ROLE_SCL_FACE_MOUNT_HANGER = "scl_face_mount_hanger"
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
#: The wedge anchor holding a ground-mounted equipment stand down to its concrete pad.
#: Its own role rather than a second product on ROLE_DECK_EQUIPMENT_ANCHOR — that part is
#: selected for a SEAL through a waterproof plane, this one for embedment in concrete, and
#: ``hardware_for_role`` holds exactly one product per role.
ROLE_EQUIPMENT_PAD_ANCHOR = "equipment_pad_anchor"
ROLE_HURRICANE_TIE = "hurricane_tie"
# A wood member held down to CONCRETE or masonry by a gusset angle — one leg screwed into
# the wood, the other anchored with a concrete screw. Its own role and not a second product
# on ROLE_HURRICANE_TIE, which ``hardware_for_role`` would refuse anyway: an H-tie is a
# wood-to-wood part whose published values are nails into lumber on BOTH legs, so at a beam
# landing on a cast column top there is nothing for the second leg to bite. The deciding
# question is the same one that splits the seam clamps above — HOW THE PART REACHES THE
# BUILDING — and a screw into concrete is not a nail into a plate.
ROLE_MASONRY_GUSSET_ANGLE = "masonry_gusset_angle"
# A wood member held down to concrete by a strap CAST INTO the pour (HETA). Not the gusset
# role: no post-installed anchor, so no anchor-exposure condition, and a different table.
ROLE_EMBEDDED_BEAM_ANCHOR = "embedded_beam_anchor"
# A heavy bolted L-angle (Simpson HL) tying one member to another at 90°. Its own role: the
# published row is BOLTS through both legs into wood, and where one leg lands on concrete
# the anchor side is an ACI 318 Ch. 17 design, not a table read.
ROLE_HEAVY_ANGLE = "heavy_angle"
# The treated block a tie part is fastened to where it cannot reach the member itself (a
# carrier soffit 3 3/4" over a stem, a filler through cladding). Lumber, billed per block.
ROLE_TIE_BLOCK = "tie_block"
# The cap over a post that a beam lands ON (rather than continues past). Its own role, not
# ROLE_BEAM_HOLD_DOWN: the KBS strap ties a beam DOWN to a post whose sides it can reach,
# while a cap seats the beam and takes uplift in one part. Both serve a post/beam joint and
# ``hardware_for_role`` holds exactly one product per role, so they cannot share.
ROLE_POST_CAP = "post_cap"
# A post held DOWN to the FRAMING it stands on. Its own role and deliberately not
# ROLE_POST_BASE: a base is a formed stirrup that a post sits INSIDE, selected by the post
# section and rated bearing on concrete through a cast-in anchor. This part is a strap
# screwed to the post face and bolted through the joist under it — different joint, different
# published table, different price. Nor is it ROLE_BEAM_HOLD_DOWN, which ties a beam down to
# a post: that is the joint at the OTHER end of the same member.
ROLE_POST_TENSION_TIE = "post_tension_tie"
# The shim pack that holds a wood beam soffit clear of the pour it lands on. Not a post base
# and not a bearing plate: it is selected by the GAP it has to hold and the alloy it has to
# hold it in, and it is the part that makes an R317.1.4 standoff countable instead of a
# sentence in an assembly's ``source``. See ConnectorKind.BEARING_STANDOFF.
ROLE_BEARING_STANDOFF = "bearing_standoff"
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
# The pair of screw tension ties joining an upper storey's braced wall panel end to the
# post below it, through the floor band on a threaded rod (IRC Figure R602.10.7 end
# condition 5). Its own role and not ROLE_EMBEDDED_STRAP_HOLDOWN: nothing here is cast into
# concrete, and the two parts are selected against different reports (ESR-2330 screws into
# wood, ESR-2920 a strap in a pour).
ROLE_FLOOR_TIE_HOLDOWN = "floor_tie_holdown"
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

    @property
    def available_lengths_in(self) -> tuple:
        return tuple(sorted(self.part_number_by_length_in))


def structural_hardware_catalog() -> tuple:
    """The shared ``library/hardware.py`` catalog.

    Imported lazily: the engine package must import without the repo-root ``library``
    package on ``sys.path`` (the plan loader puts it there when a house is loaded).
    """
    from typehaus.library.hardware import STRUCTURAL_HARDWARE

    return STRUCTURAL_HARDWARE


def hardware_capacity_records() -> tuple:
    """Parts ``library/hardware.py`` holds an allowable for but does not bill.

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

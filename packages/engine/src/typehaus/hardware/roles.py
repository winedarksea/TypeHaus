"""The stable role keys the take-off selects hardware by (re-exported by ``catalog``)."""

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
# A roof block's end angle is a different joint from a gable-wall tie, even where
# both use LS30. Keep their located populations and ordering counts independent.
ROLE_DIAPHRAGM_BLOCKING_END_TIE = "diaphragm_blocking_end_tie"
# A trussed gable end instead: the gable-end truss is designed for its own out-of-plane load,
# so the joint only holds the truss down on the plate. Its own role so the stud tie is not it.
ROLE_GABLE_TRUSS_ANCHOR = "gable_truss_anchor"
ROLE_SLOPED_JOIST_HANGER = "sloped_joist_hanger"
# A stair stringer's head on the carrying header or rim: its own role because a joist
# hanger's seat is not what a stringer's plumb cut bears in (C-C-2024 p. 308).
ROLE_STAIR_STRINGER_CONNECTOR = "stair_stringer_connector"
# A skirted stringer screwed through its flat 2x spacer into a stud: chosen so the plain shank
# spans stringer + spacer and the whole thread lands in the stud (the girt screw's rule).
ROLE_STAIR_SPACER_SCREW = "stair_spacer_screw"
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
# A sawn member hung on a narrow carrier's face (a 4x4 post): the flanges turn in, inside the
# seat width, so the part fits a face no wider than the member (LUC, C-C-2026 p. 110).
ROLE_CONCEALED_FLANGE_HANGER = "concealed_flange_hanger"
ROLE_KNEE_BRACE = "knee_brace"
ROLE_KNEE_BRACE_EQUAL_WIDTH = "knee_brace_equal_width"
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
# A non-bearing partition's plate pinned to a slab poured after the walls' footings: no
# form board to nail a MASA to, and nothing for it to resist.
ROLE_SLAB_PLATE_PIN = "slab_plate_pin"
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
#: for is the SEAL and the alloy, not the post section — see library/hardware/.
ROLE_DECK_EQUIPMENT_ANCHOR = "deck_equipment_anchor"
#: The wedge anchor holding a ground-mounted equipment stand down to its concrete pad.
#: Its own role rather than a second product on ROLE_DECK_EQUIPMENT_ANCHOR — that part is
#: selected for a SEAL through a waterproof plane, this one for embedment in concrete, and
#: ``hardware_for_role`` holds exactly one product per role.
ROLE_EQUIPMENT_PAD_ANCHOR = "equipment_pad_anchor"
# A deck ledger's post-installed anchor into a concrete wall (``Beam.ledger_on``). AWC DCA6
# asks 1/2" expansion or adhesive anchors with washers and leaves spacing to the maker.
ROLE_LEDGER_ANCHOR = "ledger_anchor"
ROLE_HURRICANE_TIE = "hurricane_tie"
#: A roof I-joist above 3:12 tied through a web stiffener. Weyerhaeuser NW-D217 note 1 limits
#: the H2.5A family to 3:12 or less and bars nailing it into the flange.
ROLE_IJOIST_ROOF_TIE = "ijoist_roof_tie"
#: Joist to joist over a beveled ridge plate (TJ-4000 R14/R14W): carries the lateral thrust.
ROLE_RIDGE_PLATE_STRAP = "ridge_plate_strap"
#: A beveled ridge plate fastened down to the wall under it. Billed per bay, a run not a joint.
ROLE_RIDGE_PLATE_SCREW = "ridge_plate_screw"
#: A joist end tied to a concrete wall's sill by the part its floor names
#: (``JoistSpec.sill_tie``, Minn. R. 1309.0404). A row/joint label, never a lookup key: the
#: part comes from ``hardware_by_model``.
ROLE_SILL_TIE = "sill_tie"
#: The same part at a footnote f blocking station, block-to-sill on a PARALLEL foundation
#: wall (``JoistSpec.station_ties``). A row/joint label like ``ROLE_SILL_TIE``.
ROLE_WALL_TOP_TIE = "wall_top_tie"
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
# Parts an authored Connector names by part number (``Connector.size``), with no derived
# role. Looked up by ``hardware_by_model`` only: never call ``hardware_for_role`` on it — it
# holds several products, and that lookup demands exactly one.
ROLE_MODELED_CONNECTOR = "modeled_connector"
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
# The one-setscrew Mini of the same clamp: a lighter-duty part, so it takes uplift-only wind
# clamps and never carries an accessory (PV kit, snow rail), which stay on the full S-5-N.
ROLE_NAIL_STRIP_MINI_SEAM_CLAMP = "nail_strip_mini_seam_clamp"
# The PV mounting kit is its own role: hardware_for_role demands one product per role,
# and the plain S-5! clamp (vent riser, exterior boxes) must keep serving its own.
ROLE_PV_SEAM_CLAMP = "pv_seam_clamp"
# The ring that secures a round pipe/conduit/leader to a seam clamp. Its own role for the
# same reason: it is a separately purchased part, in fourteen diameters, and a plan that
# says "clamp" without saying which ring is not orderable.
ROLE_PIPE_CLAMP = "pipe_clamp"
# The strap that holds that same round pipe against a seamless panel (exposed-fastener, or a
# concealed-fastener flat), by screwing through it into the framing behind. Its own role rather than
# a second product on ROLE_PIPE_CLAMP for two reasons: ``hardware_for_role`` holds exactly one
# product per role, and — like the seam-clamp pair above — the deciding question is HOW THE PART
# REACHES THE BUILDING. A ring that mounts on a seam and a strap that penetrates a panel are
# different products for different claddings, and neither one can be substituted for the other on
# site.
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
# A bolted hold-down on an end stud, on a cast-in anchor rod (HTT4 on an SSTB). Its own
# role: neither cast in (an STHD) nor floor to floor (a DTT2Z pair); read with its anchor.
ROLE_ANCHOR_ROD_HOLDOWN = "anchor_rod_holdown"
# The cast-in anchor bolt that hold-down bears on, graded on its stem-wall row. Not
# ROLE_SILL_ANCHOR_BOLT: that bolt holds a plate down at a pitch, this one an end post.
ROLE_HOLDOWN_ANCHOR_BOLT = "holdown_anchor_bolt"
# A pre-cut strap nailed across a floor band, stud to stud. Not ROLE_COIL_STRAP: that is
# bought by the coil and cut, this is one part per joint.
ROLE_FLOOR_TO_FLOOR_STRAP = "floor_to_floor_strap"
# The gasketed stainless screw that holds a multiwall glazing sheet down to its framing.
ROLE_GLAZING_PANEL_FASTENER = "glazing_panel_fastener"
# The gasketed screw that fixes an exposed-fastener metal wall/roof panel through its face
# into the supports behind. Distinct from the glazing fastener above — that one is sized to
# a sheet that must be free to move in an oversize hole, this one clamps the panel down —
# and it exists at all only because ``Material.exposed_fastener`` panels bill their fixings
# as a counted part instead of inside the $/SF cladding rate.
ROLE_EXPOSED_FASTENER_PANEL_SCREW = "exposed_fastener_panel_screw"
# The self-drilling screw that stitches two exposed-fastener panels together down their
# sidelap, metal to metal and between supports. Not the panel screw: there is no wood behind
# a sidelap for a wood thread to bite, and the panel screw's sharp point does not drill.
ROLE_SIDELAP_STITCH_SCREW = "sidelap_stitch_screw"
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
# A hung seat's load path (``SuspensionAnchor.hardware``): the saddle on the joist line and
# the swivel or shackle under it. Named by the anchor, never selected by role.
ROLE_SUSPENSION_SADDLE = "suspension_saddle"
ROLE_SUSPENSION_SWIVEL = "suspension_swivel"
ROLE_SUSPENSION_SHACKLE = "suspension_shackle"
# Counted "upgrade" fasteners (decision #105). Looked up by model, never by role, except
# where one product serves the role: the concealed panel screws (one per cladding, so the
# cost code can tell siding from roofing) and the HDG nail treated framing falls back to.
ROLE_CONCEALED_SIDING_PANEL_SCREW = "concealed_siding_panel_screw"
ROLE_CONCEALED_ROOFING_PANEL_SCREW = "concealed_roofing_panel_screw"
ROLE_CONNECTOR_NAIL = "connector_nail"
ROLE_TREATED_FRAMING_NAIL = "treated_framing_nail"
ROLE_STAINLESS_FRAMING_NAIL = "stainless_framing_nail"
ROLE_SHEATHING_NAIL = "sheathing_nail"
# Site-length through-bolts and lags an HL angle is fixed with (decision #147); the length
# is derived from the grip, so the role holds one family per diameter.
ROLE_SITE_BOLT = "site_bolt"
ROLE_SITE_LAG = "site_lag"
# Trim-to-wood and window-install fasteners (decision #147).
ROLE_TRIM_FASTENER = "trim_fastener"
ROLE_WINDOW_INSTALL_FASTENER = "window_install_fastener"

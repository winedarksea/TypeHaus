# haus: editable
# Catlin transition library — documentation overlays never alter resolved geometry.
# Editable so the UI's detail star toggle (Transition.star and the per-condition
# starred_conditions/unstarred_conditions overrides — the primary-set curation flags)
# round-trips to source; the geometry-free fields here are still design decisions.

from typehaus import Continuity, Transition


AIR_WATER_THERMAL = (
    Continuity(control="air", from_face="sheathing-ext", to_face="sheathing-ext"),
    Continuity(control="water", from_face="wrb-ext", to_face="wrb-ext"),
    Continuity(control="thermal", from_face="ci-ext", to_face="ci-ext"),
)

TRANSITIONS = (
    # star=True marks the details a framer/builder actually opens on site — the primary
    # export (`haus print --details primary`) keeps exactly these; the rest still derive.
    Transition(uid="CATR001AAAA", tag="TR-CATLIN-EAVE", condition_pattern="wall_roof:*",
               notes="notes/roof_wall_eave_detail.md", overlay="zero-overhang-eave",
               continuity=AIR_WATER_THERMAL, star=True),
    # The starred half of this pattern is the envelope crossing — concrete to framed wall
    # where the thermal, air and water layers all have to hand off. Where an interior
    # partition or bearing wall lands on interior concrete none of those layers exist to
    # continue, and the sill/anchor condition is already drawn once on the envelope sheet;
    # unstarring those keys keeps the primary set the crossings a builder actually opens.
    Transition(uid="CATR002AAAA", tag="TR-CATLIN-FOUNDATION",
               condition_pattern="wall_foundation:*",
               notes="notes/basement_to_framed_wall_detail.md",
               overlay="basement-framed-wall", continuity=AIR_WATER_THERMAL,
               documents_rules=("CR-CONC-TO-FRAMED-SILL", "CR-FOUNDATION-FOAM-RETURN"),
               star=True,
               unstarred_conditions=(
                   "wall_foundation:CATLIN_CONC_12_INT|CATLIN_INT_2X6_BRG",
                   "wall_foundation:CATLIN_CONC_12_INT|CATLIN_MUDROOM_INT_2X6_EXPOSED",
                   "wall_foundation:CATLIN_CONC_12_INT|INT_2X4_PARTITION",
                   "wall_foundation:CATLIN_INT_2X6_BRG|SAUNA_LINER_ON_CONCRETE",
               )),
    # Same curation as the foundation above: the rim band is a sheet because it is where
    # the air barrier and the insulation cross a floor line. An interior partition's rim
    # has neither — it is ordinary blocking, drawn on the framing plans.
    Transition(uid="CATR003AAAA", tag="TR-CATLIN-RIM-BAND",
               condition_pattern="storey_stack:rim:*", overlay="rim-band-air-seal",
               continuity=AIR_WATER_THERMAL, star=True,
               unstarred_conditions=(
                   "storey_stack:rim:CATLIN_CONC_12_INT|CATLIN_INT_2X6_BRG",
                   "storey_stack:rim:CATLIN_CONC_12_INT|CATLIN_MUDROOM_INT_2X6_EXPOSED",
                   "storey_stack:rim:CATLIN_CONC_12_INT|INT_2X4_PARTITION",
                   "storey_stack:rim:CATLIN_INT_2X6_BRG",
                   "storey_stack:rim:CATLIN_INT_2X6_BRG|SAUNA_LINER_ON_CONCRETE",
                   "storey_stack:rim:CATLIN_MUDROOM_INT_2X6_EXPOSED|INT_2X6_STAGGERED_PLUMBING",
                   "storey_stack:rim:INT_2X4_PARTITION",
                   "storey_stack:rim:INT_2X4_PARTITION|INT_2X6_STAGGERED_PLUMBING",
               )),
    Transition(uid="CATR004AAAA", tag="TR-CATLIN-STACK-SHELF",
               condition_pattern="stack_width_change:*", overlay="stack-width-shelf",
               continuity=AIR_WATER_THERMAL),
    Transition(uid="CATR005AAAA", tag="TR-CATLIN-FRAMED-OPENING",
               condition_pattern="opening_perimeter:CATLIN_EXT_*",
               notes="notes/roof_wall_eave_detail.md", overlay="window-head-jamb-sill",
               continuity=AIR_WATER_THERMAL, star=True),
    Transition(uid="CATR006AAAA", tag="TR-CATLIN-CONCRETE-OPENING",
               condition_pattern="opening_perimeter:CATLIN_CONC_*",
               notes="notes/sauna_basement_wall_detail.md", overlay="concrete-opening"),
    Transition(uid="CATR007AAAA", tag="TR-CATLIN-BASEMENT-OPENING",
               condition_pattern="opening_perimeter:CATLIN_BASEMENT_12",
               notes="notes/basement_to_framed_wall_detail.md", overlay="foundation-window"),
    # Bound but deliberately sheetless: the arch already reads on plans and sections.
    Transition(uid="CATR008AAAA", tag="TR-CATLIN-GARDEN-ARCH",
               condition_pattern="opening_perimeter:SUNKEN_GARDEN_*",
               suppress=True,
               # (single literal: the editable dialect forbids concatenated strings)
               suppress_reason="the sunken-garden arch is an open-air rough opening in exposed concrete — no buck, no frame, no flashing is applied at its perimeter; the arch geometry the plans and sections draw is the whole story, so a perimeter detail sheet would add nothing"),
    # Starred: the garage/breezeway threshold condition — both doors open onto the slab
    # at grade, with the ICF stem dropped to a grade beam under them, so the perimeter
    # flashing here is nothing like a standard framed opening.
    # Same reasoning as the garden arch above, one wall further north: the reveals through
    # W-B-BRICK are open arched holes in a freestanding wythe, and the flashed, bucked,
    # sealed opening is the one in the CATLIN_BASEMENT_12 wall behind them (TR-CATLIN-
    # BASEMENT-OPENING already draws that). A second sheet here would detail a perimeter
    # that has no perimeter work.
    Transition(uid="CATR015AAAA", tag="TR-CATLIN-VENEER-OPENING",
               condition_pattern="opening_perimeter:BASEMENT_BRICK_VENEER",
               suppress=True,
               # (single literal: the editable dialect forbids concatenated strings)
               suppress_reason="the veneer reveal is an open segmental arch in a freestanding brick wythe standing 1\" off the basement wall — no buck, no frame, no flashing lands at its perimeter, and the opening that does get all three is the window/door in the concrete wall behind it, detailed by TR-CATLIN-BASEMENT-OPENING"),
    Transition(uid="CATR009AAAA", tag="TR-CATLIN-GARAGE-OPENING",
               condition_pattern="opening_perimeter:GARAGE_WALL_2X6",
               notes="notes/garage_wall_detail_side.md", overlay="garage-opening",
               star=True),
    Transition(uid="CATR010AAAA", tag="TR-CATLIN-INTERIOR-OPENING",
               condition_pattern="opening_perimeter:INT_*", overlay="interior-opening"),
    Transition(uid="CATR011AAAA", tag="TR-CATLIN-CENTER-OPENING",
               condition_pattern="opening_perimeter:CATLIN_INT_2X6_BRG",
               overlay="bearing-partition-opening"),
    # Two legitimate in-plan assembly changes survive the resolver's derivation gates
    # (the sauna liner starting along the interior concrete run, and the masonry railing
    # meeting the retaining wall's 6" upstand). They are bound — covered, continuity
    # declared, construction rules documented — but deliberately sheetless.
    Transition(uid="CATR012AAAA", tag="TR-CATLIN-ASSEMBLY-JOG",
               condition_pattern="assembly_change:*",
               continuity=AIR_WATER_THERMAL,
               documents_rules=("CR-CONC-TO-FRAMED-SILL", "CR-SAUNA-LINER-RETURN",
                                "CR-PORCH-MASONRY-RETURN"),
               suppress=True,
               # (single literal: the editable dialect forbids concatenated strings)
               suppress_reason="the jog happens *along* the wall run, while a derived detail cuts perpendicular to the wall — the change of assembly is simply not in that cut plane, so any sheet here would describe a junction the drawing does not show; the returns themselves are documented by the construction rules this transition records"),
    # The sauna door breaks the hot side's vapour control layer — the foil-faced polyiso
    # has to be returned into the jamb and sealed, not just butted.
    Transition(uid="CATR014AAAA", tag="TR-CATLIN-SAUNA-OPENING",
               condition_pattern="opening_perimeter:SAUNA_*",
               notes="notes/sauna_basement_wall_detail.md", overlay="sauna-liner-opening",
               continuity=(Continuity(control="vapor", from_face="foil-polyiso",
                                      to_face="foil-polyiso"),
                           Continuity(control="air", from_face="foil-polyiso",
                                      to_face="foil-polyiso")),
               star=True),
    Transition(uid="CATR013AAAA", tag="TR-CATLIN-RIDGE-BEAM",
               condition_pattern="roof_ridge:*", overlay="lvl-ridge-hanger"),
)

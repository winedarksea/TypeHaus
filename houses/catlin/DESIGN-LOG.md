# Catlin house — design record

Why the house is the way it is. Every entry here was once in `CLAUDE.md` and was moved out
so that file could stay a constraint index an agent can read in one sitting.

**This file is history, not instruction.** Nothing here is a rule, nothing here is
authoritative about the current model, and an entry may describe a design that has since
been replaced. `CLAUDE.md`, the plan source under `plan/`, and the notes under `notes/` are
the present state. Read this when you want to know *why* a number is what it is, what was
tried before, or which engine bug a rule exists to dodge — and when a decision here
contradicts the model, the model wins.

Sections match `CLAUDE.md`'s one for one.

## Site and the four structures

- **Breezeway design (retired), in full.** Before the extruded garage gable superseded it, the fourth structure was an enclosed breezeway on freestanding 6x6 posts spanning the 4' gap door-to-door (`params/breezeway.py`), glazed in polycarbonate. The breezeway followed the doors, and nothing enforced that but one line: it was a 4'-6" enclosure centred on the midpoint of `D-M-ENTRY` (x 8'-0") and `D-G-SERVICE` (x 10'-0") — x 9'-0" as of 2026-09-09, once the two stopped being concentric. When either door moved, `_GLAZING_CENTER_X` and `_EW_FT` moved with it (`code.R311_3_exterior_landing` caught a shelter that drifted off its own door). Both doors opened onto the deck at 0'-0" and reached it from opposite directions: `D-M-ENTRY` from the house floor it shares, `D-G-SERVICE` up +1'-0" from a garage storey that sat at -1'-0". The breezeway deck did not move with grade — it was a bridge between two doors, and only its pads and piers followed the soil down. Only 7/8" of the garage's corrugated cladding panel projects past the sheathing plane, so it drips clear; the breezeway's own uncut 4' panel was measured off the cladding rather than the sheathing plane, and its core was 6" thick — a different alignment convention from the garage's. What survives of this design today is the foundation bridge (FS-BW-FLOOR, FS-BW-GARAGE), beams (BM-BW-*), a stair (ST-BW-ENTRY), a railing (RL-BW-ENTRY), and a slat screen (SC-BW-WEST); the posts, roof, and glazing described above are gone. The current design is recorded separately in notes/north_entry_structure.md.
- **Why grade sits 2'-10" below the main floor.** The basement-ceiling overhaul put a 12 5/8" deck where a 9" slab had been, and the house rose 4" rather than surrender the headroom under it — that 4" rise is folded into the 2'-10" figure.
- **Why the basement is 8'-0" even, not 9'-0".** The flat bearing seat lands the EPS deck's soffit on the same plane as the wood bays' mudsill: the deck is 14 3/8" deep and the FLOOR meets it there, so the house sits exactly where it was and the basement simply reads shallower as a result. `Storey.default_ceiling_height` still authors a fictional 9'-0" because nothing has gone back to correct it — `code.R305_ceiling_height` was changed instead to derive the real number.
- **Garage storey datum history.** The `garage` storey landed at -1'-0" "since the lifts" — i.e. after a revision raised the ICF stem's bearing reveal to `GARAGE_STEM_REVEAL` (1'-10") above grade. Before that revision, `D-G-SERVICE`'s framing and the breezeway deck it opened onto were coordinated differently; today the door's threshold is pinned at 0'-0" with the bridge deck rather than following the storey drop the way `D-G-OVERHEAD` does, which is why it needed its own +1'-0" sill and five 6.8" risers inside the garage instead of a curb-free opening.

## Shell: framing module and envelope

- The current CATLIN TRUSS WALL is the third wall stack. It replaced the Swinburne
  truss — a chiral block + plywood tab + KDAT outrigger *on edge* at 16" o.c. — which had
  in turn replaced a sheet WRB + 2" polyiso + 2" EPS + 1/2" furring on 537 eight-inch screws.
- The inner girt tier was deleted, and the reason is not economy. Bands B and C used to
  carry a plain SPF 2x4 flat buried in the foam, with the outer tier's blocks bearing on it
  and a second 5" screw into it. It sat directly on the sheathing, so it gave its own screw
  no thermal break at all, and it cost a 10.9% framing fraction in the first 1-1/2" of the
  insulation to hold up nothing but the tier above it. Removing it was worth +2.5 R.
- The screw-as-sole-load-path is defensible specifically because the block bears the
  cladding's gravity in direct compression on the sheathing, making the screw a pure
  withdrawal element rather than a shear/bearing one — that's what keeps utilisation to
  54%/38% rather than something structural failing outright.
- The build order used to be two lifts: framing/screws in one pass, then foam sprayed in
  two separate lifts around the wall's erection sequence. It is now one 4" lift sprayed
  through the 20-1/2" clear between courses and behind them, after all wood and the whole
  screw pass happen on the flat wall pre-tilt.
- Why the course datum had to be the sills, not the wall base: on a main-storey wall the
  two datums are 13-7/16" apart (`platform.py` extends the wall down over the floor rim
  band), and that mismatch used to leave a field course a half inch off an opening's own
  head or sill course before the datum was corrected.
- The girt-course phase sweep: at the old -3-1/2" phase, the opening rule was head/sill
  mirrored from the current one, and that phase is no longer available — at 24" it opens a
  24.75" bay on nine walls and `structural.girt_course_spacing` fails it. Phase zero is the
  swept winner among phases that keep every bay at or under 24.00": 13 opening edges land
  exactly on a course line, 30 sit in the 7" shadow of one. Full sweep in
  `notes/outie_window_truss_detail.md`.
- Why no window moved when the stack changed: the mount plane is the outermost furring
  layer's outer face, and the 6" stack simply comes out a different way now (a 4-1/2" block
  plus a 1-1/2" girt instead of four 1-1/2" layers) — the outer face didn't move even though
  its makeup did.
- The cladding swap was 1/2" of exposed snap-lock standing seam to 1-1/4" of exposed-fastener
  PBR panel — that 3/4" delta is what pushed `_WALL_OUTBOARD_IN` to 7.25" and dragged
  `roof_trim.py`, `breezeway.py`, the garage wall lines, and exterior electrical with it.
  Only the cladding return depth at a jamb changed with the swap; interior geometry did not,
  because walls align on `face("sheathing-ext")`.
- The garage only moved 3/8" of that same delta, because `params/breezeway.py` was also
  carrying a 3/8" rainscreen furring on the garage face that `GARAGE_WALL_2X6` dropped — a
  correction, not a rounding error.
- Mineral wool was swept from most stud bays by an owner cost review: mineral wool costs 2x
  installed versus fibreglass, reads the same 116 perm-in either way, and published STC
  tables separate assemblies by mass and decoupling, not by which wool sits in the bay. The
  batt itself is worth $4,500-6,300 for 0.9 of the 2.7-point `wall_r` shortfall; the other
  1.8 points were never in the bay to begin with.
- A sibling cladding assembly (rather than the per-wall `layer_materials` override) was the
  obvious first move and was rejected: it would have stripped the oak window stools from
  every window on a board-and-batten wall (`plan/millwork.py` scopes them to
  `("EXT_2X6",)`), minted new `opening_perimeter:` / `wall_roof:` / `wall_foundation:` keys
  and goldens, broken the exact-key star overrides in `plan/transitions.py`, and added a key
  to every table keyed by assembly. `W-S-S1` is `PLANT_EXT_2X6_HUMID` while `W-S-W4` on the
  other cladding line is too — the plant room straddles the split, and the per-wall override
  handles that without forking either assembly.
- Delivered cost of the board-and-batten-on-two-elevations switch: +$2,200 to +$5,600,
  measured line-to-line against an all-PBR baseline.
- A `corner_style_end="4-stud"` override authored on only one incident wall used to never
  take effect, and this was a real bug, not a documentation gap: the exterior loop is a CCW
  chain, so every wall's `end` is the *next* wall's `start`, and `resolve/topology.py` gave
  L-corner ownership to whichever wall *starts* there. A style authored on the wall that only
  ever *butts* the corner could never reach the pack. The fix — `resolve/framing/
  solver.py::frame_model` now resolving a corner's style from BOTH incident walls — is what
  makes an override on either wall take effect.
- The APA/BASC objection to a solid 4-stud corner post is that it is an insulable void with
  nothing in it. It doesn't apply on this house specifically because the primary insulation
  is the continuous exterior closed-cell foam, outboard of the post — the post itself never
  needed a cavity to hold batt in the first place, unlike a conventional insulated-cavity
  wall.
- The retired corner detail was the Larsen/Swinburne corner box (FHB, Jan 2024): two 1/2"
  OSB rips per corner per storey (24 total), one along each wall's own outrigger band,
  meeting at the true building corner to close both outboard faces of the ~5"x5" full-height
  void that band's own 45° mitre left standing open. A girt band has no such void — the
  courses are horizontal and butt at the corner, so each course closes its own band as it
  goes and there is nothing full-height left to cap.
- IRC R703.15's through-foam furring table is not the applicable provision for the girt/
  block crossings: every fastener there is wood-to-wood with continuous lateral support and
  nothing bears on foam, which is the condition that table is written for.
- The board-and-batten appearance's ten registrations, name by name: `BOARD_BATTEN_PROFILE`
  + the `metalPanelProfileForFinish` branch (`ui/src/three/materials.ts`), `FINISH_BASE`
  (`ui/src/nordic/palette.ts`), `_FINISH_BASE` and `_METAL_PANEL_FINISHES`
  (`emit/gltf/palette.py`), `DETAIL_FILL` + `DETAIL_HATCH` (`emit/draw/palette.py`), the
  mirrored `DETAIL_FILL` (`ui/src/components/DetailCanvas.tsx`), and `_BATTEN_PITCH_M` with
  a finish-first branch (`emit/draw/elevation_finish.py`).
- The layout-grid-struck-from-the-corner finding was an audit result, not a change: it was
  already correct and the audit did not touch it. It survived the catlin truss because the
  girts are horizontal, so what phase-locks to the 16" module now is their blocks rather
  than the band itself — the promise (the screw lands on the stud) is the same one as before.

## Bearing lines and floor decks

- `INT_2X6_BRG_PLUMBING` was chosen over bare `INT_2X6_PLUMBING` specifically to keep the
  5 1/2" fiberglass batt the staggered wall's cavity had — the swap doesn't silently strip
  the insulation.
- `BM-S-BATH-E`'s ply count: the demand at this beam is ~600 lb; two plies of
  1.75x11.875 LVL carry it many times over and would satisfy bending alone, but two plies
  is only 3.5" wide, and the 4.77" attic partition standing on the beam would overhang
  0.65" each side. Three plies (5.25") was chosen to match the bearing width, not because
  bending demanded it — it happens to land on the same section as `BM-S-HALL`, one LVL
  depth on the job.
- `SL-M-DECK` is what is left of the old 1,233 SF cast deck. The deck's soffit lands on the
  shared bearing seat, and so does the underside of the gasket under the wood bays' shared
  2x6 mudsill. The seat and depth constants sit in `params/main_deck.py` rather than the
  editable storey file precisely because they are not something a UI edit should be able
  to move.
- The basement's mixed ceiling used to be tuned to one *depth* (12 5/8") rather than one
  *seat*. That depth matched the finished floors but left the I-joists resolving inside the
  top foot of the pour, with nothing between wood and concrete. It was changed to a shared
  flat bearing seat at -13 7/16" instead, giving one plate for studs and joists and no step
  in the forms. `structural.mixed_deck_bearing_seat` was written to hold this.
- The 2 1/16" step between the two gypsum ceiling faces at the `RM-B-GYM` boundary breaks
  down as 1/2" (the LiteDeck form's steel rib) + 1 9/16" (the deck being deeper than the
  wood bay). The model states only the 1 9/16" it can derive from geometry — the rib's 1/2"
  belongs to the EPS form, and EPS is never modelled in this engine, so that portion is not
  represented even though the physical step is real.
- The derived finish band (`_BAND_Y`) carried a sheet-vinyl hall band, then briefly a
  solid-oak south bay for part of it. Both were deleted rather than replaced: the hall now
  takes the room's field `lvp`, and `RM-M-BATH1`/`RM-M-LAUNDRY` were retyped onto the same
  plank so `vinyl-sheet` has left this storey entirely; the south bay is that same plank.
- The two mudroom closet doors are `D-M-MECH` (on `W-M-MECH-S`) and `D-M-MUDC` (on
  `W-M-MUDC-N`); both open into the mudroom, which is what settled their tile.
- The mudroom suite (`RM-M-MUDROOM`, `RM-M-MECH`, `RM-M-MUD-CLOSET`) took LVP for a few
  hours on 2026-09-05, before the doorway adjacency to `D-M-MECH`/`D-M-MUDC` was checked
  against the hall. Correcting it to porcelain cost +$298 to +$627 delivered.
- The two flush walking-plane legs run `y=13'` (17.9 lf) and `x=18'` (13.6 lf). The oak bay
  along the `y=13'` leg was tried and withdrawn the same day (2026-09-05). Oak finishes at
  +1 1/2"; against the polished cap's +15/16" that leg would have needed a 9/16" reducer,
  which could not be designed out because `structural.mixed_deck_bearing_seat` only gives
  the cap 1/16" of lift, not 9/16". The height mismatch was undesirable, so the bay
  reverted to plank: -$1,980 to -$2,751 delivered, and the `oak` price row fell back under
  its sand-and-finish mobilisation minimum. Oak survives only in the two studies, where
  nothing meets a cap.
- Bug (fixed 2026-09-05): the finish zone's outline was deliberately drawn over-extended
  past the room on three sides, on the documented promise that `resolve/rooms.py` clips a
  zone. It clipped the AREA calculation but not the drawn ring, so the living-room floor
  rendered a foot outside the east and south walls at 0 FAIL. The engine fix makes an
  authored zone draw clipped, the way a derived one always did.
- `notes/mixed_deck_movement_joint.md`'s "no fibres" clause for the polished cream mix was
  superseded 2026-09-03: it now runs micro-monofilament PP at ~1.5 lb/cy (`POLISHED_MIX`).
  Macro fibre and steel remain excluded — the distinction between "no fibres" and "no
  macro/steel fibres" is the whole finding.
- `FS-S-EAST` is unchanged from the old whole-floor `FS-SECOND`; only the west field became
  open-web truss. Both fields were kept at 11 7/8" deliberately, same depth and same
  stiffness class, so the split needs no movement joint and no finish break, unlike the
  basement's concrete/wood boundary.
- The second floor's shared x=18' plate used to be split on the centreline between the
  truss and I-joist fields. That shorted the truss's seat, since an open-web floor truss
  wants 3" of bearing where an I-joist is satisfied with 1¾" — hence the deliberate
  3½"/2" asymmetric split now in `params/second_deck.py`.

## Attic and roof

- **Knee walls to a hot roof.** The attic used to be 5'-0" knee walls at 4:12, from a
  MISREADING of R305 — that every square foot of a sloped-ceiling room needs 5'-0" of
  headroom. Minn. R.1309.0305 R305.1 Exception 1 and IRC R304.1/R304.3 scope both clauses
  to the *required* floor area (70 sf), not the whole room, and R304.3 says floor under
  5'-0" simply doesn't count rather than disqualifying the room.
  `code.R305_ceiling_height` used to grade the whole room; it was fixed in the same pass
  that removed the knee walls. With the knee walls gone the pitch was free to be whatever
  the headroom wanted, and 6:12 is the shallowest standard pitch that carries the rooms.
  - The building got 1'-9 1/2" SHORTER (ridge 32'-0 5/8" → 30'-3"), the envelope lost ~572
    sf of `EXT_2X6` for +89 sf of roof, and six windows came out. Measured, not asserted:
    `haus takeoff --csv` before/after puts the redesign at -$19,400 to -$36,200. The same
    before/after run also moved by three PRICING fixes found in passing and unrelated to
    the attic — an `icf-eps` double-bill removed, and the missing
    `closed-cell-spray-foam:1.0` and `WT-2748`/`WT-2748-T` rows added — netting +$3,100 of
    previously invisible cost. The all-in line-to-line delta between the two CSVs is
    therefore -$17,200 to -$32,300; the attic itself is the bigger number.

- **`RM-A-STUDIO` floor finish history.** The room carried `floor_finish=None` over a
  `plywood-underlayment-sanded` deck until 2026-09-09: a sanded plugged panel is walkable,
  not finished, so it needed a sealer allowance with no BOM row. Sheet vinyl retires both
  — `FS-ATTIC` drops to plain `plywood-subfloor`, the sealer allowance is deleted, and
  ~357 SF joins the house's existing `vinyl-sheet` buy at ~$4-8/SF. Seamless and
  waterproof, which a room with a wet bar wants.

- **R303.1's literal-reading risk, in full.** R303.1 says "the floor area of such rooms"
  and does not cite R304.3; R304.3's own operative words are scoped to R304.1's 70 sf. On
  the literal reading this room owes 8% of its whole 356 sf, is short, and is back on
  Exception 1. The finding prints BOTH areas and the section for exactly that conversation
  — see `_r303_floor_area` in `checks/code/mn_residential/ventilation.py`, which carries
  the argument and its two known limits. `ResolvedRoom.head_limited_area_m2` measures to
  the roof UNDERSIDE (146 sf), which is why it disagrees with `code.R305_ceiling_height`'s
  190 sf off the rafter TOP.

- **Why the ERV hoods left the north gable.** Two passes moved them along the gable trying
  to get the intake off `FO-A-HALL`'s open well, and the gable was never survivable:
  `DU-ERV-EA`'s 18'-0" leg at +23'-0" ran through the rough openings of both north-gable
  windows, 8" above a 22'-0" sill in a 25'-0" head, across 2'-6" of each unit — and
  `CD-A-DATA-NE`, rerouted into the same band, crossed `WIN-A-N2` too. They ended up
  stacked on the west face at the NW chase instead.

- **The 0.4" vs 0.2" misconception on the PLANT run.** `DU-M-ERV-R-PLANT`'s route is
  LONGER, not shorter — 55'-8" against a 47'-5" straight-line estimate (9'-4" of the
  difference is rise, which an eyeballed estimate misses) — and is affordable only because
  the machine's rating point is 0.4" w.g., not the 0.2" several older comments still
  quote. The terminal being HIGH SIDEWALL rather than CEILING never gave up the height
  argument: humid air stratifies, so the extract must sit in the warm wet air at the top
  of the room, and 8'-6" is six inches under the ceiling — the argument was about height,
  not which direction the boot arrives from. Separation from `REG-S-HP-PLANT` improved
  again on 2026-09-04 when that supply moved from x=6'-8" to x=9'-4", giving 9'-2" across
  the 159 sf room.

- **Prior roof stack.** It was a vented batten roof, then a screwed nailbase stack: 1/2"
  taped ZIP → self-adhered deck vapour barrier → 3" + 3" polyiso → 5/8" OSB top deck on
  539 ten-inch SDWH screws → vapour-permeable synthetic underlayment → 1/4" ventilated mat
  → metal. R-55.1 at 19.9" deep, to clear a code minimum of R-49. The flash-and-batt
  replacement is 6.81" (perpendicular) thinner at R-53.2/13.1".
- Cost: -$12,200 to -$24,500 on the construction subtotal, of which $3,400-6,000 is a
  known phantom (roof sheathing is billed twice, in `envelope_layers` and again in
  `sheet_goods`; `also_in_sheet_goods` exists and `cli/prices.py::estimate_costs` never
  reads it). The honest saving is $8,800-18,500.

- **Ridge beam depth history.** The same plumb-cut arithmetic at 4:12 gave 13.10" and put
  the answer at 14" (`2-1.75x14 LVL`); before that the beam reached 11.875"
  (`3-1.75x11.875`), leaving the hanger seat and bottom flange 1.52" past the soffit. A
  ridge sized by bending rather than by the plumb cut would want 5 1/4" wide and the full
  LSSR header nail, rather than the 3 1/2" that only works via the ER-280 penetration
  reduction.
- The beam is ordered as three 12s rather than one 36' stick: same lineal feet, no offcut
  at 36', and a 106 lb ply instead of a 317 lb one (36' at 8.8 lb/ft/ply — this section's
  own weight, not `notes/ridge_beam_detail.md`'s 7.7 lb/ft/ply, which was struck for the
  retired 14" depth; scale by depth, width is unchanged — a 20' ply at the same rate is
  176 lb). Every piece at any depth this beam has been is a two-framer carry — no ply of
  this beam has ever needed a crane, including the 36' one-piece alternative it avoids.

## Windows and facade

**RO ladder.** 36" is the next rung up from the 27"/30" caps and breaks THREE studs (two on
a bay centre), which is why the 42" `WT-4248` sat on a bay centre until it was retired.

**Width/height family derivations.**

The juliet family (`WIN-A-S-JUL-W`/`-E`) was the house's longest-running off-module
exception. It centred on a stud line at 18" wide; widening to 24" could only go outward —
the 14" bearing pier under the ridge pins the inboard jambs — so each centre landed 3" off
module and `structural.window_framing_module` reported both. What ended the exception was
not a fifth attempt at the width but the grid moving under it: once the exterior assembly
began laying out from the layout line, 16'-0"/20'-0" became stud lines 5" further out, and
the pair fit with no retype. A further widening from 24" to 27" grew each unit 1 1/2" per
side, so the centres did not move at all; the clear bearing pier under `RB-HOUSE`'s south
bearing point closed from 24" to 21" against a 14" requirement — spent slack, not a new
constraint. At 6:12 the rake gives 7'-6 3/4" over the outer jambs, and a 64" unit on the
gable's 2'-8" sill wants 8'-2" — so the pair retyped to the width-identical WT-2754 (WT-2764
stayed catalog-only).

`WT-2748`'s sill/head datums were claimed as 2'-6"/6'-6" in this document until
**2026-09-06**. Commit `c2ed5b9d` ("Close the sunken garden's structural loop") moved all
three east sills 2'-6"→2'-8" in one silent hunk of a retaining-wall change, and every
comment quoting the old pair went stale at once. The corrected 6'-8" head — the house's own
door-head line — is a better fact than the one it replaced, not merely a correction.

**What ONE GRID PER FACADE retired.** Unifying the grid dissolved five separate defects that
had all been the same problem in different costumes: node moves made purely to buy phase
(`N-A-V1` to 22'-8" for the south gable, four more in the E/W pass); the "spent" 31'-4" west
column; the east knee band's 4" miss; the north gable's asymmetry; and the juliet pair's
accepted 3" off-module exception. All five dissolved when the grid was unified, at a cost of
20 windows moving 3"–8". The interior centreline used to run three storeys on three
different phases, each of its twelve segments restarting the module at its own start node,
before it opted into `layout_origin="line"`.

**Columns.**

The west face's four lower stations (5'-4", 10'-8", 20'-0", 24'-8") shifted 4" together
when the face re-hung on the house grid.

The west face's fifth column (31'-4") was recovered after having been spent: the second
storey's mechanical chase took its south corners 3 1/8" south so its face lands on
`FX-S-BATH1-SH`'s apron line; `N-S-CH3` moved with them; and `W-S-W1`'s grid re-phased out
from under `WIN-S-BATH-W`, which rode south to the bay centre that move created. With one
grid per line there is no per-segment phase left for a node move to disturb, so the window
returned to 31'-4" under `WIN-M-MUD` and the chase kept its 3 1/8". The 10'-8" suite header
used to cross the top ladder-backing rung at `W-S-W3`'s tee (the solver had omitted that one
nonstructural rung); the 4" the window moved took the header off it, and the backing is
complete again.

The north face used to carry a column at x=29'-4" (`WIN-M-KITCH`/`WIN-S-HALL-N`, moved there
from x=28'-0" to bring `WIN-M-KITCH` onto `FURN-M-KIT-SINKBASE` below). It was a
three-storey column until the 6:12 rake pulled `WIN-A-N2` off 29'-4" and inboard to the
gable, leaving a two-storey stack. On **2026-09-06** `WIN-S-HALL-N` moved west to 24'-0" and
the stack went with it, trading that column of two for the rectangle of four now described
in keep5.md — a precedent, not a general rule.

The face got a column back the same day, at the other end, for a different reason:
`WIN-S-BED3-N` was built to complete the north-east corner pair with `WIN-M-KITCH-N`/
`WIN-M-KIT-E` below (each unit 2'-0" off the corner). It also took `RM-S-BED3` off R303.1
Exception 1 (12.2 sf glazed/6.1 sf openable against 10.32 sf required) — a shortfall the
withdrawn 23'-4" unit below had also fixed and the moves had given back. Where a shortfall
and a composition want the same window, take both.

**The window built and withdrawn (2026-09-06).** A fourth window, also initially tagged
`WIN-S-BED3-N`, was built as a WT-1436 at x=23'-4" to fill the north gable's lower-east
corner, and withdrawn the same day in favor of the moves above — 23'-4" was the only station
the module and node `N-S-B5` allowed, 8" off the ideal and aligned with no column. Its one
lasting mark: `FURN-S-BED3-WARD` and `FURN-S-DESK3` swapped slots to clear the north wall in
`placeables.py`, and the swap is still needed today, because the wardrobe stood over x
22'-1.5"..24'-1.5" and `WIN-S-HALL-N`'s RO is 22'-9"..25'-3". The tag was reused within
hours for the WT-1424 at x=34'-0" that stands now — a different wall of the same room, a
different argument entirely.

**Rows.**

The east second storey used to run a perfect 9'-0" beat sitting 10" north of the centreline
(5'-4" of wall south, 3'-8" north). Centring it first took `N-S-E2` to 17'-8" and `N-S-E3`
to 26'-8" to buy phase, and the bedroom bays became 8'-8"/9'-0"/9'-4" to pay for it —
shrinking BED1 (whose R303.1 margin is 0.05 sf) and growing BED3 (which has two windows).
Those node positions are now incidental (the grid no longer depends on them), but the room
sizes they set are real and still govern. The inner pair then moved 4" outward onto the
unified grid, giving the row the even 9'-4" beat, three times over, described in keep5.md.

`WIN-M-LIV-E2` moved 12'-0" → 13'-4" on **2026-08-27** (one stud line north, to stack under
`WIN-S-BED1`); this passage said 12'-0" until **2026-09-06**. `N-M-E1` and `W-M-E2` were
removed when the wall was merged for `WIN-M-EAST-MID`, and `WIN-M-DIN-E2` (the window the
blank stretch was originally measured north of) was retired with them.

**2026-09-06:** the pier between `WIN-M-LIV-E1` and `WIN-M-LIV-E2` became the fireplace — an
eight-unit BESTA relayout (three south, five north of it) with the seating turned onto it.

Before the fireplace was a real modelled void, `SB-M-FIRE-MANTEL` was a `ResolvedShelfBank`
with no position, and no emitter reads `model.shelf_banks` — so it was a cut list and
nothing else, absent from the 3D and from every clearance check. It was replaced by the
wall-mounted placeable (`FURN-M-FIRE-MANTEL`/`FT-MANTEL-WALNUT-46`) described in keep5.md.

The old note claiming `FO-M-FIRE`'s span "crosses IRC R502.10's 4'-0" line" was an erratum
twice over: `haus check` grades floor-opening headers at EIGHT feet, and R502.10.1 is a
sawn-lumber rule the engine now gates on a sawn-joist profile — the I-joist opening was
never on that line to begin with.

The knee band deletion removed ~572 sf of `EXT_2X6`, along with four window units, four
bucks, four flashings, and eight jamb returns.

**Head lines.** `WIN-S-BED3`'s own source note in `second.py` claimed a 3'-0" head until
**2026-09-06**; the authored value was `ft(4)` (4'-0") the whole time. Correcting the prose
moved nothing.

**Gables.**

The north gable's history: `WIN-A-N1` moved 7'-4"→8'-0", mirroring `WIN-A-N2` at 28'-0"
about x=18', then to 6'-8"/29'-4" when the three-storey column moved to bring `WIN-M-KITCH`
onto the sink below (`WIN-A-N1` moved with it to hold the mirror). The rake then moved it
again: WT-3036 on the gable's 2'-0" sill puts the head at 5'-0", needing 2×(60+2)=124" of
clearance to the outer jamb, and 6'-8" gives only 65" — landing the pair at 12'-0"/24'-0". It
went one bay further in to 13'-4"/22'-8" on **2026-09-03** and came back out to
12'-0"/24'-0" on **2026-09-06**, where it now sits.

**The return outboard is what squares the facade:** with `WIN-S-STAIR-N` moved to 12'-0" and
`WIN-S-HALL-N` in from 29'-4" to 24'-0", both gable units stack exactly on a second-storey
partner and the north face reads as one rectangle of four.

The 145" clearance once quoted for the rake-binding note was the slack the inboard
13'-4"/22'-8" pair had; at the current 12'-0"/24'-0" station the true figure is 129" against
124" needed. `WIN-A-N1` was rehosted from `W-A-N2` to `W-A-N2B` on an earlier move.

This document claimed the stair window sat at 12'-8" and argued an 8" miss, until
**2026-09-06**; that was never true — the authored offset always resolved to 13'-4", and
correcting the prose moved nothing. The move to 12'-0" is the one real change.

The south gable used to carry SIX openings; the corner pair (`WIN-A-S1`/`S4` at
3'-4"/32'-8") has since been deleted — 21 1/2" of roof over the floor there. The flankers
moved inward and shortened (WT-1448→WT-1436); the juliets underwent a width-identical
retype (WT-2764→WT-2754), so their centres, `from_node` offsets, and the 21" clear pier
were all untouched by that move.

Mirroring the east half of the south gable once required moving `N-A-V1` from 22'-4" to
22'-8", because `W-A-S4`'s bay centres were 4" out of phase with a mirror of `W-A-S1`'s;
that node no longer sets any grid, so the move is now only a wall-segmentation choice.

**WT-1424** used to also serve the 5' knee walls, where its 2'-0" height was the only one
that cleared the plate; those walls are 1 1/2" rafter plates now and carry no glazing at
all.

**East bearing wall (BED1/BED2) — the 30" exception and its reversal.**
`WIN-S-BED1`/`BED2` used to carry a 30" RO in a bearing wall, with `max_window_ro_bearing_in`
set to 30 to allow it. The reason given at the time: R303.1 wants 9.95 sf of glazing, a
27x36 gives only 6.75 sf, and "27" cannot reach it at any height that fits under the 9'-0"
plate."

That last clause was never checked, and it was false: R303.1 binds on area (width x
height), so the width cap only binds if height has run out — and it had not. 27x54 gives
10.125 sf / 5.063 sf openable, clearing BED1 (119.66 sf, needing 9.573/4.786) by +0.55/+0.28
and BED2 (124.32 sf, needing 9.945/4.973 — the binding room) by +0.18/+0.09 — wider margins
than the 30x48 it replaced (+0.43/+0.21 and +0.055/+0.027). On the shared 3'-0" sill the head
lands at 7'-6", leaving 18" to the 9'-0" top of wall; the built framing puts a 2-2x8 header
at 7'-6"→8'-1¼" under a plate whose underside is 8'-9", leaving 7¾" of cripple — there was
never a plate conflict to design around.

Both rooms are now `WT-2754`/`WT-2754-T`, and the preference reverted to 27" for the east
bearing wall, matching every other bearing wall in the house.

## Ventilation, ducts and soffits

**ERV outdoor hoods moved off the north gable.** They used to sit at 8'/28' on the north
gable, and the argument for the gable did not survive measurement. It said "RM-M-MECH is
5'-11" x 2'-7", so no pair of hoods near the shaft can make ten feet" — the room is really
5'-3" x 1'-11" (`resolve/rooms.py` polygonizes from wall AXES and insets only by the lining,
so an exterior-wall room reads 6" past its own interior face), and the conclusion was only
ever true of a HORIZONTAL pair. It also said the main storey was too low at "20"-34" above
grade" — that is the 13 7/16" RIM BAND, not the 10'-0" wall; the interior band is
2'-10"..11'-10" above grade. Moving them to the stacked west-face siting saved 52.6 LF of R-8
wrapped 6" duct (`DU-ERV-OA` 32.3'→8.3', `DU-ERV-EA` 49.6'→21.0'), because both used to climb
24'-6" to the attic; it also empties the chase above the second storey, where four ducts used
to run and now two do. IRC M1506.3 independently waives the ten-foot rule "where the exhaust
opening is located not less than 3 feet above the air intake opening" — the engine does not
implement that exception and does not need to, but it is the second, independent reason the
exhaust must stay the upper hood. The gable mirror about x=18'-0" no longer applies to the
hoods (a facade rule for a gable, and they are not on one); `test_catlin_erv.py` now pins the
stack order instead.

**The soffit-occupancy check found two real errors on its first run, both in
`EQ-S-HP1-AH`.** It was resolving at the 9'-0" storey ceiling — a CEILING mount with no
elevation fell back to `default_ceiling_height`, which is now soffit-aware — and its case
resolved 43" across the hall instead of 21" along it, because `EquipmentType.footprint` wins
over the element's own and `EQ-T-GREE-SLIM24` stated (43, 21). It needed `rotation=deg(90)`.

**And then the case itself turned out to be fiction.** `EQ-T-GREE-SLIM24` was an explicit
"REPRESENTATIVE PLACEHOLDER … TODO verify datasheet"; the only real 43 3/8" cabinet matching
it was Gree's discontinued low-static `DUCT24HP230V1AD`, which tops out at 589 cfm against
the 750 cfm this whole duct system is sized to. So the packing this check so carefully graded
was a fit for a machine that does not exist, and the 4 7/8" slivers it left either side were
what kept `DU-S-HP-SOUTH` riserless for a fortnight. The real `EQ-T-GREE-DUC24`
(44 1/2 x 29 11/16 x 11 13/16, 0.8" ESP) needed a new box, `SF-S-HP1` in `RM-S-STUDY2`'s
ceiling; it needed no `rotation`, because the type now stated the cabinet the way it was
installed.

**And the verified type was itself wrong — `EQ-T-GREE-FLEXX-ULTRA-24-AH`/`-OD` replaced it.**
The DUC24/VIR24 record's own `source=` claimed 577-1030 cfm; the pair's real ceiling is 736 at
0.8" w.c., under the 750 this duct system is sized to. Its 13,500 Btu/h at design was an
interpolation (the read value is 14,606) and either way sat under the zone's 15,164 Btu/h
block load — `mep.heating_capacity` passed only by crediting a strip heater the DUC24 has no
aux-heat terminal to interlock with. Gree's FLEXX Ultra answers all three: 760 cfm at 1.0"
w.c., 21,000 Btu/h read at -15 F (137% of load, unaided), 24 VAC control with a factory heat
kit, HSPF2 9.0 → 10.0, and ENERGY STAR Cold Climate (AHRI 215213329) where the Vireo is not.
It costs depth — 18 1/8" against 11 13/16" — which is what took `SF-S-HP1` from a 17" drop to
21" and its underside to 7'-3". The generalisation of the generalisation: a verified datasheet
number is only as good as the column it was read from, and three of these were read from the
wrong one.

**`SF-S-HP1` moved to `RM-S-NCLOSET`'s ceiling on 2026-09-04, and the whole system reversed
with it.** The air handler is at the north end of the storey now, the trunk runs SOUTH out of
it, `DU-S-HP-SOUTH-RISE` is a collinear reducer at the trunk's south cap instead of a dogleg
round the machine, and `EQ-M-HP1-OD` crossed to the north face on its own pad
(`params/hp1_north_pad.py`).

The passage this replaces described the box as it stood in `RM-S-STUDY2`'s ceiling, arguing
for a seam that no longer binds anything: the seam is now at y=27'-8" for a different reason
(abutting `SF-S-DUCT`'s north end), and the 35"-wide box, topping out at x=21'-5 1/2", never
reaches the old wall face 14" further north.

**The return, `EQ-S-ERV-MIX`, was a mixing box for a few hours, and the register lapped three
things at once before the plenum fix.** A 30 x 16 ceiling grille split its 336 in² face
three ways: 240 in² into `DU-S-HP-RET`, 120 in² into the box, and 120 in² into bare soffit
cavity. `mep.register_duct_match` grades the pair in PLAN only and a boot is unmodelled by
convention here, so it passed anyway. The three plenum dimensions are each a clearance: 12" is
the east lane less the 2" `HANGER_GAP_M` off `DU-S-HP-SUP`; 29 1/2" stops the plenum clear of
the cabinet's south face (overlap it ALONG by an inch and the pair grades ACROSS, where the
gap is 7/8"); 18" fills the 18 1/4" cavity.

**The wall-grille alternative on `W-S-C4B` was investigated in full before being rejected.**
Its studs resolve at y 369 / 384 / 400 / 416 / 424 5/8 with a double top plate at 225..228, so
the one bay overlapping the plenum band (400 3/4..415 1/4) is blocked by the cabinet below
y=408, leaving 7 1/4" of clear bay. Cutting a stud puts that plate over a ~31" span at
~1,600 plf: f ≈ 1,940 psi against Fb ≈ 1,310. Moving the air handler does not help — the wall
is the problem, not the cabinet.

**The trade behind the 7'-3" ceilings**, made with open eyes: `RM-S-NCLOSET` and about 7'-9"
of the north hall drop to 7'-3", and `RM-S-STUDY2` gets ~29 sf back to full height with the
remainder 7" higher.

**The air-side review that followed (2026-09-04) found three more things, and two of them
nothing grades.** The balance itself was sound — 750 leaves the machine and
80+80+80+50+35+175+250 comes off it, exactly — but:
- Four supply grilles (`REG-S-HP-BED1/2/3`, `REG-S-HP-STAIR`) were authored at 8'-0" on the
  strength of a stale comment reading "9'-0" ceiling less the 12" drop". `SF-S-DUCT` actually
  drops 14" and stops at x=21'-5 1/2"; the grilles sit at 22'-6", past the box, and
  `RM-S-BED1/2/3` carry no soffit at all (0.0 sf) — they finish at 8'-11 1/2".
- `REG-S-HP-STAIR` was a short circuit: 50 cfm blown straight down 6'-2" from a 650 cfm
  return in the same room, with the return the *lower* of the two (7'-3" against 8'-0"). Fixed
  as a sidewall grille throwing west across 12'-7" of landing; its 97 1/8" elevation is
  derived from the trunk centreline at 100 1/8" less half a 6" face, not chosen.
- `REG-A-HP-STUDY`'s 100 cfm floor boot at (26'-0", 3'-4") stood inside
  `FURN-A-STUDY-CHAIR2` (x 25'-8"..27'-4", y 3'-3"..5'-1"). Moved to 25'-0", which clears both
  chairs and shortens `DU-S-HP-SOUTH` by a foot, though it is still under the legged 36" table
  — every station on that bay line from x 21'-0" to 27'-3" is under furniture.
- `DU-S-HP-SOUTH` came in at both ends, 19'-4" to 15'-8", the west by most: 6'-8" → 9'-4".
  The old west station's "centred between the two south windows" argument counted only two of
  the room's three (x 4'-0" / 9'-4" / 14'-8"); 9'-4" is the centroid of all three, so one
  terminal washes the whole south wall.
- The riser cannot shortcut up through the joists, which would have given `RM-S-STUDY2` back
  7 ft of 14" box — the obvious saving that doesn't work. 250 cfm wants ~51 in² for Manual
  D's 700 fpm, and the largest hole entertained that close to a bearing wall is ~6 1/2" round
  = 1,090 fpm.

**The return path arithmetic**, in full: at a conventional 3/4" undercut a 30" leaf passes
42 cfm at the 3 Pa ACCA/ASHRAE ceiling, so `RM-S-BED1/2/3` sit at 11 Pa and `RM-A-STUDY` at
17 Pa without the wider undercuts specified. Full arithmetic and the acoustic/carpet costs of
those undercuts: `notes/system1_return_path.md`.

**`SF-S-HP1` ran under `ST-S2A`'s flight in its old `RM-S-STUDY2` siting, and that was allowed
but bounded.** The stair climbs west along `W-S-SS2`, so over the box's north-east corner its
underside sat at or above the box's own 7'-3" face and the two finished as one plane. The
seam was placed at y=7'-6" rather than at the wall face 14" further north specifically to
avoid lapping the stringer ledger.

**`W-M-HS4` pocket door — why the cavity crossing a node is legal.** Wall segmentation at a
tee is an authoring convention (`resolve/framing/pockets.py`), so `D-M-LAUN`'s pocket can
cross node `N-M-E3` where `W-M-LS` tees in without breaking anything: a pocket occupies floor
to 6'-8" only, so the band's plates run continuously over and under it and only its vertical
edge floats. `W-M-HS4` hosted nothing when this was built, which is the only reason a 4'-0"
pocket was possible there at all.

## Basement

- **THE SLABS WERE THINNED, and the psi grade is stated per use.** The
  basement slab went 3" -> 2" XPS at **>=25 psi** (R-16.1 -> R-11.1 whole-assembly, against
  an owner target of R-10; still PASSes `code.energy_prescriptive`'s R-10 slab row), and the
  detached garage slab 3" -> **1" at 40 psi** — 40 because that is the one slab in the house
  carrying VEHICLE wheel loads, and a loaded wheel is a contact patch, not a distributed
  floor load. `RM-GARAGE` is `conditioned=False`, so nothing grades it and every number
  there is an owner choice. Three things follow:
  - **The psi grade is NOT PRICED.** `library/materials.py` has one `xps` tag with no
    compressive field, and `prices.toml` keys XPS on THICKNESS alone — so the 40 psi board
    and the 25 psi board carry one rate here and do not in the yard (40 psi runs ~20-35%
    over). Fixing that properly means a psi-bearing material tag, not another price key.
  - **XPS IS THICKNESS-QUALIFIED IN `prices.toml`, AND IT HAD TO BE.**
    `envelope_layers` qualifies its price key on `thickness_in` (`cli/prices.py`), and the
    file carried only the bare `"xps"` key — so 1", 2" and 3" board all priced at one $/SF
    blend, which made any change of foam THICKNESS cost exactly $0 in the estimate. A cost
    model that cannot see a design decision is not decision-useful. The three qualified rows
    are DERIVED from the researched blend ($0.372-0.744 per inch-SF) with labour held flat
    across thicknesses, which is the conservative reading.
  - The basement's return to 2" retired a `DECLARED_DIVERGENCES` entry in
    `test_catlin_reference_parity.py` — catlin and the reference detail agree again.

- **THE BASEMENT'S WEST HALF WAS REPLANNED ON 2026-09-05, AND WHAT IT BOUGHT IS
  CIRCULATION.** Two doors were formed through 12" interior pours — `D-B-GYM` in `W-B-CS2`
  and `D-B-NE` in `W-B-CN` — and they were the house's only openings through concrete. The
  money was small (a buck-and-blockout allowance, $500-1,200 the pair, and
  `prices.toml`'s `concrete-window-bucks-and-blockouts` row now drives to zero and is kept
  under the `glazed-green-brick` convention). The defect was that from the stair foot the
  only route to the furnace room was **stair → playroom → gym → aisle → workshop →
  furnace**. Both doors are gone. Nothing on the x=18' bearing grid moved and no concrete
  wall moved.
  - **The sauna rotated onto the south (garden) wall**, long axis east-west, and then
    **shrank east to x=8'-10" the same afternoon — see the round-two entry below.** As
    rotated it ran x 4'-8"..18'-0" by y 0'-0"..9'-5", a 12'-2" x 8'-2" clear box against the
    8'-1" x 12'-7" it was, and its south face crossed two substrates with a **2" jog between
    the two liner faces at x=8'-10"** that nothing in the model drew. The `W-B-S1B` segment
    and the `SAUNA_LINER_ON_BASEMENT_8` assembly that carried it both existed for one
    afternoon and are gone. What survives the rotation: the room keeps `WIN-B-SAUNA` and is
    entered **from the gym** through framed `W-B-CS`, a short walk from `D-B-PATIO` and the
    sunken garden, which is what the brief asks the room for.
  - **x=4'-8" was a footing's doing, and it went away with the split.**
    `structural.frost_depth` lowers a footing's local grade by any open excavation within a
    frost depth (42") of the footing SOLID, and a footing follows its wall. At the 5'-0"
    split the plan was drawn at, `FT-B-S1` — the west half — sat **exactly 42.0"** from
    `SL-SG-FLOOR`'s rim: inside the reach by floating point, and outside `SL-SG-FROST-W`'s
    own 42" shielding radius. 4'-8" bought 46" of clear. With the split retired, `FT-B-S1`
    is one strip beside the court again and the wings protect it as they always did.
  - **The bathroom rotated** north-south along the framed stair wall
    (`W-B-STR3B`/`W-B-STR2`), **3'-3 15/16" x 7'-1 1/4" clear** (3'-5 1/4" until round two
    slid its east wall 1 5/16" west). Its **wet wall is `W-B-BA-E`**,
    a new `INT_2X6_STAGGERED_PLUMBING` east partition carrying the shared vent riser at
    (13'-10 11/16", 19'-3") — and `W-B-BA-N`, which used to be the room's only stud cavity, dropped to
    a dry `INT_2X4_PARTITION` when the plumbing left it. `D-B-BATH` swings out into the
    hall, and **on this wall that takes `flip_swing=True`**: the leaf's default side follows
    the host's direction and `W-B-BA-E` runs north-to-south where `W-B-BA-N` ran west-to-east.
  - **A hall** runs west of `W-B-CN2` from the stair foot south — 3'-3 15/16" clear, part of
    `RM-B-STAIR`'s own loop, no new `Room`. It stopped at the y=18' line and crossed into the
    workshop through `O-B-HALL`, a cased opening in `W-B-CW2B`; **on 2026-09-07 it runs the
    rest of the way to the sauna's north wall** and both of those are gone (next bullet).
  - **THE HALL REACHED THE SAUNA WALL, 2026-09-07 — and it retired the replan's "accepted
    consequence".** That consequence read: the playroom is reached only via the gym
    (stair → hall → workshop → gym → `D-B-PLAY`), and the workshop is the through-route from
    the stair to the gym. Running the hall south from y=18' to y=10' on the **same
    x=13'-10 11/16" well-partition centreline** `W-B-BA-E` and `W-B-WELL` already stand on
    buys three things for the length of one partition, `W-B-HALL-W`:
    - **`D-B-GYM` lands on the hall**, not on the workshop — same uid, same position, same
      32" leaf, retyped to `DT-INT-SWING32-GLAZED`. Circulation is
      stair → hall → gym → `D-B-PLAY`, one room shorter. The glazing is not decoration: the
      hall has no window and the gym's south daylight is the only light it can borrow.
      **It stays 32"** — `W-B-CS3` offers 42 3/16" of framed run and a 36" RO leaves 3/16"
      for two jamb packs.
    - **The workshop is a room, not a corridor**, with `D-B-SHOP` — 3'-0", in `W-B-HALL-W`,
      `flip_swing=True` so the leaf goes west into the shop, hinged at the north jamb. Its
      RO centres on `D-B-GYM`'s at y=12'-3 7/16" so the equipment path is straight through.
    - **The equipment route is the hall**: 3'-0" at `D-B-FURN` (widened, position unmoved —
      it is still pinned west by `PR-B-ERV-COND`) and at `D-B-SHOP`, off a 3'-5 1/16" flight.
    - **`W-B-CW2B` and `O-B-HALL` are deleted.** The note on that wall said it *had* to exist
      or the workshop and stair loops would merge into one room. True, and now deliberate:
      the merge IS the hall. `RM-B-STAIR` goes 114.8 → 147.7 sf and keeps one seed.
    - **`W-B-SA-N` splits at `N-B-HALL-S`**; `W-B-SA-N2` is the east 4'-1 5/16", and
      `WP-B-SAUNA-SPLASH`'s second span re-datums onto it at 9 5/16".
    - **`W-M-CLN2` now stacks on nothing, and that is authored.** `W-B-CW2B` was the only
      wall under it; what is left below is `W-B-CW2`, which overlaps its x 13'-4"..18'-0" run
      by 6 11/16" — short of the 2'-0" minimum, so there is one candidate count of ZERO and
      no `integrity.stack_ambiguous` to arm (the `W-M-STRW2` precedent). The load goes into
      the deck instead: two `JoistReinforcement` blocking entries in `params/main_deck.py` at
      x=14'-6"/16'-9", `at` y=**217"** rather than 216" because `at` snaps to the nearest
      joist line and 216" is exactly equidistant from 208" and 224". They must stay LAST in
      `_WEST_FLOOR_REINFORCEMENT`.
    - **The hall inherited the workshop's service ceiling, and that is the one thing the
      change actually cost.** `RM-B-WORKSHOP` is UTILITY, which is in
      `EXPOSED_SERVICE_OCCUPANCIES`, so nothing graded a pipe in its air. `RM-B-STAIR` is
      not, and `mep.run_in_finished_volume` (3" tolerance) called three runs the moment the
      hall grew: `DU-B-ERV-R-GYM` at 8.4", `PR-B-SAUNA-VENT` at 10.7" and `PR-B-HW-SAUNA` at
      3.8". The first two are not reroutable — the gym register is east of the x=18' bearing
      line and the ERV is west of the hall, so ANY route between them crosses it — so they
      are boxed out by **`SF-B-HALL`**, a full-width bulkhead at the hall's south dead end
      (x 170.0725"..212.615", y 123.8125"..133.4375", underside 85 15/16" storey-relative,
      7'-1 15/16" clear). The third was a modelling artefact worth fixing rather than boxing:
      `PR-B-HW-SAUNA` was **stacked 1 3/16" under `PR-B-CW-SAUNA`** on the same x=17'-4"
      line, which is not how a supply pair gets hung. They are side by side now — x=17'-4"
      and 17'-3", both at 7'-10 5/8" — and both clear at 2.55". There is no elevation pair
      that fixes a stacked one: two 1/2" lines need 5/8" of separation and the band between
      the ceiling and the 3" limit is 3" deep.
    - **Lighting and outlets.** Three more `ED-T-LT-CAN3` on `CKT-LT-BACKUP` at x=190",
      y=19'-6"/15'-0"/11'-6" — 27 VA against the ~52 VA of ALWAYS_ON headroom the withdrawn
      play-room cove was measured against, so `cycle_48h.sustains_always_on` holds
      (`test_backup_calc.py`). The middle one is at 15'-0" and not the ladder's 15'-6"
      because `PR-B-HW-SAUNA` crosses there 2 9/16" below the ceiling and a recessed trim
      wants that plane. `ED-B-WORKSHOP-SW` moves onto `W-B-HALL-W`'s workshop face 5" north
      of `D-B-SHOP`'s north jamb — **the hinge side, and the only side**: the latch jamb has
      5 5/8" of wall to `W-B-SA-N2` and no box fits in it. `ED-B-HALL-RC1` is new, on
      `CKT-RC-BSMT` at y=16': NEC 210.52(H) wants it and `electrical.receptacle_spacing`
      walks {BEDROOM, LIVING, KITCHEN, DINING, OFFICE} only, so nothing will ever ask.
  - **Two things the replan cost that are worth knowing before the next edit.** S-100's
    ARCH D scale went **3/16" → 1/8"** — one new foundation assembly is one more row in the
    FOUNDATION WALL SCHEDULE, that column already carried all three schedules (the sheet has
    no width left to open a fourth with), and the scene passed the 3/16" height by 0.18".
    **Round two handed the scale back** by deleting that assembly, and the 0.18" of margin
    is still all there is: the next `FoundationWall` assembly tag anywhere in this house
    steps ARCH D down again.
    And `test_upper_storey_studs_stand_over_studs` went 112/247 → 124/255, all of it two
    walls: `W-M-C1` (the x=18' line has three basement segments under it now and `stacks_on`
    names one, so `W-B-CS3`'s studs are invisible to the metric though they share its layout
    line) and `W-M-CLN2` (forced onto `W-B-CW2B`, which restarts its module 8" off because
    `INT_2X4_PARTITION` is deliberately not on the interior grid). **`W-M-CLN2` came back off
    that stack on 2026-09-07 when `W-B-CW2B` was deleted** — it stacks on nothing now, and
    `test_catlin_contract_m3.py` moved with it.
  - **`ED-B-GYM-RC1`/`RC2` were on the wrong side of the x=18' line and nobody noticed.**
    They were authored 1" WEST of `W-B-CS`'s west face — inside the sauna, a 120V
    convenience receptacle in a 190 °F room — and `electrical.receptacle_spacing` accepts a
    device within 0.5 m of a room's clear face **regardless of which side it is drawn on**,
    so the gym counted them and nothing said so. Both are on the gym face now, and there are
    three: the line is broken by two doors, and NEC 210.52(A)(2) measures wall space between
    doorways. `ED-B-GYM-RC8` stands in the 15" of `W-B-CS3` north of `D-B-GYM`, because
    everything past `N-B-C1` is `W-B-CS2`'s pour.

- **ROUND TWO, THE SAME DAY: one substrate under the sauna, one plane beside the stair, and
  a closet in the dead space.** The replan above fixed the circulation and left three things
  that read wrong on a drawing. All three had one answer.
  - **The sauna's west wall moved from x=4'-8" to x=8'-10", onto `N-B-S1`.** ~8'-3 15/16" x
    8'-3 11/16" clear, and its south face is now **one plane on `W-B-S2`'s garden curb** —
    the 2" jog is gone, `W-B-S1B` is deleted, `SAUNA_LINER_ON_BASEMENT_8` is unregistered,
    `FT-B-S1` is one unsplit strip and `structural.frost_depth` still passes. The workshop's
    west bay took the four feet: 3'-8 3/16" → **7'-10 3/16"** clear, and
    `ED-B-WORKSHOP-PANEL1` went back to its centre. The 8'-6" two-tier bench does not fit an
    8'-4" room whose north wall gives up 3'-0" to the shower pan, so
    `FURN-SAUNA-BENCH-2T-60` was minted beside it in `library/`; the heater and its junction
    box crossed to the **south-east corner**, the only stretch of south liner clear of the
    window, the benches and the door. **`EQ-T-SAUNA-HEATER`'s 9 kW was always sized for this
    room** — the "~513 cf" in `electrical.py` matched the pre-rotation box and the shrunk one
    (519 cf), not the 745 cf the rotation grew it to.
  - **`W-B-BA-E` slid 1 5/16" west onto the stair well's partition centreline** at
    `inch(166.6875)`. Two nearly-collinear planes an inch and a third apart became one, and
    everything that references `N-B-BA-NE`/`N-B-BA-SE` rode along. The wet-wall risers did
    NOT — they are absolute coordinates in `mep_venting.py`, `mep_supply.py` and
    `mep_supply_devices.py` — and neither did `ED-B-BATH-SW`, which stood 1 5/16" inside the
    studs until `test_wall_mounted_devices_resolve_against_a_wall_face` caught it. **No
    `haus check` rule grades a wall device's depth.**
  - **`W-B-WELL` gives the well partition faces, not framing.**
    `resolve/stairs/u_split.py` already GENERATES the 2x4 plates and studs between the two
    flights — the plan this was written from said it emitted nothing, and the first build
    answered with twelve `structural.member_interference` FAILs. So
    `STAIRWELL_PARTITION_4H`'s structure layer carries **no `FramingSpec`**, which
    `framing/solver.frames_as_members` reads as monolithic — so the wall lands in
    `[wall_structure]` billing 0.47 cy of "placed spf", and `prices.toml` prices it at
    **zero** and says why. Its thickness must stay locked to
    `resolve/stairs/common._WELL_PARTITION_THICKNESS_M` (4 1/2"): `INT_2X4_PARTITION`'s
    4 3/4" pushes 1/8" into each inner stringer.
  - **`RM-B-UNDERSTAIR`, 17.5 sf that nobody could reach** — *superseded by round three
    below, which deleted `W-B-CL-N` and the room with it.* The volume under the arriving
    flight was inside `RM-B-STAIR`'s polygon, so the model called it floor. `W-B-WELL` closes
    the east side, `W-B-CL-N` the north (**47" tall, not the 52" the stringer allows — the
    upper landing's ledger is the lower obstruction and it starts at 47 5/8"**), and
    `D-B-CLOSET` opens it west into the furnace room. `RM-B-STAIR`'s seed had to move out of
    the new partition's footprint.
    - **Do not author `Room.ceiling` here and do not put a `Soffit` under the flight.** The
      real head rakes 96.7" → 54.8" and no field says that; `_clear_head` reads decks and
      soffits, a stringer is neither, so `clear_height_m` resolves to the main-floor deck and
      passes R305.1.1 honestly. An authored 53" ceiling would be taken verbatim and FAIL.
    - `DT-INT-CLOSET24` is **2'-0" x 6'-0"** and the far jamb is why: at y=28'-4" there is
      76.5" of head, a 6'-8" leaf plus header wants 82", a 6'-0" one wants 74".
    - `W-B-STR3` was retyped to `STAIRWALL_INT_2X6_BRG_UNDERSTAIR` — 5/8" Type X in
      place of the 3/4" stair plywood, per R302.7. **That cost the exposed-plywood stair face
      on this segment** (a `Wall` carries one leaf) and moved `FO-M-STAIR`'s west edge to
      `ft(10, 3.25)`, exactly as that opening's own comment predicted it would have to.
  - **The engine changed twice.** `illumination._gypsum_finishes` matched the literal
    `"gyp"`, which **no layer in this catalog contains** — every gypsum layer is `gwb*` on
    `gwb`/`gwb-x` — so `code.R302_7_under_stair_protection` could never verify protection,
    only fail or find nothing to protect. And `topology._through_pair` chose a four-way
    node's through run **alphabetically**, which at `N-B-ESS-SE` picked the two partitions
    over the bearing wall running through and reported a mixed-assembly junction; it prefers
    a continuous bearing pair now, tag order as the tie-break.
  - **`D-B-FURN` is at `ft(3, 3)` and the condensate line fixed it there.** A UI drag had put
    it at 1'-6 1/16" — `from_node` offsets the NEAR JAMB — across `CD-B-SPA`,
    `CD-B-DATA-SHOP` and `PR-B-ERV-COND`. None of the three can move (a `ConduitRun` has one
    flat elevation and `CD-B-SPA`'s south end is sleeve-pinned at -4'-0"), so the door did.
    The king stud's west face lands 0.475" off the condensate pipe: **any move of that door
    east re-opens the clash.**
  - **Two rooms had no light at all and nothing graded it.** `RM-B-SAUNA` and the new closet
    now have one each (`ED-T-LT-SAUNA-VT`, a 125 °C sauna-listed fixture with its switch
    OUTSIDE the hot room; `ED-T-LT-SPOT-SW`, integral-switch). There is **no NEC 210.70 check
    in this engine** — a missing lighting outlet is invisible to `haus check`.
  - **`EQ-B-HP2-GYM` was 5 1/2" into the ceiling and the UI drag did not do it.** Mounted at
    7'-6" AFF, a 10 53/64" cabinet tops out at 100 13/16" in a room `code.R305_ceiling_height`
    measures at 95 3/8". It is at 6'-6" now. The drag itself was kept: it is on `W-B-S3-FR`
    throwing north across the room's 18' depth, which is the better wall.
  - **`LR-B-STAIR-RAIL` still lies under the flight rather than along it** — one `Mount`
    elevation for a whole `LightRun`, measured off the slab, so it cannot rake. Pre-existing,
    now visible because the volume it runs through is a named closet. `PA-B-BFP-SAUNA`'s
    `room=` said `RM-B-SAUNA` and never was (it is 6'-7" north of the sauna); fixed.
  - **Still unresolved and not this change's:** `CD-B-SPA`'s east leg at y=1'-0", 61" over
    the slab, appears to run **through** the rotated sauna.

- **ROUND THREE, THE SAME DAY: the under-stair closet loses its north wall, and the sauna
  takes 7" off the workshop.** Two owner calls, and between them they say something about
  this model worth keeping: **both changes are bounded by things no check grades.**
  - **`W-B-CL-N` is deleted and `RM-B-UNDERSTAIR` with it.** The storage under the arriving
    flight runs the full length of it now and on under the landing deck, instead of stopping
    at y=31'-0". `W-B-WELL` keeps the east side and its north end is free — `open_end=True`
    on `N-B-CL-NE`, which is what `integrity.wall_loop_open` is for and the only honest way
    to say a partition dies in the middle of a stair well.
    - **The `Room` could not survive it.** With nothing closing the north side both seeds
      land in ONE face, and `RM-B-STAIR` and `RM-B-UNDERSTAIR` each resolved the **same
      114.8 sf polygon** — the whole shaft counted twice in every area, finish and load that
      walks rooms, at 0 FAIL. So the closet gives up its label and keeps its use:
      `D-B-CLOSET` still opens it to the furnace room, `ED-B-CLOSET-LT` still lights it (its
      `room=` is `RM-B-STAIR` now, the fixture did not move), and `EQ-B-HP2-GYM`'s
      `zone_rooms` drops the tag.
    - **`W-B-STR3` is NOT retyped back.** `code.R302_7_under_stair_protection` now passes on
      "no enclosed usable space" — the check keys on a room's occupancy and `STAIR` is not in
      `_UNDER_STAIR_OCCUPANCIES` — but the reason for the Type X did not go away with the
      label. The code hook went quiet; the wall stays as built.
  - **`W-B-SA-N` went north 9'-5" → 10'-0", and `D-B-GYM` is what stops it there.** The room
    is 8'-3 15/16" x **8'-10 11/16"** clear, 555 cf against `EQ-T-SAUNA-HEATER`'s 600 cf
    rating — 45 cf of margin, so a deeper sauna from here is a bigger heater and a bigger
    circuit, not a free change. The workshop's north strip pays for it: 8'-7" → 8'-0".
    - **The binding constraint is an opening, and nothing grades it.** The east end of this
      wall lands on `W-B-CS3`, the 4'-5" of framed x=18' line between the sauna and the
      y=13'-10" pour, and `D-B-GYM`'s rough opening starts at y=10'-11 7/16". At 10'-0" the
      wall's north face leaves 7 5/8" for the jamb pack. At **10'-6" the two overlap
      outright and `haus check` says nothing** — no rule tests a tee wall landing beside an
      opening. The coupling runs both ways: if `D-B-GYM` goes back south, this wall follows.
      **It is also why `D-B-GYM` stayed 32" when the hall reached it on 2026-09-07**: 42 3/16"
      of framed run less two jamb packs is a 32" leaf, and a 36" one would spend the 7 5/8"
      this bullet is about.
    - **Everything dimensioned off the north liner moved 7" with it**, and none of it would
      have been reported: `FURN-B-SAUNA-BENCH-E`, `FX-B-SAUNA-SH` (the pan stays in its
      corner), `FX-B-SAUNA-FD`, both `SP-B-SAUNA-*` sleeves, `PR-B-SAUNA-DRAIN`'s first
      three vertices, `PR-B-SAUNA-FD-DROP`, both condensate air gaps and
      `PR-B-SAUNA-VENT`'s riser. `D-B-SAUNA` is `from_node("N-B-SA-NE", …)` and DID report:
      it rode the node north and `structural.door_framing_module` FAILed on the stud module
      within the same build. Its offset grew 7" to hold the leaf still.
  - **A third bench, on the south liner: `FURN-B-SAUNA-BENCH-SW`, and the heater moved to
    let it grow.** `EQ-B-SAUNA-HTR` stood in the middle of the south liner and left
    3'-7 15/16" of it, which is a 2'-6" bench. On the **east liner** — `rotation=deg(270)`,
    18" face to the wall, 16" depth into the room, 2" off both liners as before — it leaves
    4'-7 15/16" and the bench is **4'-0"**. `ED-B-SAUNA-JB` came east with it and butts its
    west face; `REG-B-SUP3` and `DU-B-ERV-R-SAUNA-SUP`'s east leg followed, because "over
    the stones" is a position, not a label.
    - **What stops the bench is `ED-B-SAUNA-JB`**, not the wall: the box's base is at 18"
      AFF, exactly the bench top, so a 4'-6" carcass would reach under it and put a fixed
      seat in front of a live 9 kW junction box. 4'-0" leaves 7 15/16" to the box and
      1'-1 15/16" to the heater. Raising the box over the bench would buy that back and is
      the wrong trade in a room that stratifies.
    - **The heater is deliberately not pushed north against `D-B-SAUNA`'s jamb**, which
      would free another 1'-6" of bench and put a 30" stove at the doorway. Nothing grades
      any of this: `EquipmentType` carries no `clearances` and no rule tests a placeable
      against a wall device or an equipment footprint against a door approach.
    - `FURN-SAUNA-BENCH-48` was minted in `library/` and priced in `prices.toml` — **an
      unpriced type is silently dropped from the takeoff.**

- **Four basement assemblies, and every split is a condition, not a preference.** Two
  independent axes cross here: what covers the exterior XPS, and how thick the pour is.
  All four compose off `library/`'s `FOUNDATION_WALL_{8,12}_XPS4_CORE` plus a house-local
  skin layer, so the core cannot drift between them.
  - *The skin, and there is only one.* `BASEMENT_12`/`_8` cover the
    XPS with a 1/8" `foundation-coating-acrylic` banded from 6" below grade to the top of
    the wall — a trowel-applied acrylic coat over reinforcing mesh, authored as a
    `Layer.extent` off the `GRADE` datum, so a grade lift grows it without an edit here.
    **It was a 1/2" `foundation-protection-panel` until 2026-09-04, and the swap bought a
    verdict, not a saving.** A butted board's installed permeance is its joints, nothing in
    that product class publishes an ASTM E96 number for it, and
    `building_science.condensation` reported UNKNOWN on both assemblies for as long as it
    was authored; a seamless lamina is gradeable and both walls now PASS. Installed, the
    coating bills slightly *above* the board. The board and its price row survive as the
    named alternate, so the revert is one `material_ref` edit.
    `W-B-S1`/`W-B-S4` are on `BASEMENT_8`, which
    retired the stucco: their exposure genuinely *is* a grade band (6'-4" of fill,
    2'-2 9/16" out of the ground), so they get ~37 SF of coating. The court segments in
    between get **no skin at all** — their XPS is inside `W-B-BRICK`'s ventilated cavity,
    with no UV and no impact on it, and 273.7 SF of parge was buying a plasterer's
    mobilization to finish a surface nobody sees. `BASEMENT_8_GARDEN` and
    `_GARDEN_PARGE` survive unreferenced in `plan/assemblies.py`, documented, so the revert
    is two `assembly=` edits.
  - *The pour.* 12" used to be earned wherever a cast concrete deck landed on the
    wall top beside the sill plate and needed a bearing seat inboard of it. After the
    basement-ceiling overhaul the only cast deck left is `SL-M-DECK`, which bears on the
    east wall and the centre line — so `W-B-E1/E2` stay `BASEMENT_12` and the other
    nine segments are 8" carrying `#5 @ 41" o.c.` vertical steel, which IRC Table
    R404.1.2(8) requires at 8" where 12" reads NR (it was `#6 @ 48"` before the flat
    bearing seat made the pour exactly 8'-0", which is the table's 8'-unsupported row
    rather than the 10' row a 9'-4" wall rounds up to). **The "12" is earned only where a cast
    deck lands beside the sill plate" rule is now obsolete** — with a flat seat nothing
    competes for wall-top width, and the 12" segments that are left are left as built for
    reasons written on the walls themselves, not for bearing. `W-B-STR` and `W-B-STR3` are
    2x6 bearing stud walls — `unbalanced_fill`
    is `ft(0)` on both, and what they carry is joists and a wall stack, which is a
    stud-wall job on a footing. `W-B-CS` is the same — it
    carries wood on both faces — leaving `W-B-CS2`/`W-B-CN`/`W-B-CN2` as the interior pour
    that remains. Drop that string on any of the nine and
    `structural.foundation_unbalanced_fill` FAILs, correctly.
  The banded walls carry 4.175" outboard of the concrete face over the band and 4.05" below
  it; the court walls carry 4.05" throughout. `N-B-BRICK-W`/`-E`'s stand-off is
  `inch(-4.05)`, on the court walls' bare XPS, and the veneer's clear cavity is **1-1/2"**
  (IRC R703.8.4 wants 1" minimum). **It was `inch(-4.55)` until 2026-09-04 and that was a
  bug**: the node was struck on the old parge's finished face and did not follow the parge
  when it was deleted, so a 1/2" void sat between the XPS and the veneer's 1" `air-gap`
  layer with no layer describing it — the model said 1" where the build had 1-1/2". Moving
  the node onto the foam and growing `air-gap` to 1-1/2" cancels at the gap's outboard face,
  so the wythe, the arched reveals and the veneer's footing all stay exactly where they
  were. That is why thinning the *wall* did not move the brick, and why changing a
  *skin* thickness moves the cavity rather than the wythe. Because
  the walls align on `face("concrete-ext")`, the 4" came off the INSIDE face: the furnace
  room and the workshop each gained 4" of clear (the model still reports the old number —
  `clear_face` is inset from the wall axis, which did not move). See
  `notes/basement_to_framed_wall_detail.md`.

## Decks and the garage

- **Deck-plank-as-sheet conversion, and the breezeway's part in it (RETIRED structure).**
  As of 2026-09-03, `FS-SG-PORCH` (composite, 3bf2f48), `FS-SG-DECK` (aluminium), and
  `FS-BW-FLOOR` (composite, at the time a deck joist field) all carried their boards as
  `subfloor=DeckLayer(...)`; the `SL-SG-PORCH`, `SL-SG-DECK`, and `SL-BW-DECK` slabs that
  used to stand beside the framing were deleted, and all three planks moved from billing by
  the cubic yard out of `[concrete]` to the square foot in `[sheet_goods]`. The balcony
  converted term for term because its joists cantilever 6" and the deleted slab's outline
  *was* that cantilever.
  - **The breezeway needed an engine change, and it was one field.** At that time its plank
    oversailed the joist rim 2 3/4" at each end onto `D-M-ENTRY`'s and `D-G-SERVICE`'s
    thresholds, and a floor system's sheet used to be exactly its joist field
    (`resolve/floors.py`) — so converting it either FAILED `code.R311_3_exterior_landing` on
    both doors or laid a joist through the (now-retired) roof posts `PT-BW-1..4`.
    `JoistSpec.cantilever*` could not help: a bearing line is a span boundary, so a
    cantilever is a joist-AXIS quantity and this oversail was on the perpendicular one.
    `FloorSystem.subfloor_outline` — an authored sheet polygon that replaces the derived
    corners and touches nothing else (not the joist solver, not `deck_voids`, not the
    elevations) — is the fix, and it survives the rewrite as a general engine capability
    (see keep8.md).
  - **Bound it.** `structural.subfloor_oversail` grades an authored sheet against
    `[framing] bearing_plan_tolerance_in` (8"), because past that the uplift pass finds
    neither a derived tie nor a hanger and FAILs every member under the deck, reported
    nowhere near the deck. The old breezeway's worst edge was 3 5/8".
  - **The take-off had to move with it.** `sheet_goods_takeoff` computed area from the
    bounding box of `floor.members`, so a wider sheet would have drawn wide, passed R311.3,
    and still billed the joist field. The subfloor now reads `deck_outline`; `ceiling_below`
    keeps the framed extent, because a ceiling is nailed to the joists.
  - This entire narrative — `PT-BW-1..4`, `SL-BW-DECK`, and the breezeway-specific numbers
    above — describes the pre-rewrite breezeway structure. It is retired: the north entry is
    now a foundation bridge (`FS-BW-FLOOR`, `FS-BW-GARAGE`), beams `BM-BW-*`, a stair
    `ST-BW-ENTRY`, a railing `RL-BW-ENTRY`, and a slat screen `SC-BW-WEST`. See
    `notes/north_entry_structure.md` for the current structure; a proper rewrite of this log
    section is coming in a separate pass.
- **The garage wall rebuild, 2026-09 — four decisions moved at once.** `GARAGE_WALL_2X6` was
  2x6 @16" o.c. with empty bays and 1.5" Zip-R doing the whole thermal job (owner's choice),
  clad in 26 ga concealed nail-strip. It became 2x6 @24" o.c. / 2" ccSPF in the bays / 5/8"
  CDX / 7/8" corrugated exposed-fastener panel, and the trusses went to 24" o.c. with the
  studs (`GARAGE_ROOF`, framing factor 0.09 -> 0.0625 = 1.5/24; the two must move together or
  the R-38 blow is under-credited). Everything here is an owner choice, not a code minimum:
  `RM-GARAGE` is `conditioned=False`, exempt from `code.energy_prescriptive`,
  `building_science.condensation`, and the MN prescriptive table alike.
  - **The card read R-14.3 and was lying.** With no `CavityFill`, `analysis._layer_rsi`
    billed the 5.5" STRUCTURE layer as SOLID SPF over the full area; the honest whole-wall
    was R-7-8. It reads R-13.2 now — lower on the card, roughly double in the building. The
    shape of the whole change: ccSPF spends about a third of what the cladding and spacing
    save, and buys a real air seal.
  - There is no WRB, and that is a decision (IRC R703.2's exception for an unconditioned
    detached accessory building). The ccSPF is the air/water/vapour plane —
    `TR-CATLIN-GARAGE-OPENING` names `stud-cavity` for all four controls, not the house's
    `sheathing-ext`/`spray-foam-ext` tuple — so bucks before foam, as on the house. The CDX
    carries no `control` set for exactly this reason: bare sheathing claiming those layers
    would be a WRB nobody is buying.
  - There is no furring, and the corrugation IS the rainscreen — 7/8" of continuous open
    flute behind every sheet, more free area than the 3/8" 1x4 the wall carried before. What
    makes that drain rather than pond is the closures, ~192 LF, vented at the base and solid
    at the head. Priced as `[allowances] envelope-garage-corrugated-closure-strips`, not
    through `bug_screen:GARAGE_WALL_2X6` (which reads a rainscreen cavity depth out of the
    layer stack and therefore reads 0 SF). Do not "activate" that row by authoring a 7/8"
    airgap layer — it would add 7/8" on top of the 7/8" cladding and move both wall faces.
  - The whole 24'x24' moved 3/8" north, `GARAGE_GAP_FT` 4.6875 -> 4.71875, always for one
    reason: 3/8" more panel standing proud of the node line is 3/8" less breezeway slot. The
    uncut 4'-0" polycarbonate panel (RETIRED — see the breezeway rewrite note above) kept its
    1/2" reveal at the time. The Zip-R -> CDX swap moved nothing in that chain — the wall's
    `alignment` puts whichever sheathing it carries on the node line — so do not recess the
    sheathing to hold the cladding face still, which re-opens the old rain shelf.
  - No 16" zone at the overhead door, and it was investigated. `W-G-E` is NONBEARING (the
    ridge runs E-W; the trusses bear on `W-G-S`/`W-G-N`) and the 16'-0" opening is carried by
    its own 2-ply 14" LVL on jamb packs the solver sizes from the opening. Field studs beside
    a nonbearing opening carry nothing extra. It would also not be a local override:
    `FramingSpec.spacing` lives on the ASSEMBLY, so a closer-spaced zone is a second assembly
    tag, a second `prices.toml` row, a second `condition_gates` key, and fresh section
    goldens.
  - Three openings re-stationed onto the 24" grid, and one deliberately did not. `WIN-G-N1`
    1'-5" -> 2'-5" and `WIN-G-S1` 21'-5" -> 20'-5" (a 14" RO wants a BAY CENTRE, 12 + 24n
    along `W-G-W`); `SERVICE_DOOR_OFFSET` 5'-10" -> 6'-6", which puts that leaf's centre on
    8'-0" — the same station as `D-M-ENTRY`, so at the time the two doors the breezeway
    spanned were CONCENTRIC and `_GLAZING_CENTER_X` (RETIRED) was simply their shared centre.
    `D-G-OVERHEAD` stays at 4'-0" and its advisory stays suppressed: every legal station
    moves the ICF grade beam and makes the two brick piers 5'-0" and 3'-0".
  - The 16 garage-wall `S-5-N` seam clamps are gone (`plan/wind_clamps.py`), the exact
    precedent of the 48 house-wall `S-5-S` clamps — an N clamp closes on a nail strip's bulb,
    and a corrugated panel has no seam. Corner uplift is carried by the panel's own 640 face
    screws. The `S-5-N` price row stays: the garage ROOF is still nail strip and still
    carries 12.
  - `GARAGE_WALL_WIND_CLAMPS` survives as an empty list, and `standing-seam-nailstrip-26` and
    `zip-r` keep their price rows at 0 — the `glazed-green-brick` convention. The revert is
    layer material refs plus re-authoring sixteen constructors.
- **The overhead door orientation flip, 2026-09-07.** The garage sat with its overhead door
  facing east on `W-G-E` for a lot to the SOUTH with a driveway round the east side — a
  premise that survived in two prose comments and no `Driveway` element, and that had never
  agreed with `plan/site.py`'s own `SetbackSpec(edge=2, "FRONT")` on the NORTH edge or with
  the water service entering from the north. The ridge turned with it (`ridge_direction` "x"
  -> "y", bearing on `W-G-E`/`W-G-W`), the stem gap moved east -> north, both eaves now carry
  gutters and a leader, and the six south-slope snow guards are gone because south is a rake
  and nothing discharges over `GL-BW-ROOF` (RETIRED canopy) any more. The footprint did not
  rotate — the garage is square, the windows stayed on `W-G-W` and `D-G-SERVICE` on `W-G-S`.
  Then it moved 6'-0" east onto the house ridge: garage x 6'-0"..30'-0", centre x=18'-0".
  `GARAGE_X_WEST`/`GARAGE_X_EAST` are published beside the two y lines and the stem, the
  slab, and the landing all derive from them.
  - **The move cost the concentric doors, and the (now-retired) breezeway absorbed it,
    2026-09-09.** `D-G-SERVICE` had to travel with its wall — the move is in 24" steps (a 36"
    RO must land on a stud line measured from the wall's own start) and at x=8'-0" its king
    stud would stand 5/8" inside the corner pack, which owns the first 3 5/8" of wall. Its
    centre became x=10'-0". `D-M-ENTRY` could not follow: its east jamb was already 6" west
    of `N-M-N2` at x=10'-0", the tee where `W-M-STRW`'s bearing stack lands and runs to the
    footings, and a 36" RO cannot straddle it. So the two doors the breezeway spanned were
    2'-0" out of line, so the breezeway straddled them instead of sitting on a shared centre
    that no longer existed: `_EW_FT = 4.5` (RETIRED constant) centred on their midpoint at
    x=9'-0", glazing x 6'-9"..11'-3" (RETIRED glazing). `code.R311_3_exterior_landing` passed
    both doors (entry 90.9%, service 91.7%, bar 85%). 4'-6" was the smallest half-foot module
    clear of the 4'-1 15/32" bare tangent. The instruction not to answer any of this by moving
    the garage back still holds for the current structure.
    - **It cost the brief's E-W term and a heat pump move.** The "8 x 4 x 4" brief was retired
      in E-W and the (now-retired) roof sheet was cut to 4'-6" instead of being an exact half
      sheet (the N-S 4'-0" was still the literal uncut sheet in the 4'-0 1/2" slot). And
      `EQ-M-HP3-OD` moved 2'-4" east, to x 12'-4"..15'-2 3/8": its west face had been at
      x=10'-0", exactly the old east glazing line, and cabinet and glass interpenetrated by
      5/16" at 0 FAIL — nothing grades an Equipment against a deck or a clearance envelope,
      so only hand measurement found it. It now clears the glass by 12 11/16" (Gree's 12"
      lesser-side minimum). `SL-M-HP3PAD` went with it to x 12'-1"..15'-5", which pushed the
      front walk's west edge to x=15'-9" (a zero-clearance cabinet would still have reached
      it, at 14'-4 11/16"). These final positions are current and carry forward past the
      breezeway retirement (see keep8.md).
    - **HP3's y-axis clearances are still short, and that is a deferred owner decision.** Gree
      publishes 12" air inlet and 6'-6" discharge; this position has 8" and 25 11/16". The
      48 1/2" slot can never give more than 33 11/16" front+back to a 14 51/64"-deep cabinet,
      at any position or rotation — the fix is re-siting system 3's outdoor unit out of the
      slot. `params/hp3_pad.py::_BACK_CLEAR_IN` carries the measured numbers and is the only
      record; no check will ever mention it.
  - `EQ-M-HP1-OD` moved 6'-6" east and `ED-M-HP1-DISC` went to the WEST of it. That cabinet's
    whole siting argument is that it stands east of the garage's plan extent; the garage
    moved under it. It now oversails the house's NE corner by 3" to keep its 14" clearance to
    the garage's east gutter face (31'-10" to 36'-0" is 50"; cabinet plus clearance is 53"),
    and its disconnect is a 6 1/2" can in the 14" slot with no NEC 110.26 working space and
    nothing grading it. Both are hard bounds: that machine cannot move further either way on
    this face. `EQ-M-HP3-OD` did not move — it sits south of the garage's roof edge, in the
    48 1/2" slot, which is its documented condition.
  - Aligning `ST-G-SERVICE` under its own landing fixed a standing FAIL. The flight ran
    x 5'..8' under a landing at 6'-6"..9'-6", a stale offset nothing graded;
    `code.R312_1_guard_height`'s unguarded-edge FAIL on `SL-G-STEP-0` went with the fix.
  - `ED-G-SW` / `ED-G-EXT-SW` sit inside `D-G-SERVICE`'s rough opening — a pre-existing defect
    translated faithfully rather than silently re-sited. Nothing grades a wall device against
    an opening; the fix is ~12'-0"/12'-6", east of the real east jamb.
  - `notes/garage_orientation_lot.md` is the whole before/after and the revert recipe,
    including that a genuine south-lot revert must also flip `SetbackSpec` edges 0 and 2,
    which this change deliberately did not touch.
- **The garage wainscot deletion, 2026-09-03.** The garage had no wainscot before this
  entry's date range either — its base skin is the 24" band on the ICF stem, uniform on all
  four walls, and that is a deletion rather than a substitution. A 4'-0" wainscot had stood
  on the two 4'-0" strips of east wall flanking the overhead door, wrapped 4'-0" around each
  of the SE/NE corners — four `W-G-WAIN-*` FoundationWalls on `GARAGE_METAL_WAINSCOT`, six
  local nodes, four cap flashings at a round 4'-0". It was Glen-Gery Columbia Roman Maximus
  soldier brick until 2026-09-02 and PVDF-painted aluminium sheet after. All of it is gone,
  along with `GARAGE_BRICK_WAINSCOT`, `GARAGE_ICF_6_BRICKLEDGE`, `off-white-brick`, and both
  `_BRICKLEDGE` dicts in `params/foundations.py` — deleted outright, not kept unreferenced,
  so git history is the revert path and not a one-line `assembly=` swap.
  - **Nothing replaced it, and the piers lost nothing.** `GARAGE_ICF_6`'s `coil-gap` +
    `coil-ext` band — 2" below grade to the stem top, on a 1/4" vented standoff — always ran
    BEHIND the wainscot, deliberately: that wainscot was a vented, drained rainscreen open at
    its base, so water reached the foam behind it by design. Those two east segments
    therefore keep exactly the protection the other three walls always had. 156.2 SF is
    unchanged by the deletion, which is the check that this was a saving and not a transfer:
    the wainscot's own `[wall_structure]` row (65 SF, $1,430-2,730) and 15.5 LF of cap simply
    left the bill.
  - **The stock sheet stayed 48" x 120" and the gauge stayed 0.040-0.050", and that is the one
    counter-intuitive call here.** With only a ~24" band left, 24" trim coil is the obvious
    buy. It is the wrong one: a 48" sheet rips into exactly two 24" bands with no waste, so
    the heavier architectural sheet costs nothing per SF over coil, and the band is still the
    plow-and-shovel splash zone the gauge was chosen for. There is no backer — the sheet
    spans its fixings and never touches the foam — so dent resistance is gauge and fixing
    spacing, nothing else. Second best, only on a supply failure: 0.024" heavy-gauge 24" trim
    coil, the thickest that product line reaches. Never 0.019", which takes a permanent
    dimple from a shovel corner.
  - **The stem-top Z is new scope, not a leftover of the wainscot.** The band's top and the
    corrugated panel's base both land on the stem top, and until this change that junction
    was modelled by nothing at all — it lived in a `source=` string. `STEM_TOP_Z_FLASHING`
    (`plan/storeys/garage.py`) is six `DRIP_FLASHING` runs, 76.5 LF, broken at both stem gaps
    (the 16'-0" overhead door and the 3'-0" service door, where the stem drops to a grade
    beam and there is no band to flash). `DRIP_FLASHING` is a bent angle — flat leg plus
    outboard turn-down — which is what a Z is; `WRB_COUNTERFLASHING` is a flat pan and would
    not do. The inboard kick-out leg cannot be a second bend on the same run and is carried in
    prose, exactly as the deleted caps carried it.
  - **The Z is authored as one counter-clockwise loop and every run is `back_side="left"`.**
    Walked south W->E, east S->N, north E->W, west N->S, each wall's left-hand normal
    (`normal(d) = (-dy, dx)`) points inboard, so the turn-down hangs outboard on all six.
    Nothing grades `back_side` — get one direction wrong and the drip points at the wall at 0
    FAIL. `test_garage_base_skin_is_the_stem_band_alone_and_its_top_is_flashed` pins it;
    confirm it in the viewer too.
  - **The Z exposed an engine bug and the fix is in `emit/draw/detail_components/eave.py`.**
    `_water_anchor` picked the eave's drip-edge label by plan proximity with no elevation
    filter, so a `flashing` solid 114" below the eave, on the same wall line, was averaged
    into the anchor — the garage's `detail_wall_roof` leader for "drip edge lies ON the top
    deck" pointed at the ground. It now takes only candidates within `_ANCHOR_Z_WINDOW_IN`
    (36") of where the label is expected to land. Generous on purpose: the authored piece and
    the schematic fallback genuinely sit at different elevations, and the window rejects
    another STOREY's flashing, not a few inches of lap order.
  - **Aluminium over aluminium, and no check grades it.** `corrugated-panel-26` above the band
    is 26 ga PVDF-coated steel; the band and the Z are aluminium. They must never lap
    metal-to-metal — sealant or EPDM between, the Z's upper leg behind the corrugated — and
    aluminium must never touch concrete or fresh mortar (alkali strips the oxide film). In a
    salted splash zone that contact line is where the detail fails. Naming
    `aluminum-flat-pvdf` on the Z rather than the envelope's `metal-dark-exterior` steel trim
    coil is the whole enforcement, and it keeps band and Z one colour and one coil order.
  - `OVERHEAD_DOOR_OFFSET`'s 4'-0" lost its defence and is now an open question. The
    `structural.door_framing_module:D-G-OVERHEAD` suppression in `preferences.toml` was
    carried on the wainscot: moving the door 12" would have made its two piers 5'-0" and
    3'-0", a visibly asymmetric facade bought with one stud. That argument is gone — the base
    band is uniform and does not care where the door sits. What remains is a cost of moving,
    not a reason not to: the offset gaps the ICF stem into a grade beam, so the gap nodes,
    two stem segments, their footings, two Z break stations, and a water-service sleeve all
    travel with it. Left suppressed so the report stays clean while it is decided. Do not
    quietly re-decide it either way.
  - `W-GF-S3` / `W-GF-N2` are a kept fossil. Those stem splits exist only because the brick
    returns once needed ledged stem under them. Both halves are plain `GARAGE_ICF_6` and
    nothing stands on them, but un-splitting would churn four wall uids and four footing uids
    to express no geometric change; the census in `test_wall_and_room_counts_by_storey` and
    `test_wall_structure_takeoff` pins the count so a cleanup cannot do it by accident.
- **The garage colour history, and the green machinery kept alive.** `W-G-E` briefly carried
  Western States Metal Roofing "Classic Green"
  (westernstatesmetalroofing.com/classic-green) nail-strip and was reverted; all four garage
  walls are `GARAGE_WALL_2X6` in white today — and that white is `corrugated-panel-26`, not
  the nail strip this paragraph's machinery was built for. The machinery is unchanged and
  still works; the green revert would now be a `corrugated-panel-26`-based colourway, or a
  return to nail strip first. `standing-seam-nailstrip-26-green` is still in the catalog,
  referenced by nothing — the same convention `glazed-green-brick` is kept under, so going
  green again is a one-line `layer_materials=` change rather than a re-derivation. Two things
  were built to make it work, both still live:
  - `Wall.layer_materials` (`model/refs.py::LayerMaterial`) swaps the material of ONE named
    layer on ONE wall. Before it, a colour change *was* a duplicate Assembly restating one
    `material_ref` — and a duplicate assembly tag is also a new `prices.toml` row, a new
    `condition_gates` key, and fresh section goldens, all to say "same wall, different paint".
    It is a TUPLE of constructors, not a mapping, because `Wall` is a movable element and the
    editable dialect has no mapping literal. Appearance only — thickness, function, framing
    and banding all stay the assembly's; a layer that needs a different thickness is a
    different wall and wants its own assembly. A typo in either half is otherwise silent (the
    wall just resolves unchanged), so `integrity.wall_layer_material` FAILs on an unknown
    layer name or material tag.
  - Both renderers hardcoded the coil white and had to stop. Every metal skin authors
    `color="#6b7076"` — that is the drawing hatch tone, not the paint — so the viewer and the
    GLB emitter both painted seam cladding 0xE8E8E2 unconditionally, and no panel could ever
    state its own colour. Both now consult the material's declared `finish` first (the
    mechanism `metal-dark-exterior` already used): `classic-green-seam` -> `#2f5233` in
    `FINISH_BASE` (ui/src/nordic/palette.ts) and `_FINISH_BASE` (emit/gltf/palette.py), kept
    in step BY HAND. The green material keeps "seam" in its tag so it still gets the seam
    normal map, and keeps `skin_family="standing-seam"` so the roof edge still reads the
    garage as one continuous skin.
  - The gable triangle above a wall comes along for free: `resolve/roof_edge.py` builds the
    wall->roof closure from the host wall's own layers, so an override picks up in the
    closure with nothing authored for it.
- **The garage roof edge colour history.** The garage wore "Copper Penny" PVDF metallic here
  from 2026-08-26 to 2026-09-08, and was the one place on the site departing from the house's
  single exterior dark. It no longer is: the garage's own accents are now the Classic Green
  door wall and the Charcoal Gray stem band. `metal-copper-penny` is kept and referenced by
  nothing, the way `metal-fascia-regal-blue` is, so coming back is a one-word swap in the two
  places (fascia + `edge_trim_material`).
  - The fascia's SUBSTRATE changed with the 2026-08-26 colour, and that half must not be
    reverted. The weather face was 5/4 cellular PVC; a dark trim colour on cellular PVC is
    the classic failure — PVC's thermal movement forces a solar-reflective vinyl-safe coating
    and trim makers cap the LRV outright, and `#1c1f24` is further past that cap than the
    metallic was. Formed metal over a wood nailer has neither problem and is the ordinary
    detail on a metal-roofed building.
  - Tag-keyed in the two renderer palettes, not keyed by a declared `finish`: a fascia and a
    ridge cap are framed MEMBERS, and `memberColor` is handed the palette and no catalog, so
    a material's authored `color` is invisible to it and only the tag lookup reaches.
    `_FINISH_BASE` (`emit/gltf/palette.py`) and `FINISH_BASE` (`ui/src/nordic/palette.ts`),
    kept in step by hand. `metal-dark-exterior` already had its rows, so this swap added
    none — and the `metal-copper-penny` rows stay while that material does.
  - Neither tag contains "seam", deliberately: both renderers key the ribbed standing-seam
    finish off that substring and this is flat formed stock. Trim carries no `skin_family`
    either — that field is about the wall/roof continuous-skin reading at a zero-overhang
    edge, and trim is not skin.
- **The garage ICF stem's second face, added 2026-09-02.** `notes/garage_wall_detail_side.md`
  has always asked for protective covering on both sides of the exposed EPS; only the inside
  was built until this date.
  - Inside, `code.R316_4`: a 5/8" gypsum layer banded from the `GRADE` datum up — the 2.5" of
    interior EPS had stood bare from the slab to the stem top, ~176 SF of foam plastic facing
    an occupied space. It continues the board `GARAGE_WALL_2X6` already lines with, so it is
    the same detail, not a new one.
  - Outside, new: `coil-gap` + `coil-ext`, a PVDF-painted aluminium band
    (`aluminum-flat-pvdf`) from 2" below grade to the stem top, on a 1/4" vented standoff,
    fixed with 316 stainless gasketed screws into the ICF webs. 156.2 SF, $781-1,562. Since
    2026-09-03 this is the garage's entire base skin (see the no-wainscot entry above), and
    its top is flashed by `STEM_TOP_Z_FLASHING`.
  - **The standoff is not optional and it is not about drainage.** A painted sheet is 0
    perms. Laid flat on `eps-ext` it is a Class I retarder on the COLD side of the stem, and
    `building_science.condensation` immediately found a January dew point at the concrete —
    a crossing against a monthly MEAN, i.e. a plane that runs wet for weeks. That was a real
    FAIL on the first build of this change, not a modelling artifact. The 1/4" gap restores
    the outward drying path. Delete it and the FAIL comes straight back.
  - It ran BEHIND the east wainscot too, deliberately: that wainscot was a vented, drained
    rainscreen open at its base, so water reached the foam behind it by design and that foam
    needed the same continuous protection as the foam beside it. The wainscot was a wear
    layer over this band, never a substitute for it — which is exactly why deleting it on
    2026-09-03 took nothing away from the two east piers, and why 156.2 SF did not move.
  - Both bands are banded, not full height: below grade there is no interior to separate
    anything from, and the exterior band's 2" of bury seals its own termination rather than
    leaving a lip for water to stand on. The band pushes the stem's exterior face 0.30" east,
    which nicks the "stem and wood wall are coplanar on the outside" promise — inside
    `_axis_match`'s 1/2" and physically true. Do not recess the EPS to hold the face still;
    that re-opens the old rain shelf.

## Exterior colour, balcony and veneer

- **Why `#1c1f24` and not the `#3a3d40` it started at.** An authored colour is
  an albedo. The viewer lights with 0.8 hemisphere + 0.9 key + 0.6 IBL, over
  unit irradiance, so a dark surface leaves the shader well above its albedo —
  `#3a3d40` arrived near `#525252` and read as generic grey.
- A gutter/downspout could only say "I am category gutter" until
  `ResolvedSolid.material` was added, which is why the eaves stayed mill grey
  while the rakes went black.
- The balcony's guards used to be `POST_WHITE_PAINT` too, until it was split
  off as `RAILING_DARK_METAL`. It was six pillars and eight knee braces until
  2026-09-03; the four corners are cast concrete now and the braces are gone
  (see the balcony structure passage below).

- **The balcony's structure: four cast columns, two wood posts, three glulam
  beams** (2026-09-03; `houses/catlin/notes/balcony_moment_columns.md` is the
  design, and it supersedes `superseded/balcony_lateral_bracing_design.md`).
  - The eight 2x6 knee braces and two E-W brace rails the corner columns
    replaced are deleted outright. This was the longest-running open item in
    `plans/TODO.md`, and it closed against metal rather than for concrete: no
    catalog metal moment base survived the search. The only stock base with a
    published base moment is Simpson's MPB66Z, for a WOOD post, and its
    wet-service cap (2,610 lb-ft, ESR-3050 Table A) is *below* the 2,502 lb-ft
    R301.5 guard case on one column before any wind.
  - **12", not 10", and cover is the whole reason.** ACI 318-19 §20.5.1.3's
    1-1/2" is a code minimum, not a hundred-year number; MnDOT uses 2.5-3" in
    the same deicing regime. 2" of cover on a #5 cage inside #3 ties needs a
    6-5/8" bar circle, which needs 12". Centred on a 12" wall the round is
    flush with both faces — no ledge to pond on, and BF3's 3" east leader keeps
    1-1/2" clear.
  - Exposure is class F3 + C2, not F2, and the mix must not be reused from the
    retired 20" column: deicing salt below and planter runoff above is external
    chloride on a freeze-thaw member. Bar is hot-dip galvanized — the owner's
    call over epoxy (delaminates) and stainless (4-6x cost, and an austenitic
    thermal coefficient that fights the concrete).
  - **The beam seat is cast to line, with no grout island**, because an exposed
    non-shrink grout island is a 10-20 year element, not air-entrained and
    sitting at the wettest point on the column. The shim pack (`SS316-SHIM-35`,
    priced at `CN-SG-STDF-*`) is a modelled, priced part since 2026-09-03, one
    per wood-on-concrete beam seat. `PIER_CONCRETE_12` still carries a grout
    island at `PT-SG-COL`; aligning it is a follow-up, not an oversight.
  - **The two centre pillars stay wood 6x6**, bearing directly on the porch
    framing through a ~9"-square plank cut-out — Trex says plainly that
    composite decking bears nothing, and the cut has to clear a 5-1/2" post
    plus the `L50Z` angle legs beside it — on a 3-ply bearing pack (the
    authored joist plus two full-length sisters) with squash blocks at the beam
    line. `PT-SG-BF2` moved north onto the deck, which is what let `PT-SG-FCOL`
    shrink from a 20" round to a 12" one, and then the last 3" onto the front
    beam axis itself, where it doubles as the `RL-SG-PORCH` south-leg guard
    post at x 18'-0". A `CCQ46SDS2.5` column cap closes the uplift path at each
    — a 3-1/2" beam on a 6x6 is the unequal-width case the PC6Z is not
    published for.
  - The porch joists crossing both beams since 2026-09-03 takes both bearing
    planes at `PT-SG-BF2` out of NDS §3.10.4's END case (d/c 0.76 -> 0.35)
    without moving the pillar. The composite sheet followed the framing, so the
    plank now ends 2-3/4" outboard of `RL-SG-PORCH`'s guard line — a deliberate
    setback, since the guard blocking sits in the bay north of the beam and a
    guard on the new edge would bolt into cantilevered tips.
  - **No standoff post base at either pillar.** The `ABU66SS` went on
    2026-09-03: every published value an ABU has is measured bearing on
    concrete through a 5/8" cast-in anchor (ESR-1622 §5.6 puts even that anchor
    outside its own scope), and the 1" standoff was cited to IRC R317.1.4,
    which governs wood on concrete. Neither pillar has stood on concrete since.
    Five elements for two pillars, ~$25 the lot, 1,408 lbf at BR2 and 1,033 lbf
    at BF2 wet-derated against a hand-worked ~285 lb net uplift. An inverted
    `CCQ4.62-5.50SDS` cap stood here for one day and could not be built: at BF2
    the rim, joist tips, beam axis and post centre are one line, and at BR2 the
    squash blocks occupy the bays its side plates would hang in — and it was
    ~20x the demand. The bearing that replaced the ABU is graded, oracled in
    `notes/centre_pillar_bearing.md` — at `plies=1` and against a DRY Fc-perp
    both pillars were over, at 0 FAIL, until that calculation existed.
  - **DF-L, not SPF, and the species is a connector requirement.** ESR-2604
    §3.2.2, ESR-2330 §3.2.2, ESR-2105 §3.5.2 and ESR-3096 §3.2.2 are the same
    sentence — SG >= 0.50 at MC <= 19%. At SPF 0.42 nothing at either end of
    these two posts had a published value — the `CCQ46SDS2.5` cap on top
    included. DF-L at 0.50 fixes both ends for ~$180-450 of lumber. The clause
    being family-wide is why that call survived four base parts in one day:
    only the citation moves. Both reports' §4.1 send wet service to the NDS
    factor, so C_M 0.70 is already inside the recorded values — do not derate
    again. A `DTT2Z` stood here for part of 2026-09-03 and was superseded
    unbuilt — one-sided, no lateral value, and it did not touch the species
    problem.
  - The three beams are engineered items (`deck_beam/BM-SG-BL*`) because
    R507.5(1) publishes sawn plies only.
  - **The front row did not move when the corners changed.** A 12" column's top
    runs 3-1/4" past the beam end there, and that is a concrete top with a wash
    and a drip lip, not the exposed end grain the 2-3/4" offset was written
    for. Re-solving the row would move the deck edge, the fascia, the drip, the
    gutter and `BALCONY_FRONT_AXIS_Y_FT`.
  - **The fallback, written down:** New Castle Steel's stock HDG 6x6x3/16" post
    with a welded base plate (~$458/10') if forming and caging four tall tubes
    proves too much labour. Its base still needs a fabricated saddle on a 12"
    wall top, which is a shop drawing nobody has made.

- **Guards.** Williams Architectural Products, ICC-ES ESR-3485, 42" black
  (Menards; Eagan MN, the Ultralox factory), with Fortress Al13 Home as the
  alternate — the same alloys and coating as Trex Signature at ~$30-45/LF
  material against $72-98.
  - `RL-SG-PORCH`'s west and east legs run along 12" concrete wall tops, which
    take ESR-3485's four 1/4" x 3" baseplate anchors directly and buy no
    bracket kit. Its south leg has no wall under it, so those posts bolt
    through the plank into blocking in the joist bay north of the beam — never
    through `TR-SG-CAP-FRW/FRE` and its butyl, which is the dielectric between
    an aluminium cap and copper-treated framing.
  - `RL-SG-BALCONY` staying fascia-mounted is a roofing decision:
    `FS-SG-DECK`'s aluminium plank is the porch roof and has carried no
    penetrations since the heat pumps went to grade; surface posts would put
    ~36 holes through the only waterproof plane here. Brackets through-bolt the
    PVC fascia and the 2x8 rim per Ultralox's own instructions (four 5/16" x 4"
    bolts, nuts on the rim's inside face), landing in rim blocking authored in
    `FS-SG-DECK.reinforcements`.

- **The veneer stands on a grade beam, not on the house footing** (2026-09-05).
  `W-B-BRICK` is 129 SF of masonry exposed on both faces at the bottom of an
  open court, so it runs at outdoor temperature all winter. It used to bear on
  `FT-B-BRICK`, a 10"x5" plinth cast on `FT-B-S2`/`FT-B-S3`'s own projecting
  toe — putting that cold in series with the footings whose underside is level
  with the court floor and whose only frost protection is the R403.3 wings. It
  now bears on `W-SG-BRKBM`, a 12" x 17-3/4" beam spanning the court's 19'-0"
  between `W-SG-W1` and `W-SG-E1`. Basis: `notes/sunken_garden_veneer_beam.md`.
  - **The break was ordered twice and placed never, and that is the lesson.**
    `FT-B-BRICK` carried `assembly="FOOTING_FPSF_20"`, whose 2" `xps-bearing`
    layer *did* bill — 16.0 SF through `takeoff/envelope.py`'s
    `_LAYERED_SOLID_SCOPES` — while `FB-B-BRICK` dug a 2" `undercut` for that
    same 2" of space which billed as 0.1 cy of washed crushed stone, with
    `cast_foam_in_aggregate=True` beside it carrying no thickness, no material
    and no R-value. A `Footing` resolves to ONE extruded blob, so neither claim
    ever had a polygon. One order of foam and one order of stone for one gap
    sat at 0 FAIL for a fortnight.
  - **A better bed was not available — the geometry says so.** The wythe sits
    inside the footings' 10" toe, and any separate pour bearing on soil has to
    stay outside the 45° line off their bearing edge, at y = -12.76". That
    pushes the brick to -15.95" and opens an 11.9" slot to the house: a
    19-ft-long, 11.5-ft-deep snow trap with no way to reach the bottom. A beam
    that spans needs no soil bearing, so that constraint does not apply — which
    is the whole reason this shape was chosen and the reason the gap can be 6".
  - **It reinforces nothing, and do not let anyone say it does.** The tempting
    story is that a beam closing the court's north end props the side walls. It
    does not: `W-SG-W1`/`E1` are already restrained top and bottom (porch beams
    pocketed in HUCQ410-SDS hangers, the deck diaphragm, the garden slab at
    their feet) and PASS `structural.foundation_unbalanced_fill` on the last
    published row of IRC Table R404.1.2(8). This beam earns its ~1.05 cy on the
    thermal argument alone.
  - **The 2" board is a `Layer`, on a wall, and the face is asserted.** A
    wall's layers resolve to real polygons on real faces in a stated order,
    which a Footing's do not — that is the whole reason it moved here. The face
    is not reliable on its own: the beam is its own open wall-graph chain, so
    it takes the fallback outward sign, and sign x layer-order decides whether
    the board builds north or south. Authored the wrong way the concrete lands
    hard against `FT-B-S2/S3` and looks perfect in every view.
  - **`FT-B-S2`/`FT-B-S3` gave up 2" of south toe, by `offset` and not by
    width.** The strips keep all 20" of bearing and simply sit further under
    the house; since they carry a 7-1/4" curb and three storeys of framed wall
    standing at y = 0..+9-1/2", moving toward the load *reduces* the
    eccentricity they already had.
  - **The wythe moved 4-1/2" south and the reveals did not move at all.** On
    2026-09-04 the 6" was taken entirely in `BASEMENT_BRICK_VENEER`'s `air-gap`
    thickness with the nodes held still; on 2026-09-05 the EPS moved the
    backup's face and `N-B-BRICK-W`/`-E` followed it to -8.05" while `air-gap`
    came down to 2", the opposite bookkeeping. Either way the invariant is the
    brick's own y, which the beam fixes. The reveals are safe under both
    because `AO-B-BRICK-WIN`/`-DOOR` are placed `from_node` along the wall axis
    — a y-move leaves them concentric and `integrity.reveal_concentric` still
    passes. `N-B-BRICK-E` did have to come in from 28'-0" to 27'-6": 28'-0" is
    `W-SG-E1`'s axis, and the move walked the wythe's east 6" *inside* that
    retaining wall — 4.25 SF of brick billed into solid concrete, at 0 FAIL,
    because nothing grades masonry against a pour.
  - **2" of EPS went into that cavity 2026-09-05, and it is on the backup wall,
    not in `BASEMENT_BRICK_VENEER`.** The 6" is fixed — the beam's north face
    cannot pass -10" — so the only question was how to split it, and it is now
    2" EPS + 4" of drained air. The foam is a layer of
    `_GARDEN_CURB_CORE`/`_GARDEN_FRAMED_OUTBOARD`, the two outboard tuples the
    four backup walls share and nothing else uses, so the blast radius is
    exactly those four walls. Putting it in the veneer's own stack would have
    been worse than untidy: `code.energy_prescriptive` grades one assembly at a
    time, so foam parked there earns the wall no R and the check keeps reading
    R-37.0. It reads R-45.0 now (R-58.4 sauna, R-29.3/R-43.3 curbs), each
    exactly +8.0.
    - **The energy is a rounding error and is not the reason.** The backup was
      already R-37/R-50 framed, not the R-21.5 a `BASEMENT_8` reading suggests
      — about $2/year at 124.9 SF. The $250-487 buys a *designable anchor*: the
      beam already forced a ~10" brick-to-stud reach, and 6" of that was
      unbraced air. Now 6" is foam and 4" is cavity. The anchor is still
      engineered — see the note, §5.1.
    - **EPS and not more XPS, deliberately.** The stack is already 4" XPS plus
      damp-proofing at ~0.13 perm and can only dry inward; EPS at ~2 perms over
      2" adds R without adding a second vapour shutter and lets the wall dry
      out into the vented cavity. It also beats XPS in long-term ground
      contact, and this run's foot is in a court that can pond.
    - **`IRC R703.15`'s 4" foam limit does not govern here, and the trap is
      real**, because `plans/cost-options.md` §6 kills a different foam swap in
      this house on exactly that limit — and this wall now carries 6". R703.15
      covers cladding whose dead weight hangs on a fastener in bending, and it
      explicitly excepts anchored masonry veneer to R703.8. This wythe stands
      on the beam; its anchors take wind only.
    - **2" and not 4", and nothing graded either bound.** 4" was built first
      and sat at 0 FAIL. It was wrong twice over. (a) `EXT_2X6` stands on this
      wall's seat with its cladding face at -7.25"; 4" put the basement's face
      at -8.05", 0.8" proud of the wall above, turning the Z-flashing lap that
      the basement skin is supposed to tuck under into an upward-facing ledge.
      2" lands at -6.05", a 1.2" setback. (b) `resolve/stacking.py` fires
      `stack_width_change` on |total thickness| against a 0.5" `_TOL`, so any
      thickness added here reshuffles which junctions get a detail drawn: 4"
      pushed `GARDEN_CURB_6` inside the tolerance and 3" pushed
      `GARDEN_FRAMED_2X6` inside it, each silently deleting a live junction's
      drawing. 2" is the only purely additive value — every HEAD golden
      survives and the two sauna walls gain the detail they now warrant. The
      golden SET drift is what caught this; no check did.
    - **`eps:2.0` is a new price key, for labour not thickness.** 2" is what
      the bare `eps` row was already researched at, so the material rate
      carries across untouched; what does not is open-wall CI labour. This
      board is set in a slot behind a wythe laid after it, held by the veneer
      anchors, its bottom course worked out of an 11-1/2 ft hole: $1.10-2.10.
  - **Do not anchor the wythe to `W-SG-W1`/`W-SG-E1` to cut the anchor count.**
    It cannot carry: unreinforced 3-5/8" brick spanning 18'-8" horizontally
    runs ~400 psi of flexural tension at 20 psf against ~50 psi allowable
    parallel to the bed joints. And it is the wrong detail regardless — brick
    grows, concrete shrinks, and BIA TN 18 puts ~0.15" of movement across that
    run. Those two ends want a soft joint, not an anchor.
  - **Two engine bugs fell out of this and are fixed.**
    `local_grade_elevation_m` sheltered a footing whose CENTROID sat inside the
    heated slab, so trimming a perimeter toe 2" walked it over the line and
    turned 3/4" of frost cover into a reported 83" — whole-polygon containment
    now. And `_exterior_shells_by_storey` filled every interior ring, which was
    invisible only while the court was a *disjoint* polygon; the beam connects
    it to the house, and 610 sf of open sky became basement floor area until
    holes over an open excavation floor were kept.


## Sunken garden court

**First pass — the court went back to one flush surface (2026-09-05).** It had been dropped
7 1/4" on 2026-09-03 as a flood step, which put four elevations into a 19' court: the court
itself, a 23.7 sf stoop a riser above it, `W-SG-ARCH` standing 3 3/4" proud as a mow strip,
and the veneer beam. The owner called it back to one flush plane.

- The trade taken: water now climbs 7 1/4" to the threshold instead of 14 1/2" — 321 cf of
  ponding over the court rather than 643, against ~191 cf of direct 100-year/24-hour rain, so
  about 1.7x where it had been 3.4x with the drywell assumed fully failed. The case to watch
  is not summer rain but snowmelt over a frozen grate, where `DRW-SG-MAIN` contributes
  nothing by definition — the 7 1/4" curb is the entire dam.
- 7 1/4" was not a preference; it was the ceiling. R311.3.2 allows one riser of 7 3/4"
  (`_MAX_NONREQUIRED_STEP_DOWN`) at a non-required, inward-swinging door. A lower court needs
  a landing — which is exactly what `SL-SG-STOOP` had been, for two days, before it was
  retired (uid `SGS503AAAA`, never reuse). `code.R311_3_exterior_landing` now reads
  "D-B-PATIO lands on SL-SG-FLOOR, 7.3" below the threshold".
- `W-SG-ARCH` did not move: it carries Pu 62,051 lb and closes the walls' loop before
  backfill, and dropping its top to the rim underside gives phi-Pn 60,712, d/c 1.02. Its top
  and `_rim_underside_in` are now the same expression, so the rim bears on it, and
  `FO-SG-ARCH` retired along with the stoop. `W-SG-BRKBM`, by contrast, carries nothing
  structural — it is the veneer's thermal foundation only.
- Two values had been pinned rather than left to follow the court up; one was un-pinned.
  - `_pier_bell_bottom_ft` was pinned for a day, then made derived again (owner's call, later
    the same day, 2026-09-05): `(_court_top_in - frost_depth_in) / 12`, giving both bells 42"
    of cover rather than the 49 1/4" the pin had left them with. The pin's argument — saving
    0.1 cy of shaft against re-opening every hand-worked term in
    `notes/sunken_garden_piers.md` — was real but was overruled: a pinned literal is exactly
    what silently drifts the next time the court moves, which is how it reached 49 1/4" in the
    first place. The note and both pier test modules were reworked; shafts came back to
    128.1875", what they had been before the flood step.
  - `_veneer_beam_bottom` had been the garden slab's underside — flush, that gives a 10 1/2"
    beam over a 19'-0" span, under ACI 318-19 Table 9.3.1.1's L/16 = 14 1/4" minimum depth.
    It was held instead at -120 3/16" so the graded 17 3/4" section survives; the beam is
    simply buried. This one stays held.
- Frost got quietly better: `FT-B-S2`/`S3`'s cover below `SL-SG-FLOOR` went from 1" to 8". The
  R403.3 wings still do the work, but no longer on a fingernail.
- `plan/site.py`'s two garden spot elevations had to follow, -9'-8 11/16" → -9'-1 7/16". The
  comment beside them claiming "nothing structural reads spot elevations — they are drafting
  annotation" was false: `engineering/balcony_wind.ground_below_ft` takes the lowest spot on
  the site, and these two win it, setting `z` for the balcony columns (h 23.3' → 22.7', q_h
  18.8 → 18.6 psf, wind base moment 1,395 → 1,385 lb-ft). Safe direction, no column resized,
  and the 2,502 lb-ft guard case governs regardless — but `notes/balcony_moment_columns.md`
  and `test_pier_calcs`'s schedule both had to move with it.
- A latent bug in `space_summary` surfaced here: the interior-hole filter added 2026-09-04
  kept a ring only if it `contains(floor.representative_point())` — one point per floor — so
  a floor spanning several rings anchored only one. `W-SG-ARCH` splits the court into two
  bays, both `SL-SG-FLOOR`, and the retired stoop happened to anchor the second bay;
  retiring it dropped 281 sf of open court onto the basement's gross area. Fixed by making it
  an area-overlap test, which asks the question actually meant.

**Second pass — the porch side joins the lift, the run caps at 36" above grade, and the well
ties to the footings that feed it (2026-09-05, after the re-levelling above).** Four separate
defects, all found by looking at the model rather than by any check — none had been a FAIL,
and none could have been.

- `SPEC.retaining_top_ft` is now derived from grade, `(site_grade_in + 36)/12` = +0'-2". It
  had been +0'-6", i.e. 40" out of the -2'-10" yard. One constant does two jobs, because
  `params/raised_garden.py` reads it through `RETAINING_WALL_TOP_FT` as its apron TOP and
  derives BASE as `TOP - drop_ft`: capping the top at 36" lands the SRW base on -34", site
  grade exactly, where it used to float 4" in the air. Nothing grades a freestanding wall's
  base against the ground plane, so five `W-RG-*` legs had stood on nothing at 0 FAIL while
  the comment beside them claimed "their base is grade".
- `W-SG-W1`/`E1` now bottom on `_wall_bottom` like everything else, and
  `_PORCH_FOOTING_THICKNESS_IN` is gone. They had been held back when the three retaining
  strips rose, to keep IRC Table R404.1.2(8)'s last published row (10'-0") and to stop the
  two 13"-thick footings' undersides moving. Both arguments turned out weaker than they
  looked: 10'-0" is a ceiling, not a target — a shorter braced wall over less fill sits
  further inside the same row, and the check still passes at 9'-1 7/16" — and the frost
  answer at this edge was never cover but ASCE 32 soil replacement, the same 42" of stone
  whatever elevation the footing starts at. Holding them had left the whole under-porch dig
  9" deeper than the identical stack ten feet south, for nothing.
  - `FO-SG-TOE-N-W`/`-N-E` void the rim over them, as `W`/`E`/`S` do over the other three.
  - `FO-SG-TOE-W`/`-E` had been cut to the field's north edge while the footings ran 6" past
    it, leaving each a 4'-0" x 0'-6" tongue of footing under 3 1/2" of rim — 2.0 sf of
    concrete billed twice and cast into itself, at 0 FAIL, because
    `structural.concrete_interference` grades only ISOLATED pours and every `FT-SG-*` carries
    `under=`. The toes are now cut to `_y_ax_mid`. The assertion kept: the net rim polygon's
    intersection with every `FT-SG-*` footprint is 0.000 sf.
- `DRW-SG-MAIN` now sits on the wall beds again, with two lead runs making the tie visible.
  The well's top had been pinned to the deepest bed, correct while every bed shared one
  underside; after the lift it left the five tiles that actually feed it discharging 9" above
  the top of the stone, into undisturbed clay. `drainage.discharge_consistency` resolves the
  tag and never asks where the pipe goes, so it passed anyway. `_SG_DRYWELL_TOP` is now
  `_SG_WALL_BED_BOTTOM`, and `FD-SG-LEAD-W`/`-E` carry the ring across the 3'-0" of open
  ground into the well at that invert — two leads, not seven, because the five wall beds abut
  into one connected body of stone (W1 to W2 at y = -11.0', W2 to S through the corner lap,
  mirrored east). `FB-SG-ARCH` takes none: its bed bottoms 9" below the well and stops 2"
  from the shaft in plan, so it feeds the column through its side and a lead there would run
  uphill.
- The dowels had been above the footing they dowel into: `_dowel_z` read
  `-(basement_depth + 0.75) + footing_thickness/24` — mid-height of a garden footing whose
  underside was -118 7/16", two elevation changes prior. The bars resolved at -112 7/16" with
  the garden footing's top at -117 7/16": three #5 GFRP bars sitting 5" of open air above the
  concrete they were meant to develop into, and a 12" foam block straddling a joint that was
  not there. Nothing grades a `Dowel` against the two footings it names. Now derived off the
  joint instead — mid-way through the 8" face the two footings actually share, with the foam
  block that same 8" so it fills the joint instead of standing proud into the slab bed.
- What it was worth: 2.32 cy of concrete (151.10 → 148.78) and 9" off the whole under-porch
  excavation and the well shaft. Every yard of it had been concrete poured on top of
  something. The engineering all moved the safe way: stem 9.62' → 9.2865', system FS 1.71 →
  1.77, stem flexure 0.72 → 0.65, toe flexure 0.61 → 0.56.
  `notes/sunken_garden_court_free_body.md` §4/§6/§7 were reworked term by term rather than
  recomputed from the engine.

**Third pass — the closure's thermal break was 21" long in an 84" joint (2026-09-05).** The
two porch side walls meet the house only through a 2" XPS board on -6 3/16"..-4 3/16", and
the intent written at `DW-SG-*-STEM` was one continuous board from the house footing's
underside to the top of the porch wall. It was not continuous, in two independent ways that
hid each other, and nothing in the engine grades a thermal break for continuity, so it had
read as a designed detail at 0 FAIL.

- The block had been sized against the wall, not the footing. `_resolve_dowel` derives a foam
  block's length along the joint from the bar row — `max(row_span + 8*dia, 12")` — exactly
  right for the stem block (12", flush with a 12" wall's end face) but wrong for the footing
  block, which separates an 84"-wide strip. Three bars at 8" gave 21", leaving 63" of
  footing-to-footing concrete running from a heated basement footing into a wall standing in
  an open court. `Dowel.foam_length` is new for this: unset, it derives as before, so nothing
  else in the repo moved. The two blocks are deliberately not unified — they are sized
  against different pours.
- Where the board was missing there had been no room for it. `FT-SG-W1`'s 84" north end faces
  `FT-B-S1` over its outer 52" and `FT-B-S2` over its inner 32". S1/S4 took a 6" toe trim on
  2026-09-05 and cleared it by 2 3/16"; S2/S3 kept the 2" `offset` bought for `W-SG-BRKBM`'s
  isolation board and lapped it by 1 13/16" of solid concrete — a plan lap until the porch
  footings rose to the court plane, a real 0.406 sf x 8" volume after. Which strip a given
  inch of that joint faces had been an accident of where `W-B-S1` stops at x = 8'-10"; no
  thermal detail should turn on that. All four south strips are now on one face at -4",
  `_TOE_TRIMMED` is empty and `_SOUTH_TOE_TRIM` is superseded.
- The beam's own board was not weakened by the retreat: it still separates the veneer pour
  from the house pour across 4" of bedding stone in series with the same 2" of XPS, and
  `W-SG-BRKBM` bears nothing on that toe — it spans between the side walls. What the 2" was
  genuinely load-bearing for is the beam's north face at -10", a fact about the beam that did
  not move.
- Frost was re-checked after the trim, because moving a footing north is exactly how a false
  pass gets bought: all four still read "8" below SL-SG-FLOOR" on the R403.3 branch, not the
  ~86" `sheltered_by` answer. `test_the_veneer_beam_isolates_the_house_footing` now pins the
  84" board, the full 8" depth, and a zero plan lap against every house strip — both halves,
  because each had passed on its own while the pair was broken.
- `prices.toml`'s `thermal_break` row was rebased with it: it had priced three ~0.3 SF
  structural bearing pads that no longer exist, and now bills the four closure boards
  (27.6 SF of 2" 40 psi XPS) at $90-210 each. The four are not the same size, so check totals
  against SF rather than count.
- Concrete did not move for any of this — worth knowing before reading a takeoff diff across
  this date: the toe trim is an `offset`, so each strip slides north with its full 20" of
  bearing intact. Measured by ablation against HEAD, every assembly row was identical, total
  149.31 cy either way, with the thermal break the only quantity that changed, 3.43 → 4.60 cf.
  Any concrete delta seen across this date belongs to another change, not this one.

**The veneer's material history (2026-09-04).** `W-B-BRICK` has worn three faces: first a
flat field of `glazed-green-brick` (`#1b4332`); then the Ishtar Gate — a lapis field with
golden-yellow register bands over an unglazed brown plinth; then, since 2026-09-04, the
plinth's own brick run full height. The glaze was dropped. What is on the wall now is
`brown-brick` `#a07c5c`, ordinary ASTM C216 Grade SW face brick, the cheapest face that had
ever been on it and the only one a Twin Cities yard stocks off the shelf.

- The swap also settled a spec conflict: [BIA Tech Note 13](https://www.gobrick.com/media/file/13-ceramic-glazed-brick-exterior-walls.pdf)
  says glazed brick "should not be used in locations where they are likely to be saturated."
  The Ishtar scheme had complied only because the unglazed plinth kept the glaze above the
  splash line. An all-unglazed SW field is unconditionally right for a Minnesota sunken
  court, which is a rain sump with walls.
- `glazed-green-brick`, `glazed-lapis-brick` and `glazed-gold-brick` remain in the catalog,
  referenced by nothing, in case either scheme is wanted again — a material's appearance is
  a three-place change (`Material`, `MasonryStyle` in `ui/src/three/materials.ts`,
  `_FINISH_BASE` in `emit/gltf/palette.py`) and a revert has to find all three. Their
  `prices.toml` rows are commented out rather than removed for the same reason.
- The jitter had to move with the job, and it was the one thing that did. A material's
  appearance is `Material` + `MasonryStyle` + `_FINISH_BASE`, and `#a07c5c` was unchanged in
  all three — it is already authored a step under its target for the albedo reason above,
  and re-darkening it would be a mistake. `BROWN_BRICK_STYLE.jitterHSL` was not unchanged: it
  had been `[0.004, 0.015, 0.04]`, the glazes' near-zero, because the reason for that setting
  was a 28 SF plinth beside a glaze, where the red brick's full variegation read as mixed
  pallets with near-black units through it. The field is now 129 SF with no glaze to
  contrast against, and one flat brown at near-zero reads as a printed sheet. It became
  `[0.008, 0.035, 0.09]` — deliberately intermediate, roughly double a glaze and half of
  `BRICK_STYLE`'s `[0.02, 0.08, 0.16]`, which is the failure mode in the other direction and
  one this material had already been in once. Mortar stayed `#cfc8ba` (tan), the unglazed
  pairing. `haus render` cannot show this and never could: the CLI emitters carry only the
  flat de-jittered `_FINISH_BASE` hex (`emit/gltf/palette.py` annotates `_BROWN_BRICK_BASE` as
  exactly that), and `--view elevation` emits east/west while this wall faces south. Judge it
  in the headless viewer, or compute the recipe's extremes directly: the per-unit jitter is
  `new THREE.Color(base).offsetHSL(±j[0]/2, ±j[1]/2, ±j[2]/2)`, so a five-line node script
  prints the darkest and lightest unit a setting produces.
- The wythe became one layer — no `slot`, no `extent`. It had been five `slot="wythe"`
  regions sharing a single 3 5/8" depth position (without the slot the assembly resolves to
  an 18 1/8" wythe and shoves the wall into the garden). With one region there is nothing to
  co-locate and nothing to band, so it is the ordinary case: a plain full-height STRUCTURE
  layer taking the wall's own base and top. `Layer.slot` remains a live feature that catlin
  no longer exercises — the machinery, and the emitter regression it exists to catch, are now
  guarded on a synthetic fixture in `packages/engine/tests/test_emitter_band_parity.py`.
  Anything that had been true about band heights on the 2 2/3" course, `applyMasonryWallUv`,
  or the upper register riding `D-B-PATIO`'s head line at 88" is history, not a constraint.
- It had to stay a STRUCTURE layer, not CLADDING — the backer is a different wall, so this
  has to be the structure layer or `integrity.assembly_layers` finds none. Same precedent as
  `RETAINING_BLOCK_12`. One BOM row resulted, `BASEMENT_BRICK_VENEER:brown-brick`, 129.2 SF.
- The rate could not carry over, and that is the interesting part of the money. The old
  $15-28/SF was the standard-veneer market taken at its low end because the plinth was 24"
  off the ground — no scaffold. A full 8'-5" field needs scaffold for its upper 6', so it
  became $19-30/SF: $2,455-3,876 against the Ishtar wall's $2,573-5,467. The $19 low sits
  above the $16 the market alone would say, because 129 SF is a minimum-mobilisation masonry
  job and `prices.toml` elsewhere says a mason will not set up scaffold under ~$2,500-4,000.
  The saving is roughly $120-1,590 — real, modest, and never the point.
- Both brick reveals ended up shorter than the openings they front, and the door reveal's
  height became a free variable. `AO-B-BRICK-DOOR` went 88" → 84" → 78" and `AO-B-BRICK-WIN`
  26" → 20", all by eye and all against the gold register at 88" that no longer exists. 78"
  was kept because it still looks right — nothing requires it, and 84" is available if more
  of the door head should be covered. The overlap itself is deliberate: a masonry reveal in
  front of a rectangular hole is meant to overlap it, so the door's head is covered across
  its full width and the sauna window loses its top 6". Neither opening is a daylight or
  egress subject.
- A reveal must stay concentric with the opening it reveals, and for five days one was not.
  `AO-B-BRICK-DOOR` had been authored against `D-B-PATIO`'s position; on 2026-08-30 the door
  moved 6" west off a different node on a different wall and the reveal did not follow.
  `haus check` reported 0 FAIL the whole time, because the two are individually correct and
  nothing compared them. `integrity.reveal_concentric` now grades that — every rough opening
  with a wall standing behind it, against the nearest door or window in that wall, at a 1"
  tolerance — and `test_catlin_contract_m3` pins both pairs.
- Both arched reveals turn a voussoir ring, `ui/src/three/builders/archRing.ts`. Masonry here
  is a texture, so the arch heads had been running bond sliced by a curve; the ring is an
  annulus with polar UVs into that same tile, turning its rectangular bricks into wedges. One
  header deep (3 5/8") and 3/16" proud on every face (the proud offset exposes the skewback
  end caps; at 3/8" each had read as a black shard off the springline). The door's extrados
  crowns at 81 5/8", the window's at 52 5/8". Viewer-only; an exported `.glb` still shows the
  plain spandrel.


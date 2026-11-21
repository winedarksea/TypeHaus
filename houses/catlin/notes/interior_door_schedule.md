# Interior door schedule: function, core, seal, relief and hardware

**Owner decisions, 2026-11-03.** The single place to read what each interior door is. Types
live in `plan/interior_door_types.py` (plus the trimless and bookcase types in
`plan/storeys/main.py`); hardware bills by `DoorType.function` in `prices.toml`
`[allowances]` (`finish-door-hardware-*`), and only `D-B-SHOP`'s keyed set is authored
(`[hardware]`).

**Hardware.** Kwikset Halifax Square, satin nickel 15 (US15 / 619), house-wide; hinges in
the same finish and lot (US15A is antique nickel, a different colour). Schlage Latitude 619
is the fallback. Privacy on every bath and bedroom, passage on every other swing door.
Pockets take retail parts: a pocket privacy lock (turn inside, emergency release outside)
plus an edge pull at `D-B-BATH`; a flush pull plus an edge pull at the pantry and laundry.

**Core.** Hollow on every commodity leaf; the exceptions are the solid, steel and sauna rows
below.

**Style (owner, 2026-11-20).** Every leaf is flush and smooth. Each type names its product
(`DoorType.product_ref`, `plan/interior_door_products.py`), and the viewer's door inspector
prints it with the core, function, leaf and bottom:

| Product | Types |
|---|---|
| Steves & Sons flush HC primed composite prehung, `x62H1WASAE` (J 24 / M 30 / N 32 / Q 36, RH/LH) | every hollow `-SWING*`, `CLOSET32` (cut to 6'-0", rail re-glued) |
| Masonite 65726 flush solid-core primed prehung | every `-SOLID*`, `DOUBLE60` (prehung as a pair by the yard) |
| Masonite 14548 flush HC slab, 36x80 | both pockets (the Eclisse kit serves on the opening: EKC3680 / its 2x6 sibling) |
| Steves J62H1FADLC99 flush HC slab, 24x80 | `BYPASS48` (two), `ACCESS24` (cut to 36", rail re-glued) |
| Johnson Hardware 138F482D | `BYPASS48`'s set |
| Impact Plus BFP344-6080W flush bifold, trimmed to 56" (confirm; no stock 56") | `BIFOLD56` |
| Mastercraft 4140314/5 flush steel prehung | `STEEL36-KEYED` |
| Mastercraft full-lite steel prehung, 30" (model unread) | `STEEL30-SEALED` |
| Finnleo all-wood sauna door, or equal (model unread) | `SAUNA24` |
| Trimlite 1-lite tempered slab, 1 3/4" | `SWING30-GLAZED-TRIMLESS` (and catalog `SWING30-GLAZED`) |
| Flush solid-core slab, 1 3/4" (Trimlite / JELD-WEN class) | `SWING32-TRIMLESS-PUSH` |
| Steelcraft hollow metal, narrow lite, KD frame, or equal | `STEEL24-LITE` |

**D-M-MUDC (2026-11-20).** Two 24x80 flush HC slabs on a Johnson 138F482D 48" two-door set,
cased like every other door. Johnson's IN183834: finished opening 2W - 1" = 47" (the leaves
lap 1"), height = leaf + 2 3/8" (82 3/8" over the LVP), 3/8" at the floor; RO 49" (was 50")
x 83 3/8" over the finished floor. Track 3.459 x 2.187", lanes ~1 11/16" c-c (measured off
Johnson's drawing), the 2135 guide at the floor centre, #30 cup pulls on the mudroom faces
36" up (`flip_swing` picks that face). The start jamb stays at 16" off N-M-MUDC1, so the RO's
east edge moved 1" further from the corner pack; the head is in the 9' nonbearing partition.

**Undercut (owner, 2026-11-06).** Every interior door is a stock 6'-8" prehung cut down on
site in its 81.51" RO: jamb legs trimmed, the slab cut to hang at its undercut over the
higher finished floor. 1/2" by default (`TRIM-STANDARD.door_undercut`), 3/4" on a relief
door (`DoorType.undercut`), never outside 1/2"-3/4". The model carries it: A-601's Undercut
column prints the undercut and the cut, `advisory.door_undercut` grades it, and
`mep.door_transfer_air` grades the relief (`notes/system1_return_path.md`). A sealed door's
sweep or automatic bottom closes its undercut (`DoorType.bottom_seal`).

| Door | Rooms | Type | Function / set | Core | Bottom / seal | Relief path |
|---|---|---|---|---|---|---|
| D-M-MUD | mudroom / living | DT-INT-SWING32 | passage | hollow | 1/2" | - |
| D-M-BED | bed / closet | DT-INT-SWING32 | passage | hollow | 1/2" | - |
| D-M-MECH | mech / mudroom | DT-INT-SWING30 | passage | hollow | 1/2" | - |
| D-M-BATH1 | powder / living | DT-INT-SWING32-PRIV-SOLID | privacy | solid | 3/4" | exhaust makes up under it |
| D-M-BATH2 | bath2 / bed | DT-INT-SWING32-PRIV | privacy | hollow | 3/4" **must stay** | RM-M-BED's 20 cfm exits here (15 until 2026-11-20) |
| D-M-BED2 | bed / living | DT-INT-SWING32-TRIMLESS-PUSH | privacy | solid | kerf seal + automatic bottom | via D-M-BATH2 |
| D-M-STUDY | study booth / living | DT-INT-SWING30-GLAZED-TRIMLESS | passage | glazed | open undercut | 5 cfm out under it; opens to 174 deg on an Emtek 2256US15 3" magnetic holder |
| D-M-PANTRY, D-M-LAUN | - | DT-POCKET-INT-36 | pocket passage: flush + edge pull | - | - | - |
| D-M-MUDC | mud closet | DT-INT-BYPASS48 | closet: Johnson 138F482D, #30 cup pulls | hollow (2 x 24x80 flush slabs) | 3/8" over the LVP (set's clearance) | - |
| D-S-BED1/2 | bedroom / hall | DT-INT-SWING30-PRIV | privacy | hollow | 3/4" (needs ~1.8x more: see return note) | System 1 return |
| D-S-BED3 | bedroom / hall | DT-INT-SWING30-PRIV-STOCK | privacy | hollow | 1/2" | none: ducted return REG-S-HP-BED3-RET (2026-11-11) |
| D-S-SUITE | suite / hall | DT-INT-SWING32-PRIV-SOLID-SEALED | privacy | solid | 1/2", kerf seal + sweep | none: ducted return REG-S-HP-SUITE-RET (2026-11-09) |
| D-S-SUITEBATH | suite bath / suite | DT-INT-SWING30-PRIV | privacy | hollow | 3/4" | - |
| D-S-BATH1 | bath1 / hall | DT-INT-SWING30-PRIV-SOLID | privacy | solid | kerf seal + sweep across a 1/2" undercut | REG-S-XFER-VANITY -> lined bay -> REG-S-XFER-BATH1 |
| D-S-NCLOSET | closet / hall | DT-INT-SWING30 | passage | hollow | 1/2" | - |
| D-S-PLANT | plant / study2 | DT-INT-STEEL30-SEALED | passage | insulated steel, full tempered lite | none: compression seal + adjustable sill (2026-11-12) | closer with hold-open; the room vents through its own transfer pair (`plant_room.md`) |
| O-S-CLOSET | suite closet | DT-INT-BIFOLD56 | closet | solid (flush MDF bifold) | - | - |
| D-A-HALVES | studio / study | DT-INT-SWING32-PRIV | privacy | hollow | 3/4" (3.8 Pa: see return note) | System 1 return |
| D-A-STUBATH | studio bath / studio | DT-INT-SWING24-PRIV | privacy | hollow | 3/4" | - |
| D-A-POCKET | ERV access | DT-INT-ACCESS24 | passage | hollow (24x80 slab cut to 36") | 1/2" | - |
| D-A-STUDY | attic study | DT-INT-BOOKCASE30 | touch latch, ships with the unit (filtered out of the passage row) | solid | sealed (owner, 2026-11-12): gasketed leaf, bottom sweep | none: passes no air; the study is open to the stair |
| D-B-FURN | furnace / workshop | DT-INT-SWING36 | passage | hollow | 3/4" **must stay** | the workshop's makeup |
| D-B-SHOP | workshop / stair hall | DT-INT-STEEL36-KEYED | keyed entry 740HFL SQT 15 SMT + US15 hinges | steel | weatherstrip + sweep across a 1/2" undercut, no sill | via D-B-FURN |
| D-B-SAUNA | sauna / gym | DT-INT-SAUNA24 | own handle and roller catch, no lock | insulated wood | sealed | supply and exhaust balanced 20/20 cfm |
| D-B-PLAY | play / gym | DT-INT-DOUBLE60 | pair: passage + dummy + flush bolts | solid | jamb/head gaskets + astragal, 3/4" | 30 cfm supply exits under the pair |
| D-B-BATH | bath / stair hall | DT-POCKET-INT-36-PRIV | pocket privacy + edge pull | - | - | - |
| D-B-ESS | ESS closet | DT-INT-STEEL24-LITE | passage, spring hinges | steel | - | - |
| D-B-CLOSET | under-stair storage | DT-INT-CLOSET32 | closet (dummy knob) | hollow | 1/2" (standard; the 3/4" heater undercut is retired, 2026-11-09) | - |

**Open at order.** The sauna door's maker and its RO against the 3/4 x 9 1/4 cedar flat jamb
(the model keeps the 24" leaf's derived RO); the Halifax lever projection against the 3"
holder at D-M-STUDY; Murphy's touch latch; Kwikset's 6x6-class grille free area is read off
a reseller listing (`notes/air_distribution_products.md` §6).

**Why the bath pair is offset and 6x6.** `W-S-BD-N`'s west bay (x 8"..15 1/4") is the only
bay without plumbing; the bath face is SEKTION to 94 1/2" AFF, so its grille sits between
the SEKTION rail backing and the top plate, 7 1/4" x 7 1/8" clear. The vanity grille is
13 1/2" lower, over the mirror arches; insulation comes out of that bay and it is lined with
sheet metal. 20 cfm at 3 Pa needs 10.8 in^2; each 6x6 gives ~24 in^2.

**Why `D-M-STUDY` stops at 174 deg.** 180 - asin(3 / 29) = 174.1 deg for a 3" holder about
29" from the hinge. The leaf tip lands at y ~ 196", clear of ED-M-DINING-SW (192") and
ED-M-LIVING-RC2 (190 1/2") on W-M-C2 by ~3".

# Heat pumps on a ground pad — siting, pad, stands, line sets

Model: `params/sunken_garden.py` (`HP_PAD`, `_HP_STAND_AT`, `HP_STAND_LEGS`,
`HP_STAND_ANCHORS`), `plan/electrical.py` (the two units and their disconnects),
`plan/assemblies.py` (`HP_PAD_ON_GRADE`, `EQUIP_STAND_ALUM`), `plan/site.py` (the pad's
fall). Supersedes `notes/heat_pump_deck_mounting.md`, which is kept because the rule it
established — decision #64, a fastener through a waterproof deck lands in a sacrificial
member — still governs any future deck.

## Why the balcony was left

Owner decision, 2026-09-02. `EQ-M-HP1-OD` (Gree FLEXX Ultra 24k, 187 lb) and `EQ-M-HP2-OD`
(Gree Multi R32 30k, 145 lb) stood on `FS-SG-DECK` at +10'-0", the watertight aluminium
roof of an occupied porch. Nothing about that was unbuildable; the previous note works the
whole detail through and it holds. It was simply expensive in kinds of cost that do not
appear in a bid:

- **Eight lagged penetrations through a plane that had none**, hosted on sixteen sacrificial
  2x8 blocks laid by four `JoistReinforcement`s, each one taped, each one billed.
- **Two 3/4" condensate runs with self-regulating heater cable**, plus a cable down
  `TR-SG-LEADER-SE` that the model could not even carry, because an untraced defrost line
  over that deck is a line of ice by December.
- **Spring isolators** sized to ~44 lb/corner, because the balcony is a lightweight
  freestanding diaphragm over a porch with no house mass to borrow.
- **A standing "never soffit this balcony" constraint**, because the open joist bays were
  simultaneously the only drying path and the only inspection path those eight holes had.
- **Both units directly over the master bedroom's south windows**, and reachable for
  replacement only through a French door or by crane.

On the ground all six disappear at once, and what replaces them is a pad and eight wedge
anchors. The balcony returns to **zero deck penetrations**, which is what it was designed
as.

## The pocket, and why the row faces east

The yard pocket immediately east of the porch, bounded:

| | |
|---|---|
| west | `W-SG-E1`, the porch's east wall — faces x 27'-6" / 28'-6", top 0'-0", y -11'-0"..-0'-10" |
| north | the house's south wall, cladding face y ≈ -0'-5" |
| south | the `W-RG-EAST-BALCONY` apron return at y = -10'-6", top +0'-6" |
| east | open yard to x 36'-0" |

The house is **gable-ended** here, so nothing sheds off the roof onto the units. The
basement wall behind is `W-B-S4`, which has no windows. The only neighbour in the pocket is
`TR-SG-LEADER-SE` at (28'-9", -10'-6"), discharging at +1'-0" into the terrace slot, well
south of the pad. Nothing was authored in `plan/site.py` inside it.

**A row against the house facing south does not fit.** Two cabinets 14 9/16" and 16 13/16"
deep, each wanting its discharge clearance in front, needs 99" of the pocket's 90". So the
row stands against the porch wall instead, backs west, **facing east into the open yard** —
which is also the direction with unlimited discharge room and no reflecting surface.

| | centre | cabinet W x D | y extent |
|---|---|---|---|
| `EQ-M-HP1-OD` | (29'-7 1/5", -2'-7 1/5") | 39 x 14 9/16 | -0'-11 3/4" .. -4'-2 3/4" |
| `EQ-M-HP2-OD` | (29'-8 2/5", -6'-10 4/5") | 40 5/32 x 16 13/16 | -5'-2 3/4" .. -8'-6 7/8" |

`rotation=deg(90)` on both, unchanged from the balcony — it is what puts the long axis
along y so the discharge face reads east.

## Clearances, against the submittals (fetched 2026-09-02)

| | required | provided |
|---|---|---|
| HP1 discharge (east) | 40" | open yard, 6'-0" to x 36' and no wall |
| HP1 service side | 12" | 12.0" to HP2's north face |
| HP1 back (west) | 4" | 5.9" to `W-SG-E1`'s face |
| HP1 north end | 4" | 6.9" to the house cladding |
| HP2 front (east) | 24" | open yard |
| HP2 service side | 12" | 12.0" to HP1's south face |
| HP2 back (west) | 6" | 6.0" to `W-SG-E1`'s face |
| HP2 south end | — | 23.1" to `TR-SG-LEADER-SE` |

Two of these are **at the published minimum and not above it** — HP2's 6" back gap and the
12" service gap between the units. Both are the numbers the row was laid out from, so
neither is slack: **moving either cabinet in y or x breaks a clearance**, and the stand legs
in `params/sunken_garden.py` are derived from these centres and would have to move with it.

## The pad

`SL-SG-HPPAD`, assembly `HP_PAD_ON_GRADE`: 4" unreinforced concrete on 4" of open-graded
stone, x 28'-6"..32'-0" by y -9'-0"..-0'-7 1/5" — 29.4 sf, 0.36 cy — with an isolation joint
where it meets `W-SG-E1`. Top at **-2'-8"**, two inches proud of the -2'-10" site grade,
falling 2 1/2" over the 8'-4" east to its outer edge, which lands 1/2" below grade so the
sheet leaves onto gravel instead of ponding at a lip. The `Slab` is modelled flat at its
high edge; the fall is authored as the `ImperviousSurface` "hp pad" in `plan/site.py`, where
`code.R401_3_impervious` reads it (2.5% against the 2% required).

**Why it reaches the wall rather than stopping at x 29'-0".** The feet, not the cabinets:
HP1's published foot pattern is 15 9/16" across the depth against a 14 9/16" cabinet, so its
west leg line sits half an inch *west* of the cabinet's own back face. A pad drawn to the
cabinets left that leg overhanging by 3/8". Six inches of extra pour is the cheap answer.

**No XPS, no vapour retarder, no frost footing**, and all three omissions are deliberate.
Nothing above the pad is conditioned, so there is no heat to break; a retarder under an
exterior pad only traps the water that arrives from the top. And an equipment pad is not a
foundation: it carries 333 lb of cabinet on eight legs, it is free to move with the ground,
and a pad that lifts an inch in February and settles back in April has done nothing a line
set cannot absorb. A frost-depth footing under a mini-split is a foundation for a 333 lb
building.

## Stands and anchors

Two 18" aluminium ground stands, `EQUIP_STAND_ALUM`, modelled as four legs each
(`PT-SG-HPA1..4`, `PT-SG-HPB1..4`, 2" square, `supported_by="SL-SG-HPPAD"`), one 3/8" x 3"
316 stainless wedge anchor per leg (`CN-SG-HPA1..4` / `CN-SG-HPB1..4`, part
`SS316-WEDGE-38x3` in `library/hardware.py`). The cross-rails are in the price row, not in
the geometry — only the legs resolve as solids.

**On a pad the legs ARE the feet.** This is the one thing the move simplifies outright. On
the balcony the leg positions belonged to the deck — bay centres, six inches off every beam
axis — and could not also honour the cabinets' published foot patterns, so each stand needed
a frame spanning two different grids (decision #64 works through why). A flat slab has no
grid. Each leg now stands directly under a published foot hole and the rails carry no
cantilever:

| | part | feet, width x depth | weight |
|---|---|---|---|
| `EQ-M-HP1-OD` | `FXU24HP230V1R32AO` | 29 3/4" x 15 9/16" | 187.4 lb |
| `EQ-M-HP2-OD` | `MUL30HP230V1R32AO` | 25" x 15 19/32" | 145.5 lb |

Both cabinets are rotated 90°, so the **width** pitch runs in y and the **depth** pitch in
x. The depth direction still has no adjustment — the cast foot's obround slot runs the width
way, about 1/4" of travel there and none across the depth.

**Aluminium legs, 316 stainless anchors.** Not a finish choice: the pad is at grade in a
de-iced climate and the base plates sit in the splash and the plough line all winter.
Aluminium with 316 is the pair that does not couple; galvanised steel legs on a salted pad
are the ones that go first. The butyl-under-every-plate story from the balcony detail is
**gone** — there is no waterproof plane here and nothing to seal.

**Vibration isolation is no longer load-bearing.** The balcony needed spring isolators
because it was a low-damping timber diaphragm over occupied space. A 4" slab on stone is
not, and the ordinary neoprene or rubber grommets that ship with a stand are appropriate.
Isolating the **line set** still is — that is the transmission path most often missed, and
HP1's now runs inside a stud bay of an occupied wall.

## Snow, and Gree's 2" rule

Gree's outdoor-unit instruction says to "install 2 in above the expected snow line". The pad
gives the first 2" and the stand gives 18 more, so the **coil bottom sits about 20" above
grade**. The owner's 12" on the balcony was a balcony number, and the note that recorded it
said so: a deck swept by wind keeps its snow depth low in a way ground never does. At grade
the cold-climate guidance (18"–24") applies as written, and 18" is inside it.

Both units carry a **factory base-pan heater** — confirmed in the submittals, which closes
the open question the deck note left ("verify availability with Gree"). Defrost meltwater
drips onto the pad and runs east onto gravel: no drain pan, no piped condensate, no heater
cable, no `pan_drain_ref`. `EQ-M-HP3-OD` has stood at grade on the north side on exactly
those terms since it was authored.

## Sound

60 dBA (HP1) and 58 dBA (HP2) at the manufacturer's rating distance. The pocket is a
three-sided reflector — the porch wall west, the house north, the apron south — so it
returns sound **east and up**, and up means `WIN-M-LIV-S1` (the living room, x 31'-5"..
33'-11") and `WIN-S-STUDY2` above it. This is worse than an open corner and better than the
balcony was: the balcony put both compressors at +10'-0", level with the second-storey
glazing and eight feet from the master bedroom's own windows, with a deck plank under them
acting as a soundboard. Concrete on stone radiates nothing. **No mitigation is modelled.**
If it turns out to matter, a slatted screen on the pad's east edge is the move that does not
touch a clearance — a screen on the north or south end takes the service gaps that are
already at their minimum.

## Line sets — routes, lengths, limits

**Not modelled.** `pipe_runs` carries drain, vent, water_cold and water_hot and no
refrigerant system, so there is no `PipeRun` for a line set to be; the `outdoor_ref` pairing
on each head is the record, and the money is in the `hvac-refrigerant-line-sets` allowance
in `prices.toml`, which grew ~50 LF for this move and is not re-priced (at $26–49/LF the
added footage is inside its own spread, and the number was always a lump).

Gree's published limits, from the same submittals:

| | line | total | per port | rise | precharge |
|---|---|---|---|---|---|
| FXU24 (HP1) | 3/8"–3/4" | 164 ft | — | 49 ft | 31 ft + 0.323 oz/ft |
| MUL30 (HP2) | 1/4"–3/8" per port | 263 ft | 82 ft | 82 ft | 131 ft |

**One penetration through the main-floor band**, at y = 0, x ≈ 30'-6" — sleeved, sloped to
the outside, flashed, with an expansion loop inside. The band there runs -1'-1 7/16"..0'-0",
i.e. 1'-9"..2'-10" above grade, and `FS-M-EAST`'s joists run in x, so the south bay is a
straight east-west run with nothing to notch. **No sleeve element is authored**, and that is
deliberate rather than an omission: `SleevePenetration` is concrete-only in this engine and
there is no framed-wall equivalent, so a fake sleeve would put a cast-in item on the pour-day
schedule that nobody pours. It is recorded here instead.

- **HP2** (three ports, 1/4–3/8): west inside the band bay to x 20'-0" and x 16'-0", then
  7'-6" up the wall cavity behind `EQ-M-HP2-LIVING` and `EQ-M-HP2-BED`; the gym head runs
  north 9'-0" in the basement ceiling to `EQ-B-HP2-GYM`. About 25–30 ft each against an 82 ft
  per-port limit and 263 ft total. Inside the 131 ft precharge — no added charge.
- **HP1** (3/8–3/4): up the `W-M-S2` / `W-S-S2` stud bay at x ≈ 29'–30', clear of
  `WIN-M-LIV-S1` (31'-5"..33'-11"), `WIN-S-STUDY1` (27'-4"), `WIN-S-STUDY2` (32'-8") and
  `D-S-DECK-E` (18'-10"..23'-10"); neither wall is braced, so the bay is available. Through
  the main top plates, the second-floor band and the second top plates into `FS-ATTIC`'s
  first bay (y 0"..16", joists in x), then 5'-0" west into `SF-S-HP1`'s east end at
  x 24'-9". About **40 ft of line and 21 ft of rise against 164 ft and 49 ft** — comfortable
  on both, and about +3 oz of R32 over the 31 ft precharge.

## Electrical

`ED-M-HP1-DISC` and `ED-M-HP2-DISC` moved from the second-storey south wall down to
`W-M-S2`'s exterior face, at x 30'-0" and x 35'-0", 5'-0" AFF, centres 1 5/8" off the
cladding for the can's true 3 1/4" depth (the `ED-M-HP3-DISC` convention). Both clear of
`WIN-M-LIV-S1`'s rough opening and of either unit's own working space, which is the pad in
front of it. A disconnect one storey above the machine it kills is not within sight of it in
any sense NEC 440.14 means, so this was not optional once the units came down. `CKT-HP1` and
`CKT-HP2` carry no route, so nothing changed in `plan/circuits.py`.

## What is not modelled

- **The line sets and their sleeve** — above; the sleeve because no framed-wall sleeve type
  exists, the line sets because no refrigerant `PipeRun` system does.
- **The stands' cross-rails** — in `column:EQUIP_STAND_ALUM`'s price row, not in geometry.
- **The pad's fall** — the `Slab` is flat at its high edge; the fall is the
  `ImperviousSurface`.
- **Anchorage capacity.** Both units left the deck, so `mep.deck_equipment_support_coverage`
  no longer sees them and the engineering register no longer carries
  `equipment_anchorage/EQ-M-HP1-OD` / `-HP2-OD`. That is honest — the item those records
  named was *anchorage to a deck*, and there is no deck. Wind on a cabinet 20" off the
  ground behind a 2'-10" wall in Exposure B is a different and far smaller problem than wind
  on the same cabinet at +10'-0"; it is still not calculated here. The eight wedge anchors
  are a bolt-down-per-the-instruction detail (IRC M1401.4), not a designed restraint.

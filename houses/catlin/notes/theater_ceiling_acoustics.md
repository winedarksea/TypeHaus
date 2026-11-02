# Theater ceiling: decoupled gypsum on resilient channel (RM-B-PLAY-N)

2026-11-01. Rule `CR-PLAY-CEIL-RC` (`plan/assemblies/catalog.py`): `floor:ceiling_channel`,
`dimension` 24", `scope_ref="RM-B-PLAY-N"`, billed as `resilient-channel` (RC-1, "25 ga. resilient
channel"). The model bills channel only; gypsum comes from `FS-M-NE.ceiling_below`. The finder
bills area / spacing (285.5 sf / 2 ft = 142.7 LF) and ignores orientation, so the rules below are
the install spec.

## Assembly
- Framing: FS-M-NE 11 7/8" open-web trusses at 12" o.c., running E-W (x). Bottom chords are the
  only fastening surface.
- Channel: RC-1 along **y**, perpendicular to the trusses (a channel parallel to a chord screws
  to one chord and decouples nothing). **24" o.c.**: the published maximum for one layer of 5/8"
  gypsum on RC-1 is 24" o.c. (1/2" board: 16"); channel spacing is independent of the 12" truss
  spacing, and the 12" framing is well inside RC-1's rated load. Sources: ClarkDietrich
  RC install guidelines (`CD_RC-InstallationGuidelines.pdf`, clarkdietrich.com); USG/GA-600 Fire
  Resistance and Sound Control Design Manual RC-1 listings (not re-read; confirm before ordering).
- Channel to truss: one screw per chord crossing through the mounting flange (1 1/4" #6 Type W,
  ClarkDietrich guide). Mounting flange faces the room, board flange down, per the maker's
  arrow. Lap splices 4" minimum, overlapped over a chord, never between.
- Board: one layer 5/8" gypsum, long edge **perpendicular to the channels** (along x, parallel
  to the trusses). End joints land on a channel, staggered between rows. No second layer.

## Screws: channel only, off the chords
- 1" (preferred) or 1 1/8" Type S bugle, **into the board flange only**, 12" o.c. along the
  channel (maker's guide), kept clear of every chord line. Chords are 12" o.c., so the screw
  line lands between chords.
- Why not longer. RC-1 stands the board flange about 1/2" below the chord face (RC-1 offset; the
  resolver uses 1/2"). Tip past the flange = screw - 5/8" board - 0.018" (25 ga) flange:
  - 1": 1.000 - 0.625 - 0.018 = **0.357"**, 0.143" short of the chord plane.
  - 1 1/8": 1.125 - 0.625 - 0.018 = **0.482"**, 0.018" short; a flexed flange or an overdriven
    screw reaches it. Use only if 1" will not bite; a 1 1/4" (0.607") would touch.
- A screw that reaches a chord (or a chord-line channel flange screwed through to wood) is a rigid
  bridge: the channel is bypassed and the isolation largely lost. NRC and USG report this
  short-circuit as the main field failure of RC assemblies (NRC-CNRC research on resilient-
  channel installation errors; USG Gypsum Construction Handbook, RC-1 section; Green Glue /
  Soundproofing literature repeat it). The 1" rule is the control; no 1 5/8" or longer screw
  ever goes into this ceiling.

## Install sequence
1. Trusses and sprinkler/MEP rough-in done; ducts and pipes clear of the channel plane (they
   run inside the truss depth: `DU-B-ERV-R-PLAY` in the web openings). The channel lowers the
   finished ceiling about 1/2".
2. Strike y-lines at 24" o.c.; hang channel, one Type W per chord crossing.
3. Insulation in the truss bays if specified; do not fill the 1/2" channel gap.
4. Hang board with 1" Type S into the channel only, 1/4" off every wall.
5. Tape and finish; fill the perimeter gap with painter's caulk.

## Perimeter and penetrations
- **1/4" gap** at all walls, filled with painter's (acrylic latex) caulk, never rigid hard
  contact, no screws or corner bead tied to wall plates. Billed in `prices.toml [allowances]`
  `paint-theater-ceiling-perimeter-caulk` (68 LF).
- **No ceiling lights or boxes.** The six wall sconces stay. `ED-B-PLAY-N-JB` is on `W-B-N1`
  since 2026-11-02 (`plan/electrical_branches.py`).
- **`REG-B-SUP2` supply boot is sealed to the board** (flexible collar, acrylic caulk) and is
  not tied rigidly through the channel or to a chord. It sits mid-bay at y=20'-6" on the
  cavity duct (`plan/mep_registers.py`), so no chord is in its way.

## Not modelled
The rule adds no ceiling solid or height: `haus check` finished-ceiling and R305 numbers are
unchanged by it. The real ceiling is about 1/2" lower than the model reads (open in
`plans/TODO.md`).

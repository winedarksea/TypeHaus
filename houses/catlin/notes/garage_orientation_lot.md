# Garage orientation and the lot it was drawn for

**Status: a CORRECTION, recorded 2026-09-07.** The overhead door faced east for a lot the
rest of the model does not describe. This note holds the premise that was retired, the
evidence that it was already inconsistent, the full before/after, and the recipe for going
back.

## 1. The premise that was retired

The garage was drawn 24'x24' with its 16'-0" overhead door on `W-G-E`, facing **east**, and
its ridge running east-west. That was right for a parcel to the **SOUTH** of the house with
a driveway coming around the **east** side: the car approached from the south-east, turned
north up the east flank of the house, and met the door square.

By 2026-09-07 that premise survived in exactly two prose comments and nowhere else:

- `plan/storeys/garage.py:4` — *"Overhead door faces east (driveway side)"*
- `plan/site.py` (the front-walk `ImperviousSurface`) — *"drains east to the driveway"*

**There is no `Driveway` element anywhere in the model, and there never was.** Nothing in
`plan/`, `params/` or `library/` describes a drive, an apron beyond the 4'-deep front walk,
or an approach. The east-facing door was carried entirely by those two sentences.

## 2. Why it was already inconsistent

`plan/site.py` has always declared the opposite lot, in the two places the engine actually
reads:

- `SetbackSpec(edge=2, ft(30), "FRONT")` — **edge 2 is the NORTH parcel edge**, and it is
  the one carrying the 30' front setback. `edge=0`, the south edge, is `"REAR"`.
- The water service enters from the **north**, "matching the street on the NORTH", and
  `PR-G-HYDRANT-CW` runs north from the house to the yard hydrant on that basis.

So the setbacks, the utility entry and the door disagreed about which side the street was
on for as long as both existed. Turning the door north is what makes the garage front-load
off the street the parcel already declares, and it is a correction rather than a preference.

## 3. What actually moved

**Nothing about the footprint.** The garage is square, so the walls, nodes, stem, slab and
footings are all still 24'x24' and the four wall tags still mean the four compass faces. The
windows stayed on `W-G-W` and `D-G-SERVICE` stayed on `W-G-S` at x=8'-0", concentric with
`D-M-ENTRY`. What turned is the door, the ridge, and everything downstream of those two.

| | before | after |
|---|---|---|
| `D-G-OVERHEAD` host / position | `W-G-E`, `from_node("N-G-SE", 4'-0")` | `W-G-N`, `from_node("N-G-NE", 4'-0")` |
| opening band | y 45'-0"…61'-0" | x 10'-0"…26'-0" (centre on the wall's midpoint, as before) |
| `OVERHEAD_DOOR_OFFSET` | 4'-0" | **4'-0", unchanged** — see §5 |
| `RF-GARAGE.ridge_direction` | `"x"` | `"y"` |
| `RF-GARAGE.bearing_refs` | `("W-G-S", "W-G-N")` | `("W-G-E", "W-G-W")` |
| bearing roles | S/N BEARING, E/W NONBEARING | **E/W BEARING, S/N NONBEARING** |
| eaves / rakes | eaves S+N, rakes E+W | eaves E+W, rakes S+N |
| `EaveGutter.edges` | `("south",)` | `("east", "west")` |
| downspouts | `TR-G-LEADER-E` only | `TR-G-LEADER-E` + `TR-G-LEADER-W` |
| stem gap | east wall, `W-GF-E1`/`-E-DR`/`-E2` | north wall, `W-GF-N2`/`-N-DR`/`-N` |
| stem walls / footings | 10 / 10 | **9 / 9** |
| Z-flash runs | S 6'-3"+14'-3", E 4'-0"x2, N 24'-0", W 24'-0" | S unchanged, **E one 24'-0"**, **N 4'-0"x2**, W unchanged |
| Z-flash total | 76.5 LF | **76.5 LF** |
| snow guards | 6 x S-5! ColorGard on the south slope | **none** — see §4 |
| roof seam clamps | 12 `S-5-N`, eaves at y 39'-2 7/8" / 65'-10 7/8" | 12 `S-5-N`, eaves at x 2'-6 1/4" / 29'-5 3/4" |
| `ED-G-EXT-LT` (see §6) | one light, `W-G-E` cladding face, `rotation=deg(90)`, 8'-10" over the apron | **a pair**, `ED-G-EXT-LT-E` + `-W` on the `W-G-N` cladding face at x 28'/8', `rotation=deg(0)`, 7'-6" over the apron |

Retired uids: `CGF006` (`N-GF-E-DRN`), `CGF106` (`W-GF-E2`), `CGF206` (`FT-GF-E2`). Every
other element re-used an existing uid — `N-GF-N-BRICK` was retagged `N-GF-N-DRE` **in
place**, at the coordinate it already had, because (26', `GARAGE_Y_NORTH`) is exactly the
new door's east jamb. A relic of the deleted brick wainscot became a real jamb node.

## 4. The snow guards are gone, and that is earned

Six `S-5! ColorGard` guards stood on the south slope for one target: the garage shed south
onto the breezeway's polycarbonate canopy `GL-BW-ROOF`, 3.0' below the eave in the discharge
band. South is a **rake** now. A rake sheds along itself into the eave beside it, so nothing
discharges over the breezeway. The two slopes face east (open ground and the HP1 pad, which
is a cabinet at grade, not a roof) and west (the window wall and the walk, nothing below).

`structural.sliding_snow` only sees ROOFS below a slope, so it reports nothing either way —
the absence of a target is the design fact, not the check's silence. If the ridge ever turns
back, the guards come back with it; their row is written out in `plan/storeys/garage.py`.

## 5. The 4'-0" offset travelled unchanged, on purpose

`OVERHEAD_DOOR_OFFSET` is an open owner question: the 16'-0" opening's centre lands 12" off
the 24" framing module and cuts 9 stud lines where 8 would do. `structural.door_framing_module`
reports it and `preferences.toml` suppresses it under the key
`structural.door_framing_module:D-G-OVERHEAD` — keyed on the DOOR tag, not the wall, so the
suppression followed the door across walls with no edit at all.

The rotation deliberately carried the question across rather than settling it in passing.
Do not re-decide it either way as part of a geometry change.

## 6. And then the garage was centred on the house ridge (same day)

A second, independent decision: put the garage under the house's ridge at x=18'-0". It was
x 0'…24' — its west wall aligned with the house's — centre x=12'-0", six feet west of the
ridge. **It is x 6'-0"…30'-0" now, centre x=18'-0", dead on it.**

### 6.1 The move is in 24" steps, and the third step cost the concentric doors

`D-G-SERVICE`'s 36" RO must sit on one of `GARAGE_WALL_2X6`'s 24" stud lines measured from
its own wall's start, so the wall line and the door travel together in whole modules. The
door could not stay at x=8'-0": the sole plate starts 5/8" inboard of the node line, the
3-stud corner pack takes the next 3.0", so the corner owns the first **3 5/8"** of wall, and
the door's king wants to stand at x=6'-3". The furthest west node that clears it is
x 5'-11 3/8". Centring needs 6'-0". **Five-eighths of an inch.**

So the door went with the wall, to centre x=10'-0" (`SERVICE_DOOR_OFFSET` still 2'-6").

**`D-M-ENTRY` could not follow, and that is the finding worth keeping.** Its east jamb is
already 6" west of `N-M-N2` at x=10'-0" — the tee where `W-M-STRW`'s bearing stack lands on
the north wall and runs unbroken to the footings — and a 36" RO cannot straddle it. The
entry is pinned at centre x=8'-0" by a load path.

**The two doors the breezeway spans are therefore 2'-0" out of line, and
`params/breezeway.py` is untouched**: still 4'-0" of enclosure centred on x=8'-0", still one
uncut polycarbonate sheet, still `_GLAZING_CENTER_X = 8.0`. `code.R311_3_exterior_landing`
reports it as an ERROR against `D-G-SERVICE`, correctly and deliberately —
**an owner decision to centre the garage first, look at it, and adjust the breezeway after.**
That FAIL is the one deliberate red this change leaves. Do not answer it by moving the
garage back.

**Exactly half the leaf opens onto air.** The deck sheet spans x 6'-0"…10'-0" and
`D-G-SERVICE`'s RO is 8'-6"…11'-6", so 1'-6" of the 3'-0" door has deck under it and 1'-6"
does not — over a 2'-10" drop to the garage slab on the inside. **This is a safety condition,
not a drafting nicety**, and it is the reason the finding is an ERROR rather than a warning.

Closing it later means one of: widening the breezeway to ~6'-0" to span both ROs (6'-6"…
11'-6") and giving up the uncut sheet; skewing it; or moving `D-M-ENTRY`, which needs the
`W-M-STRW` tee to move and it cannot.

### 6.2 What followed the garage, and what did not

- **`GARAGE_X_WEST` / `GARAGE_X_EAST` are now published** beside `GARAGE_Y_SOUTH`/`NORTH`,
  and `params/foundations.py` derives the stem nodes, the slab and the service-door landing
  from them. Two latent bugs fell out: `_STEP_X0` and the service-door gap nodes were
  offsets ALONG the wall being used as absolute x, correct only while the wall started at
  x=0'-0".
- **`FX-G-HYDRANT` went to x=11'-0"** — the same 5'-0" off the west wall it always had. Its
  clear zone derives from `FT-GF-W`'s 45° influence line and travels with the footing; left
  at x=5'-0" absolute the hydrant would stand inside that footing's own 20" strip.
- **`PR-G-HYDRANT-CW` now jogs, and that is what the move cost.** It was dead straight north
  at x=5'-0"; it turns east 6'-0" at y=38'-0" in the yard slot — the only band clear of both
  structures' footings — and crosses the garage foundation at x=11'-0", under the grade beam
  `FT-GF-S-DR` inside `SP-GF-S-HYD`'s protection sleeve. +6 LF and two elbows.
- **`ST-G-SERVICE` and `RL-G-SERVICE` moved onto their own landing, and that FIXED a
  standing FAIL.** The flight ran x 5'…8' under a landing at x 6'-6"…9'-6" — a stale offset
  from an older `SERVICE_DOOR_OFFSET`, overlapping by only 1'-6". Both are x 8'-6"…11'-6"
  now, square under the door, and `code.R312_1_guard_height`'s unguarded-edge FAIL on
  `SL-G-STEP-0` went with it.
- **`EQ-M-HP1-OD` moved 6'-6" east**, to x 33'-0"…36'-3". Its whole siting argument is that
  it stands EAST of the garage's plan extent so its 40" discharge is into open front yard;
  the garage moved under it, and the edge west of it stopped being a rake at x=25'-4" and
  became an eave with a gutter face at 31'-10". 6'-6" is the smallest move that gives its
  14" far-end clearance back.
  - **It oversails the house's NE corner by 3", deliberately.** 31'-10" to 36'-0" is 50";
    the cabinet plus its clearance is 53". The alternative was to sit flush and take 11"
    instead of 14" — trading a published-unknown airflow clearance for a mounting cosmetic.
    Airflow won. Gree publishes only the **4" back** clearance for this chassis; the 14" is
    margin this site happened to have, and **nothing in `haus check` grades it either way.**
- **`ED-M-HP1-DISC` moved 32'-0" → 32'-5", to the WEST of its machine**, into the 14" band
  between the gutter line and the cabinet. **It is a 6 1/2" can in a 14" slot with no NEC
  110.26 working space to speak of, and nothing grades that.** It is the accepted cost of
  centring, and it is a hard bound: the cabinet cannot move west (gutter) or east (corner),
  so the can has nowhere better on this face. If the working space is wanted back, the fix
  is to move `EQ-M-HP1-OD` off the north face entirely.
- **`EQ-M-HP3-OD` did NOT move.** It sits at y 37'-3 1/4"…38'-6", entirely SOUTH of the
  garage's roof edge at y=39'-4 5/8", discharging into the 48 1/2" slot — which is its
  documented condition and is unchanged by anything that happens to the garage's x.
- **`ED-G-EV-1450`, `CD-B-GARAGE` and its three sleeves did not move**: the EV outlet is a
  station on the south wall's interior face and is still well inside its new x 6'…30' run.
- **Not moved and worth knowing:** `ED-G-SW` and `ED-G-EXT-SW` translated faithfully to
  x 10'-6" and 10'-0" and are **inside `D-G-SERVICE`'s rough opening** (8'-6"…11'-6"). That
  is a **pre-existing defect carried forward, not a new one** — the comment beside them
  believed `from_node` gave the far jamb, so it read the door as 3'-6"…6'-6". Nothing grades
  a wall device against an opening. Putting them east of the real east jamb (~12'-0" and
  12'-6") is a small separate edit and is the right fix.

### 6.3 Three garage detail drawings gained the breezeway deck, and that is a deliverable change

`detail_wall_foundation-GARAGE_ICF_6-GARAGE_WALL_2X6`,
`detail_storey_stack-rim-GARAGE_ICF_6-GARAGE_WALL_2X6` and
`detail_stack_width_change-GARAGE_ICF_6-GARAGE_WALL_2X6` each picked up `FS-BW-FLOOR`
(uid `BWFS01AAAA`) — two joists and the composite plank — in section. Nothing about the
breezeway moved. The garage's south wall now starts at x=6'-0" instead of x=0'-0", so the
representative cut for that assembly pair lands where the deck butts the stem rather than on
a clear stretch of it, and the deck is genuinely there.

** The golden SET is unchanged: 85 files, none added, none deleted. ** That is the thing to
check after a move like this — `resolve/stacking.py::stack_width_change` fires on a 0.5"
tolerance, so a change of thickness anywhere in the stack can silently delete or mint a
detail. Six file CONTENTS changed (those three, plus the opening perimeter, the wall/roof
detail and the centre section) and all of it is coordinates.

### 6.4 What it is worth in the bill

Essentially nothing: **−$88 to −$139** on the construction total across BOTH changes. The
extra eave of gutter and the second downspout are paid for by six deleted snow guards, one
deleted stem wall and footing, and one fewer sill run. Z-flash holds at exactly **76.5 LF**
before and after, and the cladding's 96.3 LF is unchanged — only re-cut, 4x12' + 2x26' where
it was 4x14' + 2x24', which is the rakes and eaves swapping places.

## 7. The revert recipe

> ⚠ **Written for the 2026-09-07 state, and the service door has moved since.** On
> 2026-09-11 `D-G-SERVICE` went into the garage's SW corner (`SERVICE_DOOR_OFFSET` 2'-6" →
> 0'-7", RO 6'-7"..9'-7"), the exterior landing narrowed to its east jamb
> (`LANDING_EAST_FT` = `SERVICE_RO_EAST_FT`), the stem gap under it closed (`W-GF-S-DR` is
> `_STEM`, its nodes pinned at x 8'-3"/11'-9" as a fossil for `SP-GF-S-HYD`), and the stair,
> handrail, backing band, switches and `SL-D-NORTH-BRIDGE` cut are literals that followed it.
> The `ft(6, 6)` below presumes the door still at 2'-6" off `N-G-SW`; a revert today walks
> `params/north_entry_frame.py`'s constants and those literals back as well.

Turning the door back east is the table in §3 read right-to-left, plus §4's guard row and
§6's translation (set `GARAGE_X_WEST`/`GARAGE_X_EAST` back to `ft(0)`/`ft(24)`,
`SERVICE_DOOR_OFFSET` back to `ft(6, 6)`, and walk §6.2's list backwards). It is a plan-source edit only — no seal is staled, because
`houses/catlin/engineering.toml` does not exist and `header/D-G-OVERHEAD` is unsealed.

**A genuine south-lot revert is more than the garage.** The parcel itself has to turn:

- `plan/site.py` — flip `SetbackSpec` edge **2** from `"FRONT"` to `"REAR"` and edge **0**
  from `"REAR"` to `"FRONT"`, with the 30'/… dimensions that go with them. **Today's change
  does not touch either**, precisely because the site already agreed with the new door.
- The water service entry would have to leave the north face, taking `PR-G-HYDRANT-CW`,
  `SP-B-N3-HYD` and the hydrant's whole lateral with it.
- The front walk's "drains east to the driveway" sentence would become true again.

Turning the door without turning those is what produced the inconsistency this note records.
Do not do half of it.

## 6. The door light became a pair, later the same day

Turning the door north left one sconce on one side of a 16'-0" opening — it lit half the
apron and read as an accident on a face that is otherwise symmetrical about the door. It is
now `ED-G-EXT-LT-E` (the original element, uid `QTG0004AAA`, retagged in place) and
`ED-G-EXT-LT-W`, one on each 4'-0" pier at x 28'-0" and x 8'-0", mirrored about the door's
centreline at x 18'-0" and 2'-0" clear of both the jamb and the corner.

Both dropped from 7'-0" storey-relative to 5'-8" — 8'-10" over the apron to **7'-6"**, which
is 6" over `D-G-OVERHEAD`'s 7'-0" head. That is the height at which the two of them read as
framing the opening; the old one sat nearly at the 9'-10" plate. The 9" housing tops out at
8'-3", still 1'-7" under it.

One switch drives both — `ED-G-EXT-SW`, unmoved, ganged beside `ED-G-SW` at the service
door. There is no reason to light half an opening. The fitting, `ED-T-LT-SCONCE-EXT`, is
unchanged and already priced; its `prices.toml` row now reads 3 ea.

**Two coordinates in §3 were off by 6'-0" and are corrected above** (the opening band, and
the jamb the retagged `N-GF-N-DRE` sits on). Both were written as absolute x while
`GARAGE_X_WEST` was 0'-0"; it has been 6'-0" since the garage moved. The same stale reading
survives in `params/foundations.py`'s comment at the `N-GF-N-DRE` row, which still says 20'.

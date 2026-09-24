---
title: "Partition Tops and the Deflection Gap"
---

# Notes

Design reasoning, not a calculation. Nothing here is oracled and no test reproduces a number
from it; what it records is a decision, the product behind the decision, and the one thing
the decision deliberately does **not** do.

## 1. The bug this started from

Seven attic partitions resolved **11-7/8" too tall.** `resolve/roof_geometry.py` rakes a
`ToRoof` wall to `roof_height_at` — the roof **deck** plane — so `W-A-STU-N` topped out at
255"→315" where the TJI 230 rafter *soffit* over it is 243-3/8"→303-3/8". The studs and the
raked double top plate ran through the full depth of the rafter.

`roof_underside_at` — "underside of the roof structure at a plan point, **what a wall below
must reach**" — had been sitting in that same module the whole time, read by three checks and
wired into no wall top.

Nothing caught it. `checks/structural/interference.py` clears a plate-against-rafter contact
unconditionally as a birdsmouth seat, which on a bearing wall it is. The other 51 partitions
carried the same error by a different route: `extend_walls_to_platform` lifts a wall to the
storey datum above, which is the **top** of the joists, not their soffit.

## 2. The decision: 3/4" clear, house-wide, and a screw that holds it there

A partition's top plate stops **3/4" clear of the structure above** — not tight to it.

Tight is the failure. The deck above a partition deflects under live load; a partition packed
against it becomes a prop and picks up load it was never framed, detailed or connected for,
and the first visible symptom is a cracked ceiling joint. Simpson say it in the technical
guide's own words: a 0" gap "may result in unintended loading of the partition wall".

The 3/4" is not a round number somebody liked. It is the sleeve on a **Simpson Strong-Drive
SDPW DEFLECTOR** screw, which is the part that makes the gap buildable: a polymer sleeve holds
the plate off the member above while the screw's point is driven into it, so the joint is
**restrained laterally and released vertically**. The screw carries the wall's out-of-plane
reaction into the framing and carries nothing downward. That release is the entire product.

This finally makes `plan/storeys/attic_studio.py`'s standing instruction —
`** DETAIL EVERY ToRoof TOP WITH A SLIP/DEFLECTION GAP **`, with "the model has no field for
it, so it lives here" — a modelled fact instead of a comment.

## 3. The part, and why it is the 6" one

| | SDPW14312 | SDPW14500 | SDPW19600 |
|---|---|---|---|
| length × shank | 3-1/2" × 0.140" | 5" × 0.140" | 6" × 0.195" |
| sleeve | 1.38", blue | 2.88", orange | 3.10", gray |
| drive | 6-lobe T-25 | 6-lobe T-25 | 6-lobe **T-40** |
| published gap | to 3/4" | to 1-1/2" | to 1-1/2" |
| min. penetration | 1/2" | 1/2" | **3/4"** |
| published top plate | single 2x / built-up to 2-1/4" | single 2x / built-up to 2-1/4" | **double 2x** and thinner |

Catlin frames a **double 2x top plate — 3"** — on all eleven of its interior assemblies, so
the part is the **SDPW19600**. Length arithmetic would have said otherwise and would have been
wrong: 3/4" gap + 3" plate + 3/4" minimum penetration = **4.50"**, which the 5" SDPW14500
reaches comfortably. But Simpson publish that screw's allowables and its spacing table for a
single 2x or a built-up plate to 2-1/4", and the SDPW19600's for the double 2x. Reaching a
joint and being published for it are two different questions, and the table decides.

Consequences of that, worth knowing because they are field consequences: a different shank, a
different pilot, and a **T-40** bit rather than the T-25 every other Simpson screw on this
house takes. The 3/8" predrill goes through the top plate only — the supporting member is not
predrilled, and the sleeve must not enter it.

**These screws do have published numbers**, which was a surprise: IAPMO UES ER-192 Table 37,
also printed in Fastening Systems Technical Guide C-F-2025TECHSUP pp. 100–101. At a 3/4" gap
on a double 2x the SDPW19600 is **165 lbf** allowable lateral, ASD, C_D = 1.6, safety factor
5.0, SPF at SG 0.42 — identical at 0" and 3/4" offset. Both numbers are transcribed onto the
catalog record in `library/hardware/`, in `lateral_f1_lb`/`lateral_f2_lb`, and `uplift_lb`
is left `None` and must stay `None`: this joint releases vertically on purpose.

There is also a maximum-spacing table (8'/10' walls at 5 psf) whose worst case for this part
is 42"/36". Every count this house bills sits inside it. Grading that properly would be a
`PublishedSpan` and it is recorded in `plans/TODO.md` rather than done here. So is the other
open document: **every member these screws land in is an engineered product** — TJI 230
rafters, I-joists, open-web floor trusses — and the joist maker's own fastener rules govern as
much as Simpson's. ER-192 permits them (flange ≥ 1-1/8"); nobody has read the other side.

## 4. The two tops, and why only one moved

A `ResolvedWall` carries two tops and the 3/4" rule governs one of them.

| field | what it is | owner |
|---|---|---|
| `plate_top_z_m`, `top_z0_m`, `top_z1_m` | the **framing** top | `resolve/partition_top.py` |
| `z1_m` | the **body** top — layer prisms, the gypsum bill, the stair-enclosure extent, the wet wall a riser climbs | `resolve/platform.py` |

Moving both — cutting the body at the joist soffit as well — was simulated against the full
check registry and costs **four new FAILs** on a house `scripts/verify.sh` holds at its two
deliberate ones:

* `code.R312_1_1_stair_open_side` — cutting `W-S-SS2`'s body at the joist soffit opens a
  12-5/8" slot in `ST-S2A`'s enclosure. Every storey-line partition gets the same slot.
* `mep.wet_wall_occupancy` ×3 — `PR-B-CW-HYD-RISER`, `PR-B-CW-SBATH` and `PR-B-HW-SBATH` climb
  the full storey line *inside* their wet wall, which is what the pipes actually do. Shorten
  the wall and the pipe sticks out.

`platform.py`'s own docstring already states the asymmetry: on a storey line the plate stops
short and the finish keeps lapping the rim. So the rule is one-directional. The body **follows
the plate down** where the plate falls — drywall runs to the top plate, and
`layer_bands.clamp_to_plates` already trims it there — and **follows the plate up** where the
plate rises, which is the basement, where partitions author 8'-0" in a 8'-0 1/16" storey and
reach nothing. What the body may never do is drop below the storey line it was lifted to.

In the attic the two coincide, because gypsum cannot pass through a rafter either.

**Still open**, and recorded rather than quietly dropped: roughly 220 sf of gypsum is still
billed through the joist band on the storey lines. Answering it means moving `W-S-SS2`'s guard
coverage and re-authoring three riser extents — a design pass, not a resolve fix.

## 5. Which walls, and the two gates that are not optional

`resolve/partition.py` is the single predicate three passes share. A partition is a wall that
is not a foundation, carries no cladding, is not authored `BEARING`, and that **nothing names
as a bearing ref**. Two gates earn their place:

* **The `bearing_refs` sweep is generic over element kinds.** A `Stair` and a `FloorOpening`
  carry the field too, and they hold the two walls a narrower sweep gets wrong: `W-S-SS2` (in
  `ST-S2A.bearing_refs`) and `W-S-SN3`, a header at a deck hole.
* **`runs_full_storey_height`** — an authored `ToRoof` top, or a framing top within one plate
  course of the storey's ceiling line. Catlin's distribution has a clean hole in it and that is
  the honest basis: **in** at 0" (main, second) and 15/16" (the basement's authored 8'-0"),
  **out** at 6-15/16" and worse, with nothing between. It is what keeps the sauna hot room —
  a room inside a room — the 20" tub-deck curbs, the three fireplace wythe segments and the
  breezeway screen skirt out. Three of those sit inside `platform._MAX_BAND_M`, so that guard
  does not save them.

58 walls pass. The tolerance is widened *downward* by exactly the gap, because the pass moves
the plate it selects and the fastener take-off asks the same question of the resolved model:
without it `W-B-CE` would stop being a partition the moment it was treated as one.

## 6. What is billed, and what is not

`takeoff/partition_fasteners.py` counts **one screw per crossing, never a pitch along the
plate**, because a screw has to land in something. Three cases:

| condition | rule | catlin |
|---|---|---|
| partition **perpendicular** to the framing above | one per resolved crossing | 101 |
| partition **under** a parallel member (≥1" over the plate) | 24" o.c., fencepost both ends | 7 |
| partition **between** members | one blocked bay per framing module | 80 |

The third case is a **blocking condition, and the blocking lumber is billed nowhere.** It is a
required framing condition this model does not carry: `resolve/floor_blocking.py` blocks a
bearing line *under* a wall, which is the mirror joint, not this one. (`attic_studio.py`'s
"SOLID BLOCKING BETWEEN JOISTS" is that mirror joint — `W-A-STU-N`'s **sole** plate.) The row's
`basis` says so in as many words. Splitting the parallel case in two is not optional: coding
only the blocking branch would call for blocking in the twelve bays that already have a joist
in them.

**Three partitions are refused and named rather than billed**, and the refusal rides on the
basis of the rows that were billed — a zero-count line with no part number reaches the
per-trade RFQ and the S-series hardware schedule as an order line for nothing:

* `W-B-CE` and `W-B-BA-E` stand under `SL-M-DECK`'s SIP soffit. There is no wood in it. A
  fastener into a SIP is a different part on a different rule and nobody has chosen one.
* `W-B-WELL` frames no top plate at all.

The gap is **measured, not assumed** — a rafter's underside is interpolated along its own rake
and the raked plate along the wall's — and a measured gap outside the sleeve's range bills
nothing. That refusal is also what would have stopped this billing a screw across the
-11-7/8" gap the attic had before §1 was fixed, which is why the geometry had to land first.

## 7. The other side of the document: what the JOIST MAKER permits

§3 left this open — "every member these screws land in is an engineered product … nobody has
read the other side." This is that read (2026-09-19). It is research, not a calculation; no
number here is oracled.

### 7.1 Sources

| | |
|---|---|
| Weyerhaeuser **TB-808**, *Bottom Flange Trus Joist® TJI® Joist Attachment Connections*, July 2025 (expires 7/2027) — Table 1 (flange sizes), Table 2 (withdrawal), the four design-consideration bullets | [PDF](https://www.weyerhaeuser.com/application/files/1517/5399/9413/TB-808.pdf) |
| Weyerhaeuser **TB-206**, *Fastener Spacing in Weyerhaeuser Engineered Wood Products*, July 2026 (expires 3/2027) — Table 1 (TJI joists) with footnotes [1], [3], [6], [12] | [PDF](https://www.weyerhaeuser.com/application/files/7217/8552/3166/TB-206.pdf) |
| Weyerhaeuser **TJ-4000** *Trus Joist® TJI® Joist Specifier's Guide*, July 2025 — flange widths (p. 2), "Nail interior partitions to the joists when possible" | [PDF](https://www.weyerhaeuser.com/application/files/5617/5451/8519/TJ-4000.pdf) |
| Simpson **C-F-2023** Fastening Systems catalog p. 105 — the SDPW dimension table | [PDF](https://supplyhog.nyc3.cdn.digitaloceanspaces.com/orgill/docs/Simpson_Strong_Tie_103403162_Catalog.pdf) |
| Simpson Strong-Tie (UK/EU) **SDPW technical data sheet** — the installation sequence and "The polymer sleeve shall not penetrate into the supporting member" | [PDF](https://pim.strongtie.eu/api/v1/public/download/gb/en/product/2163/SDPW.pdf) |

**Not found, and stated rather than invented:** the text of **IAPMO UES ER-192 Table 37** and of
**C-F-2025TECHSUP pp. 100–101** could not be retrieved (no public copy; `uniform-es.org` served
an empty file, strongtie.com is JS-rendered). The "flange ≥ 1-1/8"" gate is corroborated only
indirectly, by the Simpson AU data sheet's "I-Joist shall have minimum flange thickness of
28.5 mm" (= 1.122"). **ICC-ES ESR-2236 is the wrong report** — it covers SDS/SDW screws; the
SDPW is listed under ER-192. And **no floor-truss fabricator (MiTek, Alpine) publishes a
fastener schedule for screws into chords at all**: the truss side's published guidance is
SBCA's, and it is about the joint, not the screw.

### 7.2 The facts read, against what this house has

| | TJI 230, 11-7/8" | open-web floor truss, 11-7/8" |
|---|---|---|
| where | `RF-HOUSE` rafters, `FS-M-WEST/MECH/STAIR/EAST`, `FS-S-EAST`, `FS-ATTIC` | `FS-S-WEST` only |
| target | bottom flange, **1.25" thick × 2.30" wide** (TB-808 Table 1; TJ-4000 spells the width 2-5/16") | 2x4 SPF **flat** bottom chord, 1.5" × 3.5" |
| species | flange graded at **G = 0.50** (TB-808) | SPF, **G = 0.42** |

⚠ **`profiles._TJI_SERIES_IN` carries `"230": (2.3125, 1.5, 0.375)` — the 1.5" flange thickness
is wrong.** TB-808 Table 1 publishes **1.25"** for TJI 110/210/230 (1.375" is 360/560). Nothing
downstream breaks today (1.25" still clears both the 1-1/8" gate and the 3/4" penetration), but
a guard answered off the resolved section would be answering off 1.5".

**And the part is fatter than §3's table says.** C-F-2023 p. 105: SDPW19600 is **0.275" O.D.
(thread outer) on a 0.195" shank**, thread length **3"**, sleeve 3.10", T-40. §3's "6" × 0.195"" is
the shank. The 5" SDPW14500 is 0.205"/0.205", thread 2".

### 7.3 Verdict per floor system

**TJI 230 — PERMITTED, CONDITIONED, and the conditions are Weyerhaeuser's, not Simpson's.**

* The flange passes Simpson's own gate: 1.25" ≥ 1-1/8".
* Penetration: 6" − (3/4" gap + 3" double plate) = **2.25"** below the plate. The flange is only
  1.25" thick, so ~1" of tip sits in the 3/8" OSB **web**. TB-808: *"Penetration into the web is
  permitted."* Simpson's 3/4" minimum is met inside the flange alone. The 3" thread covers the
  whole 2.25", so no shank stands in the flange.
* Edge distance: TB-206 fn [3] recommends **5/8"** on a TJI 230. A screw on the joist centreline
  has ~1.15". The 3/8" predrill must therefore be centred on the joist — which is already the
  installation instruction ("ensuring the hole … aligns with the centre of the joist/truss").
* **The screw is outside TB-206 Table 1.** Footnote [1] extends the nail spacings to wood screws
  only *"provided the lengths and root diameters are less than or equal to the nail sizes listed"*
  — the fattest listed is 16d common at **0.162"**, and this shank is 0.195". So Weyerhaeuser
  publishes **no row** for it in a TJI flange, and footnote [12] is what governs instead: *"See
  screw manufacturer's recommendations … End distances, edge distances, and capacity … must be
  sufficient to minimize splitting."* The question is handed back to Simpson, which is a
  permission, not a refusal — but it means **no Weyerhaeuser spacing row may ever be quoted for
  this screw**. The nearest published row (16d common, wide face of flange, TJI 110/210/230) is
  **6" o.c. / 6" minimum end distance**, and it is a conservative stand-in, not a citation.
* The load path is lateral. TB-808's **500 lb per 5 ft** bottom-flange concentrated-load cap
  (250 lb each side, no duration increase) is a *gravity* limit and this joint carries nothing
  downward by design — but if the release ever failed, 165 lbf × two screws in 5 ft is inside it.
* TJ-4000 contemplates the joint in its own words — *"Nail interior partitions to the joists when
  possible"* — though in its squeak-prevention context, for a wall standing **on** the deck.

**Open-web floor truss (`FS-S-WEST`) — PERMITTED, and the condition is not the fastener.**
The chord is 1.5" × 3.5" SPF: 3/4" penetration is trivial, a centred screw has 1.75" of edge
distance, and ER-192's allowable is itself derived at SPF G = 0.42, so the published number
describes this member exactly rather than conservatively. Nothing in the fastener is at issue.
What *is* at issue is the truss: a chord is a designed member and a partition hung off it is a
load the fabricator must have been given. `FS-S-WEST` is already blocked on a fabricator
submittal (`plans/TODO.md`, and catlin's own `CLAUDE.md`), and **this joint goes on that
submittal**: the screw must land in a **chord**, never a web or a plate connector, and the
partition's out-of-plane reaction must be named on the truss design drawing.

**`SL-M-DECK` (SIP) — unchanged.** §6 already refuses `W-B-CE` and `W-B-BA-E`; nothing here
opens them.

### 7.4 What the E6 `PublishedSpan` row must carry as guards

Already implied by §3, and each must be *answered* or `_unanswered` makes the row a drift
UNKNOWN:

1. `double 2x top plate` — 3.0". The row is published for that plate and no other.
2. gap 3/4", within the part's published 0 – 1-1/2".
3. penetration into the supporting member ≥ 3/4", **all of it in the flange or chord**.
4. spacing ≤ the table's worst case for this part, **42" (8' wall) / 36" (10' wall) at 5 psf**.
5. SPF at G = 0.42, ASD, C_D = 1.6, safety factor 5.0 — lateral only; **no uplift or withdrawal
   is claimed** (`uplift_lb` stays `None`).

New, from this read, and the reason E6 was blocked on it:

6. **supporting flange thickness ≥ 1-1/8"** (ER-192's gate). Answer it at **1.25"** for a
   TJI 230 — *not* at the resolved section's 1.5", which is wrong (§7.2).
7. **edge distance ≥ 5/8"** from the flange edge on a TJI (TB-206 fn [3]); the screw is on the
   member centreline.
8. **end distance ≥ 6"** from a flange end, and **on-centre spacing ≥ 6"** (TB-206 Table 1, 16d
   common, wide face — the nearest published row). Never binding at one screw per crossing, but
   it is the guard that would catch a screw driven at a joist end or a trimmed truss end.
9. **the screw enters the WIDE face of the flange** (the soffit), never the narrow edge — TB-206
   lists 16d common into a narrow edge as *"Not Recommended"*.
10. **supporting member is a TJI flange or a floor-truss chord**, never a SIP, a web, or a plate
    connector.
11. **a Weyerhaeuser spacing row may not be cited for this fastener** — 0.195" root exceeds every
    nail in TB-206 Table 1 (max 0.162"). If the check ever tries to grade spacing against a
    Weyerhaeuser table, that is a drift UNKNOWN, not a PASS.

Guard 11 is the one that makes the row honest: this joint is permitted by the joist maker's
*general* rule and by the fastener maker's own report, and by no published row that names both.

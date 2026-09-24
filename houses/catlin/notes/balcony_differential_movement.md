# The balcony's tilted beams, their bearings, and what actually moves — hand-worked basis

**House:** catlin
**Structure:** `BM-SG-BLW/BLC/BLE` (the three treated-glulam balcony beams), the six pillars
under them (`PT-SG-B{R,F}{1,2,3}`), the six `SS316-SHIM-35` standoff packs at their seats
(`CN-SG-STDF-*`), `FS-SG-DECK`'s aluminium plank, and the four beam-pocket hangers
`CN-SG-HGR-W/-E/-FW/-FE`.
**Written:** 2026-09-12, by hand. It oracles no calculation module: nothing here is encoded,
and §7 says so positively.
**Companions:** `notes/centre_pillar_bearing.md` grades the bearing STRESS at the three-ply
pack under `PT-SG-BR2`/`BF2` and says nothing about its shrinkage — §6 is the other half.
`notes/balcony_moment_columns.md` carries the four cast columns and the glulam span.
`notes/beam_water_protection.md` carries the pocket and the beam tops as a water question.
**What is asked of the reviewer:** three things, in order of consequence. (1) §5's aluminium
expansion gap — the number has to come from Wahoo's installation guide and could not be
retrieved; the arithmetic beside it says how large the movement is. (2) §3's lapped-shim
taper, as a detail a carpenter can actually build. (3) §2's door: the tilted deck now meets
`D-S-DECK-E` 2.42" ABOVE the study's finished floor.

> ## ⚠ THE THERMAL QUESTION THAT PROMPTED THIS NOTE IS A NON-ISSUE, AND SAYING SO IS THE
> ## POINT — BECAUSE TWO OTHER MOVEMENTS ARE NOT.
> The open item asked whether mixed concrete and wood supports are thermally compatible.
> §4 works it: **0.05" of differential over an 8.4' column across a 130 °F range.** It is
> an order of magnitude below the two movements that matter, which are the aluminium plank
> against the wood frame (§5, ~0.57") and one-way cross-grain shrinkage at the two wood
> centre pillars (§6, 0.1–0.2", permanent). Do not spend a detail on the first and skip
> the other two.

> ## ⚠ THE DECK IS A PLANE NOW, AND ITS HIGH EDGE IS AT THE STUDY DOOR.
> Since 2026-09-23 `resolve/floor_tilt.py` seats each `FS-SG-DECK` joist on the tilted beams
> at its own station and resolves the plank as the plane over them (§2). The datum is the
> beams' south node; the north edge, at `D-S-DECK-E`, stands **2.42"** higher. That put it
> above the study's finished floor, so the datum came down 3" to 9'-9" (owner, 2026-09-23).

---

## 1. The slope, and the two numbers it is between

`SPEC.balcony_fall_in_per_ft` raises the rear (north, house-side) pillar row so the deck
falls south, away from the house.

**2026-09-14: the FALL is now the authored number and the rise is derived from it.** It was
the other way round — `SPEC.rear_pillar_rise_in = 2.0`, with whatever slope that worked out
to over whatever run the bearing rows happened to be at. Owner's call: hold 1/4" per foot,
which is the trade standard for a walking deck and still twice AridDek's published minimum.

| term | working | value |
|---|---|---|
| rear bearing line | `_y_rear_pillar` | −2.500' |
| front bearing line | `_y_front_pillar` | −9.833' |
| run between bearings | (−2.500) − (−9.833) = 7.333' | **88.0"** |
| fall | `SPEC.balcony_fall_in_per_ft` | **0.250 in/ft** |
| rise | 0.250 × 7.333 | **1.833"** (was 2.00") |
| AridDek recommended minimum | manufacturer | 0.125 in/ft |
| margin | 0.250 / 0.125 | **2.0×** |

The slope is correct and generous. `PT-SG-BR2` is graded against IRC Table R507.4. The
"10'-0" at 48.3 ft², 5/32" of room" once recorded here was an engine table bug: the 2018 IRC
gives a 6x6 a flat 14'. Since `BM-SG-BLC` went flush-framed (2026-09-16), BR2 stands 10.59'.

Two answers that close the parts of the open item that were about the *mechanism*:

* **A chamfer cannot produce slope.** A chamfer is a bevel on a corner. The fall runs N–S,
  *along* the beams, and it is the whole member that has to leave level.
* **Sleepers are a dead end in both directions.** Laid on the joists they would run N–S,
  parallel to the AridDek plank, and the plank would lose the perpendicular bearing it is
  designed around. Laid on the beam tops they move the interference from column-into-beam to
  joist-into-beam, because `FloorSystem.top_elevation` is a single value too.

## 2. What the engine did with the slope until 2026-09-12, and what it does now

`resolve/envelope.py::_resolve_post` shortens a post's authored height rather than overriding
its top, and its docstring says this is precisely so "any intentional base offset (the 2"
rear-row drainage rise)" survives. It does survive. `_resolve_beam` then emitted a flat
prism, so the beams never tilted. Measured off `out/model.json` before the fix:

| element | top |
|---|---|
| `PT-SG-BR1` / `BR2` / `BR3` | 102.875" |
| `PT-SG-BF1` / `BF2` / `BF3` | 100.875" |
| `BM-SG-BL{W,C,E}` soffit | 100.875", flat |

**Every rear column ran 2" up inside the beam it carries, and `haus check` reported 0 FAIL.**
`structural.concrete_interference` is scoped to isolated pours, and nothing in the engine
grades a column tangent to a beam.

The fix is `Beam.top_rise_end` (`model/structure.py`): the end node's top relative to the
start node's, resolved through a `SolidSweep` because a member out of level is not a prism.
The three beams are now authored south-end-first and tilted 2.636" over their 116" length —
the 88" between bearings plus the 8" they oversail the front row and the 20" they oversail
the rear. Re-measured after:

| station | beam soffit | post top | gap |
|---|---|---|---|
| front bearing, y = −9.833' | 100.8750" | 100.8750" | **0** |
| rear bearing, y = −2.500' | 102.8750" | 102.8750" | **0** |

**The joists and the deck follow the beams (2026-09-23).** `resolve/floor_tilt.py` reads
each joist end's z off its own bearing — the beam's top at that joist's station — so
nothing is authored twice (`FloorSystem.top_rise`, which restated the beams' rise, is
gone). Both beams rise alike, so each joist is level E-W: a staircase of 1/4" steps across
the 12" o.c. field. The plank is the plane over those tops. Worked by hand at 1/4 in/ft
(1/48 in/in), datum at the beams' SOUTH node, y = −10'-6" (the plank's south edge), joist
top 9'-9" = 117.000" since 2026-09-23 (`FS-SG-DECK.top_elevation`; 3" under the old 10'-0"):

| station | y | rise over datum | joist seat (beam top) | plank top |
|---|---|---|---|---|
| plank south edge, beam start | −126" | 0 | 117 − 11.25 = 105.750" | 117 + 1.5 = **118.500"** |
| first joist line | −125.25" | 0.75/48 = 0.0156" | **105.766"** | — |
| last joist line | −10.75" | 115.25/48 = 2.401" | 108.151" | — |
| plank north edge, beam end | −10" | 116/48 = **2.417"** | 108.167" | **120.917"** |

Until this change the datum sat at the first joist line, so every joist hung **1/64"** inside
its beam (`joints/bearing.py` carried the slack for it); now the seat is exact.

**What it found — `D-S-DECK-E`.** The door is in `W-S-S2` (axis y = 0, exterior face
−6.94"), over the deck's HIGH edge. Model threshold = wall framing base 120.000" + sill 0;
`RM-S-STUDY2`'s finished floor (oak) 121.500". At the 10'-0" datum the deck there was
123.917": **3.92" above the model threshold and 2.42" above the finished floor** — it was
flush (121.500") while the
plane was flat. `code.R311_3_exterior_landing` now FAILs: its landing band reaches 0.05 m
(1.97") above a threshold, and a deck standing a step UP at an in-swinging door is also a
water question. Closing it is a design decision (lower the balcony datum ~2 3/8", or step
the deck at the door), not an engine one.

**Closed 2026-09-23 (owner): the datum came down 3".** Deck at the door 120.917": 0.92" above
the model threshold (inside R311.3's 1.5"), **0.58" below the finished floor**; PASS. The
fall is unchanged, and so is every column-to-beam seat — beams and columns moved together.

## 3. A tilted beam needs a tapered bearing, and the part is already at every seat

A 0.0227 in/in tilt across a 6" bearing leaves **0.136"** of gap at the uphill edge
(6 × 0.0227). A tilted beam set on a level cast seat therefore bears on a *line*, not a
plane, and the 27 sq in of bearing §7 of `notes/centre_pillar_bearing.md` relies on is not
there until something takes up the taper.

**Do not specify a custom tapered metal shim.** Tapered stainless shims are laser-cut or CNC
items from shim specialists; they are not a stock construction part, and a detail that calls
for one turns a carpentry operation into a fabrication lead time.

Use what is already at all six of these seats: `SS316-SHIM-35`, the 1/2"–1" 316 stainless
standoff shim pack authored at `CN-SG-STDF-R1/R3/F1/F3` and `CN-SG-STDF-COL/FCOL`. A shim
*pack* is a stack of leaves; lapping the leaves — full leaves at the low edge, progressively
short ones toward the high edge — forms the 1/8"-over-6" taper directly, over the EPDM
isolator the seat detail already prescribes, which conforms the last few thousandths under
load. Two published positions say this slope is inside the range a conforming pad handles:

* **SJI** does not require a sloped bearing seat below **3/8" per foot**. This deck is at
  0.273 in/ft, comfortably under.
* **Bridge practice** specifies tapered elastomeric bearing pads for sloped girders to the
  nearest **1/16"**. 0.136" over the bearing is two of those steps.

## 4. The thermal question, worked — and it is a non-issue

| term | working | value |
|---|---|---|
| column height | `PT-SG-BF1`, base to soffit | 8.4' = 100.8" |
| concrete α | published | 5.5 × 10⁻⁶ /°F |
| wood α, parallel to grain | published range 1.7–2.5 × 10⁻⁶ | take 2.5 × 10⁻⁶ /°F |
| temperature range | −30 °F to +100 °F, Ramsey County | 130 °F |
| concrete movement | 100.8 × 5.5e−6 × 130 | **0.072"** |
| wood movement | 100.8 × 2.5e−6 × 130 | **0.033"** |
| differential | 0.072 − 0.033 | **0.039"** |

Under 1/25". And wood's drying shrinkage runs the *other* way over the same season, which is
why WoodWorks' published position is that wood-frame buildings need not account for thermal
movement at all. **The concrete-to-wood pairing needs no expansion detail.**

## 5. The movement that does need a number: the aluminium plank

| term | working | value |
|---|---|---|
| deck width, E–W | `_DECK_OUTLINE` | 21.5' = 258" |
| 6005-T5 aluminium α | published | 13 × 10⁻⁶ /°F |
| surface swing, dark deck in sun to winter night | −30 °F to +140 °F | 170 °F |
| cumulative growth across the field | 258 × 13e−6 × 170 | **0.57"** |

**An order of magnitude larger than anything the supports do**, and it accumulates through
the interlocked plank joints rather than at one end. This is the only expansion detail on
this deck that needs a dimension, and the dimension is Wahoo's: their published gap
requirement is in the AridDek installation guide and was not in the public pages. **Pull it
before the plank is ordered.** The arithmetic above says what it has to accommodate.

## 6. ~~The movement that does need a detail: cross-grain shrinkage at the two centre pillars~~ — VOIDED 2026-09-14

> **There is no cross-grain path at these two pillars any more, so this section grades a
> joint that no longer exists.** On 2026-09-14 `PT-SG-BR2` and `PT-SG-BF2` came off
> `FS-SG-PORCH` and onto the concrete column tops — `PT-SG-COL` and `PT-SG-FCOL` — on
> ABU66SS standoff bases. **All six pillars bear on concrete now**, so the dishing this
> section is about cannot happen: there is no softwood depth across the grain under any of
> the six, and the three-ply sister pack the argument rests on was retired with the
> arrangement (`_DECK_BORNE_PILLAR_REINFORCEMENTS` in `params/sunken_garden.py`).
>
> Of the three answers below, only **(3)** survives, and it survives for a different reason:
> the `CCQ46SDS2.5` cap stays shim-adjustable at those two seats because a six-point bearing
> on two pours and two wall tops still wants a way to take a leaf at the first-season
> inspection. (1) and (2) are about a pack that is gone.
>
> Kept rather than deleted because the reasoning is what a reader restoring the deck-borne
> arrangement needs — it is the movement half of the joint `notes/centre_pillar_bearing.md`
> grades the stress half of, and that note is kept for the same reason. See its own
> 2026-09-14 section.

Four of the six pillars bear on concrete. `PT-SG-BR2` and `PT-SG-BF2` do not: they stand on
`FS-SG-PORCH`, on the three-ply 2x12 sister pack `notes/centre_pillar_bearing.md` grades.

Cross-grain shrinkage in an 11 1/4" depth of softwood, green to in-service EMC, is on the
order of **0.1–0.2"** — *permanent, one-way, and at the middle two of six supports*, so what
it does is dish the centre of the deck. It is not cyclical and no gap absorbs it.

Three things answer it, and all three are already in the model:

1. **The squash blocks at the beam line bypass most of the cross-grain path.** Load runs
   through end grain rather than across the ply depth wherever they are continuous.
2. **Specify KD stock for the sister pack.** Kiln-dried at lay-up puts the plies near
   in-service EMC, which is most of the movement gone before the pillar is set.
3. **Keep the `CCQ46SDS2.5` cap shim-adjustable at those two seats.** A cap that can take a
   leaf at the first-season inspection is the difference between a detail and a repair.

## 7. What is NOT graded here

* **No calculation module reads this note.** Nothing in §§1–6 is encoded, no check reports
  it, and `haus engineering` carries no item for it. It is a hand-worked record of three
  movement questions and their answers; if any of it is later encoded, `oracled_by` is where
  it gets registered.
* **The beam's bending, shear and deflection are not here.** They are a prescriptive read
  against a published span table (`_BALCONY_BEAM_PUBLISHED`), graded by
  `checks/structural/published.py`.
* **The bearing STRESS at the centre pillars is not here** — `notes/centre_pillar_bearing.md`
  §2–4. This note covers only what that joint does over time.
* **The four beam pockets' hanger capacity is not here.** `HUC212-3`'s published concrete row
  is recorded on the catalog record itself (`library/hardware/`), and §8 below is only the
  part of that joint this note owns.
* **No wind, seismic or snow load appears anywhere above.** Every movement here is thermal or
  hygroscopic.

## 8. The four beam pockets, as a movement and durability joint

The back and front porch beams land in 6" pockets cast in the 12" `W-SG-W1`/`E1` walls, on
`HUC212-3` concealed-flange hangers (retyped from `HUCQ410-SDS` on 2026-09-12 — that part is
not published for concrete and its seat was 15/16" too narrow; `library/hardware/`).

**The hanger is not what carries the beam.** 4 1/2" × 6" = **27 sq in** of the three-ply
bears directly on the cast sill of the pocket, and that is the gravity path whatever hangs
beside it. The hanger's work here is uplift and lateral restraint, and its published
5,085 lbf concrete download is headroom rather than load path. A reviewer should not credit
the hanger with work the sill is already doing, and a value engineer should not delete the
hanger on the grounds that the sill carries the load.

**Detail the pocket against standing water, and it is not optional.** The C-C masonry/concrete
hanger table's footnote 5 reads *"Products shall be installed such that Titen screws are not
exposed to weather"*, and a pocket in the wall of an open garden is weather until it is
detailed not to be. What makes the footnote satisfied: the pocket floor back-sloped to drain
outward, a formed pan flashing under the bearing turned up at the back and lapped out over
the wall face, an air gap at the beam end and sides so the end grain is not buried in a damp
socket, and sealant at the top of the pocket only — never at the bottom, which would make the
socket a cup. `notes/beam_water_protection.md` is the note that owns this detail; it is
repeated here because the fastener's published capacity now depends on it.

## Sources

- Simpson Strong-Tie *Wood Construction Connectors* catalog **C-C-2017**, p. 280,
  "HU/HUC/HSUR/L Hangers (cont.)" — the masonry/concrete table, updated 04/17/17, read
  2026-09-12. HUC212-3 (Max.), Concrete columns: 1,800 lbf uplift (160%), 5,085 lbf download
  (100/125%), through (22) 1/4" × 2 3/4" Titen 2. Footnote 5 is quoted in §8.
- Simpson Strong-Tie C-C-2017, p. 136 — Face-Mount Hangers, Solid Sawn Lumber (SPF/HF),
  HU212-3 / HUC212-3 row: 14 ga, W 4 11/16", H 10 5/16", B 2 1/2".
- AWC **NDS 2018** Supplement — softwood shrinkage coefficients (§6) and thermal expansion
  parallel to grain (§4).
- **WoodWorks**, "Thermal expansion in wood-frame buildings" — the published position that
  thermal movement need not be accounted for in wood-frame construction (§4).
- **SJI** *Standard Specification for Joist Girders / K-Series* — bearing seats need not be
  sloped below 3/8 in per foot (§3).
- **AASHTO LRFD Bridge Design Specifications** §14.7 — tapered elastomeric bearing pads for
  sloped girders, specified to the nearest 1/16 in (§3).
- **Aluminum Association** *Aluminum Design Manual*, Part I — 6005-T5 coefficient of thermal
  expansion, 13 × 10⁻⁶ /°F (§5).
- **Wahoo Decks AridDek installation guide** — minimum slope (1/8 in per foot, §1) and the
  plank expansion gap (§5, **NOT RETRIEVED** — the public product pages do not carry it).

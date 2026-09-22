# What the trades may cut out of this house's framing — worked by hand

Oracle for `typehaus/resolve/mep_bores.py`, `mep.run_through_stud`, `mep.run_through_plate`,
`mep.run_through_header` and the R502.8.1 half of `mep.run_member_crossing`. Reproduced by
`packages/engine/tests/test_mep_bores.py` (§1-§5) and
`packages/engine/tests/test_e2_header_and_plate_tie.py` (§6-§7).

IRC R502.8.1 (joists) and R602.6 / R602.6.1 (studs and plates) were on `mn_residential`'s
**not-covered** list from the day the profile was written until 2026-09-17. Everything below
was worked from the code text and this house's own resolved members, before the predicates
existed.

---

## 1. The three percentages, and why the wall's job decides them

R602.6 states its limits as fractions of the stud's **depth** — the 5 1/2" of a 2x6, the
3 1/2" of a 2x4 — not of its 1 1/2" face. Four numbers, and the pair that matters most here
is the first two:

| condition | notch | bore |
|---|---|---|
| bearing wall / exterior wall | 25% | 40% |
| non-bearing partition | 40% | 60% |
| doubled stud (max **two successive**) | — | 60% |

And one dimension that is not a percentage: **5/8" of stud must remain either side of the
hole**, whatever the fraction says.

**Worked on this house's two stud sizes, for a 2" DWV vent** (2.375" real outside, from
`resolve/pipe_sections` — the nominal 2" is not the hole):

* **2x4, non-bearing.** 60% × 3.500" = **2.100"**. The pipe is 2.375". **Over by 0.275".**
  This single line of arithmetic is the whole reason a vent wall is framed 2x6, and it is
  why `PR-B-SAUNA-VENT`, `PR-A-STUBATH-VENT` and `PR-A-BAR-VENT` are all findings.
* **2x6, non-bearing.** 60% × 5.500" = **3.300"** ≥ 2.375". Legal, with
  (5.500 − 2.375)/2 = **1.562"** of stud either side — comfortably past the 5/8" edge rule.
* **2x6, bearing.** 40% × 5.500" = **2.200"**. The pipe is 2.375". **Over by 0.175".** The
  same pipe, the same stud, and the wall's job flips the verdict. Nothing in the geometry
  says which it is, so the check reads `JoistSpec.bearing_refs` — the model's own statement
  of what carries what — rather than guessing from "exterior".

**And a 3" drain**, 3.500" outside: 3.500 > 3.300, so a 3" drain is over the limit in a
non-bearing 2x6 by two-tenths of an inch. `PR-B-WC2-DRAIN` is that case. A 3" drain in a
2x6 is at the line in every house; the honest fixes are a 2x8 wet wall or a furred chase,
and neither is something an engine may pick.

**And a 4" ERV radial**, 4.000" outside: over the non-bearing 2x6's 3.300" by seven-tenths
of an inch and over a bearing 2x6's 2.200" by nearly two. Three of catlin's basement
radials are that case. A 4" round duct is not bored through a stud in practice at all — it
goes over the plate, through a soffit or in a floor bay — so these want re-routing rather
than a bigger hole.

**What is NOT a bore at all.** Once the penetration is **as wide as the member's own
depth** it has stopped being a hole drilled in a member that stays whole: a 6" duct does
not go through a 2x6, it goes through a framed opening with a header over it, and R602.6
governs neither. The verdict there is **UNKNOWN with that sentence**, not "exceeds 60%" —
reporting an 18" duct as an over-size bore is arithmetic about a hole nobody would drill.
No table in this engine grades the header either, and §6 says so by name rather than by
silence. Catlin's 6",
10" and 18" duct-through-wall penetrations are all in this class, and they were eight of
the nineteen findings before the rule was stated.

---

## 2. `W-S-SN3`, the staggered wet wall — counted stud by stud

The case the reviewer's framing policy names: *"a staggered wall uses the actual stud
positions, never 'the wall is empty'."* This wall is `INT_2X6_STAGGERED_PLUMBING` — a 2x6
plate with 2x4 studs alternating between two rows — and it is the wall the suite bath was
laid out around.

**What resolves.** Axis on **y = 268"**, from x = 115.5" to x = 216.0". Thirteen studs:
`stud-000` is a 2x6 at the end, and `stud-001`…`stud-012` are 2x4s at x = 123.5, 131.5,
139.5, … every 8", alternating **y = 267"** (odd) and **y = 269"** (even).

**Each 2x4's plan footprint.** `orient` is (1, 0), the wall direction, so the 1 1/2" face
lies along the wall and the 3 1/2" depth across it. A stud centred at y = 267 therefore
occupies **265.25 … 268.75**, and one at y = 269 occupies **267.25 … 270.75**. The two rows
overlap over 267.25 … 268.75, which is 1 1/2" of shared band down the middle of the wall.

**A 2" vent travelling along the wall, at three stations.** Its swept plan band is its
centreline ±1.1875".

| centreline | band | rows it meets | studs bored |
|---|---|---|---|
| **y = 268"** (the axis) | 266.81 … 269.19 | both | **11** |
| **y = 270"** (north row) | 268.81 … 271.19 | 269 only | **5** |
| **y = 266"** (south row) | 264.81 … 267.19 | 267 only | **6** |

Six against eleven, from a two-inch move. That is the number a rule applied to "the wall"
cannot produce, and it is the number that decides whether this run is buildable: eleven 2x4
bores at 2.375" are eleven findings, and five are five — all of them still over the 2.100"
limit, because the stagger changes how MANY studs are cut and not whether the hole fits.

(The counts are 5 and 6 rather than 6 and 6 because the leg is worked from x = 120" to
x = 210", which starts past `stud-001` on one row and stops short of `stud-012` on the
other. The point is the ratio, and it is exact.)

---

## 3. A top plate is conditional, not forbidden

R602.6.1: a top plate cut or notched more than **50% of its width** needs a galvanized metal
tie **16 ga (0.054") × 1 1/2"**, lapping **6" past the opening each way**, with **eight 10d
nails each side**.

* **2x6 plate, 3.500" wide face** — wait, a plate lies flat, so its width is the wall's
  nominal depth: 5.500" for a 2x6 wall, 3.500" for a 2x4. Half of those is **2.750"** and
  **1.750"**.
* A 2" drain (2.375") through a **2x4** plate is over the line and needs the tie.
  A 3" drain (3.500") through a **2x6** plate is over it too. Both are the ordinary detail.
* A 1 1/4" supply (1.375" outside) through either is under it and needs nothing.

**The over-50% case was UNKNOWN until 2026-09-19, and the reason was a missing word.** The
section *permits* the cut with a tie, and the model had no vocabulary for a plate tie at all —
`FramedMember.connection` is a free-form string nothing reads for this — so the absence of a
tie in the model was not evidence of absence on the job. §7 closes that.

---

## 4. Joists: R502.8.1, and the two limits the z window does not cover

`mep.run_member_crossing` already asks whether a run FITS between a floor's members
(`resolve/mep_crossings.member_window`, the drain note's §3). That is not the same question
as whether the HOLE is legal, and on a solid-sawn joist the two can disagree:

* **hole ≤ D/3.** A 2x8 is 7.250" deep, so the window under R502.8.1 (2" clear of both
  edges) is 3.250" — and D/3 is **2.417"**. A 3" drain at 3.500" outside fails both; a
  2 1/2" hole at 2.875" fits the window comfortably and is still **0.458" over D/3**. That
  gap is what the second limit is for.
* **2" clear of any other hole or notch.** Two 2" drains crossing the same joist 3" apart
  on centre leave 3.000 − 1.1875 − 1.1875 = **0.625"** between their edges. Each hole is
  legal on its own; the pair is not. No per-run pass can see this, so the check collects
  every crossing on a floor keyed by member first.
* **no notch in the middle third of the span**, ever; ≤ D/6 in the outer thirds, ≤ D/4 at
  an end bearing, and no notch longer than D/3.

**None of it applies to an engineered member.** An open-web truss hands a service its web
space and cuts nothing; an I-joist and an LVL are cut to the fabricator's chart. Those are
**UNKNOWN**, and a generic "open webs are borable" is not evidence that THIS hole is. On
catlin that covers nearly every floor — the 11 7/8" floor trusses and the 11 7/8" I-joists
alike — which is why §4 has no catlin FAIL to point at and §1 and §2 have eleven.

---

## 5. What this note does not do

* **No structural grading of what is left.** R502.8.1 and R602.6 are prescriptive envelopes.
  What a legal hole does to a member's capacity is `structural.*`'s question, and neither
  section asks it.
* **No repair is proposed.** R602.6.1's tie is stated as the condition under which a cut
  plate is acceptable, never as something the engine adds to a model. Introducing a strap,
  a reinforcement or a wider stud to make a route legal is a structural redesign and
  belongs to a person.
* **No notch is ever proposed.** A run wants a bore; where the model authors a notch it is
  graded, and the router will not invent one at any price.

---

## 6. A header is collected, and honestly ungraded

**The bug was one literal.** `leg_crossings` listed the categories it would measure —
`stud`, `king`, `jack`, `cripple`, `plate`, `sill` — and `header` was not among them. So a
run passing over a door met *nothing*, and the report was silent about the one member in a
wall carrying an opening's whole tributary load into two jacks. Silence is not a verdict, and
it is the failure mode this whole module exists to end.

**`header` is NOT added to `STUD_CATEGORIES`, and that is deliberate.** R602.6 describes
studs. A stud is a column: the question a hole asks it is how much section is left to carry
axial load, which is why the rule is a plain fraction of the depth. A header is a beam with a
point load's worth of roof or floor on it, and what a hole costs it depends on where along
the span it sits and what the span carries. The two questions are not the same question and
one table cannot answer both. So a header gets its own predicate, `header_bore`, and its own
check id, `mep.run_through_header`.

**And the honest answer is UNKNOWN.** No IRC section publishes a bore or notch table for a
header: R502.8.1 is floor joists, R802.7 is rafters and ceiling joists, R602.6 is studs, and
R602.7 sizes headers without saying anything about drilling one. Grading a 2-2x8 header
against R502.8.1 because its section is also a rectangle is exactly the mistake `_engineered`
refuses one product family further along. So the verdict prints the numbers — the diameter,
the depth — and names the gap, with the remedy being the header designer's own allowable.
R502.8.1's D/3 is quoted **for scale only**, and the basis text says so in those words.

**One case is determinate and needs no table**: a penetration as deep as the member. That is
not a hole drilled in a member that stays whole, it is the header's removal, and a severed
header does not carry the opening under it. FAIL.

**Worked on this house.** Six runs meet a header, all of them `2-2x8` (3.000" x 7.250"):

| run | wall | penetration | verdict |
|---|---|---|---|
| `PR-B-KITCH-DRAIN` | `W-B-CW` | 2.38" | UNKNOWN — inside a joist's D/3 = 2.42", which decides nothing here |
| `PR-M-S-BATH1-DRAIN` | `W-B-CW` | 3.50" | UNKNOWN |
| `PR-B-MAIN-DRAIN` | `W-B-CW` | 4.50" | UNKNOWN |
| `DU-B-ERV-R-SAUNA-SUP` / `-EXH` | `W-B-CW` | 4.00" | UNKNOWN |
| `DU-B-ERV-R-GYM` | `W-B-CS3` | 4.00" | UNKNOWN |

Six UNKNOWNs where there were none is not a regression — it is six holes through a header
that nobody had looked at. Four of the six are over half the header's depth, which is the
kind of number a person wants in front of them whether or not a table grades it.

### 6a. Where along the header, and how much of it (2026-09-22)

**Every one of those six printed dead midspan until today, and the station was a bug.**
`leg_crossings` read `shape.centroid` for both the station and the elevation it sampled the
run at. For a STUD that is where the run meets it, and nothing moved. For a HORIZONTAL
member — a plate, a sill, a header — the centroid is the member's own midpoint, so all six
crossings of `header-0` reported x = 57.00" (the middle of a 37.50"–76.50" member) and were
graded at the elevation the run happens to have there. A hole's cost to a bending member is
a question about WHERE ALONG THE SPAN it sits, so a midspan station is not a detail: it is
the single fact a hole chart is indexed on. The station is now the centroid of the run's own
AXIS where it lies inside the member, falling back to the swept envelope where the axis
misses and only the envelope grazes. (The axis, not the envelope: an envelope clipped by the
member's END drags its own centroid inward, which put the 39.00" crossing at 39.25".)

**And a partial overlap is a NOTCH, not a bore.** `MemberCut.through_in` is how much of the
run's outside diameter the member actually loses at that station — the run's OD band clipped
against the member's own z band. `DU-B-ERV-R-SAUNA-SUP` runs at −21.94", 0.25" above the
header's −22.19" top, so a 4" duct takes **1.75" off the top face** and not a 4" bore; it
was only ever admitted by `leg_crossings`' ±radius slop and now says why. The rest sit
wholly inside the member and their `through_in` equals their diameter.

| run | member | station (x, y) | z | OD | cut | reading |
|---|---|---|---|---|---|---|
| `DU-B-ERV-R-SAUNA-SUP` | `W-B-CW` `header-0` | **39.00", 216"** | −21.94" | 4.00" | **1.75"** | notch off the top, **dead on the west jack face** (RO is x 39"-75") |
| `DU-B-ERV-R-SAUNA-EXH` | `W-B-CW` `header-0` | **45.00", 216"** | −23.44" | 4.00" | **3.25"** | notch off the top, 7.50" in from the member end (6.00" from the west jack face) |
| `PR-B-KITCH-DRAIN` | `W-B-CW` `header-0` | **54.00", 216"** | −27.21" | 2.38" | 2.38" | bore, 3.00" west of midspan, low in the section |
| `PR-M-S-BATH1-DRAIN` | `W-B-CW` `header-0` | **54.77", 216"** | −26.48" | 3.50" | 3.50" | bore, near midspan |
| `PR-B-MAIN-DRAIN` | `W-B-CW` `header-0` | **72.00", 216"** | −25.04" | 4.50" | 4.50" | bore, **3.00" from the east jack face** (RO ends x=75") |
| `DU-B-ERV-R-GYM` | `W-B-CS3` `header-0` | **216", 156.00"** | −25.44" | 4.00" | 4.00" | bore, 8.94" from the member's north end (7.44" from the north jack face) |

Both headers are `2-2x8` (3.000" x 7.250"), 39.00" long, z −29.44"…−22.19". Every verdict is
still UNKNOWN: no IRC table reaches a header and none was invented to reach one. What changed
is that the numbers a person (or a published chart) needs are now true.

**The short-cripple gap — recorded, NOT exploited.** Above `D-B-FURN`'s header there is
**6.56"** of cripple to the plate. `stud_bore` grades a hole against the stud's DEPTH
(a non-bearing 2x8: 60% of 7.25" = 4.35"), and says nothing at all about the member's
LENGTH — so this engine would **PASS a 4.00" hole through a 6.56" cripple**, leaving 1.28" of
wood above it and 1.28" below. R602.6 is written about a stud running floor to plate; a
6.56" block with a 4" hole in it is not a bored stud, it is two 1.28" slivers. No route in
this house may be taken through that zone on the strength of that PASS. Closing the gap
properly means a length-aware predicate (a hole's clear wood above and below, as R502.8.1
states for a joist's edges), and it is not attempted here.

---

## 7. `PlateTie` — the word the model was missing

R602.6.1 permits a top plate cut past 50% of its width **with** a galvanized 16 ga x 1 1/2"
tie lapping 6" past the opening each way on eight 10d nails a side (§3). The check could only
say UNKNOWN because nothing in the model could say the strap was there. `PlateTie` is that
word: `wall`, an optional `covers` list of run tags (empty = every cut in that wall's top
plate), a `product`, and R602.6.1's own four numbers as defaults.

It is a **spec and not a solid** — it resolves to no geometry and bills no unit — for the
same reason the check reads it off the authored plan rather than the resolved model: the fact
being recorded is "this detail is drawn", not "this part is here at this point". The engine
reads it and never writes it, exactly as `mep_bores` states the tie as a *remedy* and never
applies one: introducing a strap to make a route legal is a structural redesign.

**With the word, absence becomes evidence of absence, and the verdict becomes a FAIL** naming
the element to author. That is the trade the suppression in `preferences.toml` was waiting
for.

**And the same "this is not a cut at all" guard that §1 gives a stud now applies to a plate.**
Once the penetration is as wide as the plate, the plate is *interrupted* rather than notched:
that is a framed opening with a header over it, and R602.6.1 is about a plate that stays
continuous either side of a cut. Reporting `18.00" out of a 3.50" plate` was arithmetic about
a notch nobody would cut.

**Catlin's thirteen, split by that guard** (it was fifteen when §3 was written; D3 moved two
ducts):

| class | count | runs |
|---|---|---|
| real R602.6.1 cut, over 50%, no tie authored → **FAIL** | 4 | `PR-B-KITCH-DRAIN` @ `W-B-ESS-W`; `PR-B-SAUNA-VENT` @ `W-B-SA-N2`, `W-B-ESS-W`, `W-B-ESS-S` — all 2.38" through a 2x4 plate against the 1.75" line |
| penetration as wide as the plate → framed opening, **UNKNOWN** | 9 | the 4", 6", 10" and 18" ducts (`DU-B-ERV-R-SAUNA-*`, `DU-ERV-RISER-*`, `DU-S-HP-*`) |

Four is the number this house has to answer, and it answers it by authoring four ties:

```python
PlateTie(uid="", tag="PTIE-W-B-ESS-W", wall="W-B-ESS-W", product="Simpson PSPN58")
PlateTie(uid="", tag="PTIE-W-B-ESS-S", wall="W-B-ESS-S", product="Simpson PSPN58")
PlateTie(uid="", tag="PTIE-W-B-SA-N2", wall="W-B-SA-N2", product="Simpson PSPN58")
```

(Three, not four: `W-B-ESS-W` carries two of the four cuts and one tie with an empty `covers`
ties every cut in that wall. Where a wall's plate is cut in two places far apart, author two
ties with explicit `covers` instead — the strap is a real 12"-long part at a real station, and
a single blanket entry would be claiming one part does two jobs.)

---

## 8. A header hole chart, read — and why no row of it reaches these six (2026-09-22)

§6 said the verdict is UNKNOWN because no **IRC** table publishes a bore limit for a header.
The remedy it named was "the header designer's own allowable", and for a Trus Joist header
that allowable is published: Weyerhaeuser **TJ-9000** *Trus Joist Beam, Header and Column
Specifier's Guide*, April 2021, **p.26, ALLOWABLE HOLES**. The engine can hold it now —
`PublishedHole` on `Door`/`DoorType`/`RoughOpening`, graded by
`resolve/mep_hole_chart.py` through `header_bore(..., chart=...)`. What follows is the chart
as read, then the chart worked against this house.

### 8.1 The chart, transcribed

**1.55E TimberStrand® LSL headers and beams.** Allowed hole zone suitable for headers and
beams with uniform and/or concentrated loads anywhere along the member. **Round holes only.
No holes in headers or beams in plank orientation.** The zone is drawn as **8" off each
bearing**, the middle **1/3 of the depth**, and two holes no closer than **2 x the diameter
of the largest hole**.

| header or beam depth | maximum round hole |
|---|---|
| 9 1/2" | 3" |
| 11 7/8" | 3 5/8" |
| 14"–16" | 4 5/8" |

**Other Trus Joist® headers and beams** (1.3E TimberStrand LSL, Microllam® LVL, Parallam®
PSL). **Uniform loads only**; no holes in cantilevers; round holes only; none in plank
orientation. Microllam LVL and Parallam PSL take the **middle 1/3 of the SPAN** as their
zone, which is a stricter shape than the LSL page's 8".

| header or beam depth | maximum round hole |
|---|---|
| 4 3/8" | 1" |
| 5 1/2" | 1 3/4" |
| 7 1/4"–20" | **2"** |

Note the shape of the first table: every maximum is a shade under a third of its own depth
(11.875/3 = 3.96 against 3.625). The diameter limit and the depth band are one rule stated
twice, which is why a chart transcribed as a diameter alone is not the chart.

### 8.2 What depth actually fits

Neither of these headers can simply grow. Above `D-B-FURN`'s head there is **13.82"** to the
top plate (the 7 1/4" header plus 6 9/16" of cripple) and above `D-B-GYM`'s **13.00"**. So
**11 7/8" is the deepest Trus Joist member either opening can take**, and 11 7/8" caps the
LSL page at **3 5/8"** and the LVL/PSL page at **2"**. A 14" member — the row that publishes
4 5/8" and would be the only one reaching `PR-B-MAIN-DRAIN`'s 4.50" — does not fit in either
wall.

### 8.3 The six, each against the row that would be best for it

Read at the deepest member that fits, **1.55E TimberStrand LSL, 11 7/8"**: 3.625" maximum,
8" off each bearing, hole zone 3.958"–7.917" up from the bottom face (so **3.958" of clear
wood** to the nearer face), holes 2 x diameter apart. The bearing is the **jack face** and
not the member end — a header runs over its jacks, so `D-B-FURN`'s 39.00" member bears on a
36.00" clear span with 1.50" of jack at each end.

| run | cut | from bearing | clear to nearer face | to the next hole | verdict |
|---|---|---|---|---|---|
| `DU-B-ERV-R-SAUNA-SUP` | 1.75" **notch** | 0.00" | 0.00" | 6.00" | **refused: round holes only** |
| `DU-B-ERV-R-SAUNA-EXH` | 3.25" **notch** | 6.00" | 0.00" | 6.00" | **refused: round holes only** |
| `PR-B-KITCH-DRAIN` | 2.38" bore | 15.00" ✓ | **1.04"** vs 3.96" | **0.77"** vs 7.00" | over the zone, twice |
| `PR-M-S-BATH1-DRAIN` | 3.50" bore ✓ | 15.77" ✓ | **1.20"** vs 3.96" | **0.77"** vs 7.00" | over the zone, twice |
| `PR-B-MAIN-DRAIN` | **4.50"** vs 3.625" | **3.00"** vs 8" | 0.60" vs 3.96" | 17.23" ✓ | over on every term |
| `DU-B-ERV-R-GYM` | **4.00"** vs 3.625" | **7.44"** vs 8" | 1.25" vs 3.96" | — | over on size and zone |

**One fact governs all six and it is not the diameter.** Every one of these runs passes
within **1 1/4" of the header's bottom face**, because every one of them is a service under
a floor deck crossing a wall just above a 6'-8" door head. The chart's hole zone is the
middle third of the depth, so **a deeper header moves the zone UP and further from every one
of them**: 11 7/8" wants 3.96" of clear wood where 7 1/4" wants 2.42", and not one of the six
has even 1.30". **Depth is not the lever here, and retyping either header to LSL buys
nothing** — which is why neither was retyped and neither opening carries a `PublishedHole`
row. Authoring one would turn six honest UNKNOWNs into six FAILs and state a design that is
not built.

`PR-B-MAIN-DRAIN` is the one that does not even get to that argument: 4.50" is over the
3 5/8" of the only depth that fits, and 3.00" from the east jack face is inside the 8" no row
of this chart allows a hole in. **No published chart closes it**; it is a rerouted run or an
engineered header, and §8.2's 13.82" is the number any such design starts from.

### 8.4 What the engine now does with a chart it is given

Four outcomes and no fifth, the `checks/structural/published.py` discipline:

* **drift** — the row was read for a member the model no longer has, a ply count nothing
  states, or a span longer than the row's. UNKNOWN naming the mismatch, never a PASS off a
  stale row. A guard the crossing cannot answer (no span, no bearings) is a *mismatch*, not
  agreement.
* **refused** — a notch against a round-hole chart, a diameter over the row, a hole inside
  the bearing zone or outside the depth band, or two holes closer than the chart allows.
* **PASS** — with the zone printed term by term and the chart's own `condition` after it.
* **no chart** — exactly §6's answer, word for word. The `_engineered` refusal ("cut to the
  fabricator's chart") now sits BELOW the chart lookup, which is the whole feature: handing
  the engine that very chart has to be reachable, and without one nothing moved.

**Minimum spacing is a fact about the MEMBER, not about one run.** `PR-B-KITCH-DRAIN` and
`PR-M-S-BATH1-DRAIN` are 0.77" apart in one header and each is a legal diameter on its own;
the pair is what no chart allows. `mep.run_through_header` therefore collects every header
cut in the house keyed by member before it grades any of them — the R502.8.1 `nearest_cut_in`
idiom of §4, one member family along.

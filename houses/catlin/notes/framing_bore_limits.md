# What the trades may cut out of this house's framing — worked by hand

Oracle for `typehaus/resolve/mep_bores.py`, `mep.run_through_stud`, `mep.run_through_plate`
and the R502.8.1 half of `mep.run_member_crossing`. Reproduced by
`packages/engine/tests/test_mep_bores.py`.

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
Nothing in this engine grades the header either, and that is said out loud. Catlin's 6",
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

**The verdict for the over-50% case is UNKNOWN, not FAIL**, and the distinction is the
section's own: it *permits* the cut with a tie, and this model has no vocabulary for a plate
tie at all — `FramedMember.connection` is a free-form string nothing reads for this. Absence
of a tie in the model is not evidence of absence on the job. The day a plate can carry a
connector this becomes an honest PASS or FAIL.

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

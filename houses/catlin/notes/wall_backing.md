# In-wall backing — the height schedule and where it comes from

**House:** catlin
**Structure:** every `WallBacking` in `plan/backing.py` and `plan/backing_wet.py` (70 bands).
**Written:** 2026-09-09. **Revised 2026-09-12**: the wet-wall plywood band became three 2x
courses (§4), and `advisory.wall_backing_bearing` was added (§5).
**Oracle for:** nothing. This is a **sources note**, not a calculation note — there is no
arithmetic here to reproduce, only a set of heights and the authority behind each one.
`advisory.wall_backing_present` grades coverage against it; no engine table repeats it.
**Companions:** `notes/interior_selections.md` §"What has to reach a trade before a wall
closes" — the prose this file finally makes buildable.
**What is asked of the reviewer:** confirm that each height below is the one *this* family
wants, and that the wet-wall band's cost (below) is the trade you mean to make.

> ⚠ **This is the only irreversible item in the house.** Every other decision here can be
> revisited with a screwdriver. Retrofit backing after tile is $1,500–4,000 per wall.

> ⚠ **Almost none of this is code.** Do not let the presence of a citation column suggest
> otherwise. See §2.

---

## 1. The height schedule

| Item | Band | Where the number comes from |
| --- | --- | --- |
| Grab bar | 32" to 39 1/4", 2x8 nominal min, flush with framing | CRC R328.1.1 |
| Grab bar (bar centreline) | 33"–36" | ADA 609.4 |
| Mirror / medicine cabinet | blocks topping at 40" and 76" | Fox Cities Habitat QRG ch. 10a |
| Towel bar | block topping at 60" (bar lands 48"–54") | Habitat QRG ch. 10a |
| *(this house)* wet-wall courses | 32"–39 1/4", 44"–53 1/4", 72"–79 1/4" | §4 — CRC R328.1.1 plus two chosen heights |
| Toilet paper holder | block topping at 26", span ≥ 12" | Habitat QRG ch. 10a |
| Kitchen upper cabinets | ~54" (36" counter + 18" clear) and ~84" for a 30" box | NKBA 2023 Planning Guidelines |
| Wall-hung vanity | bracket band under a 32"–34" top | manufacturer rough-ins |
| Closet rod | 66" single; 80" / 40" double | trade practice |
| Handrail | 34"–38" above the nosings | IRC R311.7.8 |
| TV mount | screen centre 42"–48" | trade practice — **not** 60" |

The Habitat numbers are a production spec rather than an opinion, which is why they are
preferred over the many contradictory blog figures: they are what a builder hands a framing
crew, and all of them are 2x6 laid flat.

## 2. What the code requires, and what it does not

**Required.** A handrail or guard carries **IRC Table R301.5**'s 200 lb concentrated load,
applied in any direction at any point along the top — adopted by Minnesota as the 2020
Minnesota Residential Code through Minn. Rules ch. 1309. The IRC states the load and
prescribes **no attachment detail at all**, so the blocking behind a rail is discretionary in
form and mandatory in effect.

> ⚠ The 200 lb load is **Table R301.5**, not R311.7.8.5. R311.7.8.5 is *grip size*, and the
> subsection numbering moves between editions — cite the table.

**Not required, anywhere in a Minnesota single-family house.**

* ADA does not reach a private residence; it governs public accommodations and government
  facilities. Its 609.4 (33"–36") and 609.8 (250 lb) are the numbers everyone borrows.
* The 250 lb grab-bar load is **IBC 1607.7**, whose one- and two-family exception reduces
  handrails and guards to the 200 lb case. The IRC sets no grab-bar load whatsoever.
* The A117.1 "reinforcement in lieu of grab bars" allowance is a multifamily / Group R
  accessible-unit rule.
* No Minnesota amendment analogous to CRC R328 was found. Confirm with DLI before relying on
  that as a *negative* finding.

**So the geometry above is borrowed, and California's is the version worth borrowing.**
CRC **R328.1.1** requires grab-bar reinforcement in dwellings: not less than 2x8 nominal,
32" to 39 1/4" above the floor, flush with the framing; continuous in a shower; continuous at
each end and the back wall of a tub; both side walls of a water closet, or one side plus the
back. It is the best-written statement of this requirement in any US code.

This is why `advisory.wall_backing_present` is ADVISORY and says whose number it is. A
preference dressed as code trains the reader to ignore the code findings too.

## 3. Not fireblocking

IRC **R302.11** is a *draft stop* that fills the cavity edge to edge. Backing is a *fastening
target* laid flat on the stud face. They are different members and a block that satisfies one
rarely satisfies the other.

R302.11's horizontal rule bites at intervals **not exceeding 10 ft**, so an ordinary 8' wall
triggers none — every horizontal 2x in a catlin bathroom is backing, not fireblocking. The
places it would bite here are the walls over 10 ft and, more sharply, R302.11 item 2's
soffits and dropped ceilings and item 3's stair-stringer tops and bottoms.

`checks/code/mn_residential/profile.py` declares R302.11 **outside this engine's coverage**,
and nothing in `plan/backing.py` changes that. Fireblocking remains un-modelled and is the
framer's and the inspector's to carry.

## 4. What this house bought

Until 2026-09-12 every wet wall carried **one continuous 3/4" Structural 1 plywood band,
48" tall, 32"–80" AFF** — 17 of them, 106 LF + 8 LF ordered, about 13 sheets. It is retired.
**Every one of those walls puts 5/8" gypsum straight on the studs**, so a 3/4" sheet either
stands proud of the finish plane or is let into them; §5 of this note used to claim the
second, which for a 48"-tall band means routing a 3/4" × 48" dado across roughly 65 studs.
Nothing draws that and nothing prices it. The three courses below are laid flat and **fitted
between the studs**, which is what the kitchen rails have always meant by "2x8 flat": nothing
stands proud, nothing is dadoed, and the framer cuts to the bay.

### The three wet-wall courses

| Course | Profile | Bottom | Top | What it answers |
| --- | --- | --- | --- | --- |
| `-GRAB` | 2x8 | 32" | 39 1/4" | CRC R328.1.1 verbatim — 2x8 nominal min, 32"–39 1/4", flush with the framing |
| `-MID` | 2x10 | 44" | 53 1/4" | towel bar (48"), robe hook, slide-bar lower bracket, `FURN-M-BATH2-CAB`'s 48" rail |
| `-HIGH` | 2x8 | 72" | 79 1/4" | shower arm (78"), slide-bar upper bracket, high hook |

All three on the 16 full-height wet walls; `W-A-STU-W` gets `-GRAB` and `-MID` only, because
its plate is at 72 3/4" and `CARF01AAAA:rafter-020` rakes across it at 60 7/8".

> ⚠ **What this gives up.** The retired band was continuous 32"–80". The courses leave
> **39 1/4"–44", 53 1/4"–72" and everything above 80 1/4" unbacked.** A screw in one of those
> gaps has nothing behind it. The policy has not changed — these are three standard anchor
> heights authored where a screw *might* land, not a fit to today's fixtures; only one
> modelled body in the whole house (`FURN-M-BATH2-CAB` at 48" on `W-M-HS1`) sat inside the
> old 48" band at all, and `-MID` still covers it.

**What it gains beyond the flat wall.** A per-bay block can be omitted or shifted at the bay
a shower valve and its risers occupy. A continuous sheet cannot, and §5 flags that overlap as
ungraded.

**Only one of the four anchors the old prose named is finish backing.** The valve body, the
tub spout and the shower arm are the plumber's **rough-in blocking**, set with the rough-in.
Only the grab bar is this file's business.

| Band | Count | Material |
| --- | --- | --- |
| Wet walls, `-GRAB` + `-HIGH`, 2x8 flat | 33 | +148 LF on the 1,010 LF 2x8 row |
| Wet walls, `-MID`, 2x10 flat | 17 | 114 LF of the 172 LF 2x10 row |
| Kitchen and curtain-rod rails, 2x8 flat | 10 | part of the same 2x8 row |
| Closet rods, 2x8 flat | 2 | " |
| Plumbing access panel frames, 2x8 flat | 5 | " |
| `BK-G-W-RAIL-FOOT` handrail block, 2x12 flat | 1 | 8 LF of 1.5x11.25 |

**Cost, stated honestly.** The three courses run **$674–1,086** against the retired band's
**$647–1,128**. That is a wash against today's price rows — which assume no dado — and a
clear saving once let-in labour is priced. **The reason for the change is buildability, not
money.** `prices.toml` keeps the two retired plywood rows at 0 LF so the comparison does not
have to be re-derived.

> ⚠ The old note recorded that `plan/fixture_types_wc.py` says "a continuous band costs about
> twelve dollars". That is right for the 12"-wide strip it describes and wrong by two orders
> of magnitude for anything that covers a 40"–80" range. It is still wrong; the prose has not
> been fixed. Read the table above, not that sentence.

## 5. Not done, and why

* **Handrail backing is not authored.** All five wall-mounted rails in this house serve a
  stair, so they rake, and a `WallBacking` band is level — it cannot follow one. They also
  stand 5"–8" off the nearest wall axis on brackets, and two of the five square onto no wall
  the derivation can find at all. Resolving the rail-to-wall association is the prerequisite,
  and it is real work rather than an oversight. **This is the one item on the list with a
  code load behind it (§2), so it is the one most worth finishing.**
* **Backing capacity is not computed anywhere.** Whether a 3/4" plywood band carries a 250 lb
  grab bar is an engineering question and belongs to a named register item (decision #65),
  not to a check with no load to compute against. `advisory.wall_backing_present` grades
  *coverage*, the discipline `mep.deck_equipment_support` already keeps.
* **Nothing grades a band against a pipe or a wire.** `structural.member_interference` reads
  members only, and there is no member-versus-`PipeRun` check in `checks/mep/`. A course at
  44"–53 1/4" in a wet wall passes straight through the plane a shower valve and its risers
  occupy, at 0 FAIL, and a reader should not infer that silence means clearance. What the
  three courses change is the *remedy*: a 2x fitted between studs can be omitted or shifted
  at the one bay the valve occupies, and the framer decides that at the wall. The continuous
  sheet that used to stand here could not be, which is part of why it is gone (§4).
* **A band's ends are graded; its middle is not.** `advisory.wall_backing_bearing` (added
  2026-09-12) requires both ends of every resolved band run to land within 1" of a stud face
  or at the wall's own end, because a block with a free end is nailed at one end only. It was
  written against a real defect: `BK-G-W-RAIL-FOOT` was a 12" block in a 24" o.c. bay that
  lapped one stud by 1/4" and floated 10 1/4" clear at the other end, at 0 FAIL. It is now
  cut to fill its bay, 192 3/4"–215 1/4". The check says nothing about what the band spans
  between those ends, and nothing about capacity.

## 6. Sources

* IRC Table R301.5 / R311.7.8 as adopted — Minn. Rules ch. 1309; City of Anoka MN residential
  handrail handout.
* CRC R328.1.1 — aging-in-place grab-bar reinforcement.
* IBC 1607.7 — loads on handrails, guards, grab bars.
* 2010 ADA Standards 609.4, 609.8, 604.5, 604.7 — US Access Board.
* Fox Cities Habitat for Humanity, "Blocking for Bathroom", QRG ch. 10a, Jan 2025.
* NKBA Kitchen & Bath Planning Guidelines, 2023.
* IRC R302.11 fireblocking — ICC; City of Austin MN residential fireblocking handout.

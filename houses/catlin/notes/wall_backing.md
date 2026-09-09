# In-wall backing — the height schedule and where it comes from

**House:** catlin
**Structure:** every `WallBacking` in `plan/backing.py` (34 bands).
**Written:** 2026-09-09.
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

| Band | Count | Material |
| --- | --- | --- |
| Wet walls, 32"–80", 3/4" plywood | 16 | 106 LF ordered, ~$620–1,090 |
| W-A-STU-W knee wall, 32"–56" | 1 | 8 LF |
| Kitchen and curtain-rod rails, 2x8 flat | 10 | part of the 238 LF 2x8 row |
| Closet rods, 2x8 flat | 2 | " |
| Plumbing access panel frames, 2x8 flat | 5 | " |

> ⚠ **The wet-wall band costs more than the prose that asked for it assumed.**
> `plan/fixture_types_wc.py` says "a continuous band costs about twelve dollars", which is
> right for the 12"-wide strip it describes and wrong by roughly two orders of magnitude for
> the 48"-tall band authored here. The 48" band is what actually covers the stated 40"–80"
> range of anchors in one piece, and it is ~13 sheets of 3/4" ply. If that trade is not
> wanted, the lever is `_WET_HEIGHT` in `plan/backing.py`, and the cost of narrowing it is
> that a future anchor outside the surviving band has nothing behind it.

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
  members only, and there is no member-versus-`PipeRun` check in `checks/mep/`. A 32"–80"
  band in a wet wall passes straight through the plane a shower valve and its risers occupy,
  at 0 FAIL. The band is built let-in flush with the stud face, which is how CRC R328.1.1
  specifies it and how a framer installs it, so the overlap is intended — but nothing in the
  engine proves that, and a reader should not infer that silence means clearance.

## 6. Sources

* IRC Table R301.5 / R311.7.8 as adopted — Minn. Rules ch. 1309; City of Anoka MN residential
  handrail handout.
* CRC R328.1.1 — aging-in-place grab-bar reinforcement.
* IBC 1607.7 — loads on handrails, guards, grab bars.
* 2010 ADA Standards 609.4, 609.8, 604.5, 604.7 — US Access Board.
* Fox Cities Habitat for Humanity, "Blocking for Bathroom", QRG ch. 10a, Jan 2025.
* NKBA Kitchen & Bath Planning Guidelines, 2023.
* IRC R302.11 fireblocking — ICC; City of Austin MN residential fireblocking handout.

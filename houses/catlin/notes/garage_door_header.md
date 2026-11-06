# `D-G-OVERHEAD` header — published-table read

**House:** catlin, Ramsey County, Minnesota (MN Residential Code 2020, adopting the 2018 IRC).
**Structure:** the 16'-0" overhead door opening in `W-G-N`, headed with a 2-ply 14" LVL.
**Written:** 2026-09-11, from the specifier's guide, before the check was pointed at it.
**Oracle for:** nothing in `typehaus/engineering/` — this is a PRESCRIPTIVE read, graded by
`structural.header_prescriptive` through `checks/structural/published.py`, and pinned by
`tests/test_header_spec_framing.py`.
**What is asked of the reviewer:** whether the row in §2 is the right row. The arithmetic
is a table lookup; the judgement is the substitution in §3.

> ⚠ **This is not an engineered beam and must not be re-delegated as one.** It was an
> engineering item (`header/D-G-OVERHEAD`) until 2026-09-11 on the reasoning that IRC
> R602.7's table stops at 8'. It does — and the beam supplier's table does not. A published
> row is a document a reviewer opens; nothing a seal adds to. See the root `CLAUDE.md`
> Engineering section.

---

## 1. The opening, and what it carries

| Term | Working | Value |
|---|---|---|
| Rough opening | authored width of `D-G-OVERHEAD` | **16'-0"** |
| Host wall | `W-G-N`, the garage's north wall, NONBEARING | gable end |
| What it carries | `RF-GARAGE` bears on `W-G-E`/`W-G-W` only; over the door stand the gable-end truss and the wall's own skin | no roof, no floor |
| Header authored | `Door.header_spec` | **2-ply 14" LVL** |
| Jacks each end | framed by the solver | **3** |
| Ground snow | `Site.ground_snow_load_psf` | 50 psf |
| Flat-roof snow | Ps, ASCE 7-16 §7.3 at Ce/Ct/Is = 1.0 | 35 psf |
| Roof dead | the figure every residential header table is indexed at | 15 psf |

## 2. The row, read verbatim

Weyerhaeuser **TJ-9000** *Trus Joist Beam, Header and Column Specifier's Guide* (Nov 2013),
p.9, **"Headers Supporting Roof"**, snow-load column at **115%** duration:

> 40 psf live + 15 psf dead, **24' house width**, **16'-3" rough opening** →
> **3-1/2" x 14" Microllam LVL**, two trimmers each end.

A 3-1/2" x 14" Microllam is two 1-3/4" plies, which is the 2-ply 14" LVL the model authors.
The opening is 16'-0" against the row's 16'-3", so the read is inside the row and not on it.

## 3. The substitution: an envelope, not the load

**The row is for a BEARING EAVE wall. `W-G-N` is a GABLE END, and it carries no roof.**
`RF-GARAGE` names `W-G-E` and `W-G-W` as its bearing lines; the north wall stands under the
gable-end truss, which bears on it continuously and sheds only its own weight and the rake's
strip of sheathing into it. `structural.wall_role_load` finds nothing derivable on `W-G-N`
(2026-11-06), which is why it is authored NONBEARING. Read that way the opening needs nothing
past R602.7.4 — but a 16' opening is past that rule's 8', and an overhead door hangs its track
and operator off the head, so the LVL stays (owner, 2026-11-05).

The "Headers Supporting Roof" row is therefore a **conservative envelope**: it sizes the beam
for half a 24'-wide roof it does not carry. Two smaller margins in the same direction: this
site's **Ps is 35 psf** and the row is read at its **40 psf** column; and **three jacks** are
framed each end against the row's **two trimmers**. The read is recorded on the element's
`condition`, because an envelope is still a read of a row that assumes something else.

## 4. What is NOT graded here

- **The jamb pack.** Three jacks each end is what the solver frames; whether the sill and
  the concrete under them take the reaction is not checked by anything in this engine.
- **The door operator's own loads.** A sectional door's track hangs off the header and its
  opener applies a cyclic uplift at mid-span. The row covers gravity.
- **Deflection under the door's own weight,** as distinct from the L/240 live and L/180
  total the row is published at.
- **Anything about the door.** This is the beam over the hole.

## Sources

- **Weyerhaeuser TJ-9000**, *Trus Joist Beam, Header and Column Specifier's Guide*, Nov 2013
  — p.9 "Headers Supporting Roof". Cite the edition actually read; a later edition's row may
  differ and the drift guards on `PublishedSpan` do not notice a document being reissued.
- **IRC R602.7** — the prescriptive header table this opening is past, and the reason a
  second document is needed at all.

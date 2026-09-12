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
| Host wall | `W-G-N`, the garage's north wall | gable end |
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

## 3. The substitution, and why it is conservative

**The row is for a BEARING EAVE wall. `W-G-N` is a GABLE END.** A header in an eave wall
picks up half the roof span; a header in a gable end picks up the rake, which is a fraction
of it. Reading the eave row for a gable-end opening over-states the load, and that is the
direction a substitution has to err in. It is recorded on the element's `condition` rather
than quietly relied on, because a conservative read is still a read of a row that assumes
something else.

Two smaller ones in the same direction: this site's **Ps is 35 psf** and the row is read at
its **40 psf** column; and **three jacks** are framed each end against the row's **two
trimmers**.

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

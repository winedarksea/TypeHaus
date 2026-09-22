# `haus calcs` — the calculation package

```
.venv/bin/haus calcs houses/catlin                    # -> houses/catlin/out/calcs/
.venv/bin/haus calcs houses/catlin --out /tmp/review  # anywhere else
.venv/bin/haus calcs houses/catlin --item retaining_wall/W-SG-E2   # one member + front matter
```

The thing you hand a professional engineer. `haus engineering` answers *where does this
house stand* at a glance and is meant to be read in a terminal; this is a set of
calculations somebody opens in an editor, marks up, and sends back — one per design family,
each with a member schedule, over an appendix of per-member data.

## What it emits

```
out/calcs/
  README.md               index + how to read this package
  00-cover.md             project, jurisdiction, date, model content hash, engine version,
                          where both gates stand, NOT-FOR-CONSTRUCTION banner
  01-design-criteria.md   wind / snow / ground / materials / bases
  02-item-register.md     every item, its governing limit state, its seal, its oracle note
  03-open-items.md        the gap register — what is not finished, and who owns each one
  04-assumptions.md       every distinct record note, grouped by kind and COLLAPSED:
                          rows that differ only in their numbers print once, with the
                          numbers as [1], [2] … and a table of what each member put there
  05-scope-of-review.md   what a stamp on this package would and would not cover —
                          the computed items by id, the deferred ones somebody else
                          seals, and what is answered prescriptively and is not here
  06-conventions.md       how every calculation reads and what none of them covers,
                          said ONCE — the boilerplate that used to repeat 52-55 times
  calcs/
    retaining_wall.md       THE CALCULATIONS — one per design family, with a member
    deck_post.md            schedule. This is what a reviewer reads.
    ...
  appendix/
    retaining_wall.md               the per-member data behind one family's schedule:
    deck_post.md                    one column per member. THIS is what the PDF prints
    ...                             when asked for the appendix
    retaining_wall__W-SG-E2.md      one nine-section sheet per item — diffable machine
    ...                             data, on disk, never printed
```

A family calculation is named for its `kind`. An appendix sheet's filename is the item id
with `/` written `__`, so the id is recoverable from the filename and a directory listing
sorts by kind.

## One calculation per design family, not one per item

Until 2026-09-18 `calcs/` led with one nine-section sheet per item, and for twelve cast
columns that was twelve copies of ACI 318-19 §22.4.2.1 with an element tag and four numbers
changed. A reviewer checking a family of members wants the clause once, the arithmetic
once, and a **schedule** saying which member is which and which one governs.

So `calcs/<kind>.md` carries:

1. **Scope** — what this family is
2. **References** — every citation the whole family rests on, deduped, printed once and
   numbered `R1`, `R2` …, which is how the appendix's limit-state tables cite one without
   reprinting 400 characters of it per member
3. **Member schedule** — one row per member: elements, governing limit state, demand,
   capacity, d/c, status, coverage, seal — and under it, the pointer to
   `appendix/<kind>.md`
4. **The calculation, worked at the governing member** — the inputs as
   `symbol = value unit`, then each limit state as its own substitution beside its ratio
   and citation. Substitutions with units, because a row reading `9,461 / 7,150 = 1.32` is
   checkable only by somebody who already knows what went into the 9,461
5. **Result** — the family's counts, and the member the verdict comes from
6. **Assumptions and exclusions** — a pointer to `04-assumptions.md` under this kind,
   where the family's notes are printed collapsed with the items each reaches. Printed
   there and here was 20 pages of one 108-page PDF
7. **Open inputs** — per member, only the members that have any
8. **Independent check** — the family's oracle notes and the tests that reproduce them
9. **What this calculation does not cover** — this family's coverage word, over the
   standing exclusions on `06-conventions.md`
10. **Per-member fingerprints** — what a seal on any one member would be pinned against

The governing member is picked by status first and ratio second: an INCOMPLETE member has
no ratio to lose with and is a bigger fact about the family than an OK member at 0.98.

`appendix/` keeps every field the per-item sheet ever carried, in the nine-section order
below. Nothing was dropped in the restructure; the machine data stopped being the document.

## The appendix is a table per family, not a sheet per member (2026-09-22)

The per-item sheets were **192 of a 307-page PDF** — 63% of the package — and each repeated
its family's references, its exclusions and its table keys. So the PDF stopped printing
them, and `appendix/<kind>.md` prints the numbers instead: the members' summaries, then the
inputs as rows and the members as columns, then every limit state as
`demand / capacity = d/c` with the citation's number (`R4`) in the family calculation's §2.
The per-member sheets are still written, still hold every field, and are still what a diff
between two runs is taken over — they are machine data rather than the document.

`haus calcs --pdf` leaves the appendix out and says so on its divider page, which names the
folder the data is in: **a silent omission is exactly the defect `sheet_order`'s docstring
exists to prevent.** `haus calcs --pdf --appendix` and `haus handoff --full` print the
per-family tables (X-33 on catlin against the old X-192).

**The boilerplate is said once.** Five strings — the draft-gate sentence, the load-case
sentence, the "bold row governs" key, the limit-state table key and the coverage
statement — appeared on 52 to 73 sheets. They are on `06-conventions.md` now, the S-1 page
in front of the calculations, and a family sheet points at it.
`tests/test_calc_pdf.py::test_no_boilerplate_line_is_printed_twice` masks the kind name and
the numbers out of every long line the emitter writes and fails if one reaches two printed
files; record-derived text is exempt, because two kinds may legitimately state the same
assumption and that is the register's word, not the emitter's.

## The nine sections (the appendix sheets)

Standard US structural-calc order. A header block (item, elements, basis, basis version,
local status, seal, fingerprint, house, generation date) and then:

1. **Scope** — the record's summary
2. **References** — every citation, deduped in first-appearance order, basis first
3. **Given** — the inputs, with units and the fingerprint quantum each is rounded to
4. **Analysis** — the limit states, with the governing row bold and each row's ratio
   labelled `demand / capacity` or `FS (required / achieved)`
5. **Result** — `d/c = X, governed by <state> (<citation>)`, and PASS or OVER
6. **Assumptions and exclusions** — the record's notes, verbatim
7. **Open inputs** — the `missing` tuple, when the item is INCOMPLETE
8. **Independent check** — the oracle: the hand-worked note, its section, and the test that
   reproduces it
9. **What this sheet does not cover** — the standing boundary of every sheet

**Every field printed already exists on the `EngineeringRecord`.** The emitter chooses a
layout and a rounding and invents no number, no citation and no assumption — which is the
property that keeps the package regenerable rather than a document somebody maintains
beside the model.

## Two guarantees

**Byte-determinism.** Two runs over an unchanged model produce identical files, so a diff
between them is a real change in the model or in a calculation. Regenerate the package; do
not edit it. `emit/md_writer.py` is the single table renderer behind this (and behind
`haus millwork --md`), for the same reason `emit/csv_writer.py` is hand-written: one
newline convention, one float format, one escaping rule.

**The printed fingerprint is the one to pin.** The digest on a sheet is exactly what
`haus engineering --fingerprint <id>` computes, which is what a PE pastes into
`engineering.toml`. A NO_CALC item prints no digest and says why — a stamp over it can be
recorded but never pinned, and an unpinned stamp satisfies no gate.

## The design-criteria page is derived, never typed

Wind through `typehaus/wind.py`, ground through `engineering/soil.py`, materials off the
values the calculations actually consumed, bases off the records. A criteria page that can
drift from the calculations it fronts is worse than none: it is the page a reviewer trusts
to place every number behind it. Where one calculation used 3,000 psi and another 5,000,
both appear with the items that used each — that disagreement is a fact a reviewer needs,
not something to average.

## Oracles

Every registered kind declares the hand-worked note(s) that independently reproduce its
arithmetic, via `oracled_by(KIND, Oracle(note=..., section=..., test=...))` in the calc
module. `EngineeringResults` stamps it onto every record of that kind, so a calc module
cannot thread the field through five constructors and forget one.

`tests/test_calc_package.py::test_every_registered_kind_names_an_oracle_note_that_exists`
is the root `CLAUDE.md` rule — *a calc that only agrees with itself is not verified* — made
mechanical: every kind names a note, every note exists on disk, every named test exists.

`Oracle` is deliberately **not** in the fingerprint. A seal is a statement about the numbers
a calculation consumed; staling one because somebody renamed a note would make the stamp
mean less, not more.

## Deferred items

**Thirty items in catlin** are computed by nothing, by decision. `engineering/deferred.py`
declares each kind's designer of record, what they must produce and which permit-set line it
unblocks, and `03-open-items.md` is generated straight off that table. They are exactly as
blocking as they were before they had names; what changed is that the outstanding work is now
an assignment rather than an absence.

**Most of them are NOT the supplier's**, and this paragraph said the opposite until
2026-09-18 — it read "a fabricator's or a supplier's sealed design governs" and named seven
items, a count that had been stale through four separate expansions. Today: two trussed roofs
and their uplift path are a fabricator's; the rest — the wall tops under the balcony's
fixed-base columns, the court's veneer beam, the thermal-break transfer, the tiered apron,
and (2026-09-18) the fixed bases' rotational stiffness and the column head joints — name the
**structural engineer of record**, which is to say the person the handoff bundle is addressed
to. A reviewer told "these are not yours" about twelve items that are theirs is the one
sentence in a handoff that can cost a whole review cycle.

**An exact count does not belong in this document.** It went stale four times because a
number about one house was written into the format's own specification; `haus engineering`
and `03-open-items.md` are generated and are always right. The figure above is a sense of
scale, and the day it disagrees with the CLI, trust the CLI.

**A deferral is not the only alternative to a calculation.** Where a manufacturer publishes
a span table, reading a row is a *prescriptive* act and belongs in neither lane: the element
authors a `PublishedSpan` and `checks/structural/published.py` grades it. Three items left
the register that way on 2026-09-11 — a garage-door header, an I-joist roof and three
glulam deck beams — without anybody stamping anything. Before declaring a new `Deferral`,
check that the member's own supplier has not already answered the question.

## The PDF

`haus calcs --pdf` flattens the same sheets through `takeoff/calc_pdf.py` (page furniture in
`calc_pdf_layout.py`) and writes `out/calcs.pdf`: a cover, then the markdown paginated at a
fixed measure, page-anchored so a reviewer's note on page 14 stays on page 14. The cover's
index and every item tag in the register are **internal links**, and a file named in a code
span links to its first page and prints its label (`X-3`) beside it — which is why the
renderer iterates to a fixed point over both the index and those labels. It exists because no jurisdiction accepts
Markdown and a seal has to bind to a flattened file.

Markdown stays the source of truth. The PDF is derived on every run and never edited
beside the sheets; a correction goes into the model or the calc module, not into the page.
Its metadata is pinned (no CreationDate, no ModDate) so two runs over an unchanged model
produce identical bytes, which is what lets `haus handoff` prove a bundle was regenerated
rather than touched up.

`05-scope-of-review.md` is the front-matter page that says what a stamp on that PDF would
and would not cover: the computed items by id, the deferred ones a fabricator seals
instead, and the open inputs that must close first.

## `MANIFEST.json`

Every run writes `MANIFEST.json` — sorted relative path to sha256 — beside the front
matter. It does two jobs. A reviewer can check that the file they are reading is the file
that was sent. And the *next* run deletes anything the previous manifest listed and this
run did not produce, which is how the folder stays a statement about the current model: a
sheet for an item the house no longer has reads as a calculation somebody did.

`haus calcs --item` writes one sheet plus the front matter and prunes nothing — "absent
now" there means "not asked for". The helpers are in `takeoff/handoff.py`, shared with
`haus handoff`.

The permit set keeps S-105 as its engineering page, and S-105 names both `out/calcs/` and
the oracle note per item, so the drawings and the calculations reference each other.

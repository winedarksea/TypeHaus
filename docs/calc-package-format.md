# `haus calcs` — the calculation package

```
.venv/bin/haus calcs houses/catlin                    # -> houses/catlin/out/calcs/
.venv/bin/haus calcs houses/catlin --out /tmp/review  # anywhere else
.venv/bin/haus calcs houses/catlin --item retaining_wall/W-SG-E2   # one sheet + front matter
```

The thing you hand a professional engineer. `haus engineering` answers *where does this
house stand* at a glance and is meant to be read in a terminal; this is forty-odd sheets
somebody opens in an editor, marks up, and sends back.

## What it emits

```
out/calcs/
  README.md               index + how to read this package
  00-cover.md             project, jurisdiction, date, model content hash, engine version,
                          where both gates stand, NOT-FOR-CONSTRUCTION banner
  01-design-criteria.md   wind / snow / ground / materials / bases
  02-item-register.md     every item, its governing limit state, its seal, its oracle note
  03-open-items.md        the gap register — what is not finished, and who owns each one
  04-assumptions.md       every distinct record note, deduped, grouped by kind
  calcs/
    retaining_wall__W-SG-E2.md      one sheet per item
    ...
```

A sheet's filename is the item id with `/` written `__`, so the id is recoverable from the
filename and a directory listing sorts by kind.

## The nine sections

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

Five items in catlin are computed by nothing, by decision — a fabricator's or a supplier's
sealed design governs. `engineering/deferred.py` declares each kind's designer of record,
what they must produce, and which permit-set line it unblocks, and `03-open-items.md` is
generated straight off that table. They are exactly as blocking as they were before they had
names; what changed is that the outstanding work is now an assignment rather than an absence.

## No PDF

A ~40-sheet calc series with variable-length assumption prose and long ACI citations would
need pagination and text wrapping that `emit/draw/sheet_writer` has never had to do, with no
golden harness behind it. Markdown is the source of truth; render it with your own tooling.
The permit set keeps S-105 as its engineering page, and S-105 now names both `out/calcs/`
and the oracle note per item, so the drawings and the calculations reference each other.

# Calculation sheet pattern: how a kind shows its working

A family sheet (`calcs/<kind>.md`) has to let a PE check every number with a calculator,
without opening the code (2026-11-22 review, E §6B #1). Everything below is data on the
records or declared beside the kind; the renderers (`takeoff/calc_family.py`,
`calc_worked.py`, `calc_sheet.py`, `calc_appendix.py`) print it the same way for every kind.
None of it is hashed, so filling it in stales no seal and needs no `BASIS_VERSION` bump.

Worked examples: `engineering/roof_beam_glulam.py` + `truss_on_beam.py` (inline working),
`engineering/glulam_beam_working.py` and `column_head_working.py` (working split into a
sibling module to keep the calc module under 500 lines), and `rafter` (a deferred kind:
nothing to do, its `Deferral` fills sections 8 and 10).

## The sheet, section by section

| § | Section | Comes from |
|---|---|---|
| — | header table | basis, method (`calc_criteria.DESIGN_METHOD`), coverage, status/seal when uniform |
| 1 | Scope | `record.summary` |
| 2 | References | every `basis` and `citation`, near-duplicates collapsed to one `R<n>` with a values table |
| 3 | Member schedule | governing state per member; status/coverage/seal columns only when they differ |
| 4 | Working | per **template** (members running the same limit states): symbols, free body, summary table, each state's steps, load combinations |
| 5 | Result | governing member, d/c, PASS / OVER, the 1.000 limit |
| 6 | Stated bases and owner acceptances | `StatedBasis` from the kind and the records |
| 7 | Assumptions | pointer to `04-assumptions.md` (`record.notes`, collapsed) |
| 8 | Open inputs | `record.missing`; a deferral's designer and deliverable |
| 9 | Independent check | `oracled_by` notes (no test paths: the PE does not have the repo) |
| 10 | Not covered | `NotCovered` from the kind, the records and any `Deferral` |
| — | one line | fingerprints for the seal form |

## What a kind does

### 1. Working per limit state: `LimitState.working`

A tuple of `Step`s, in calculation order. Each step is one line on the sheet:

```
`f_b` = 12 M / S = 12 x 3,858 / 129.3 = **358.1 psi** — bending stress
```

```python
Step(symbol="f_b", meaning="bending stress", value=f_b, unit="psi",
     equation="12 M / S", numbers=f"12 x {num(m)} / {num(sm)}",
     source="")  # the clause or table row, when the step comes from one
```

Rules:

- **Build the steps from the very numbers the state is built from**, in the same function.
  Never recompute a demand in a second place. A test
  (`test_a_worked_kind_shows_the_working_of_every_state_it_grades`) requires one step's
  `value` to equal the state's `demand` and another's to equal its `capacity`.
- **Symbols and equations are plain ASCII** (Latin-1 at most: `^2`, `x`, `sqrt()`, `<=`,
  `phi`): the PDF font has no Greek or maths glyphs.
- Format numbers with `item.num` (positional, four significant figures, no exponent).
- `meaning` is plain words a PE reads without the code: "largest bending moment over the
  load patterns", not "env.moment_lb_ft".
- `source` names the clause or table row a value comes from: `"NDS Supplement Table 5A;
  Table 5.3.1 wet"`, `"ACI 318-19 §22.8.3.2"`. A value read off a table has no
  `equation`, only `source`.
- Steps shared by several states (the line loads) are listed in each; the sheet prints a
  step once per member and writes "as above" after that.
- A result that comes from a search (an envelope over load patterns, a numerical
  integration) is one step whose `equation` says what was searched and whose `numbers`
  give its inputs: `max |M(x)|` = "w_D on a, s and b; w_S on each of the 8 subsets; …".
- Detailing rows (`is_detailing`) may stay without working; every other row needs it.

### 2. Load combinations: `LimitState.combination` and `combination_factors`

Every graded state names its combination, in words a reviewer can reproduce, and the
factors as letters: `("D + S, unfactored (ASD), C_D 1.15 for snow", (("D", 1.0), ("S", 1.0)))`.
Declare them once as module constants and reuse them (see `column_head_working`).
**Cite an equation number only where it has been read at the source**: IBC 2018
Eqs. 16-1…16-16 are images on UpCodes and could not be verified in wave 3, so the
converted kinds name the combination and the method (ASD / strength) without a number;
`ASCE 7-16 §2.4.1(7) 0.6D + 0.6W` is used where the repo already cites it. The sheet
prints a "Load combinations used" table under each worked member.

### 3. Plain-word symbols

Each input in the symbol table prints a meaning. Precedence: `Quantity(label=...)`, then
`declare_sheet(KIND, labels={"name": "meaning"})`, then the shared dictionary in
`takeoff/calc_labels.py` (add only names that mean the same thing in every kind). A flag
(`unit="-"` or a name ending `_presumed`) prints as yes/no.

### 4. What the calculation does not cover: `NotCovered`

```python
NotCovered(what="lateral-torsional stability",
           why="C_L is taken as 1.0 because the roof deck sheathes the compression edge",
           owner="the sealing engineer",            # a role, never a name
           closes_by="confirming the deck is fastened to the beam's top edge")
```

Declare the kind's rows with `declare_sheet(KIND, not_covered=(...))`; a row true of one
member only goes on `EngineeringRecord.not_covered`. Re-use the module's existing
"NOT GRADED" / "not checked" text — but say **who** closes it and **by what**. Owners in
use: the sealing engineer; the owner (stated basis); the truss fabricator; the contractor
at excavation; an outside designer named by a `Deferral`. The summary's owner table
(`calc_summary._family_rows`) reads these rows.

### 5. Stated bases and owner acceptances: `StatedBasis`

An input that rests on a decision rather than a code row or a measurement. Kinds:
`OWNER_BASIS`, `OWNER_ACCEPTED`, `OWNER_READING` (a reading of a published row),
`SPECIFIED` (specified, not yet confirmed). Shared ones live in
`engineering/owner_bases.py` (deck snow, curtains, overhangs, connector readings); add the
rest there (HL43 heel-vertical reading on `deck_tie`, the dowel 0.92 acceptance on
`column_support`, the court snow + perched basis on `retaining_system`, the court soil
"design closed on specified parameters; not yet confirmed"). Attach with
`declare_sheet(bases=...)` or `EngineeringRecord.bases`, and drop the free-text copy from
`record.notes` once the basis prints in section 6.

### 6. Free-body sketch: `declare_sheet(figure=...)`

A function `record -> Figure | None`, called on each worked member. A `Figure` is ASCII
lines (at most 72 characters) printed in a fenced block, so the markdown and the PDF show
the same deterministic picture with no image pipeline. Read every number off the record
(`record.value("span")`, a step's value), never recompute. `engineering/sketch.py` has
`beam_on_two_posts`, `cantilever_wall` and `pinned_post`; add a shape there when two kinds
share it. Not to scale; labels carry the dimensions.

## Per kind, for the LA-fill lanes

For each kind in your split:

1. Add `working=` and `combination=`/`combination_factors=` to every non-detailing
   `LimitState` (inline, or a `<kind>_working.py` sibling if the module would pass 500
   lines).
2. `declare_sheet(KIND, not_covered=..., bases=..., labels=..., figure=...)`.
3. Move owner bases out of `notes` into `StatedBasis` (via `owner_bases.py`).
4. Add the kind to `WORKED_KINDS` in `tests/test_calc_package.py`.
5. Regenerate (`haus calcs houses/catlin` twice, `diff -r`) and read the sheet as a PE
   would: can every number in section 4 be checked with a calculator from what is printed?

The jargon sweep (E-16: dates, "this engine", check ids, Python names in `notes` and
citations) is the same pass.

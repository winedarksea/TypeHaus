# Type:Haus — repo guide

```
.venv/bin/haus build houses/catlin        # the CLI. No PYTHONPATH, no uv.
.venv/bin/python -m pytest packages/engine/tests -q
scripts/verify.sh                         # the full CI gate
```

`.venv/bin/python` is 3.11.16 and `typehaus` is installed **editable** into it, so the
console script `.venv/bin/haus` is the real entry point. `uv` is **not** installed; ignore
any `uv sync` / `PYTHONPATH=packages/engine/src python -m typehaus.cli.app` incantation you
find in older docs. Pytest defaults are configured in `packages/engine/pyproject.toml`
(`-n 6 --dist loadfile`, ~4 min for the full suite) — bare `pytest` is already parallel.

## Non-negotiables

- **Never hand-write a uid.** `.venv/bin/haus fmt houses/<name>` mints them. A colliding
  uid is now a load-time ERROR, but the cheap fix is to never author one.
- **`# haus: editable`.** A UI-movable element (walls, openings, placeables, fixtures,
  MEP, lighting) must live in a file whose first lines carry the `# haus: editable`
  marker, or UI edits are silently dropped on write-back. The editable dialect is a
  constrained declarative subset: no `frozenset`, no multi-line string concatenation, and
  a 1-tuple needs its trailing comma. `haus build --inspect` lints without importing.
- **Quantities are the product; dollars are opt-in** (`plans/01-decisions.md` #28). No
  price, wage, or productivity data ships in the engine — a house owns its own numbers in
  `houses/<name>/prices.toml`.
- **Files under 500 lines**, per `AGENTS.md`. And aim to keep comments concise and token-efficient. There is no need for long essays to explain a single point that a few quick words can summarize effectively.

## Layout

- `packages/engine/` — the `typehaus` package: `quantities` → `model` → `source` (load +
  dialect) → `resolve` → `checks` / `takeoff` / `emit` / `server` / `cli`.
- `library/` — the shared, reviewed catalog of assemblies, materials, and types. Promoting
  a house-local item into it follows `CONTRIBUTING.md`.
- `houses/catlin/` — the reference house (see its own `CLAUDE.md`); `houses/starter/` — the
  `haus new` template.
- `ui/` — the React/three.js editor; `plans/` — the living design docs and decision log.

## Commands worth knowing

```
.venv/bin/haus doctor                     # environment sanity: venv, install, ui/dist, gitignore
.venv/bin/haus check houses/catlin        # failures only; --only all restores every finding
.venv/bin/haus fmt houses/catlin          # mints uids, formats plan source
.venv/bin/haus serve houses/catlin        # editor; does NOT reload engine code — restart it
.venv/bin/haus takeoff houses/catlin      # BOM (+ costs when prices.toml exists)
.venv/bin/haus takeoff houses/catlin --csv out/estimate.csv   # estimating-software intake
.venv/bin/haus tasks houses/catlin --csv out/tasks.csv        # work packages for a PM tool
.venv/bin/haus millwork houses/catlin                         # hardwood cut list for the mill
.venv/bin/haus millwork houses/catlin --md out/milling.md --csv out/milling.csv
.venv/bin/haus costs import out/estimate.csv --house houses/catlin   # actuals back in
scripts/verify.sh --fast                  # tests + ruff + mypy, skipping builds/bench/npm
```

`haus check` exits 1 on any FAIL, not only on an ERROR — `--exit-on error` is the older,
looser gate, and `scripts/verify.sh` does **not** use it on catlin: the reference house is
held to a clean report, 0 FAIL. See `houses/starter/CLAUDE.md` for the one house that
*does* carry deliberate reds, and why a template is the right place for them.

## Engineering, and the two gates

Some requirements fall outside the prescriptive tables — a 10' cantilever retaining wall, a
round column with no IRC R507.4 row, a trussed roof. Those are not UNKNOWNs. A finding
carries an `Authority` (PRESCRIPTIVE or ENGINEERED) *orthogonal to* its `Result`, and names
an item id `<kind>/<element-tag>` that a professional seal can cover (decision #65).

```
.venv/bin/haus engineering houses/catlin                  # what needs a seal, and what governs
.venv/bin/haus engineering houses/catlin --item retaining_wall/W-SG-E2   # term by term
.venv/bin/haus engineering houses/catlin --fingerprint retaining_wall/W-SG-E2
.venv/bin/haus print houses/catlin --sealed               # the submittal gate
```

- `typehaus/engineering/` is a **leaf package**: it imports `model`/`resolve`/`quantities`/
  `wind` and **never `checks`**. Its output is an `EngineeringRecord` (demand, capacity,
  ratio, governing limit state, citation), not a `Finding` — `Finding` has nowhere to hold
  numbers. `checks/_authoring.engineered()` is the one bridge between them.
- **Every calculation is oracled against an independently hand-worked note** in
  `houses/<name>/notes/`, the way `typehaus/wind.py` is oracled against
  `catlin_truss_engineering.md`. A calc that only agrees with itself is not verified.
- **draft** = this engine computed it and it checks out; `haus print` gates here, because
  draft approval is exactly what a permit-ready printoff is for. **sealed** = a licensed PE
  stamped it *and* the pinned fingerprint still matches the model.
- The seal lives in `houses/<name>/engineering.toml` (`docs/engineering-toml-format.md`),
  never on the elements: those are `# haus: editable` and undoable, and `_content_hash`
  hashes every `plan/**/*.py`, so a stamp written into plan source would change the hash it
  is pinned against. **The engine reads that file and never writes it.**
- `Result.NOT_APPLICABLE` is a fourth verdict — "the condition this rule governs does not
  exist in this building" — and must be **earned** from positive evidence of absence. "No
  masonry guard anywhere in the plan" is N/A. "No dryer modeled" in a house with a laundry
  is a real gap, and stays UNKNOWN.

## Costs and schedule

Dollars are opt-in and live in the house: `houses/<name>/prices.toml` (unit prices, plus
`[basis]` / `[waste]` / `[contingency]` / `[markup]` / `[tax]`), `costs.toml` (what was
actually paid), `tasks.toml` (work-package status). The engine ships no price data, ever.

- `cli/price_file.py` owns the file format; `cli/prices.py` owns the join to the BOM.
- `takeoff/cost_model.py` is the `net -> waste -> ordered -> contingency -> markup -> tax`
  ladder. A `merged` (installed, split unknown) subtotal is never divided.
- `takeoff/tasks.py` derives work packages at (trade x storey), ordered by
  `emit/trades.CONSTRUCTION_SEQUENCE`. Task ids are stable GlobalIds, so re-exporting
  updates rather than duplicates. No durations, crew sizes or dates — the model cannot know
  them.

`haus serve` watches `houses/<name>/` only. After editing anything under
`packages/engine/`, **restart the server** or the viewer shows stale geometry.

see also AGENTS.md

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
- **Files under 500 lines**, per `AGENTS.md`.

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
held to a clean report, 0 FAIL. (It ran on the looser gate for part of 2026-08-23, while
three `structural.deck_beam_span` advisories stood against the sunken garden's balcony
beams. Those are fixed, not accepted — see `houses/starter/CLAUDE.md` for the one house
that *does* carry deliberate reds, and why a template is the right place for them.)

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

# Catlin reference details — read-only

The fidelity bar for Catlin's transition details, copied from
`/Users/colincatlin/Documents-NoCloud/house/catlin-house`.

- `*.json` — the `Pset_ifcPlot_*` `ParamsJSON` dicts extracted from that repo's
  `catlin_house/out/catlin_house.ifc` by `scripts/extract_catlin_reference_params.py`.
  **These are the dimensional source of truth** and the only thing the test suite reads
  (`test_catlin_reference_parity.py`). Committed so the suite never depends on the other
  repository or on ifcopenshell being installed.
- `scripts/` — the hand-authored matplotlib detail drawings and their shared
  `detail_utils.py`. **Reference only**: never imported, never executed by the suite. They
  are here so the drawing vocabulary (flashing profiles, french drain, slab assembly,
  insect screen, notes column, legend) can be read alongside the code that reproduces it.

The rendered reference PNGs are deliberately *not* copied here — they are ~1.3 MB each and
git cannot delta-compress them. For the visual acceptance gate, read
`houses/catlin/out/render/detail_*.png` against `catlin_house/out/*_ifc.png` in the source
repo directly.

Catlin is expected to evolve past this source as the design is refined. Parity tests
therefore assert dimensions and drawing *vocabulary*, never pixels, and record intentional
departures in `DECLARED_DIVERGENCES` rather than freezing the house.

To refresh the parameters after a change in the source repo:

```
PYTHONPATH=packages/engine/src .venv/bin/python scripts/extract_catlin_reference_params.py
```

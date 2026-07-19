# Contributing a library item

`library/` is the shared, reviewed catalog. House plans are the right place to try a
new assembly, transition, material, fixture, or furniture item before it is promoted.

## Promotion flow

1. Author and exercise the item in `houses/<house>/`; keep the house-specific choice in
   that house.
2. Verify the item is generally reusable, declarative, has a stable tag, and does not
   include project coordinates, owner data, or proprietary mesh assets.
3. Add the item to the focused `library/` module and export it from `library/__init__.py`.
   Include the original technical source in `source`; empirical ratings such as STC must
   cite a published test or manufacturer assembly and must not be estimated.
4. Add the item to the relevant catalog tuple (`ALL_ASSEMBLIES`, materials, types, or
   transitions) and add a focused assertion when its framing or interface contract is
   non-obvious.
5. Run the library render and model checks:

   ```sh
   PYTHONPATH=packages/engine/src .venv/bin/python -m pytest -q \
     packages/engine/tests/test_model_and_emit.py
   ```

   The per-item card-render test is the required smoke test for every shared assembly.
   CI runs this suite, so an unresolved material reference or non-renderable card blocks
   the contribution.

## Assets and rights

Only original or redistributably licensed assets belong in `library/`. Imported furniture
from a vendor or 3D warehouse remains in `houses/<house>/furniture/` with its source note.
Do not copy product drawings into the repository merely to support a catalog record; link
to the authoritative source instead.

## Review checklist

- Tags are stable, descriptive, and unique.
- Every material reference resolves through the shared library.
- Dimensions and framing describe the published configuration exactly.
- Sources identify the test, report, or manufacturer system used for an empirical value.
- The item has no house-specific geometry, permit claim, or unlicensed asset.

# Rename Checklist

`Type:Haus` is locked (#9) but engineered for a cheap rename. To rebrand, change:

1. `packages/engine/pyproject.toml` — `name = "typehaus"` (PyPI package).
2. `packages/engine/src/typehaus/` — the single import-root directory.
3. Find/replace `typehaus` imports across the tree.
4. `packages/engine/src/typehaus/_meta.py` — `PROJECT_NAME`, `PROJECT_URL`,
   `IFC_APP_NAME`, `PSET_PREFIX`. (The pset prefix `Pset_TH` is brand-agnostic; keep or bump.)
5. `ui/src/branding.ts` — the single UI brand constant file (M2).
6. GitHub repo name, docs site, `docs/RENAME.md` header.

The CLI binary stays `haus` regardless — user muscle memory survives a rename.

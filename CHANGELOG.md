# Changelog

All notable changes to `typehaus`. This project follows [semantic versioning](https://semver.org).

## 0.1.0 — 2026-09-09

**The first working publish.** `0.1.0a0` is on PyPI and is unusable: that wheel contained
only `typehaus/`, with no shared catalog, no `haus new` template, and no license text. Every
house plan does `from library import ...`, so `pip install typehaus==0.1.0a0` installed an
engine that could not load or scaffold a single house. Nothing in the source tree could see
the break, because from a checkout every one of those paths resolves anyway. Do not install
`0.1.0a0`.

### Packaging

- The shared catalog now lives inside the package as `typehaus/library/` and ships in the
  wheel. It is deliberately not a top-level `library` in site-packages: that name belongs to
  an unrelated project on PyPI, and installing both would break one of them. Plan source is
  unchanged — `from library import ...` still works, aliased by the loader.
- The `haus new` starter template ships in the wheel, so a pip-installed engine can scaffold
  a house without a checkout to copy one from.
- The pre-built editor ships in the wheel. `pip install 'typehaus[server]' && haus serve`
  now delivers the browser app instead of answering the "UI not built" 404. A checkout's own
  `ui/dist` still wins, so a local rebuild is never shadowed by the packaged copy.
- The license text ships in the wheel, declared with PEP 639 `license = "MIT"`.
- The sdist repeats the wheel's force-includes, so it can rebuild an equivalent wheel.
- `haus doctor` reports the packaged UI alongside the checkout's `ui/dist`.
- CI asserts wheel contents (`scripts/check_wheel.py`), prints the catlin permit set, and
  publishes to PyPI through Trusted Publishing on a published release.

### Engine

- An empty or absent `uid` is now a load-time ERROR, alongside the existing collision error.
  `haus fmt` mints a uid only where the keyword is absent entirely and never visits
  `params/*.py` at all, so an element authored there with `uid=""` used to load clean and
  then collide every derived IFC GlobalId onto the value derived from the empty string —
  erasing that element's geometry three layers downstream.
- `ruff check packages/engine/src` is clean.

### Known limitations

- `mypy --strict` reports errors across the engine and is not a release gate.
- `Room.clear_face` is inset from the wall axis rather than the finish face, which skews room
  polygons and areas on thick walls. Fixing it moves every golden; it is the first item after
  this release.
- `resolve/framing/profiles.cross_section` falls back to a 1.5x5.5 rectangle for any profile
  string it cannot parse, silently, rather than raising.
- `PipeRun` elevations are storey-relative while `ConduitRun` elevations are absolute.

# `engineering.toml` format

Who sealed which engineered requirements, when, and against which version of the model.
Loaded by `typehaus.engineering.register.load_register`; see that module's docstring for
why the seal lives in a file rather than on the elements.

The file is **optional**. A house that has not been to an engineer simply has none, and
behaves exactly as it did before this file existed. **The engine never writes it** — a seal
is a human act, and `haus engineering --fingerprint <item>` prints the value to paste in.

## What it is for

Some requirements in a house fall outside the prescriptive tables — a retaining wall past
IRC Table R404.1.2(8), a round column with no R507.4 row, a trussed roof. Those checks
report their verdict with `Authority.ENGINEERED` and name an **item id**:

```
<kind>/<element-tag>          e.g.  retaining_wall/W-SG-E2
```

`haus engineering` lists every item in the house. This file records the professional
signoffs over them.

**The element tag is always a real element, including when the item is about a GROUP.**
`retaining_system/W-SG-ARCH` grades a four-wall court as one free body, and it is keyed on
the cross-member whose presence closes the loop and whose removal breaks it — the element a
seal is really being taken over, and the edit that should stale that seal. A group key like
`retaining_system/SG-COURT` would invent a name the model does not contain, and an item id
that names nothing cannot be pointed at, cannot be diffed, and cannot go stale. The other
members ride in `element_tags`, so the finding still lights up the whole court.

## Grammar

```toml
[[signoff]]
id        = "SG-LATERAL-01"      # required — unique within the file
scope     = "Sunken-garden lateral system: retaining walls and the porch columns on them"
covers    = ["retaining_wall/W-SG-E2", "retaining_wall/W-SG-S", "deck_post/PT-SG-FCOL"]
engineer  = "Jane Doe, PE"       # required — as it appears on the seal
license   = "MN 12345"           # required
sealed_on = "2026-09-14"         # required — ISO date, YYYY-MM-DD
document  = "notes/sg_lateral_2026-09-14.pdf"   # optional; the engine never reads it
note      = "Sliding governs at 1.62; shear keys added at the base of E2 and W2."

  [signoff.fingerprint]          # optional, but see "Pinning" below
  "retaining_wall/W-SG-E2" = "8f31c0a2d4e51b76"
  "retaining_wall/W-SG-S"  = "1a7c93be04d2f5e8"
```

Rules the loader enforces, loudly, rather than defaulting around:

- Every key in `id`, `scope`, `covers`, `engineer`, `license`, `sealed_on` must be present.
- `covers` is a list of item id strings.
- `sealed_on` must be an ISO date.
- Two `[[signoff]]` entries may not share an `id`, and **one item may not be covered by two
  signoffs** — one item, one seal.
- A `[signoff.fingerprint]` key that `covers` does not list is an error. It reads as
  protection and provides none, because nothing would consult it.

A malformed file raises `ValueError` naming the key. It is never silently ignored.

## Pinning, and why a seal without it is not enough

A stamp is a statement about a *specific* design. Once the model moves, the stamp is no
longer a statement about what is being built — and nothing in the file would say so.

The fingerprint closes that. It is a 16-hex digest over:

- the item's kind and key,
- **the inputs the calculation consumed**, each rounded to the quantum that input declares
  (lengths to 1 mm, loads to 1 psf), so float noise from a solver round-trip cannot stale a
  seal but a real change can,
- the calc module's `basis_version`, so a seal also goes stale when **the calculation**
  changes and not only when the model does,
- the governing ratio, as a tripwire for a calc edit whose author forgot to bump the basis.

Four states result:

| state | meaning | satisfies `--sealed`? |
|---|---|---|
| **fresh** | the pinned value matches what the suite computes now | yes |
| **stale** | it does not — the model or the calculation moved after sealing | **no** |
| **unpinned** | the signoff covers the item but pins no fingerprint | **no** — printed as "stamped, not pinned" |
| **unsealed** | no signoff covers this item | no |

`unpinned` deliberately does not count. A stamp that cannot go stale says nothing at all
about the model in front of the reader, which would make the seal a decoration.

An item this engine computes nothing for — a trussed roof, where the fabricator's design
governs — has no inputs and so cannot be pinned. Its signoff is recorded and prints as
"stamped, not pinned", and it never opens the final gate. That is correct: the engine has
no way to notice if the roof changes under it.

## The two gates

- **draft** — every blocking checklist item passes, and an engineered item satisfies it on
  this engine's own calculation alone. `haus print` gates here, because a draft approval is
  exactly what a permit-ready printoff is for.
- **sealed** — draft, **and** every engineered item carries a FRESH signoff.
  `haus print --sealed`, `haus permit-check --sealed` and `haus engineering --require-seal`
  gate here.

## Workflow

```
haus engineering houses/catlin                    # what needs a seal, and what governs
haus engineering houses/catlin --item retaining_wall/W-SG-E2   # the calc, term by term
haus engineering houses/catlin --fingerprint retaining_wall/W-SG-E2
# ... send the item's calc out for review; when it comes back sealed, write the
#     [[signoff]] block above and paste the fingerprint into [signoff.fingerprint].
haus engineering houses/catlin --unsealed         # what is still outstanding
haus print houses/catlin --sealed                 # the submittal gate
```

See also: `docs/prices-toml-format.md`, whose conventions this file follows, and decision
#65 in `plans/01-decisions.md` for why authority is orthogonal to verdict.

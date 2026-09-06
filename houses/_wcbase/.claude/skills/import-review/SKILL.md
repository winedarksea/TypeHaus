---
name: import-review
description: Walk an architect's modified IFC against the baseline via haus diff, accept/reject each change as a plan-source edit, rebuild, and re-diff until clean.
---

# /import-review

Bring an architect/engineer's revisions back into the plan source (the agentic-merge half of
the round-trip, → 20 §Diff).

## Steps
1. **Diff:** `haus diff <external.ifc> .` — writes `out/diff.json` (structured per-change
   deltas + match confidence) and prints a human table. Read `diff.json`.
2. **Read the plan source** the changes touch so each delta maps to a concrete element.
3. **Walk each change**, deciding accept or reject:
   - `moved` / `resized` / `attr-changed` → apply the delta as a keyword-arg edit on the
     element (same immutable `uid`), dimensions via quantity constructors.
   - `added` → author the new element (leave `uid=` off; `haus fmt` mints it).
   - `deleted` → remove the element's constructor call.
   - `replaced (was TAG)` → update the element in place; keep the original `uid`.
   - Low-confidence matches: inspect before trusting; a near-miss may be a genuine add+delete.
4. **Log decisions** to `out/import-decisions.md` (accepted / rejected + why) — this becomes
   the reply to the architect.
5. **Rebuild + re-diff:** `haus build .` then `haus diff <external.ifc> .`. Repeat until the
   report is empty or the remaining items are intentionally deferred (note them).
6. **Look:** `haus render --view plan .` to confirm the merged geometry still reads well.

## Guardrails
- Every accepted change is a plan-source edit through the normal editable dialect — never a
  hand-edit of `out/`. Preserve `uid`s so identity (and the architect's next diff) survives.

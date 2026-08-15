"""Shared Finding constructors for the checks tiers (→ 12 §Checks framework).

Every check module used to hand-roll its own ``_pass``/``_fail``/``_unknown``/``_advisory``
trio — the same four ``Finding(...)`` shapes, reconstructed independently in dozens of
modules under ``checks/``, ``resolve/``, and ``source/``. That duplication is what this
module retires: one place builds a Finding, everything else calls it.

Four shapes cover every call site found in the tree:

* ``passed``   — WARN severity, PASS result. A check succeeded; WARN is the general
  severity for check output, reserved severity ERROR is for hard blockers only.
* ``failed``   — ERROR severity, FAIL result. A hard blocker — `permit.py`'s integrity
  gate treats any ERROR-severity finding as blocking, regardless of check_id.
* ``unknown``  — WARN severity, UNKNOWN result, message auto-prefixed "UNKNOWN — ". The
  tri-state contract (#32): a rule that cannot evaluate reports UNKNOWN, never a pass.
* ``advisory`` — the general form, for the handful of call sites that need a result/severity
  combination the three named helpers don't cover (most commonly WARN severity paired with
  a FAIL result: an advisory finding that should show up as a failure without tripping the
  permit gate, which keys off ERROR severity alone).

The actual implementation lives in :mod:`typehaus.findings` (see the comment there) — this
module exists so every checks-tier module can import these from a stable, checks-flavored
path without needing to know that. ``resolve/`` and ``source/`` modules that need the same
four import straight from :mod:`typehaus.findings`, because importing this module (a
submodule of ``typehaus.checks``, whose package ``__init__`` eagerly imports the entire
checks tree) from a module the checks tree itself imports would be a circular import — this
package is the leaf side of the checks -> resolve dependency, never the other way.
"""

from __future__ import annotations

from typehaus.findings import Finding, Result, advisory, failed, passed, unknown


def structural_advisory(cid: str, msg: str, tags: tuple[str, ...], result: Result,
                        fix_hint: str | None = None) -> Finding:
    """A structural finding prefixed to say out loud that a prescriptive table lookup is not
    an engineered design. Five ``checks/structural/`` modules each defined this identically —
    the one thing distinguishing it from plain ``advisory`` is the message prefix, not a
    different Finding shape."""
    return advisory(cid, f"[advisory, not engineering] {msg}", tags, result, fix=fix_hint)


__all__ = ["advisory", "failed", "passed", "structural_advisory", "unknown"]

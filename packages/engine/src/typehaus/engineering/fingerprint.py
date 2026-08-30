"""What makes a professional seal checkable rather than decorative.

A stamp on a drawing is a statement about a *specific* design. Once the design moves, the
stamp is no longer a statement about what is being built — but nothing in a file says so,
and a stale seal reads exactly like a fresh one. This module gives a seal something to be
pinned against.

The three decisions that make it usable, and each is a decision against an easier one:

**Hash the inputs, not the model.** Hashing ``PlanModel._content_hash`` would stale every
seal in the house when someone moves a doorknob. Hashing the finding's message would stale
one on a reword. What an engineer sealed is the set of facts their calculation consumed —
so that is what is hashed, and nothing else.

**Declare the rounding.** Geometry that survives a round trip through metres and a solver
carries float noise, and a 7'-0" wall re-derived as ``2.1336000000000003`` is the same wall.
Each :class:`Quantity` names its own quantum (lengths 1 mm, loads 1 psf), so the tolerance a
seal survives is visible beside the number rather than buried in a hashing routine.

**Include the basis version.** A fingerprint over the inputs alone answers "did the model
change" and is silent on "did the calculation change" — which would let an edit to the
arithmetic slip under a stamp that is still, on paper, valid. ``basis_version`` closes that,
and the governing ratio rides along as a tripwire for the calc author who forgot to bump it.

The engine **never writes** ``engineering.toml``. ``haus engineering --fingerprint <id>``
prints the current value for a person to paste in, which keeps the act of pinning a seal a
human one.
"""

from __future__ import annotations

import hashlib
from enum import Enum

from typehaus.engineering.item import EngineeringRecord

#: Bumped only when the *hashing scheme itself* changes, which stales every seal in every
#: house at once. That is a deliberate, and deliberately rare, event.
SCHEME_VERSION = "1"


class Freshness(Enum):
    """How a seal stands against the model as it is now."""

    FRESH = "fresh"        # the pinned fingerprint matches what the suite computes today
    STALE = "stale"        # it does not — the model or the calculation moved after sealing
    UNPINNED = "unpinned"  # the signoff covers the item but pins no fingerprint for it
    UNSEALED = "unsealed"  # no signoff covers this item at all


def fingerprint(record: EngineeringRecord) -> str:
    """A 16-hex-character digest of exactly what a seal is a statement about.

    Stable across runs and across machines: everything hashed is either a literal from the
    record or a value put through its own declared quantum first.
    """
    parts = [
        f"scheme={SCHEME_VERSION}",
        f"kind={record.kind}",
        f"key={record.key}",
        f"basis_version={record.basis_version}",
    ]
    # Sorted by name so that reordering the calc's own bookkeeping cannot stale a seal.
    for quantity in sorted(record.inputs, key=lambda q: q.name):
        parts.append(f"in:{quantity.name}={quantity.rounded():.6g}{quantity.unit}")
    ratio = record.ratio
    # Two decimals: the tripwire is meant to catch a calculation that changed its answer,
    # not to re-stale a seal every time the last digit of a float moves.
    parts.append(f"ratio={'none' if ratio is None else format(ratio, '.2f')}")
    digest = hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()
    return digest[:16]

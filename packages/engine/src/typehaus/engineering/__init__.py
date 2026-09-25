"""``typehaus.engineering`` — first-principles structural calculations, as records.

The claim this package makes, and the one it must keep, is that a result here *mirrors what
an engineer would compute*. Two things enforce that and nothing else does:

* **Every calculation is oracled against an independently hand-worked note** in
  ``houses/<name>/notes/``, the way ``typehaus/wind.py`` is oracled against
  ``catlin_truss_engineering.md``. A calculation that only agrees with itself is not
  verified.
* **Computing is not sealing.** A record's own PASS opens the *draft* gate — enough for a
  permit-ready printoff — and never the final one. Only a licensed PE's signoff in
  ``engineering.toml``, pinned to a matching fingerprint, does that.

Import direction: this package reads ``model`` / ``resolve`` / ``quantities`` / ``wind`` and
**never** ``checks``. That is what lets ``CheckContext`` carry the results without a cycle,
and it is the same leaf discipline ``findings.py`` documents for itself.
"""

from __future__ import annotations

from typehaus.engineering.deferred import DEFERRALS, Deferral
from typehaus.engineering.fingerprint import (
    SETTLED,
    Freshness,
    fingerprint,
    pinnable,
)
from typehaus.engineering.item import (
    EngineeringRecord,
    LimitState,
    Oracle,
    Quantity,
    Scope,
    Status,
    item_id,
    no_calc,
)
from typehaus.engineering.register import (
    REGISTER_FILENAME,
    EngineeringRegister,
    ExternalDesign,
    Signoff,
    load_register,
)
from typehaus.engineering.registry import (
    NO_ENGINEERING,
    EngineeringContext,
    EngineeringResults,
    calc,
    keys,
    keys_of,
    records_of,
    registered_kinds,
)

__all__ = [
    "DEFERRALS", "Deferral",
    "EngineeringContext", "EngineeringRecord", "EngineeringRegister", "EngineeringResults",
    "ExternalDesign", "Freshness", "LimitState", "NO_ENGINEERING", "Oracle", "Quantity",
    "REGISTER_FILENAME", "SETTLED", "Scope", "Signoff", "Status", "pinnable",
    "calc", "fingerprint", "item_id", "keys", "keys_of", "load_register", "no_calc", "records_of",
    "registered_kinds",
]


def _discover() -> None:
    """Import every module under this package: importing a calc module is what registers it.

    Auto-discovered rather than listed, so a new family cannot silently vanish from
    ``haus engineering``, S-105 and the permit gate for want of an import line.
    """
    import importlib
    import pkgutil

    for info in pkgutil.walk_packages(__path__, prefix=f"{__name__}."):
        importlib.import_module(info.name)


_discover()

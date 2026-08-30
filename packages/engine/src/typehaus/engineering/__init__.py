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

# Importing a calc module is what registers it, so this list IS the suite: a family nobody
# imports here silently vanishes from `haus engineering`, from S-105 and from the permit
# gate, exactly as an unimported ``cmd_*`` module vanishes from ``haus --help``. Each one
# imports ``engineering.item``/``engineering.registry`` directly rather than this package,
# so the order here is free — but the presence of the line is not.
from typehaus.engineering import retaining_wall  # noqa: F401  (registration)
from typehaus.engineering.fingerprint import Freshness, fingerprint
from typehaus.engineering.item import (
    EngineeringRecord,
    LimitState,
    Quantity,
    Status,
    item_id,
    no_calc,
)
from typehaus.engineering.register import (
    REGISTER_FILENAME,
    EngineeringRegister,
    Signoff,
    load_register,
)
from typehaus.engineering.registry import (
    NO_ENGINEERING,
    EngineeringContext,
    EngineeringResults,
    calc,
    keys,
    records_of,
    registered_kinds,
)

__all__ = [
    "EngineeringContext", "EngineeringRecord", "EngineeringRegister", "EngineeringResults",
    "Freshness", "LimitState", "NO_ENGINEERING", "Quantity", "REGISTER_FILENAME",
    "Signoff", "Status",
    "calc", "fingerprint", "item_id", "keys", "load_register", "no_calc", "records_of",
    "registered_kinds", "retaining_wall",
]

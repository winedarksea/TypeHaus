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
from typehaus.engineering import (
    base_rotation,  # noqa: F401  (registration)
    column_base,  # noqa: F401  (registration)
    column_head_joint,  # noqa: F401  (registration)
    column_support,  # noqa: F401  (registration)
    deck_post,  # noqa: F401  (registration)
    deferred,  # noqa: F401  (registration — the kinds this engine defers to a designer)
    girt_screw,  # noqa: F401  (registration)
    glulam_beam,  # noqa: F401  (registration)
    lateral_system,  # noqa: F401  (registration)
    post_bearing,  # noqa: F401  (registration)
    retaining_system,  # noqa: F401  (registration)
    retaining_wall,  # noqa: F401  (registration)
    roof_beam,  # noqa: F401  (registration)
    spread_footing,  # noqa: F401  (registration)
    thermal_break,  # noqa: F401  (registration)
    veneer_beam,  # noqa: F401  (registration)
    wall_panel,  # noqa: F401  (registration)
)
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
    "base_rotation", "column_base", "column_head_joint", "column_support", "deck_post",
    "deferred", "girt_screw", "glulam_beam",
    "lateral_system", "roof_beam",
    "registered_kinds",
    "retaining_system",
    "retaining_wall", "spread_footing", "thermal_break", "veneer_beam", "wall_panel",
]

"""``houses/<name>/engineering.toml`` — who sealed what, when, and against which model.

Why a file rather than fields on the elements. Four reasons, and the last one is fatal:

1. One stamp covering three walls and six pillars would be duplicated nine times, or else
   referenced by a tag — which reinvents this file with worse ergonomics.
2. A PE's seal is a fact about the outside world on a date, not a design decision. The repo
   already draws this line for work-package status (``takeoff/task_state.py``: "closing out
   a work package is not a plan edit") and for dollars (#28).
3. Element files carry ``# haus: editable`` — they are UI-writable and sit in the undo
   journal. Un-stamping a sealed design with Ctrl-Z is that same lie about a legal document.
4. **Fatal.** ``source/loader.py::_content_hash`` hashes every ``plan/**/*.py``. Writing a
   stamp into plan source would change the very hash the stamp is pinned against.

Conventions follow ``cli/price_file.py``: an absent file is ``None``, not an error, so a
house that has not been to an engineer behaves exactly as it did before this existed; a
malformed one raises ``ValueError`` naming the key, and nothing is ever silently defaulted.

The engine reads this file and never writes it. It does not read the referenced PDF either
— ``document`` is a pointer for a human, and pretending to have verified a document's
contents would be a worse lie than not carrying one.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

try:  # tomllib is stdlib on 3.11+; the engine still supports 3.9
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - exercised on <3.11 only
    import tomli as tomllib  # type: ignore[no-redef,import-not-found]

from typehaus.engineering.fingerprint import Freshness, fingerprint
from typehaus.engineering.item import EngineeringRecord

REGISTER_FILENAME = "engineering.toml"

_REQUIRED = ("id", "scope", "covers", "engineer", "license", "sealed_on")


@dataclass(frozen=True)
class Signoff:
    """One sealed document and the engineering items it covers."""

    id: str
    scope: str
    covers: tuple[str, ...]
    engineer: str
    license: str
    sealed_on: date
    document: str | None = None
    note: str | None = None
    #: item id -> the fingerprint that was current when the seal was made. An item listed in
    #: ``covers`` but absent here is *pinned to nothing*: it prints as "stamped, not pinned"
    #: and never satisfies the final gate, because a stamp that cannot go stale is a stamp
    #: that says nothing about the model in front of you.
    fingerprints: Mapping[str, str] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.fingerprints is None:
            object.__setattr__(self, "fingerprints", {})

    def credit(self) -> str:
        """"Jane Doe, PE (MN 12345), 2026-09-14" — the line A-000 and S-105 letter."""
        return f"{self.engineer} ({self.license}), {self.sealed_on.isoformat()}"


@dataclass(frozen=True)
class EngineeringRegister:
    """Every signoff a house declares, indexed by the items they cover."""

    signoffs: tuple[Signoff, ...] = ()

    def covering(self, item_id: str) -> Signoff | None:
        """The signoff that covers this item, or ``None``.

        First match wins, and duplicates are refused at load time rather than resolved
        here — two seals over one item is a question for a person, not a tie-break rule.
        """
        for signoff in self.signoffs:
            if item_id in signoff.covers:
                return signoff
        return None

    def freshness(self, record: EngineeringRecord) -> tuple[Freshness, Signoff | None]:
        """How the seal on this item stands against the model as it is right now."""
        signoff = self.covering(record.item_id)
        if signoff is None:
            return Freshness.UNSEALED, None
        pinned = signoff.fingerprints.get(record.item_id)
        if not pinned:
            return Freshness.UNPINNED, signoff
        if pinned == fingerprint(record):
            return Freshness.FRESH, signoff
        return Freshness.STALE, signoff


def load_register(house_dir: Path | None) -> EngineeringRegister:
    """Read ``engineering.toml``; an absent file is an empty register, never an error."""
    if house_dir is None:
        return EngineeringRegister()
    path = Path(house_dir) / REGISTER_FILENAME
    if not path.exists():
        return EngineeringRegister()
    try:
        data = tomllib.loads(path.read_text())
    except tomllib.TOMLDecodeError as exc:
        raise ValueError(f"{path}: not valid TOML — {exc}") from exc
    entries = data.get("signoff", [])
    if not isinstance(entries, list):
        raise ValueError(f"{path}: [[signoff]] must be an array of tables")
    signoffs = tuple(_signoff(entry, path, index) for index, entry in enumerate(entries))
    _refuse_duplicates(signoffs, path)
    return EngineeringRegister(signoffs=signoffs)


def _signoff(entry: Any, path: Path, index: int) -> Signoff:
    where = f"{path}: [[signoff]] #{index + 1}"
    if not isinstance(entry, dict):
        raise ValueError(f"{where} is not a table")
    for key in _REQUIRED:
        if key not in entry:
            raise ValueError(f"{where} is missing required key `{key}`")
    covers = entry["covers"]
    if not isinstance(covers, list) or not all(isinstance(x, str) for x in covers):
        raise ValueError(f"{where} (`{entry['id']}`): `covers` must be a list of item ids "
                         f"like \"retaining_wall/W-SG-E2\"")
    sealed_on = entry["sealed_on"]
    if isinstance(sealed_on, str):
        try:
            sealed_on = date.fromisoformat(sealed_on)
        except ValueError as exc:
            raise ValueError(f"{where} (`{entry['id']}`): `sealed_on` must be an ISO date "
                             f"(YYYY-MM-DD), got {sealed_on!r}") from exc
    if not isinstance(sealed_on, date):
        raise ValueError(f"{where} (`{entry['id']}`): `sealed_on` must be a date")
    prints = entry.get("fingerprint", {})
    if not isinstance(prints, dict) or not all(isinstance(v, str) for v in prints.values()):
        raise ValueError(f"{where} (`{entry['id']}`): [signoff.fingerprint] must map an "
                         f"item id to a hex string")
    unknown_pins = sorted(set(prints) - set(covers))
    if unknown_pins:
        # A fingerprint pinned for an item the signoff does not cover reads as protection
        # and provides none — nothing consults it. Loudly wrong beats quietly inert.
        raise ValueError(f"{where} (`{entry['id']}`): [signoff.fingerprint] pins "
                         f"{', '.join(unknown_pins)}, which `covers` does not list")
    return Signoff(
        id=str(entry["id"]), scope=str(entry["scope"]), covers=tuple(covers),
        engineer=str(entry["engineer"]), license=str(entry["license"]),
        sealed_on=sealed_on,
        document=entry.get("document"), note=entry.get("note"),
        fingerprints=dict(prints),
    )


def _refuse_duplicates(signoffs: tuple[Signoff, ...], path: Path) -> None:
    seen_ids: set[str] = set()
    seen_items: dict[str, str] = {}
    for signoff in signoffs:
        if signoff.id in seen_ids:
            raise ValueError(f"{path}: two [[signoff]] entries share id `{signoff.id}`")
        seen_ids.add(signoff.id)
        for item in signoff.covers:
            if item in seen_items:
                raise ValueError(
                    f"{path}: `{item}` is covered by both `{seen_items[item]}` and "
                    f"`{signoff.id}` — one item, one seal")
            seen_items[item] = signoff.id

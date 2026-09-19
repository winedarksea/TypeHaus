"""``houses/<name>/engineering.toml`` — who sealed what, when, and against which model.

Why a file rather than fields on the elements. Four reasons, and the last one is fatal:

1. One stamp covering three walls and six pillars would be duplicated nine times, or else
   referenced by a tag — which reinvents this file with worse ergonomics.
2. A PE's seal is a fact about the outside world on a date, not a design decision. The repo
   already draws this line for work-package status (``takeoff/task_state.py``: "closing out
   a work package is not a plan edit") and for dollars (#28).
3. Element files carry ``# haus: editable`` — they are UI-writable and sit in the undo
   journal. Un-stamping a sealed design with Ctrl-Z is that same lie about a legal document.
4. **Fatal.** A stamp in plan source would be *read back by the thing it is a statement
   about*. The seal names item ids and pins ``fingerprint(record)`` for each; those records
   are computed from the plan, so a plan that also contained the seal would be an input to
   its own pin. (This reason used to be stated as "``_content_hash`` hashes every
   ``plan/**/*.py``, so the stamp would change the hash it is pinned against" — **that
   mechanism is false.** Nothing pins a seal against ``content_hash``; see
   ``fingerprint.py``, which rejected hashing the model on purpose.)

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

from typehaus.engineering.fingerprint import Freshness, fingerprint, pinnable
from typehaus.engineering.item import EngineeringRecord

REGISTER_FILENAME = "engineering.toml"

#: The delimiters ``engineering/scaffold.py`` wraps every field a person must replace in.
#: A scaffold is a form, and a form returned with its blanks still in it is not a seal — so
#: the loader refuses one rather than treating "<<ENGINEER NAME, PE>>" as an engineer's name.
PLACEHOLDER = ("<<", ">>")

_REQUIRED = ("id", "scope", "covers", "engineer", "license", "sealed_on")


@dataclass(frozen=True)
class ExternalDesign:
    """An outside designer's sealed document, and what it was issued for.

    **What a deferred item is pinned to instead of a fingerprint.** A trussed roof is
    designed by its fabricator; this engine computes nothing for it, so there are no inputs
    to hash and nothing that could go stale when the roof changes. Pinning the DOCUMENT is
    the honest substitute: a revision and a sha256 say which paper was accepted, and the
    envelope says what it was accepted FOR — the spans, loads and conditions the supplier
    ran it at. A reviewer compares that envelope to the model; the engine cannot, and does
    not pretend to.

    The engine does not open the document and does not verify the digest. That is the same
    rule ``document`` has carried since this file existed, and for the same reason: claiming
    to have checked a PDF's contents would be a worse lie than not carrying one. The digest
    is there so a person can check it, and so that a REVISED document read as revised.
    """

    #: Path or reference to the sealed document, as the person recorded it.
    document: str
    #: The supplier's own revision marking — "Rev C, 2026-08-14". Not a date: a document
    #: reissued the same day is a different document and must read as one.
    revision: str
    #: sha256 of that document, lowercase hex. The engine records it and never computes it.
    sha256: str
    #: The geometry and load envelope the document was issued for, in the supplier's terms.
    #: This is the whole of what a reviewer has to check by hand, so it is required rather
    #: than optional — an acceptance with no envelope is an acceptance of nothing.
    envelope: str


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
    #: item id -> the outside designer's document this item is accepted against, for an item
    #: this engine computes nothing for. See :class:`ExternalDesign`. An item may carry this
    #: OR a fingerprint and not both: one says "the model has not moved", the other says
    #: "somebody else designed this and here is their paper", and an item cannot be
    #: both at once.
    external: Mapping[str, ExternalDesign] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.fingerprints is None:
            object.__setattr__(self, "fingerprints", {})
        if self.external is None:
            object.__setattr__(self, "external", {})

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
        # Before the fingerprint, because an externally designed item HAS no fingerprint to
        # compare and the answer is not "unpinned".
        if record.item_id in signoff.external:
            return Freshness.ACCEPTED, signoff
        pinned = signoff.fingerprints.get(record.item_id)
        if not pinned:
            return Freshness.UNPINNED, signoff
        # ** THE STATUS TEST, AND IT GOES BEFORE THE COMPARISON. ** A `NO_CALC` record has
        # no inputs, so `fingerprint()` digests the same empty set every time and any pinned
        # value that happens to equal it read FRESH here — a seal reporting itself current
        # against a calculation that does not exist. The three renderers refused to MINT
        # such a digest; none of them could refuse one already in the file.
        if not pinnable(record):
            return Freshness.UNPINNABLE, signoff
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
    # Before anything is parsed, and before the date in particular: an unedited scaffold
    # would otherwise fail on `sealed_on` and send the reader to fix the wrong field.
    _refuse_placeholders(entry, where)
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
    external = _external(entry, where, covers, set(prints))
    return Signoff(
        id=str(entry["id"]), scope=str(entry["scope"]), covers=tuple(covers),
        engineer=str(entry["engineer"]), license=str(entry["license"]),
        sealed_on=sealed_on,
        document=entry.get("document"), note=entry.get("note"),
        fingerprints=dict(prints), external=external,
    )


_EXTERNAL_REQUIRED = ("document", "revision", "sha256", "envelope")


def _external(entry: dict[str, Any], where: str, covers: list[str],
              pinned: set[str]) -> dict[str, ExternalDesign]:
    """``[signoff.external."<item id>"]`` -> :class:`ExternalDesign`, strictly.

    Every key is required. An acceptance missing its envelope accepts nothing, and one
    missing its revision or digest cannot tell a reissued document from the one that was
    actually reviewed — which is the failure mode this whole block exists to close.
    """
    tables = entry.get("external", {})
    if not isinstance(tables, dict):
        raise ValueError(f"{where} (`{entry['id']}`): [signoff.external] must be a table "
                         f"of item id -> document")
    unknown = sorted(set(tables) - set(covers))
    if unknown:
        raise ValueError(f"{where} (`{entry['id']}`): [signoff.external] accepts "
                         f"{', '.join(unknown)}, which `covers` does not list")
    both = sorted(set(tables) & pinned)
    if both:
        # One says "the model has not moved"; the other says "somebody else designed this".
        # An item carrying both is a claim nobody can act on.
        raise ValueError(f"{where} (`{entry['id']}`): {', '.join(both)} carries BOTH a "
                         f"fingerprint and an [signoff.external] acceptance — an item is "
                         f"pinned to this model or to somebody else's document, not both")
    out: dict[str, ExternalDesign] = {}
    for item_id, table in tables.items():
        spot = f"{where} (`{entry['id']}`): [signoff.external.\"{item_id}\"]"
        if not isinstance(table, dict):
            raise ValueError(f"{spot} is not a table")
        _refuse_placeholders(table, spot)
        for key in _EXTERNAL_REQUIRED:
            if not str(table.get(key, "")).strip():
                raise ValueError(f"{spot} is missing required key `{key}`")
        out[item_id] = ExternalDesign(
            document=str(table["document"]), revision=str(table["revision"]),
            sha256=str(table["sha256"]).lower(), envelope=str(table["envelope"]))
    return out


def _refuse_placeholders(entry: dict[str, Any], where: str) -> None:
    """Refuse a signoff still carrying a scaffold's blanks.

    ``haus handoff`` writes ``engineering.toml.draft`` with ``<<ENGINEER NAME, PE>>`` and
    friends. Copying it over unedited is the one plausible way to produce a file that looks
    like a seal register and records nobody's seal, so the loader names the field.
    """
    opener, closer = PLACEHOLDER
    for key, value in sorted(entry.items()):
        if isinstance(value, str) and opener in value and closer in value:
            raise ValueError(
                f"{where}: `{key}` still holds the scaffold placeholder {value!r}. This "
                f"file was copied from `engineering.toml.draft` without being filled in — "
                f"a form with its blanks still in it is not a seal.")


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

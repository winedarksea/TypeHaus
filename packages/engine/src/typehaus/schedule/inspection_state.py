"""``inspections.toml`` — what the AHJ actually said, beside what the code requires.

Same idiom as ``takeoff/costs.py`` and ``takeoff/task_state.py``: the loader raises on a
malformed file naming the offending key, the writer is deterministic and sorted, and
neither depends on the server. Outside the PatchOp/undo journal, like the other two — a
passed inspection is not a plan edit, and undo must never un-pass one.

**The engine reads this file and never writes it during a build.** Only an explicit
``PUT /inspections`` writes, exactly as ``engineering.toml`` is read and never written.

Two things that look alike and are not. ``waived`` is the AHJ saying this inspection is not
required *here* — a fact about the jurisdiction's discretion. ``not_applicable`` is this
building not having the condition the inspection covers — a fact about the model, earned
from positive evidence in :mod:`typehaus.schedule.applicability`. Neither is derivable from
the other and conflating them would let a shrug close a gate. A waiver is therefore a table
with a ``by``, a ``date`` and a ``ref``, not a free string: it outranks model evidence, so
it has to say who granted it.

**Attempts, not a result.** One inspection is called more than once. ``attempts`` is an
ordered list and the state derives from the last of them; a second attempt used to overwrite
the first, which lost the correction list the reinspection exists to answer. ``partial`` is
real and common — half the house passed and the inspector wants a second look at one
corner — and it releases only the scope it names.

**Instances.** ``[entries.footing]`` is the default instance of the ``footing`` spec;
``[entries."footing/court"]`` is a second one, with its own scope, booking and attempts. A
house pours its footings twice and gets inspected twice, and one result slot per code line
could not say so.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:  # tomllib is stdlib on 3.11+; the engine still supports 3.9
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - exercised on <3.11 only
    import tomli as tomllib  # type: ignore[no-redef,import-not-found]

INSPECTIONS_FILENAME = "inspections.toml"

#: What an AHJ writes on the card. ``partial`` is real and common and folding it into
#: ``fail`` would lose the distinction the owner schedules against.
RESULTS = ("pass", "fail", "partial")

#: How a request reaches the authority. Saint Paul takes a phone call in a 90-minute window
#: or a PAULIE portal request; the state's electrical is a filed request. Which one this
#: authority uses changes what the board asks the owner to do, so it is a field.
METHODS = ("phone", "portal", "email")

ENTRY_FIELDS = ("requested", "scheduled", "inspector", "note", "scope", "checked",
                "requires", "attempts", "waived")
_ENTRY_LISTS = ("scope", "checked", "requires")
ATTEMPT_FIELDS = ("date", "result", "inspector", "corrections", "approved", "note")
AUTHORITY_FIELDS = ("label", "phone", "portal_url", "window", "lead_days", "method",
                    "source_url", "confirmed")
PERMIT_FIELDS = ("number", "issued", "expires", "code_edition", "nec_edition", "note")
WAIVER_FIELDS = ("by", "date", "ref", "note")
_EXTRA_FIELDS = ("id", "label", "authority", "after", "gates", "check_ids", "on_site",
                 "code_refs", "milestone", "applies_when")


@dataclass(frozen=True)
class Authority:
    """Who to call. House-owned: the engine ships no phone numbers.

    ``lead_days``, ``window`` and the reinspection fee are **not published** by Saint Paul
    DSI. Minn. R. 1300.0210 subp. 4 obliges the authority to state them at permit issuance,
    so they are open items the board asks for rather than numbers the engine supplies.
    ``confirmed`` is the date the owner last checked the number against the source, because
    a wrong number on a 7:30am deadline is the error this file exists to prevent.
    """

    label: str
    phone: str | None = None
    portal_url: str | None = None
    #: When they take calls, as the AHJ words it: ``"7:30-9:00 M-F"``.
    window: str | None = None
    #: Business days' notice they ask for. A number the *jurisdiction* states.
    lead_days: int | None = None
    method: str | None = None
    source_url: str | None = None
    confirmed: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {name: getattr(self, name) for name in AUTHORITY_FIELDS}


@dataclass(frozen=True)
class Permit:
    """The permit this build runs under, and the code editions it was pulled against.

    An edition is a **field**, not a constant: Saint Paul's 2026 NEC applies to electrical
    permits pulled after 2026-08-17, and the 2024-IRC-based Minnesota code has no effective
    date yet, so which cycle a 2027 permit lands in is not something the engine may assume.
    """

    number: str | None = None
    issued: str | None = None
    expires: str | None = None
    code_edition: str | None = None
    nec_edition: str | None = None
    note: str | None = None

    @property
    def is_empty(self) -> bool:
        return not any(getattr(self, name) for name in PERMIT_FIELDS)

    def as_dict(self) -> dict[str, Any]:
        return {name: getattr(self, name) for name in PERMIT_FIELDS}


@dataclass(frozen=True)
class Waiver:
    """The AHJ saying this inspection is not required here — with the evidence."""

    by: str
    date: str | None = None
    ref: str | None = None
    note: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {name: getattr(self, name) for name in WAIVER_FIELDS}


@dataclass(frozen=True)
class Attempt:
    """One visit by the inspector, and what they wrote on the card."""

    date: str
    result: str
    inspector: str | None = None
    #: What has to change before the next attempt. The reinspection exists to answer these.
    corrections: tuple[str, ...] = ()
    #: On a ``partial``: the element-tag globs and/or visit slugs this attempt released.
    approved: tuple[str, ...] = ()
    note: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {"date": self.date, "result": self.result, "inspector": self.inspector,
                "corrections": list(self.corrections), "approved": list(self.approved),
                "note": self.note}


@dataclass(frozen=True)
class InspectionEntry:
    """The owner's record of one inspection **instance**, keyed by ``id`` or ``id/scope``."""

    requested: str | None = None
    scheduled: str | None = None
    inspector: str | None = None
    note: str | None = None
    #: Element-tag globs and/or visit slugs this instance covers. Empty means the whole
    #: building, which is what a single-instance inspection is.
    scope: tuple[str, ...] = ()
    checked: tuple[str, ...] = ()
    requires: tuple[str, ...] = ()
    attempts: tuple[Attempt, ...] = ()
    waived: Waiver | None = None

    @property
    def last(self) -> Attempt | None:
        return self.attempts[-1] if self.attempts else None

    @property
    def result(self) -> str | None:
        """The state, derived from the last attempt. Never a slot anybody overwrites."""
        return self.last.result if self.last is not None else None

    @property
    def approved(self) -> tuple[str, ...]:
        """The scope released so far: a partial pass releases only what it names."""
        if self.result == "pass":
            return ("*",)
        out: list[str] = []
        for attempt in self.attempts:
            if attempt.result in ("pass", "partial"):
                out.extend(attempt.approved or (("*",) if attempt.result == "pass" else ()))
        return tuple(dict.fromkeys(out))

    @property
    def is_empty(self) -> bool:
        return not any(getattr(self, name) for name in ENTRY_FIELDS)

    def as_dict(self) -> dict[str, Any]:
        return {"requested": self.requested, "scheduled": self.scheduled,
                "inspector": self.inspector, "note": self.note,
                "scope": list(self.scope), "checked": list(self.checked),
                "requires": list(self.requires),
                "attempts": [a.as_dict() for a in self.attempts],
                "waived": self.waived.as_dict() if self.waived else None,
                "result": self.result, "approved": list(self.approved)}


@dataclass(frozen=True)
class ExtraInspection:
    """An inspection this house needs that the profile does not list.

    catlin's girt-screw hold is one: ``authority = "owner"``, because a hold the owner
    placed on themselves is not an AHJ visit and giving it a phone number would be a lie.
    """

    id: str
    label: str
    authority: str = "building"
    after: tuple[str, ...] = ()
    gates: tuple[str, ...] = ()
    check_ids: tuple[str, ...] = ()
    on_site: tuple[str, ...] = ()
    code_refs: tuple[str, ...] = ()
    milestone: str = ""
    applies_when: str | None = None

    def as_spec(self) -> Any:
        from typehaus.checks.jurisdiction import InspectionSpec

        return InspectionSpec(id=self.id, label=self.label, authority=self.authority,
                              after=self.after, gates=self.gates,
                              check_ids=self.check_ids, on_site=self.on_site,
                              code_refs=self.code_refs, milestone=self.milestone,
                              applies_when=self.applies_when)


def spec_of(key: str) -> str:
    """``"footing/court"`` -> ``"footing"``. The instance suffix is everything after it."""
    return str(key).split("/", 1)[0]


def instance_of(key: str) -> str:
    parts = str(key).split("/", 1)
    return parts[1] if len(parts) > 1 else ""


@dataclass(frozen=True)
class InspectionsState:
    authorities: Mapping[str, Authority] = field(default_factory=dict)
    entries: Mapping[str, InspectionEntry] = field(default_factory=dict)
    extra: tuple[ExtraInspection, ...] = ()
    permit: Permit = field(default_factory=Permit)

    def entry(self, inspection_id: str) -> InspectionEntry | None:
        return self.entries.get(inspection_id)

    def instances(self, spec_id: str) -> dict[str, InspectionEntry]:
        """Every instance key of one spec, default instance first."""
        return {key: entry for key, entry in sorted(self.entries.items())
                if spec_of(key) == spec_id}


def _strings(raw: Any, where: str, name: str) -> tuple[str, ...]:
    if isinstance(raw, str) or not isinstance(raw, (list, tuple)):
        raise ValueError(f"{where}: {name!r} must be an array of strings")
    return tuple(str(item) for item in raw)


def _attempts(raw: Any, where: str) -> tuple[Attempt, ...]:
    if not isinstance(raw, (list, tuple)):
        raise ValueError(f"{where}: 'attempts' must be an array of tables — one per visit "
                         "by the inspector, in order")
    out: list[Attempt] = []
    for index, item in enumerate(raw):
        at = f"{where}: attempts #{index + 1}"
        if not isinstance(item, dict):
            raise ValueError(f"{at} must be a table")
        unknown = set(item) - set(ATTEMPT_FIELDS)
        if unknown:
            raise ValueError(f"{at}: unknown field(s) {sorted(unknown)}; "
                             f"expected {list(ATTEMPT_FIELDS)}")
        if not item.get("date") or not item.get("result"):
            raise ValueError(f"{at}: needs a 'date' and a 'result'")
        result = str(item["result"])
        if result not in RESULTS:
            raise ValueError(f"{at}: result {result!r}; expected one of {list(RESULTS)}")
        if result == "partial" and not item.get("approved"):
            raise ValueError(f"{at}: a 'partial' must name the scope it 'approved' — a "
                             "partial that releases everything is a pass")
        out.append(Attempt(
            date=str(item["date"]), result=result,
            inspector=str(item["inspector"]) if item.get("inspector") else None,
            corrections=(_strings(item["corrections"], at, "corrections")
                         if item.get("corrections") else ()),
            approved=(_strings(item["approved"], at, "approved")
                      if item.get("approved") else ()),
            note=str(item["note"]) if item.get("note") else None))
    return tuple(out)


def _waiver(raw: Any, where: str) -> Waiver:
    if not isinstance(raw, dict):
        raise ValueError(f"{where}: 'waived' must be "
                         "{ by = \"...\", date = \"...\", ref = \"...\" } — a waiver "
                         "outranks the model's own evidence, so it has to say who granted "
                         "it and what the record is")
    unknown = set(raw) - set(WAIVER_FIELDS)
    if unknown:
        raise ValueError(f"{where}: waived has unknown field(s) {sorted(unknown)}")
    if not raw.get("by"):
        raise ValueError(f"{where}: waived needs a 'by' — who at the authority said so")
    return Waiver(by=str(raw["by"]),
                  date=str(raw["date"]) if raw.get("date") else None,
                  ref=str(raw["ref"]) if raw.get("ref") else None,
                  note=str(raw["note"]) if raw.get("note") else None)


def _entry(key: str, raw: Any, path: Path) -> InspectionEntry:
    where = f"{path}: [entries.{key!r}]"
    if not isinstance(raw, dict):
        raise ValueError(f"{where} must be a table")
    unknown = set(raw) - set(ENTRY_FIELDS)
    if unknown:
        legacy = sorted(set(unknown) & {"result", "result_date", "reinspect", "history"})
        hint = (f" — {legacy} is the old single-result spelling; run `haus site migrate`"
                if legacy else "")
        raise ValueError(f"{where}: unknown field(s) {sorted(unknown)}; "
                         f"expected {list(ENTRY_FIELDS)}{hint}")
    values: dict[str, Any] = {}
    for name in ("requested", "scheduled", "inspector", "note"):
        values[name] = str(raw[name]) if raw.get(name) else None
    for name in _ENTRY_LISTS:
        values[name] = _strings(raw[name], where, name) if raw.get(name) else ()
    values["attempts"] = _attempts(raw["attempts"], where) if raw.get("attempts") else ()
    values["waived"] = _waiver(raw["waived"], where) if raw.get("waived") is not None else None
    return InspectionEntry(**values)


def _authority(key: str, raw: Any, path: Path) -> Authority:
    where = f"{path}: [authorities.{key}]"
    if not isinstance(raw, dict):
        raise ValueError(f"{where} must be a table")
    unknown = set(raw) - set(AUTHORITY_FIELDS)
    if unknown:
        raise ValueError(f"{where}: unknown field(s) {sorted(unknown)}; "
                         f"expected {list(AUTHORITY_FIELDS)}")
    if "label" not in raw:
        raise ValueError(f"{where}: missing 'label'")
    method = str(raw["method"]) if raw.get("method") else None
    if method is not None and method not in METHODS:
        raise ValueError(f"{where}: method {method!r}; expected one of {list(METHODS)}")
    lead = raw.get("lead_days")
    return Authority(
        label=str(raw["label"]), method=method,
        lead_days=int(lead) if lead is not None else None,
        **{name: (str(raw[name]) if raw.get(name) else None)
           for name in ("phone", "portal_url", "window", "source_url", "confirmed")})


def _permit(raw: Any, path: Path) -> Permit:
    if not raw:
        return Permit()
    if not isinstance(raw, dict):
        raise ValueError(f"{path}: [permit] must be a table")
    unknown = set(raw) - set(PERMIT_FIELDS)
    if unknown:
        raise ValueError(f"{path}: [permit] unknown field(s) {sorted(unknown)}; "
                         f"expected {list(PERMIT_FIELDS)}")
    return Permit(**{name: (str(raw[name]) if raw.get(name) else None)
                     for name in PERMIT_FIELDS})


def _extra(raw: Any, path: Path, index: int) -> ExtraInspection:
    where = f"{path}: [[extra]] #{index + 1}"
    if not isinstance(raw, dict):
        raise ValueError(f"{where} must be a table")
    unknown = set(raw) - set(_EXTRA_FIELDS)
    if unknown:
        raise ValueError(f"{where}: unknown field(s) {sorted(unknown)}; "
                         f"expected {list(_EXTRA_FIELDS)}")
    for required in ("id", "label"):
        if not raw.get(required):
            raise ValueError(f"{where}: missing {required!r}")
    return ExtraInspection(
        id=str(raw["id"]), label=str(raw["label"]),
        authority=str(raw.get("authority", "building")),
        after=_strings(raw["after"], where, "after") if raw.get("after") else (),
        gates=_strings(raw["gates"], where, "gates") if raw.get("gates") else (),
        check_ids=(_strings(raw["check_ids"], where, "check_ids")
                   if raw.get("check_ids") else ()),
        on_site=_strings(raw["on_site"], where, "on_site") if raw.get("on_site") else (),
        code_refs=(_strings(raw["code_refs"], where, "code_refs")
                   if raw.get("code_refs") else ()),
        milestone=str(raw.get("milestone") or ""),
        applies_when=str(raw["applies_when"]) if raw.get("applies_when") else None,
    )


def load_inspections(house_dir: Path) -> InspectionsState:
    """Read ``inspections.toml`` if the house carries one; an absent file is empty state."""
    path = Path(house_dir) / INSPECTIONS_FILENAME
    if not path.exists():
        return InspectionsState()
    data = tomllib.loads(path.read_text())
    unknown = set(data) - {"authorities", "entries", "extra", "permit"}
    if unknown:
        raise ValueError(f"{path}: unknown top-level key(s) {sorted(unknown)}; expected "
                         "[authorities.<id>], [entries.<id>], [permit], [[extra]]")
    raw_extra = data.get("extra") or []
    if not isinstance(raw_extra, list):
        raise ValueError(f"{path}: 'extra' must be an array of tables ([[extra]])")
    return InspectionsState(
        authorities={str(key): _authority(str(key), raw, path)
                     for key, raw in (data.get("authorities") or {}).items()},
        entries={str(key): _entry(str(key), raw, path)
                 for key, raw in _flatten_entries(data.get("entries") or {}).items()},
        extra=tuple(_extra(raw, path, i) for i, raw in enumerate(raw_extra)),
        permit=_permit(data.get("permit"), path),
    )


def _flatten_entries(raw: Any) -> dict[str, Any]:
    """``[entries."footing/court"]`` arrives from tomllib as a nested table. Re-join it.

    TOML reads a dotted or quoted key with a slash as one key, but ``[entries.footing.court]``
    — which a hand edit can produce — arrives nested, and the two spellings have to mean the
    same instance or the file means something different depending on how it was typed.
    """
    out: dict[str, Any] = {}
    for key, value in raw.items():
        if isinstance(value, dict) and value and all(isinstance(v, dict)
                                                     for v in value.values()):
            for sub, body in value.items():
                out[f"{key}/{sub}"] = body
            continue
        out[str(key)] = value
    return out


# The writer, the ops and the migration live next door: this module is the vocabulary and
# the loader, and the three together would be well past 500 lines.
from typehaus.schedule.inspection_toml import (  # noqa: E402
    apply_inspection_op,
    migrate_entries,
    toml_string,
    write_inspections,
)

__all__ = [
    "ATTEMPT_FIELDS", "AUTHORITY_FIELDS", "ENTRY_FIELDS", "INSPECTIONS_FILENAME",
    "METHODS", "PERMIT_FIELDS", "RESULTS", "WAIVER_FIELDS", "Attempt", "Authority",
    "ExtraInspection", "InspectionEntry", "InspectionsState", "Permit", "Waiver",
    "apply_inspection_op", "instance_of", "load_inspections", "migrate_entries",
    "spec_of", "toml_string", "write_inspections",
]

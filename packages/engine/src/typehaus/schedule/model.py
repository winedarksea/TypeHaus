"""The schedule vocabulary: visits, inspections, readiness — as data.

``takeoff/tasks.py`` derives a work **package** at (trade x storey). That is the right
grain for money and the wrong grain for a phone call: catlin's concrete is roughly six
mobilisations across two subs with inspections between them, and the plumbing sleeves go
in before the pour while the trade order puts plumbing after framing.

A :class:`Visit` is the schedulable unit — one sub, one arrival — and it is **authored**,
in ``tasks.toml``, because who comes when is the owner's judgement. The engine proposes
splits (:mod:`typehaus.schedule.propose`) and derives readiness
(:mod:`typehaus.schedule.readiness`); it computes no dates, no durations and no order.

Nothing in this package grades the building. A readiness state is a statement about
*authored site state plus findings someone else produced*; the facts about the building
stay in ``checks/``. ``tests/test_schedule_leaf.py`` is what keeps that true.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

#: Visit status. ``done`` is the sub's claim that they are finished; ``verified`` is the
#: owner's own walk of the handoff list afterwards. They are different facts and an
#: owner-builder needs both — the whole point of the exercise is that nobody else is
#: checking.
VISIT_STATUSES = ("todo", "scheduled", "in_progress", "done", "verified")

#: Readiness of a visit. Derived, never authored.
VISIT_READINESS = ("ready", "blocked", "in_progress", "done", "verified")

#: Readiness of an inspection. ``waived`` and ``not_applicable`` are different sentences:
#: the first is the AHJ saying it is not required here, the second is this building not
#: having the condition the inspection covers.
INSPECTION_READINESS = ("passed", "failed", "scheduled", "requested", "ready",
                        "not_ready", "not_applicable", "waived")

#: Authorities an :class:`~typehaus.checks.jurisdiction.InspectionSpec` may name.
AUTHORITIES = ("building", "electrical", "plumbing", "mechanical", "report", "owner")


@dataclass(frozen=True)
class Constraint:
    """One thing that must be true before a visit can proceed.

    ``kind`` says where it came from, which is what lets the UI order them worst-first and
    lets the owner tell "I have not ordered the windows" from "the model says this wall
    fails": ``visit`` (a predecessor), ``inspection``, ``authored`` (a hand-written hold),
    ``finding`` (a FAIL on this visit's elements) or ``attention`` (an UNKNOWN — never
    blocking, since "we could not evaluate this" must not stop a pour).
    """

    kind: str
    #: The visit slug, inspection id, check id — or None for a bare authored label.
    ref: str | None
    label: str
    #: Authored clearance date, prose. Set means the owner ticked it off.
    cleared: str | None = None
    #: ``"blocking"`` or ``"attention"``.
    severity: str = "blocking"
    element_tags: tuple[str, ...] = ()
    #: The three fields that turn a hold into a task: who is on the hook, what unsticks it,
    #: and when to chase. Authored on the hold; empty on a derived constraint, which has no
    #: owner but the model.
    owner: str | None = None
    next_action: str | None = None
    follow_up: str | None = None
    #: ``"locate"`` for a Gopher State One Call ticket. A typed hold the board can date.
    ticket_kind: str = ""
    ticket: str | None = None
    ticket_start: str | None = None
    refresh_agreement: bool = False
    #: Derived from a typed hold: when it arms, when it expires, and the sentence that says
    #: how. Empty on every untyped hold — see :mod:`typehaus.schedule.locates`.
    armed: str | None = None
    expires: str | None = None
    derived: str = ""

    @property
    def met(self) -> bool:
        return self.cleared is not None

    def as_dict(self) -> dict[str, Any]:
        return {"kind": self.kind, "ref": self.ref, "label": self.label,
                "cleared": self.cleared, "severity": self.severity,
                "element_tags": list(self.element_tags), "owner": self.owner,
                "next_action": self.next_action, "follow_up": self.follow_up,
                "ticket_kind": self.ticket_kind, "ticket": self.ticket,
                "ticket_start": self.ticket_start,
                "refresh_agreement": self.refresh_agreement,
                "armed": self.armed, "expires": self.expires, "derived": self.derived}


@dataclass(frozen=True)
class HandoffItem:
    """What a visit must leave in place for the next one, derived from the model.

    The owner ticks these on the walk. ``derived`` carries the sentence that says where the
    number came from, and it earns its place: several of these items exist precisely to say
    "the model knows the count and not the positions" out loud, which is the difference
    between a checklist and a guess.
    """

    id: str
    label: str
    count: int | None = None
    element_tags: tuple[str, ...] = ()
    #: The tags that decide **which visit owns this item**, where they differ from the
    #: elements it names. A sleeve item lists 40 sleeve tags and belongs to whichever
    #: arrival pours its host wall, so its scope is the host — intersecting the sleeve tags
    #: against a concrete visit's footing tags would drop the item from every visit.
    #: Empty means the item is scoped by ``element_tags``.
    scope_tags: tuple[str, ...] = ()
    #: Manifest sheet number to bring ("A-301"), or None.
    sheet_ref: str | None = None
    derived: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {"id": self.id, "label": self.label, "count": self.count,
                "element_tags": list(self.element_tags), "sheet_ref": self.sheet_ref,
                "derived": self.derived}

    @property
    def scope(self) -> tuple[str, ...]:
        return self.scope_tags or self.element_tags


@dataclass(frozen=True)
class Visit:
    """One sub, one arrival. Authored in ``tasks.toml``; ids derived, never hand-minted."""

    slug: str
    id: str
    #: The work package this visit draws its rows and tags from.
    package: str
    label: str
    trade: str
    storey: str
    milestone: str = ""
    status: str = "todo"
    scheduled: str | None = None
    assignee: str | None = None
    contact: str | None = None
    note: str | None = None
    depends_on: tuple[str, ...] = ()
    rows: tuple[tuple[str, str], ...] = ()
    element_tags: tuple[str, ...] = ()
    constraints: tuple[Constraint, ...] = ()
    #: Handoff item ids the owner has ticked.
    checked: tuple[str, ...] = ()
    estimate_fmt: str = ""
    holdback_open: bool = False
    #: True when this visit is the whole package (nobody authored a split).
    implicit: bool = True
    #: True for a ``site/<label>`` visit that draws from no work package at all.
    standalone: bool = False
    #: False takes this visit out of package-level predecessor expansion.
    blocks_successors: bool = True
    #: True where this visit deliberately shares BOM rows with another.
    shared_rows: bool = False
    #: Ordered pauses inside this one arrival, as dicts — the shape
    #: ``takeoff/visit_state.Checkpoint.as_dict`` writes.
    checkpoints: tuple[dict[str, Any], ...] = ()
    #: ``done`` was claimed while a blocking hold was open. Listed first on the board.
    exceptions: tuple[dict[str, Any], ...] = ()
    #: Handoff items passed on deliberately, with the reason.
    skipped: tuple[dict[str, Any], ...] = ()
    log: tuple[dict[str, Any], ...] = ()
    updated: str | None = None
    #: The owner's intent, and the date they actually confirmed with the sub. The engine
    #: reads both and moves neither — see :mod:`typehaus.schedule.timing`.
    planned: str | None = None
    booked: dict[str, Any] | None = None
    #: Working days on site, authored. ``None`` is "needs confirmation", never a default.
    duration_days: int | None = None
    #: What has to be on site before this arrival, as dicts.
    materials: tuple[dict[str, Any], ...] = ()
    #: Key into ``[contractors]`` in ``tasks.toml``.
    contractor: str | None = None
    #: The handoff set changed under existing ticks — the owner has to walk it again.
    needs_rewalk: bool = False
    #: Ticks naming a handoff item this model no longer derives. Reported, never deleted.
    orphan_ticks: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {"slug": self.slug, "id": self.id, "package": self.package,
                "label": self.label, "trade": self.trade, "storey": self.storey,
                "milestone": self.milestone, "status": self.status,
                "scheduled": self.scheduled, "assignee": self.assignee,
                "contact": self.contact, "note": self.note,
                "depends_on": list(self.depends_on),
                "rows": [{"section": s, "key": k} for s, k in self.rows],
                "element_tags": list(self.element_tags),
                "checked": list(self.checked), "estimate_fmt": self.estimate_fmt,
                "holdback_open": self.holdback_open, "implicit": self.implicit,
                "standalone": self.standalone,
                "blocks_successors": self.blocks_successors,
                "shared_rows": self.shared_rows,
                "checkpoints": [dict(p) for p in self.checkpoints],
                "exceptions": [dict(x) for x in self.exceptions],
                "skipped": [dict(x) for x in self.skipped],
                "log": [dict(x) for x in self.log], "updated": self.updated,
                "needs_rewalk": self.needs_rewalk,
                "orphan_ticks": list(self.orphan_ticks),
                "planned": self.planned, "booked": self.booked,
                "duration_days": self.duration_days,
                "materials": [dict(m) for m in self.materials],
                "contractor": self.contractor}


@dataclass(frozen=True)
class VisitReadiness:
    """Whether this visit can be called in, and what is in the way if not."""

    slug: str
    state: str
    #: Worst-first, and never truncated: the second blocker is what the owner works on
    #: while waiting for the first.
    constraints: tuple[Constraint, ...] = ()

    @property
    def blockers(self) -> tuple[Constraint, ...]:
        return tuple(c for c in self.constraints
                     if c.severity == "blocking" and not c.met)

    @property
    def attention(self) -> tuple[Constraint, ...]:
        return tuple(c for c in self.constraints if c.severity == "attention")

    def as_dict(self) -> dict[str, Any]:
        return {"slug": self.slug, "state": self.state,
                "constraints": [c.as_dict() for c in self.constraints]}


@dataclass(frozen=True)
class Applicability:
    """Does this inspection's condition exist in this building, and how do we know?

    ``applies`` is deliberately tri-state. ``None`` means the model gives no conclusive
    evidence either way, and the inspection is then listed as "applicability unknown" —
    never dropped. N/A is earned from positive evidence of absence (→ ``findings.Result``).
    """

    key: str
    applies: bool | None
    evidence: str

    def as_dict(self) -> dict[str, Any]:
        return {"key": self.key, "applies": self.applies, "evidence": self.evidence}


@dataclass(frozen=True)
class Prerequisite:
    """One thing an inspection needs before it can be requested."""

    kind: str          # "inspection" | "visit" | "check" | "on_site"
    ref: str | None
    label: str
    met: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {"kind": self.kind, "ref": self.ref, "label": self.label, "met": self.met}


@dataclass(frozen=True)
class InspectionReadiness:
    """An inspection, its state, and everything standing between it and a phone call."""

    #: The **instance** key: ``"footing"`` for the default one, ``"footing/court"`` for a
    #: second. A visit depends on one instance or, by the bare spec id, on all of them.
    id: str
    label: str
    authority: str
    sequence: int
    state: str
    #: The jurisdiction's spec this instance is of. Equal to ``id`` on the default instance.
    spec_id: str = ""
    #: Element-tag globs and/or visit slugs this instance covers. Empty is the whole house.
    scope: tuple[str, ...] = ()
    #: The scope released so far — ``("*",)`` on a full pass, the named globs on a partial.
    approved: tuple[str, ...] = ()
    attempts: tuple[dict[str, Any], ...] = ()
    after: tuple[str, ...] = ()
    gates: tuple[str, ...] = ()
    applicability: Applicability | None = None
    prerequisites: tuple[Prerequisite, ...] = ()
    #: ``(check_id, result, detail, element_tags)`` — passes included, unlike the UI's
    #: default findings view. Before an inspection you want the green ones too.
    checks: tuple[tuple[str, str, str, tuple[str, ...]], ...] = ()
    on_site: tuple[tuple[str, bool], ...] = ()
    entry: dict[str, Any] | None = None
    #: True for an inspection the house added in ``inspections.toml``, not the profile.
    extra: bool = False
    milestone: str = ""
    code_refs: tuple[str, ...] = ()

    @property
    def unmet(self) -> tuple[Prerequisite, ...]:
        return tuple(p for p in self.prerequisites if not p.met)

    @property
    def resolved(self) -> bool:
        """Does this inspection stand out of the way of everything it gates?"""
        return self.state in ("passed", "not_applicable", "waived")

    def releases(self, tags: tuple[str, ...]) -> bool:
        """Is this inspection out of the way *for these elements*?

        A ``partial`` releases only the scope it approved: a visit whose tags fall entirely
        inside it sees the inspection as resolved, and every other visit stays blocked.
        That is the whole reason ``partial`` is a third result rather than a soft fail.
        """
        from fnmatch import fnmatch

        if self.resolved:
            return True
        if self.state != "failed" or not self.approved:
            return False
        if "*" in self.approved:
            return True
        return bool(tags) and all(
            any(fnmatch(tag, pattern) for pattern in self.approved) for tag in tags)

    def as_dict(self) -> dict[str, Any]:
        return {"id": self.id, "label": self.label, "authority": self.authority,
                "sequence": self.sequence, "state": self.state,
                "spec_id": self.spec_id or self.id, "scope": list(self.scope),
                "approved": list(self.approved),
                "attempts": [dict(a) for a in self.attempts],
                "after": list(self.after), "gates": list(self.gates),
                "applies": (self.applicability.applies
                            if self.applicability is not None else True),
                "evidence": (self.applicability.evidence
                             if self.applicability is not None else ""),
                "extra": self.extra, "entry": self.entry,
                "milestone": self.milestone, "code_refs": list(self.code_refs),
                "prerequisites": [p.as_dict() for p in self.prerequisites],
                "checks": [{"check_id": cid, "result": res, "detail": detail,
                            "element_tags": list(tags)}
                           for cid, res, detail, tags in self.checks],
                "on_site": [{"label": label, "checked": done}
                            for label, done in self.on_site]}


@dataclass(frozen=True)
class Milestone:
    """A contiguous slice of the construction sequence, with the inspections inside it."""

    id: str
    label: str
    trades: tuple[str, ...]
    visits: tuple[str, ...] = ()
    inspections: tuple[str, ...] = ()
    state: str = "not_started"    # not_started | in_progress | done

    def as_dict(self) -> dict[str, Any]:
        return {"id": self.id, "label": self.label, "trades": list(self.trades),
                "visits": list(self.visits), "inspections": list(self.inspections),
                "state": self.state}


@dataclass(frozen=True)
class Board:
    """Everything the site surface renders, derived in one pass."""

    profile_name: str
    visits: tuple[Visit, ...] = ()
    readiness: dict[str, VisitReadiness] = field(default_factory=dict)
    inspections: tuple[InspectionReadiness, ...] = ()
    milestones: tuple[Milestone, ...] = ()
    #: Authored visit/inspection slugs that no longer derive from the model.
    stale: tuple[str, ...] = ()
    #: Load-time rule violations and dependency loops, each naming its file and key. The
    #: board renders the last valid state *plus* this banner — a silently dropped edge is
    #: worse than an error, because nothing says so.
    errors: tuple[str, ...] = ()
    #: ``(trade, inspection ref)`` gates the engine refused to imply, and why. Printed by
    #: ``haus site validate`` so a dropped edge is visible rather than magic.
    dropped_gates: tuple[tuple[str, str], ...] = ()
    #: package slug -> everything the package covers, so ``rules.unassigned_scope`` can say
    #: which rows and tags a hand-written split forgot.
    package_rows: dict[str, tuple[tuple[str, str], ...]] = field(default_factory=dict)
    package_tags: dict[str, tuple[str, ...]] = field(default_factory=dict)

    def visit(self, slug: str) -> Visit | None:
        for visit in self.visits:
            if visit.slug == slug:
                return visit
        return None

    def inspection(self, inspection_id: str) -> InspectionReadiness | None:
        for record in self.inspections:
            if record.id == inspection_id:
                return record
        return None

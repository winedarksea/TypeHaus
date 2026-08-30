"""In-memory PatchOp applicator — apply ops to a pydantic ``PlanModel`` without touching
source (→ 21 responsiveness plan, Phase 2b).

An edit's fast path applies its ops directly to the loaded plan, resolves, and pushes to the
UI, then writes the libcst source back on a background thread. This module is the op → plan
interpreter that mirrors :mod:`typehaus.source.writeback` (op → source), so a macro and a
hand op share one applicator.

**One value-encoding path.** A field value is turned into source text by the exact same
:func:`~typehaus.source.ops.encode_value` the writeback uses, then evaluated in the dialect
call namespace (``Wall``, ``Node``, ``ft``, ``pt``, enums, …). There is no second
value-semantics implementation to drift from source, and the reconciliation backstop
(compare the reloaded-from-source plan against the in-memory one) bounds any residual bug to
a brief flicker + log rather than silent corruption.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from typehaus.model.base import Element
from typehaus.model.ids import new_uid
from typehaus.model.plan import PlanModel
from typehaus.model.registry import _kind_has_uid, element_kinds
from typehaus.source.ops import DELETE_FIELD, PatchOp, encode_value


class InMemoryApplyError(RuntimeError):
    """An op could not be applied to the in-memory plan (unknown kind, missing target)."""


@lru_cache(maxsize=1)
def _namespace() -> dict[str, Any]:
    """The dialect eval namespace — every name a plan module imports from ``typehaus``."""
    import typehaus

    ns = {k: v for k, v in vars(typehaus).items() if not k.startswith("_")}
    from typehaus.model.registry import constructor_namespace

    ns.update(constructor_namespace())
    return ns


def _eval_value(kind: str, name: str, value: Any) -> Any:
    """Encode one field value to dialect source, then evaluate it to a pydantic value."""
    expr = encode_value(kind, name, value)
    try:
        return eval(expr, dict(_namespace()))  # noqa: S307 - dialect-only names, encoded here
    except Exception as exc:  # noqa: BLE001 - surfaced as an apply error
        raise InMemoryApplyError(f"cannot evaluate {kind}.{name} = {expr!r}: {exc}") from exc


def _build_element(op: PatchOp) -> tuple[Element, str | None]:
    """Build a fresh element for an ``add`` op. Returns (element, minted_uid_or_None).

    A uid already present in ``op.fields`` (the inverse of a delete) is kept so identity
    round-trips; otherwise one is minted and returned so the caller can pin the *same* uid
    into the source writeback (both paths must agree on the uid)."""
    cls = element_kinds().get(op.type)
    if cls is None:
        raise InMemoryApplyError(f"unknown element kind {op.type!r}")
    fields = dict(op.fields)
    minted: str | None = None
    if _kind_has_uid(op.type) and not fields.get("uid"):
        minted = new_uid()
        fields["uid"] = minted
    kwargs: dict[str, Any] = {"tag": op.tag}
    for name, value in fields.items():
        if name == "tag":
            continue
        if name == "uid":
            kwargs["uid"] = value
            continue
        kwargs[name] = _eval_value(op.type, name, value)
    try:
        element = cls(**kwargs)
    except Exception as exc:  # noqa: BLE001
        raise InMemoryApplyError(f"cannot construct {op.type} {op.tag!r}: {exc}") from exc
    return element, minted


def _update_element(el: Element, op: PatchOp) -> Element:
    updates: dict[str, Any] = {}
    for name, value in op.fields.items():
        if value == DELETE_FIELD:
            # Reset to the field's default (undo of an added kwarg). model_fields carries it.
            fld = type(el).model_fields.get(name)
            if fld is None:
                continue
            default = fld.get_default(call_default_factory=True)
            updates[name] = default
            continue
        updates[name] = _eval_value(op.type, name, value)
    return el.model_copy(update=updates)


def _find_storey(elements: dict[str, list[Element]], tag: str) -> str | None:
    for storey_tag, group in elements.items():
        if any(e.tag == tag for e in group):
            return storey_tag
    return None


def _add_storey(
    plan: PlanModel, elements: dict[str, list[Element]], op: PatchOp
) -> str | None:
    """Best-effort storey for an ``add``: a referenced element's storey, else the storey that
    already holds this kind, else the first storey. Reconciliation corrects any miss."""
    for ref_field in ("host", "start_node", "end_node", "room", "wall_ref"):
        ref = op.fields.get(ref_field)
        if isinstance(ref, str):
            storey = _find_storey(elements, ref)
            if storey is not None:
                return storey
    for storey_tag, group in elements.items():
        if any(e.element_kind == op.type for e in group):
            return storey_tag
    return plan.storeys[0].tag if plan.storeys else None


def can_apply_in_memory(plan: PlanModel, ops: list[PatchOp]) -> bool:
    """True if every op targets an existing element with update/delete, or is an add whose
    target storey is unambiguous. Callers use this to gate the fast path; anything else falls
    back to the (always-correct) source writeback + reload."""
    elements = {s: list(v) for s, v in plan.elements.items()}
    for op in ops:
        if op.op in ("update", "delete"):
            if _find_storey(elements, op.tag) is None:
                return False
        elif op.op == "add":
            if op.type not in element_kinds():
                return False
        else:
            return False
    return True


def apply_ops_to_plan(plan: PlanModel, ops: list[PatchOp]) -> tuple[PlanModel, dict[str, str]]:
    """Apply ``ops`` to ``plan`` in memory. Returns (new_plan, minted_uids).

    ``minted_uids`` maps an added element's tag to the uid minted for it, so the source
    writeback can pin the identical uid (the two paths must not diverge on identity)."""
    elements: dict[str, list[Element]] = {s: list(v) for s, v in plan.elements.items()}
    minted: dict[str, str] = {}
    for op in ops:
        if op.op == "update":
            storey = _find_storey(elements, op.tag)
            if storey is None:
                raise InMemoryApplyError(f"no element {op.type} {op.tag!r} to update")
            group = elements[storey]
            for i, el in enumerate(group):
                if el.tag == op.tag:
                    group[i] = _update_element(el, op)
                    break
        elif op.op == "delete":
            storey = _find_storey(elements, op.tag)
            if storey is None:
                raise InMemoryApplyError(f"no element {op.type} {op.tag!r} to delete")
            elements[storey] = [e for e in elements[storey] if e.tag != op.tag]
        elif op.op == "add":
            element, minted_uid = _build_element(op)
            if minted_uid is not None:
                minted[op.tag] = minted_uid
            storey = _add_storey(plan, elements, op)
            if storey is None:
                raise InMemoryApplyError(f"no storey to host added {op.type} {op.tag!r}")
            elements.setdefault(storey, []).append(element)
        else:
            raise InMemoryApplyError(f"unknown op {op.op!r}")
    new_elements = {s: tuple(v) for s, v in elements.items()}
    return plan.model_copy(update={"elements": new_elements}), minted

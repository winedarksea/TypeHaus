"""Detail-annotation write flow — materialize seed notes into authored source (WP3, → 11b).

A transition detail's default annotations render as read-only seed nodes (``uid=None``) until
the user makes them editable. ``seed_detail_annotations`` is the one new macro that turns those
seeds into authored ``DetailAnnotation(...)`` adds in ``plan/details.py``; after that, every
edit (offset drag, text change) is a plain ``PatchOp`` on the registered element — no further
macro machinery (``PatchOp`` is generic over any registered element kind).
"""

from __future__ import annotations

from typing import Any

from typehaus.model.plan import PlanModel
from typehaus.model.remap import MutationResult
from typehaus.model.views import DetailAnnotation
from typehaus.quantities.length import m
from typehaus.quantities.point import Point2D
from typehaus.source.macros import MacroError
from typehaus.source.serialize import element_add_op

DETAILS_FILE = "plan/details.py"
DETAILS_LIST = "DETAIL_NOTES"

_VALID_KINDS = frozenset({"note", "leader", "dimension"})


def _slug(key: str) -> str:
    out = "".join(c if c.isalnum() else "-" for c in key)
    return out.strip("-").upper()[:32] or "DETAIL"


def seed_detail_annotations(
    plan: PlanModel, condition_key: str, annotations: list[dict[str, Any]]
) -> MutationResult:
    """Materialize seed annotations for ``condition_key`` into authored source.

    Each spec is ``{kind, anchor_uid, anchor_face, text, offset?: [x_m, y_m]}`` — the same
    shape the detail viewer renders as a seed. Emits one ``add DetailAnnotation`` per spec,
    riding the standard journal (revision-guarded, undoable).
    """
    if not condition_key:
        raise MacroError("seed_detail_annotations needs a 'condition_key'")
    if not annotations:
        raise MacroError("seed_detail_annotations needs at least one annotation")
    existing = {
        a.tag for a in plan.elements_of_kind("DetailAnnotation")
    }
    slug = _slug(condition_key)
    ops = []
    for index, spec in enumerate(annotations):
        try:
            kind = str(spec["kind"])
            anchor_uid = str(spec["anchor_uid"])
            anchor_face = str(spec["anchor_face"])
            text = str(spec.get("text", ""))
        except (KeyError, TypeError) as exc:
            raise MacroError(f"bad annotation spec {spec!r}: {exc}") from exc
        if kind not in _VALID_KINDS:
            raise MacroError(f"unknown annotation kind {kind!r}")
        offset = None
        raw = spec.get("offset")
        if raw is not None:
            if not isinstance(raw, (list, tuple)) or len(raw) != 2:
                raise MacroError(f"offset must be [x_m, y_m], got {raw!r}")
            offset = Point2D(m(float(raw[0])), m(float(raw[1])))
        tag = f"DA-{slug}-{index + 1}"
        suffix = 0
        while tag in existing:
            suffix += 1
            tag = f"DA-{slug}-{index + 1}-{suffix}"
        existing.add(tag)
        element = DetailAnnotation(
            tag=tag, condition_key=condition_key, kind=kind, anchor_uid=anchor_uid,
            anchor_face=anchor_face, offset=offset, text=text,
        )
        ops.append(element_add_op(element, tag=tag, hint_list=DETAILS_LIST,
                                  hint_file=DETAILS_FILE))
    return MutationResult(ops=ops)

"""``Slab.kind``: catlin authors every kind, and each equals the derivation."""

from __future__ import annotations

from types import SimpleNamespace

from typehaus.checks.integrity.slab_kind import slab_kind_matches_assembly
from typehaus.emit.draw.foundation_schedule import slabs_on_grade
from typehaus.findings import Result
from typehaus.model.floors import Slab
from typehaus.resolve.slab_kind import derive_slab_kind


def _slabs(plan, model):
    for solid in model.solids:
        element = plan.by_tag(solid.tag) if solid.tag and not solid.derived else None
        if isinstance(element, Slab):
            yield solid, element


def test_catlin_authored_kind_equals_derived(catlin_plan, catlin_model_ro):
    pairs = list(_slabs(catlin_plan, catlin_model_ro))
    assert len(pairs) == 22
    for solid, slab in pairs:
        assert slab.kind is not None, slab.tag
        assert derive_slab_kind(catlin_model_ro, slab, solid.storey, solid.z0_m) == slab.kind, \
            slab.tag


def test_tub_deck_is_a_platform_off_the_foundation_sheet(catlin_model_ro):
    tub = next(s for s in catlin_model_ro.solids if s.tag == "SL-M-TUBDK")
    assert tub.category == "slab_platform"
    assert "SL-M-TUBDK" not in {s.tag for s in slabs_on_grade(catlin_model_ro)}


class _Plan:
    """Delegates to the real plan, overriding chosen elements."""

    def __init__(self, plan, override):
        self._plan, self._override = plan, override

    def by_tag(self, tag):
        return self._override.get(tag) or self._plan.by_tag(tag)

    def __getattr__(self, name):
        return getattr(self._plan, name)


def test_check_passes_fails_and_is_na(catlin_plan, catlin_model_ro):
    ctx = SimpleNamespace(plan=catlin_plan, model=catlin_model_ro)
    assert [f.result for f in slab_kind_matches_assembly(ctx)] == [Result.PASS]

    tub = catlin_plan.by_tag("SL-M-TUBDK")
    wrong = _Plan(catlin_plan, {"SL-M-TUBDK": tub.model_copy(update={"kind": "pour"})})
    findings = slab_kind_matches_assembly(SimpleNamespace(plan=wrong, model=catlin_model_ro))
    assert [(f.result, f.element_tags) for f in findings] == [(Result.FAIL, ("SL-M-TUBDK",))]

    unauthored = {s.tag: e.model_copy(update={"kind": None})
                  for s, e in _slabs(catlin_plan, catlin_model_ro)}
    na = slab_kind_matches_assembly(SimpleNamespace(plan=_Plan(catlin_plan, unauthored),
                                                    model=catlin_model_ro))
    assert [f.result for f in na] == [Result.NOT_APPLICABLE]

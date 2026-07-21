"""WP7 — IFC openings: IfcOpeningElement voids + IfcWindow/IfcDoor fillings, GUID round-trip."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from pathlib import Path

import pytest

from typehaus.diff import build_report
from typehaus.diff.ifc_adapter import baseline_elems, external_elems
from typehaus.emit.ifc import emit_ifc
from typehaus.model.ids import derive_guid

pytest.importorskip("ifcopenshell")


@pytest.fixture(scope="module")
def catlin_ifc(catlin_model, tmp_path_factory) -> Path:
    out = tmp_path_factory.mktemp("ifc") / "catlin.ifc"
    emit_ifc(catlin_model, out, lod="core")
    return out


def test_every_opening_emits_a_void_and_a_filling(catlin_model, catlin_ifc):
    import ifcopenshell

    f = ifcopenshell.open(str(catlin_ifc))
    n = len(catlin_model.openings)
    assert n > 0
    windows = f.by_type("IfcWindow")
    doors = f.by_type("IfcDoor")
    filled = [opening for opening in catlin_model.openings if opening.kind != "rough_opening"]
    assert len(windows) + len(doors) == len(filled)
    # Every opening voids its host; only installed products receive filling relationships.
    assert len(f.by_type("IfcOpeningElement")) == n
    assert len(f.by_type("IfcRelVoidsElement")) == n
    assert len(f.by_type("IfcRelFillsElement")) == len(filled)
    # doors vs windows follow the resolved is_door flag
    assert len(doors) == sum(1 for o in catlin_model.openings if o.is_door)


def test_filling_guid_matches_diff_adapter_prediction(catlin_model, catlin_ifc):
    import ifcopenshell

    f = ifcopenshell.open(str(catlin_ifc))
    emitted = {p.GlobalId for p in f.by_type("IfcWindow") + f.by_type("IfcDoor")}
    puid = catlin_model.plan.project.project_uuid
    for opening in catlin_model.openings:
        if opening.kind == "rough_opening":
            continue
        assert derive_guid(puid, opening.uid) in emitted


def test_openings_survive_the_self_diff_by_global_id(catlin_model, catlin_ifc):
    # The diff adapter predicts each window/door GUID as derive_guid(uuid, opening.uid); a
    # self-emitted IFC must therefore match every opening by GlobalId — never add or delete
    # one (placement centroids are a separate whole-model convention, out of scope here).
    report = build_report(baseline_elems(catlin_model), external_elems(catlin_ifc))
    kinds = {c.kind.value if hasattr(c.kind, "value") else c.kind for c in report.substantive()}
    added_deleted = [c for c in report.substantive()
                     if (getattr(c.kind, "value", c.kind) in ("added", "deleted"))]
    assert added_deleted == [], f"round-trip should match all elements by GUID; {kinds}"


def test_rough_opening_emits_only_the_wall_void(catlin_model, tmp_path):
    import ifcopenshell

    model = deepcopy(catlin_model)
    source = model.openings[0]
    model.openings[0] = replace(source, kind="rough_opening", is_door=False, type_ref=None)
    out = tmp_path / "rough-opening.ifc"
    emit_ifc(model, out, lod="core")

    f = ifcopenshell.open(str(out))
    assert len(f.by_type("IfcOpeningElement")) == len(model.openings)
    filled = [opening for opening in model.openings if opening.kind != "rough_opening"]
    assert len(f.by_type("IfcWindow")) + len(f.by_type("IfcDoor")) == len(filled)
    assert len(f.by_type("IfcRelFillsElement")) == len(filled)

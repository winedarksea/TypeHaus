"""The garage's exterior linear is hosted on the Sill to Soffit's flange (decision #143)."""

from __future__ import annotations

import pytest

from typehaus.quantities import M_PER_IN
from typehaus.resolve.cladding_trim.wall_tops import exposed_wall_top_edges, wall_top_tag
from typehaus.resolve.led_sections import section_extent


def test_garage_runs_sit_on_the_flange_tight_to_the_cladding(catlin_model_ro):
    edges = {wall_top_tag(e): e for e in exposed_wall_top_edges(catlin_model_ro)
             if e.product == "CORRUGATED_SILL_TO_SOFFIT"}
    runs = [r for r in catlin_model_ro.light_runs if r.tag.startswith(("LR-G-EAVE", "LR-G-GABLE"))]
    assert len(runs) == 6
    for run in runs:
        edge = edges[run.host_ref]
        face, width = edge.face, section_extent(run.section)[0]
        zs = run.z_path_m or (run.z_m,) * len(run.path)
        for (x, y), z in zip(run.path, zs, strict=True):
            station = x * face.d[0] + y * face.d[1]
            flange = edge.z_start + (edge.z_end - edge.z_start) * (
                (station - edge.start) / (edge.end - edge.start))
            assert z == pytest.approx(flange, abs=M_PER_IN / 32), run.tag
            inside = x * face.n[0] + y * face.n[1] - width / 2
            assert inside == pytest.approx(face.back + face.layer.thickness_m, abs=1e-6)

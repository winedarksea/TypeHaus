"""code.R316_4 on synthetic stacks: the R316.6 listing pass and the 23/32" panel wording."""

from __future__ import annotations

from types import SimpleNamespace

from typehaus.checks.code.mn_residential.foam_plastic import foam_plastic_thermal_barrier
from typehaus.findings import Result
from typehaus.model.assembly import Assembly, Layer
from typehaus.model.enums import LayerFunction
from typehaus.model.materials import Material
from typehaus.quantities import inch

_LISTING = "Intertek CCRR-0435 §5.5: without the R316.4 barrier, max 4 in."
_MATERIALS = (
    Material(tag="polyiso", name="Polyiso", foam_plastic=True),
    Material(tag="polyiso-listed", name="Listed polyiso", foam_plastic=True,
             thermal_barrier_listing=_LISTING),
    Material(tag="shiplap", name="Shiplap"),
    Material(tag="plywood", name="Plywood"),
)


def _ctx(*layers: Layer):
    assembly = Assembly(tag="A-TEST", layers=layers)
    library = SimpleNamespace(materials=_MATERIALS,
                              resolve_assembly=lambda tag: assembly)
    wall = SimpleNamespace(assembly="A-TEST", element_kind="Wall")
    return SimpleNamespace(plan=SimpleNamespace(library=library,
                                                all_elements=lambda: [wall]))


def _layer(name, ref, t, fn):
    return Layer(name=name, material_ref=ref, thickness=inch(t), function=fn)


def _sauna(foam_ref: str):
    return _ctx(_layer("liner", "shiplap", 1.0, LayerFunction.FINISH),
                _layer("foam", foam_ref, 2.0, LayerFunction.INSULATION))


def test_listed_foam_passes_and_cites_its_listing():
    [finding] = foam_plastic_thermal_barrier(_sauna("polyiso-listed"))
    assert finding.result is Result.PASS
    assert "R316.6" in finding.message and _LISTING in finding.message


def test_unlisted_foam_behind_wood_liner_stays_unknown():
    [finding] = foam_plastic_thermal_barrier(_sauna("polyiso"))
    assert finding.result is Result.UNKNOWN
    assert "'liner' (shiplap) is not identified as an approved thermal barrier" in (
        finding.message)


def test_thin_sheathing_names_the_23_32_panel():
    ctx = _ctx(_layer("sheathing", "plywood", 0.5, LayerFunction.SHEATHING),
               _layer("foam", "polyiso", 2.0, LayerFunction.INSULATION))
    [finding] = foam_plastic_thermal_barrier(ctx)
    assert finding.result is Result.UNKNOWN
    assert '23/32"' in finding.message and '5/8"' not in finding.message
    assert "under the 23/32" in finding.message


def test_full_panel_sheathing_is_still_unclassified():
    ctx = _ctx(_layer("sheathing", "plywood", 23 / 32, LayerFunction.SHEATHING),
               _layer("foam", "polyiso", 2.0, LayerFunction.INSULATION))
    [finding] = foam_plastic_thermal_barrier(ctx)
    assert finding.result is Result.UNKNOWN
    assert "also admits 23/32" in finding.message

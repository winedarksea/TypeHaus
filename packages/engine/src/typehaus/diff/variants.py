"""Named house variants — declared overrides on one base plan (WP2.14, → 21b §Variant compare).

A variant is *not* a second copy of the house. It is a name plus the short list of overrides
that make it different, declared in the house's ``variants.toml`` next to ``preferences.toml``:

```toml
[[variant]]
name = "2x4-ci"
description = "thinner studs, the insulation moved outboard"
assembly_swaps = { CATLIN_EXT_2X6 = "CATLIN_EXT_2X4" }

[[variant]]
name = "thicker-ci"
description = "3in exterior polyiso instead of 2in"

  [[variant.layer_thickness]]
  assembly = "CATLIN_EXT_2X6"
  layer = "polyiso"
  thickness_in = 3.0
```

Every variant resolves from the same authored source, so nothing drifts: building one is
"load the plan, apply these overrides, resolve" (→ 11b §Fork — the honest duplicate resolve,
not an overlay/patch scheme). An override that names an assembly or layer the plan does not
have is an error, never a silent no-op — a mistyped variant must not quietly compare a house
against itself.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

try:  # tomllib is stdlib on 3.11+; the engine still supports 3.9
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - exercised on <3.11 only
    import tomli as tomllib  # type: ignore[no-redef]

from typehaus.quantities import inch

if TYPE_CHECKING:
    from typehaus.diff.compare import VariantSelection
    from typehaus.model.plan import PlanModel

VARIANTS_FILENAME = "variants.toml"


@dataclass(frozen=True)
class LayerThicknessOverride:
    """Retune one layer of one assembly — the CI-thickness sweep, as a declaration."""

    assembly: str
    layer: str
    thickness_in: float

    def label(self) -> str:
        return f"{self.assembly}.{self.layer}={self.thickness_in}in"


@dataclass(frozen=True)
class VariantSpec:
    """One named member of this house's variant set."""

    name: str
    description: str = ""
    assembly_swaps: dict[str, str] = field(default_factory=dict)
    layer_thickness: tuple[LayerThicknessOverride, ...] = ()

    def selection(self, house: Path) -> VariantSelection:
        from typehaus.diff.compare import VariantSelection

        return VariantSelection(house=Path(house), swaps=dict(self.assembly_swaps),
                                layer_thickness=self.layer_thickness, label=self.name)

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "assembly_swaps": dict(self.assembly_swaps),
            "layer_thickness": [
                {"assembly": item.assembly, "layer": item.layer,
                 "thickness_in": item.thickness_in}
                for item in self.layer_thickness
            ],
        }

    @property
    def override_count(self) -> int:
        return len(self.assembly_swaps) + len(self.layer_thickness)


def load_variants(house_dir: Path) -> tuple[VariantSpec, ...]:
    """Read ``variants.toml``. A house without the file simply declares no variants."""
    path = Path(house_dir) / VARIANTS_FILENAME
    if not path.exists():
        return ()
    data = tomllib.loads(path.read_text())
    specs: list[VariantSpec] = []
    for entry in data.get("variant", ()):
        name = entry.get("name")
        if not name:
            raise ValueError(f"{path}: every [[variant]] needs a name")
        specs.append(VariantSpec(
            name=str(name),
            description=str(entry.get("description", "")),
            assembly_swaps={str(k): str(v)
                            for k, v in (entry.get("assembly_swaps") or {}).items()},
            layer_thickness=tuple(
                LayerThicknessOverride(assembly=str(item["assembly"]),
                                       layer=str(item["layer"]),
                                       thickness_in=float(item["thickness_in"]))
                for item in entry.get("layer_thickness", ())
            ),
        ))
    names = [spec.name for spec in specs]
    duplicates = {name for name in names if names.count(name) > 1}
    if duplicates:
        raise ValueError(f"{path}: duplicate variant name(s) {sorted(duplicates)}")
    return tuple(specs)


def find_variant(specs: tuple[VariantSpec, ...], name: str) -> VariantSpec:
    spec = next((item for item in specs if item.name == name), None)
    if spec is None:
        raise ValueError(f"no variant named {name!r}; declared: "
                         f"{', '.join(item.name for item in specs) or '(none)'}")
    return spec


def apply_layer_thickness(plan: PlanModel,
                          overrides: tuple[LayerThicknessOverride, ...]) -> PlanModel:
    """Return a copy of ``plan`` whose library carries the retuned layer thicknesses.

    The rewrite lands on the authored assembly (both its core ``layers`` and its
    ``default_lining``), so every wall referencing it — and every variant resolving against
    it — reflows from the same edit, exactly as an authored thickness change would.
    """
    if not overrides:
        return plan
    library = plan.library
    assemblies = list(library.assemblies)
    for override in overrides:
        index = next((i for i, item in enumerate(assemblies)
                      if item.tag == override.assembly), None)
        if index is None:
            raise ValueError(f"variant override names unknown assembly "
                             f"{override.assembly!r}")
        assembly = assemblies[index]
        updated, hit = {}, False
        for attribute in ("layers", "default_lining"):
            rebuilt = []
            for layer in getattr(assembly, attribute):
                if layer.name == override.layer:
                    rebuilt.append(layer.model_copy(
                        update={"thickness": inch(override.thickness_in)}))
                    hit = True
                else:
                    rebuilt.append(layer)
            updated[attribute] = tuple(rebuilt)
        if not hit:
            raise ValueError(f"assembly {override.assembly!r} has no layer "
                             f"{override.layer!r}")
        assemblies[index] = assembly.model_copy(update=updated)
    return plan.model_copy(update={
        "library": library.model_copy(update={"assemblies": tuple(assemblies)}),
    })

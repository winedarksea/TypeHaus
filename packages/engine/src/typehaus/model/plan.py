"""PlanModel — the validated whole-building authored model (→ 02 §Pipeline)."""

from __future__ import annotations

from collections.abc import Iterable, Iterator

from pydantic import Field

from typehaus.model.assembly import Assembly, ConstructionRule
from typehaus.model.base import Element, HausModel
from typehaus.model.electrical import Circuit, LoadManagement
from typehaus.model.materials import Material
from typehaus.model.product import Product
from typehaus.model.project import Building, Project, Storey
from typehaus.model.types import (
    ApplianceType,
    DoorType,
    DuctProductType,
    ElectricalDeviceType,
    EquipmentType,
    FixtureType,
    FurnitureType,
    RailingType,
    RegisterType,
    WindowType,
)
from typehaus.model.views import Transition


class Library(HausModel):
    """Shared definitions the plan references by tag (assemblies, materials, types)."""

    materials: tuple[Material, ...] = ()
    assemblies: tuple[Assembly, ...] = ()
    # The chosen-product catalog. Identity only — never a price (#28); a material or a
    # ``*Type`` names one by tag through its ``product_ref``.
    products: tuple[Product, ...] = ()
    door_types: tuple[DoorType, ...] = ()
    window_types: tuple[WindowType, ...] = ()
    furniture_types: tuple[FurnitureType, ...] = ()
    railing_types: tuple[RailingType, ...] = ()
    fixture_types: tuple[FixtureType, ...] = ()
    appliance_types: tuple[ApplianceType, ...] = ()
    equipment_types: tuple[EquipmentType, ...] = ()
    register_types: tuple[RegisterType, ...] = ()
    # The duct itself as a product, keyed by the (material, nominal diameter) pair a
    # ``DuctRun`` states and ``prices.toml``'s ``[ducts]`` already qualifies on. Nothing
    # in the takeoff needs it; the static budget does.
    duct_product_types: tuple[DuctProductType, ...] = ()
    electrical_device_types: tuple[ElectricalDeviceType, ...] = ()
    circuits: tuple[Circuit, ...] = ()
    load_managements: tuple[LoadManagement, ...] = ()
    transitions: tuple[Transition, ...] = ()
    construction_rules: tuple[ConstructionRule, ...] = ()

    def assembly(self, tag: str) -> Assembly | None:
        return next((a for a in self.assemblies if a.tag == tag), None)

    def material(self, tag: str) -> Material | None:
        return next((m for m in self.materials if m.tag == tag), None)

    def product(self, tag: str) -> Product | None:
        return next((p for p in self.products if p.tag == tag), None)

    def resolve_assembly(self, tag: str) -> Assembly | None:
        """Resolve a variant against its base — unchanged layers track the base (#35)."""
        asm = self.assembly(tag)
        if asm is None or asm.variant_of is None:
            return asm
        base = self.resolve_assembly(asm.variant_of)
        if base is None:
            return asm
        layers = list(base.layers)
        for sub in asm.substitute:
            layers = _apply_substitution(layers, sub)
        update = {
            "tag": asm.tag,
            "layers": tuple(layers),
            "variant_of": asm.variant_of,
            "stc": asm.stc if asm.stc is not None else base.stc,
            "interfaces": asm.interfaces or base.interfaces,
        }
        # A variant's own scalar fields are its own. Copying the base and overriding only
        # the layer stack silently dropped them: a variant that states its purchasing
        # ``source``, its own room-side ``default_lining``, a different ``junction_policy``
        # or ``role`` resolved with the base's. Each falls back to the base when unset, so
        # a variant that says nothing still tracks its base exactly as before.
        for field in ("label", "source"):
            value = getattr(asm, field)
            if value is not None:
                update[field] = value
        if asm.default_lining:
            update["default_lining"] = asm.default_lining
        defaults = type(asm).model_fields
        for field in ("junction_policy", "role"):
            value = getattr(asm, field)
            if value != defaults[field].default:
                update[field] = value
        return base.model_copy(update=update)


def _apply_substitution(layers: list, sub: object) -> list:
    from typehaus.model.assembly import Substitution

    assert isinstance(sub, Substitution)
    names = [layer.name for layer in layers]
    span = sub.span
    if span.mode == "outside_of":
        i = names.index(span.anchor)
        return layers[: i + 1] + list(sub.replacement)
    if span.mode == "inside_of":
        i = names.index(span.anchor)
        return list(sub.replacement) + layers[i:]
    a, b = names.index(span.anchor), names.index(span.anchor_b)  # type: ignore[arg-type]
    lo, hi = sorted((a, b))
    return layers[:lo] + list(sub.replacement) + layers[hi + 1 :]


# The building every storey belongs to when a house authors no ``Project.buildings``. Not a
# real structure — the name a one-structure model reads so ``building_of`` is total.
IMPLICIT_BUILDING = "building"


class PlanModel(HausModel):
    """The validated authored model, before resolve. Whole-building (→ 02 §Pipeline)."""

    project: Project
    library: Library = Library()
    # Per-storey element lists, keyed by storey tag. Storey defs live in `storeys`.
    storeys: tuple[Storey, ...] = ()
    elements: dict[str, tuple[Element, ...]] = Field(default_factory=dict)
    # Set by the loader, never serialized into authored plan source.  Sidecar asset paths
    # (for example imported house-local furniture) resolve relative to this directory.
    source_root: str | None = None

    def storey(self, tag: str) -> Storey | None:
        return next((s for s in self.storeys if s.tag == tag), None)

    # --- the building axis (a storey is a datum; the container is the building) ----------
    #
    # ``building`` is a pure function of storey, so none of this needs a new field on a
    # ``Resolved*`` class, a re-keying of ``elements``, or a per-element override. Everything
    # downstream asks the plan.

    def buildings(self) -> tuple[Building, ...]:
        """The authored structures, or the one implicit building every storey belongs to.

        The fallback is what keeps the axis inert for a house that authors nothing: one
        building, every storey in it, so ``building_of`` is total and every building-scoped
        consumer reduces to the whole-model behaviour it had before.
        """
        if self.project.buildings:
            return self.project.buildings
        return (Building(tag=IMPLICIT_BUILDING, name=self.project.building.name),)

    def building_of(self, storey_tag: str) -> str:
        """The building tag owning ``storey_tag``. Total: unknown or unclaimed reads first."""
        storey = self.storey(storey_tag)
        if storey is not None and storey.building:
            return storey.building
        return self.buildings()[0].tag

    def building(self, tag: str) -> Building | None:
        return next((b for b in self.buildings() if b.tag == tag), None)

    def storeys_of(self, building: str) -> tuple[Storey, ...]:
        """Every storey of one building, in authored order."""
        return tuple(s for s in self.storeys if self.building_of(s.tag) == building)

    def building_order(self, building: str) -> int:
        """Index of a building in sheet order; unknown sorts last, never first."""
        tags = [b.tag for b in self.buildings()]
        return tags.index(building) if building in tags else len(tags)

    def cells(self) -> tuple[tuple[Building, Storey], ...]:
        """Every (building, storey) pair, buildings in sheet order then authored storey order.

        The "cell" is the unit that a sheet, an ``IfcBuildingStorey`` and a space summary are
        really about — never the storey alone, which two buildings may share an elevation on.
        """
        by_building = {b.tag: b for b in self.buildings()}
        return tuple(
            (by_building[tag], storey)
            for tag in by_building
            for storey in self.storeys_of(tag)
        )

    def storey_elements(self, storey_tag: str) -> tuple[Element, ...]:
        return self.elements.get(storey_tag, ())

    def all_elements(self) -> Iterator[Element]:
        for group in self.elements.values():
            yield from group

    def elements_of_kind(self, kind: str) -> Iterator[Element]:
        for el in self.all_elements():
            if el.element_kind == kind:
                yield el

    def by_tag(self, tag: str) -> Element | None:
        return self._tag_index().get(tag)

    def _tag_index(self) -> dict[str, Element]:
        """Tag -> element, built once per plan instance.

        This was a linear scan over ``all_elements()``. On the reference house ``resolve``
        called it ~4,000 times, which walked 1.18 M elements and cost ~13% of resolve's
        self-time — the single hottest entry in the profile. First tag wins, matching the
        old ``next(...)`` semantics on duplicates.

        The cache is keyed on the identity of the ``elements`` mapping it was built from,
        not merely stored on the instance: ``with_elements`` goes through ``model_copy``,
        which shallow-copies ``__dict__``, so an instance-only cache rides along onto the
        copy and answers for elements that copy no longer has. Comparing identity makes any
        copy, reconstruction or deserialization miss and rebuild.
        """
        cached = self.__dict__.get("_tag_index_cache")
        if cached is not None and cached[0] is self.elements:
            return cached[1]
        index: dict[str, Element] = {}
        for el in self.all_elements():
            if el.tag not in index:
                index[el.tag] = el
        object.__setattr__(self, "_tag_index_cache", (self.elements, index))
        return index

    def with_elements(self, storey_tag: str, items: Iterable[Element]) -> PlanModel:
        merged = dict(self.elements)
        merged[storey_tag] = tuple(items)
        return self.model_copy(update={"elements": merged})

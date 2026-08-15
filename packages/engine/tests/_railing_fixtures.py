"""Synthetic railings, resolved into real solids (→ AGENTS.md §3: shared setup).

Every guard the Catlin house authors is a *flat baluster* guard, and its five ``serves_stair``
railings are handrails with no infill at all — so cable, panel, mesh and every raking infill
have zero coverage in the reference house. These build a railing on a minimal plan and run
the real resolver over it, so the tests measure the geometry that ships rather than a
re-derivation of it.
"""

from __future__ import annotations

from typehaus.model.enums import RailingKind
from typehaus.model.structure import Railing
from typehaus.model.types import RailingType
from typehaus.quantities import ft, inch, pt
from typehaus.resolve.model import ResolvedModel
from typehaus.resolve.railings import resolve_railing


class _FakeMaterial:
    def __init__(self, tag: str, color: str | None) -> None:
        self.tag = tag
        self.color = color
        self.hatch = None


class _FakeLibrary:
    def __init__(self, railing_types=(), materials=()) -> None:
        self.railing_types = list(railing_types)
        self.materials = list(materials)


class _FakeStorey:
    tag = "main"
    elevation = ft(0)


class _FakePlan:
    """The narrowest plan the railing resolver reads: one storey, a library, one element."""

    def __init__(self, elements, library) -> None:
        self._elements = list(elements)
        self.library = library
        self.storeys = [_FakeStorey()]

    def storey_elements(self, _tag):
        return list(self._elements)

    def all_elements(self):
        return list(self._elements)

    def by_tag(self, tag):
        return next((e for e in self._elements if e.tag == tag), None)


def railing(tag: str = "RL-T", *, path=None, **kw) -> Railing:
    """A guard with the reference house's proportions, overridable field by field."""
    defaults = dict(
        uid=f"RLT{tag[-6:]:0>7}"[:10], tag=tag,
        path=path or (pt(ft(0), ft(0)), pt(ft(10), ft(0))),
        kind=RailingKind.METAL_FASCIA_MOUNT,
        height=inch(42), base_elevation=ft(0), post_spacing=inch(60),
        post_size="2x2", rail_count=2, assembly="RAILING_DARK_METAL",
    )
    defaults.update(kw)
    return Railing(**defaults)


def railing_type(tag: str = "RT-T", **kw) -> RailingType:
    defaults = dict(tag=tag, name="test railing product")
    defaults.update(kw)
    return RailingType(**defaults)


def resolve_railings(railings, *, types=(), materials=(), stairs=()) -> ResolvedModel:
    """Resolve ``railings`` into a model's solids, exactly as the pipeline would.

    ``materials`` is ``{tag: color}``; a colour with an 8-digit ``#RRGGBBAA`` alpha under
    ``ff`` is what makes an infill translucent, so that mapping is the whole knob the
    ``railing_glass`` category turns on.
    """
    library = _FakeLibrary(
        railing_types=types,
        materials=[_FakeMaterial(tag, color) for tag, color in dict(materials).items()],
    )
    model = ResolvedModel(plan=_FakePlan(railings, library))
    model.stairs.extend(stairs)
    findings = []
    for element in railings:
        findings.extend(resolve_railing(model, element, "main"))
    model.railing_findings = findings  # type: ignore[attr-defined]
    return model


def solids_of(model: ResolvedModel, tag: str, *categories: str) -> list:
    """This railing's solids in ``categories``, in the order the resolver emitted them."""
    wanted = set(categories) if categories else None
    return [s for s in model.solids
            if s.tag.startswith(f"{tag}-")
            and (wanted is None or s.category in wanted)]


def infill_of(model: ResolvedModel, tag: str) -> list:
    return solids_of(model, tag, "railing_infill", "railing_glass")


def centroid(solid) -> tuple[float, float]:
    return (sum(x for x, _y in solid.outline) / len(solid.outline),
            sum(y for _x, y in solid.outline) / len(solid.outline))


def inches(value_m: float) -> float:
    return value_m / 0.0254

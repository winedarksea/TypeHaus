"""R316.4 — the thermal barrier over foam plastic.

Foam plastic burns fast and gives off a lot of smoke doing it, so the code does not let it
face an occupied room: R316.4 asks for 1/2" gypsum wallboard, 5/8" wood structural panel, or
a material meeting the NFPA 275 acceptance criteria, between the foam and the interior.

Nothing enforced it here, and catlin has 8" of EPS deck form over its dining end whose only
protection is a single 5/8" gypsum layer at the bottom of ``CATLIN_DECK_EPS_INT``. Deleting
that layer — a plausible edit; it is the last line of a four-line stack and it changes no
R-value the energy check grades — would have been silent.

WHAT THIS DOES NOT DO. It reads authored assemblies, so it grades the *specification*, not
the built thing: a penetration cut through the barrier, a service chase left open, an attic
hatch, R316.5's long list of exceptions (attics and crawl spaces with limited access, sill
plates, foam under a slab, siding backer board) are all outside it. Nothing here claims a
code result; it claims that the drawn stack does or does not put an approved barrier between
the foam and the room.
"""

from __future__ import annotations

from collections.abc import Sequence

from typehaus.checks.code.mn_residential._common import _fail, _pass, _unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.model.assembly import Assembly, Layer
from typehaus.model.enums import LayerFunction
from typehaus.model.materials import Material
from typehaus.quantities import inch

_CID = "code.R316_4"
_CODE = "R316.4"

#: R316.4 verbatim: "not less than 1/2-inch gypsum wallboard".
_MIN_GYPSUM = inch(0.5)
#: R316.4's second named alternative, "5/8-inch wood structural panel". The model has no
#: field that identifies a wood structural panel — ``struct-1-plywood``, ``osb`` and
#: ``plywood-subfloor`` all are, and nothing on ``Material`` says so — so a sheathing layer
#: inboard of foam produces an UNKNOWN naming it rather than a pass or a failure. Adding the
#: datum is a smaller change than guessing at it, and guessing is how a fire rule quietly
#: stops applying (see ``fire_separation._gypsum_grade`` on the same temptation).
_MIN_WOOD_PANEL = inch(0.625)
#: Concrete and masonry pass R316.4 through its NFPA 275 clause without argument — the test
#: is a 250°F rise over the barrier in 15 minutes plus integrity, and an inch of concrete is
#: not close to the line. Recognised by DENSITY rather than by tag, which is the only
#: property of the substance the model actually records: 1600 kg/m3 sits below every
#: concrete, brick and grouted-CMU entry in the catalog (1900-2240) and well above every
#: wood, foam and board one (32-720).
_MASS_BARRIER_DENSITY = 1600.0
_MIN_MASS_BARRIER = inch(1.0)

#: Layers that interpose no protection at all: a furring strip stands the finish off, an air
#: gap is air, a membrane is a film. Foam behind only these is foam facing the room.
_TRANSPARENT_TO_FIRE = frozenset({
    LayerFunction.FURRING, LayerFunction.AIRGAP, LayerFunction.MEMBRANE,
})


def _material(ctx: CheckContext, ref: str | None) -> Material | None:
    return next((m for m in ctx.plan.library.materials if m.tag == ref), None)


def _interior_first(ctx: CheckContext, assembly: Assembly) -> bool:
    """Is layer 0 the interior face of this stack?

    The catalog's convention is interior -> exterior and that is what a wall follows. A
    FLOOR or deck assembly does not: ``CATLIN_DECK_EPS_INT`` runs cap, foam, furring rib,
    gypsum — top to bottom — because the room it faces is the one UNDER it. Reading the
    convention literally there would put the concrete cap against the ceiling and grade the
    stack backwards, which is the sort of quiet inversion that makes a fire check useless.

    Two signals, then the convention. CLADDING is by definition the weather face. GYPSUM is
    by definition a room face — nobody hangs board outside. ``LayerFunction.FINISH`` looks
    like a third and is a TRAP: catlin's south basement wall finishes its OUTBOARD face with
    a parge coat over the sunken garden, so keying on FINISH reads that wall inside out and
    reports the parge as the thermal barrier over foam that is in fact behind eight inches
    of concrete.
    """
    functions = [layer.function for layer in assembly.layers]
    if LayerFunction.CLADDING in functions:
        return functions.index(LayerFunction.CLADDING) > len(functions) / 2
    gypsum = [index for index, layer in enumerate(assembly.layers)
              if getattr(_material(ctx, layer.material_ref), "gypsum_type", None) is not None]
    if gypsum:
        return gypsum[0] < len(functions) / 2
    return True


def _barrier_verdict(ctx: CheckContext,
                     layers: Sequence[Layer]) -> tuple[str, str]:
    """``(verdict, phrase)`` for the layers between the foam and the room.

    EVERY layer in the span is examined, not just the first: R316.4 asks for an approved
    barrier somewhere between the foam and the interior, and where it sits in the sandwich
    is not the code's business. The roof is why — its polyiso is separated from the room by
    the rafter cavity and then by the ceiling board, and stopping at the first substantial
    layer (the ZIP deck) would have reported UNKNOWN over a gypsum ceiling that is right
    there.

    A layer too THIN to qualify is reported as such rather than passed over silently: a 3/8"
    board is a stated intention to protect the foam that falls short, which is a different
    and more interesting answer than "nothing here protects it".
    """
    thin: list[str] = []
    unclassified: list[str] = []
    for layer in layers:
        if layer.function in _TRANSPARENT_TO_FIRE:
            continue
        material = _material(ctx, layer.material_ref)
        if material is None:
            unclassified.append(f"'{layer.name}' names no material in the catalog")
            continue
        if getattr(material, "gypsum_type", None) is not None:
            if layer.thickness.meters + 1e-9 >= _MIN_GYPSUM.meters:
                return "pass", f"{layer.thickness.fmt()} gypsum ('{layer.name}')"
            thin.append(f"only {layer.thickness.fmt()} of gypsum ('{layer.name}'), under "
                        "R316.4's 1/2\"")
            continue
        density = getattr(material, "density", None)
        if density is not None and density >= _MASS_BARRIER_DENSITY:
            if layer.thickness.meters + 1e-9 >= _MIN_MASS_BARRIER.meters:
                return "pass", (f"{layer.thickness.fmt()} of {material.tag} "
                                f"('{layer.name}'), a mass barrier")
            thin.append(f"only {layer.thickness.fmt()} of {material.tag} ('{layer.name}')")
            continue
        if layer.function is LayerFunction.SHEATHING:
            unclassified.append(
                f"'{layer.name}' is {layer.thickness.fmt()} of {material.tag}; R316.4 also "
                "admits 5/8\" wood structural panel, and no field on Material says whether "
                "this is one")
            continue
        unclassified.append(f"'{layer.name}' ({material.tag}) is not identified as an "
                            "approved thermal barrier")
    if unclassified:
        return "unknown", "; ".join(unclassified)
    if thin:
        return "fail", "; ".join(thin)
    return "fail", "nothing between the foam and the room"


@check(Tier.CODE, _CID)
def foam_plastic_thermal_barrier(ctx: CheckContext) -> list[Finding]:
    """Every authored assembly whose interior-most substance is foam plastic needs a
    barrier in front of it."""
    out: list[Finding] = []
    # An assembly used by nothing but footings and pads has no interior face for a barrier to
    # be on. R316.4 separates foam from *the interior of a building*; a strip footing is
    # buried on all six sides, and an insulated footing form's whole point is that the foam
    # is between the concrete and the soil. Read off what uses the assembly rather than off
    # the assembly itself, because the same layer stack in a wall would need the barrier.
    _BURIED_ONLY = ("Footing", "Pad")
    used: dict[str, set[str]] = {}
    for element in ctx.plan.all_elements():
        tag = getattr(element, "assembly", None)
        if tag:
            used.setdefault(tag, set()).add(element.element_kind)
    for tag in sorted(used):
        if used[tag] <= set(_BURIED_ONLY):
            continue
        assembly = ctx.plan.library.resolve_assembly(tag)
        if assembly is None or not assembly.layers:
            continue
        if assembly.role == "band":
            # IRC R316.5.3 and R316.5.4: foam plastic installed under a slab-on-ground, or
            # in a foundation, is exempt from R316.4's thermal barrier. A band has no
            # interior-most face at all — it is buried on both sides — so grading one would
            # be reporting that soil is not gypsum.
            continue
        layers = list(assembly.layers)
        if not _interior_first(ctx, assembly):
            layers.reverse()
        # ``default_lining`` is the interior-of-structure finish stack (#34) — it is not in
        # ``layers`` and it is where the gypsum lives on every framed wall in this house.
        # Leaving it out reported UNKNOWN on the whole exterior envelope, over foam that a
        # 5/8" board covers. A room may override it (``Room.wall_lining``), so this grades
        # the DEFAULT: an override that removes the board is a case this does not see, and
        # is named in the module docstring's list of what it does not do.
        layers = list(assembly.default_lining) + layers
        # Walk out from the room. The FIRST foam layer is the one R316.4 is about — foam
        # behind it is already covered by whatever covers this one.
        for index, layer in enumerate(layers):
            material = _material(ctx, layer.material_ref)
            if material is None or not getattr(material, "foam_plastic", False):
                continue
            verdict, phrase = _barrier_verdict(ctx, list(reversed(layers[:index])))
            if verdict == "pass":
                out.append(_pass(_CID, f"{tag}: {layer.thickness.fmt()} of "
                                       f"{material.tag} is behind {phrase}", _CODE))
            elif verdict == "fail":
                out.append(_fail(_CID, f"{tag} puts {layer.thickness.fmt()} of "
                                       f"{material.tag} ('{layer.name}') toward the "
                                       f"interior with {phrase}; R316.4 requires 1/2\" "
                                       "gypsum, 5/8\" wood structural panel or an NFPA "
                                       "275 barrier", (tag,), _CODE))
            else:
                out.append(_unknown(_CID, f"{tag}: {phrase}", (tag,), _CODE))
            break
    if not out:
        return [_pass(_CID, "no authored assembly puts foam plastic toward an interior "
                            "face — R316.4 has nothing to protect", _CODE)]
    return out

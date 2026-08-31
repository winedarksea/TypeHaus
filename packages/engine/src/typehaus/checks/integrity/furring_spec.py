"""A FURRING ``FramingSpec`` field that no frame will ever read (→ 12 §Checks).

Two guards, one shape. ``FramingSpec`` is one record serving a STRUCTURE layer's studs, a
rainscreen batten grid, the Swinburne outrigger and the catlin girt course, and most of its
fields are read by exactly one of those four. A field set on the wrong kind of layer is not
refused by the model and not reported by the solver — it simply frames as if the author had
never written it, which is the quietest way a plan can be wrong.

They live outside ``checks.py`` because that file is at its size limit and because these two
ask one question the others do not: not *is this geometry possible* but *does this statement
have a reader*.
"""

from __future__ import annotations

from typehaus.checks._authoring import advisory
from typehaus.findings import Finding, Result, Severity
from typehaus.model.assembly import Layer
from typehaus.model.enums import LayerFunction


def _err(msg: str, assembly_tag: str, hint: str) -> Finding:
    return advisory("integrity.assembly_layers", msg, (assembly_tag,), Result.FAIL,
                    fix=hint, severity=Severity.ERROR)


def furring_spec_findings(assembly_tag: str, layer: Layer) -> list[Finding]:
    """Every authoring guard on one layer's ``FramingSpec``, in one call."""
    return (_standoff_findings(assembly_tag, layer)
            + _course_datum_findings(assembly_tag, layer))


def _standoff_findings(assembly_tag: str, layer: Layer) -> list[Finding]:
    """A furring band cannot be both a girt course and a Swinburne outrigger.

    ``standoff="block"`` says the band bears on 3-1/2" blocks at the framing module and
    takes one long screw per block (the catlin truss girt, ``framing/truss_girts.py``);
    ``laid="edge"`` stands the stick up in the band, which is the Swinburne outrigger and
    frames on a plywood tab (``framing/truss_frame.py``). Two different frames read the two
    fields, and a layer carrying both is claimed by neither — so it silently frames as an
    ordinary batten and the whole standoff, blocks, screws and all, disappears.
    """
    spec = layer.framing
    if spec is None or getattr(spec, "standoff", "none") != "block":
        return []
    if spec.laid != "edge":
        return []
    return [_err(
        f"assembly {assembly_tag} layer {layer.name} sets standoff=\"block\" and "
        "laid=\"edge\" together; a girt course is laid flat on its blocks and an "
        "outrigger stands on edge on a tab — one layer cannot be both",
        assembly_tag,
        'drop laid="edge" for a girt band, or standoff="block" for an outrigger')]


def _course_datum_findings(assembly_tag: str, layer: Layer) -> list[Finding]:
    """``course_datum``/``course_offset`` on a band whose courses do not exist.

    Both fields phase the *elevation* module of a horizontal furring band — where the
    courses count from, and how far the whole ladder slides off that datum
    (``resolve/framing/furring.course_phase``). Nothing else reads them. On a vertical
    band, on a STRUCTURE layer, or on a layer with no ``FramingSpec`` direction at all,
    they are a silent no-op: the author states a course phase, the build ignores it, and
    the wall frames on the old one with no finding anywhere to say so.

    ERROR rather than WARN for the reason ``_standoff_findings`` is: the field is not a
    preference the solver may decline, it is an instruction with exactly one reader, and a
    band that is not that reader has been given an instruction nobody will carry out.
    """
    spec = layer.framing
    if spec is None:
        return []
    stated = [name for name in ("course_datum", "course_offset")
              if getattr(spec, name, None) not in (None, "wall-base")]
    if not stated:
        return []
    if (layer.function is LayerFunction.FURRING
            and (spec.direction or "").strip().lower() == "horizontal"):
        return []
    return [_err(
        f"assembly {assembly_tag} layer {layer.name} sets {' and '.join(stated)} on a "
        "layer that frames no courses; both phase the elevation module of a FURRING "
        'layer with direction="horizontal" and are read nowhere else',
        assembly_tag,
        'give the layer direction="horizontal" on a FURRING function, or drop the '
        "course phase")]

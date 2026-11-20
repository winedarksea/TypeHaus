"""Horizontal FLEXX coordination: enclosure fit does not establish service access.

The product view supplies sizes but no dimensioned connection stations. Preserve
that gap while testing the space the chosen horizontal configuration actually needs.
"""

from shapely.geometry import Polygon

from typehaus.checks._authoring import failed, not_applicable, passed, unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.model.placeable_symbols._gree_flexx import SERVICE_CLEARANCE_IN

CHECK_ID = "mep.air_handler_coordination"
MODEL_SYMBOL = "gree-flexx-ultra-24-horizontal"


@check(Tier.INTEGRITY, CHECK_ID)
def air_handler_coordination(ctx: CheckContext):
    types = {product.tag: product for product in ctx.plan.library.equipment_types
             if product.model_representation
             and product.model_representation.symbol == MODEL_SYMBOL}
    objects = {obj.tag: obj for obj in ctx.model.canvas_objects}
    soffits = {soffit.tag: soffit for soffit in ctx.model.soffits}
    findings = []
    for equipment in ctx.plan.all_elements():
        product = types.get(getattr(equipment, "type_ref", None))
        obj = objects.get(equipment.tag)
        if product is None or obj is None:
            continue
        tags = (equipment.tag,)
        soffit = soffits.get(getattr(equipment, "soffit_ref", None))
        if soffit is not None:
            enclosure = Polygon(soffit.outline)
            if any(not enclosure.covers(Polygon(zone)) for zone in obj.required_clearances):
                findings.append(failed(
                    CHECK_ID,
                    f"{equipment.tag}: the {SERVICE_CLEARANCE_IN:g} inch front-panel service "
                    f"zone extends through {soffit.tag}'s side enclosure. An underside hatch "
                    "does not provide front-panel access. Revise the orientation/enclosure "
                    "and keep the return duct out of the service zone.",
                    tags + (soffit.tag,)))
            else:
                findings.append(unknown(
                    CHECK_ID, f"{equipment.tag}: the front service zone fits the enclosure; "
                    "duct, suspension and panel-removal access still need coordination.", tags))
        else:
            findings.append(unknown(
                CHECK_ID, f"{equipment.tag}: verify the front-panel service zone against "
                "walls, ducts and suspension; no soffit enclosure was declared.", tags))
        unresolved = [port.tag for port in product.ports if not port.is_exact()]
        if unresolved:
            findings.append(unknown(
                CHECK_ID, f"{equipment.tag}: connection stations remain schematic for "
                f"{', '.join(unresolved)}. The supply opening size is verified; its setback "
                "and the return clear aperture are not dimensioned. Case-level duct "
                "connectivity does not verify transition fit or drains (linesets: "
                "mep.lineset_reach). "
                "Confirm the delivered cabinet revision before fabrication.", tags))
        else:
            findings.append(passed(
                CHECK_ID, f"{equipment.tag}: all port stations are exact.", tags))
    return findings or [not_applicable(CHECK_ID, "No horizontal FLEXX air handler is placed.")]

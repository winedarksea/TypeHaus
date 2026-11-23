"""Footing piers, graded prescriptively (decision 16, 2026-11-22).

``engineering/footing_pier.py`` says which cast piers are part of their footing. Here:

* ``footing_pier_finding`` — ``structural.deck_post_size``'s verdict for one: IRC R507.4 sizes
  sawn-lumber posts; a cast pier that is a pedestal above grade is the R507.3 footing, its pad
  graded by ``structural.deck_footing_size``.
* ``pinned_pier_embedment``, emitted on ``structural.column_base`` by ``lateral_racking`` — a
  pier under a PINNED roof post stands free at its head, so its own drag and the post's base
  half are turned around in the soil: IBC 2018 §1807.3.2.1 Eq. 18-1, non-constrained (no rigid
  floor at grade, no diaphragm above it), S1 from Table 1806.2 at d/3, no §1806.3.4 doubling,
  embedment SHAFT ONLY (grade to the pad top; the pad is not credited).

Oracle: ``houses/catlin/notes/north_entry_piers.md`` §6c.
"""

from __future__ import annotations

from typehaus.checks.registry import CheckContext
from typehaus.findings import Finding, failed, passed, unknown

_ID = "structural.column_base"
_CODE = "IBC 2018 §1807.3.2.1, Table 1806.2"


def footing_pier_finding(ctx: CheckContext, deck_tag: str, post) -> Finding | None:  # type: ignore[no-untyped-def]
    """PASS for a footing pier under a deck, else ``None`` (the caller delegates it)."""
    from typehaus.checks.structural._engineering import engineering_context
    from typehaus.engineering.footing_pier import PEDESTAL_RATIO, exposed_ft, is_footing_pier
    from typehaus.engineering.pier_basis import cast_piers

    ectx = engineering_context(ctx)
    pier = next((p for p in cast_piers(ectx) if p.tag == post.tag), None)
    if pier is None or not is_footing_pier(ectx, pier):
        return None
    out = exposed_ft(ectx, pier.tag) or 0.0
    return passed(
        "structural.deck_post_size",
        f"deck {deck_tag} bears on {post.tag}, a {post.size} cast pier standing {out:.2f}' "
        f"out of grade ({out * 12.0 / pier.diameter_in:.2f} x its diameter) on its own pad, "
        f"laterally braced at its head by the tied deck: it is the deck's R507.3 footing "
        f"(Figure R507.3's pier from the footing to the bearing; the IRC states no height, so "
        f"the ACI 318-19 plain-concrete pedestal definition, h/d <= {PEDESTAL_RATIO:.0f}, is "
        f"used as a conservative proxy), not an R507.4 post. Its pad "
        f"is graded by structural.deck_footing_size, its depth by structural.frost_depth",
        (deck_tag, post.tag), code="IRC R507.3")


def pinned_pier_embedment(ctx: CheckContext) -> list[Finding]:
    """IBC 1807.3.2.1 on every cast pier under a pinned roof post."""
    from typehaus.checks.structural._engineering import engineering_context
    from typehaus.engineering.footing_pier import grade_ft
    from typehaus.engineering.pole_embedment import required_embedment_ft
    from typehaus.engineering.roof_moment import pinned_pier_poles
    from typehaus.engineering.soil import presumptive
    from typehaus.model.structure import Pad

    ectx = engineering_context(ctx)
    poles = pinned_pier_poles(ectx)
    if not poles:
        return []
    grade = grade_ft(ectx)
    soil = presumptive(ectx.soil_class, basis=ectx.soil_basis)
    out: list[Finding] = []
    for tag, (shear, moment, basis) in sorted(poles.items()):
        pier = ctx.plan.by_tag(tag)
        pad = ctx.plan.by_tag(getattr(pier, "supported_by", "") or "")
        if grade is None or soil is None or not isinstance(pad, Pad) \
                or pad.bottom_elevation is None:
            out.append(unknown(_ID, f"{tag}: IBC 1807.3.2.1 needs Site.grade, a soil class and "
                               f"the pad under the pier", (tag,), code=_CODE))
            continue
        pad_top = (pad.bottom_elevation.inches + pad.thickness.inches) / 12.0
        depth = grade - pad_top
        height = moment / shear - depth
        b_ft = float(pier.size.split()[0]) / 12.0
        need = required_embedment_ft(shear, height, b_ft, soil.lateral_bearing_psf_per_ft)
        msg = (f"{tag}: P {shear:,.1f} lb ASD at h {height:.3f}' above grade, b {b_ft * 12:.0f}\" "
               f"round, S1 {soil.lateral_bearing_psf_per_ft:.0f} psf/ft x d/3 "
               f"({soil.citation}, no §1806.3.4 doubling): Eq. 18-1 needs d {need:.2f}' against "
               f"{depth:.2f}' of shaft from grade to the pad top (pad not credited), d/c "
               f"{need / depth:.2f}. Load: {basis}")
        tags = (tag, pad.tag)
        if need <= depth:
            out.append(passed(_ID, msg, tags, code=_CODE))
        else:
            out.append(failed(_ID, msg, tags, code=_CODE,
                              fix="deepen the pad or widen the shaft"))
    return out

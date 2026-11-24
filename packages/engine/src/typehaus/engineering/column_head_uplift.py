"""Uplift at a column head for ``column_head_joint``: the roof q_h and a sealed deck.

Split out of ``column_head_joint`` (file size); arithmetic unchanged. ``UpliftBuild`` carries
the surrogate's own numbers to the sheet.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from typehaus.engineering.balcony_loads import CURTAIN_OWNER_BASIS
from typehaus.engineering.item import Step, num
from typehaus.engineering.registry import EngineeringContext


@dataclass(frozen=True)
class UpliftBuild:
    """The surrogate's own numbers, so the sheet prints the build-up and not only the total."""

    what: str          # "roof" or "sealed deck"
    at: str            # where q_h is taken: "the top of the guard", "the roof's ridge"
    q_h: float         # velocity pressure at the height the pressure is taken, psf
    wind_psf: float    # 0.6 q G C_f
    dead_psf: float    # the dead load the uplift is relieved by (unfactored)
    area_ft2: float
    net: float         # (wind_psf - 0.6 dead_psf) x area, lb

    def steps(self) -> tuple[Step, ...]:
        from typehaus.wind import ASD_WIND_FACTOR
        from typehaus.wind_tables import GUST_EFFECT_RIGID, MAX_VERIFIED_CASE_AB

        net_psf = self.wind_psf - ASD_WIND_FACTOR * self.dead_psf
        return (
            Step("q_h", f"velocity pressure at {self.at}", self.q_h, "psf",
              source="ASCE 7-16 eq. 26.10-1 at the site's wind basis"),
            Step("p_up", "uplift pressure on a solid band, at the bound on any published "
              "free-roof coefficient", self.wind_psf, "psf", "0.6 q_h G C_f",
              f"{num(ASD_WIND_FACTOR)} x {num(self.q_h)} x {num(GUST_EFFECT_RIGID)} x "
              f"{num(MAX_VERIFIED_CASE_AB)}",
              "ASCE 7-16 §29.3 solid-sign C_f at its Case A/B ceiling; ASD 0.6"),
            Step("p_dead", "dead load that holds it down (0.6D)", ASD_WIND_FACTOR * self.dead_psf,
              "psf", "0.6 D", f"{num(ASD_WIND_FACTOR)} x {num(self.dead_psf)}"),
            Step("A_trib", f"{self.what} area the column carries", self.area_ft2, "ft2"),
            Step("U_net", "net uplift per unit area", net_psf, "psf", "p_up - p_dead",
              f"{num(self.wind_psf)} - {num(ASD_WIND_FACTOR * self.dead_psf)}"),
        )


def sealed_deck_uplift(ctx: EngineeringContext, pier: Any, notes: list[str]
                       ) -> tuple[float, UpliftBuild] | None:
    """0.6D + 0.6W uplift on a SEALED deck, ASD lb per column; ``None`` for an open-jointed one.

    ASCE 7-16 gives an open-jointed walking surface no uplift. A watertight plank (an aluminium
    deck system) is a roof over the space below, so the same surrogate the roof columns use
    applies — ``0.6 q G C_f`` at the Case A/B bound, less 0.6 of the deck's dead — spent on
    the column's tributary (review B-06). The reviewer's hand estimate with C_N -1.5 was 380 lb.
    """
    from typehaus.engineering.deck_tie_basis import deck_wind
    from typehaus.engineering.pier_basis import DECK_DEAD_LOAD_PSF
    from typehaus.model.floors import FloorSystem
    from typehaus.wind_tables import asd_solid_band_psf

    post = ctx.plan.by_tag(pier.tag)
    deck = next((d for d in ctx.plan.all_elements() if isinstance(d, FloorSystem)
                 and d.service == "deck"
                 and any(pier.tag in (getattr(ctx.plan.by_tag(r), "bearing_refs", ()) or ())
                         for r in d.joists.bearing_refs or ())), None)
    plank = getattr(getattr(deck, "subfloor", None), "material_ref", "") or ""
    if deck is None or not plank.startswith("aluminum-deck"):
        notes.append(
            "NO UPLIFT ROW: this column carries no roof (roof tributary 0 ft2, computed) and "
            "its deck is an open-jointed walking surface, which ASCE 7-16 assigns no uplift.")
        return None
    wind = deck_wind(ctx, deck, [post])
    if wind is None:
        return None
    up = asd_solid_band_psf(wind.q_h_psf)
    area = pier.statics_area_ft2 or pier.tributary_ft2
    uplift = (up - 0.6 * DECK_DEAD_LOAD_PSF) * area
    build = UpliftBuild("sealed deck", "the top of the guard on the deck", wind.q_h_psf, up,
                        DECK_DEAD_LOAD_PSF, area, uplift)
    notes.append(
        f"UPLIFT: this deck's plank ({plank}) is SEALED — the porch's roof — so ASCE 7-16's "
        f"no-uplift rule for an open-jointed surface does not hold. GRADED as an OPEN structure "
        f"(the bound the roof columns use): 0.6 x {wind.q_h_psf:.2f} psf x G x C_f 1.8 = "
        f"{up:.2f} psf up, less 0.6 x {DECK_DEAD_LOAD_PSF:g} psf of deck dead (planters "
        f"excluded), on this column's {area:.1f} ft2 (the beam's STATICS area under full "
        f"load, as gravity takes it). The joist ties and the plank's own fastening see the "
        f"same uplift.")
    spacing_ft = float(deck.joists.spacing.inches) / 12.0
    net_psf = up - 0.6 * DECK_DEAD_LOAD_PSF
    notes.append(
        f"JOIST-TO-BEAM UPLIFT TIES (named, not a state of this record): the sealed deck's net "
        f"{net_psf:.1f} psf up reaches each beam through the ties at every joist crossing, "
        f"{net_psf:.1f} psf x {spacing_ft:g}' joist spacing x the beam's 9.75' strip = "
        f"{net_psf * spacing_ft * 9.75:,.0f} lb per tie, against the catalog's H10ASS uplift "
        f"1,040 lb (Simpson C-C-2026 p.300, `library/hardware/roof_ties.py`; read there, since "
        f"this package may not read the catalog): about 0.10. No check grades it yet, and the "
        f"H2.5ASS on each beam's two end joists (a half strip) is not compared; the plank's own "
        f"fastening to the joists is outside this record too.")
    notes.append(
        "OWNER BASIS, no internal pressure: the porch curtains are stowed in high wind, so the "
        "porch is OPEN and no GC_pi is taken under the sealed deck. " + CURTAIN_OWNER_BASIS)
    return uplift, build


def roof_q_h(ctx: EngineeringContext, tag: str) -> float | None:
    """q_h at the ridge of the roof(s) this column carries, the ``roof_moment`` datum."""
    from typehaus.engineering.balcony_wind import ground_below_ft
    from typehaus.model.spatial import Roof
    from typehaus.model.structure import Beam, Post
    from typehaus.wind import velocity_pressure_psf, wind_basis

    basis = wind_basis(ctx.plan.project.site)
    if basis is None:
        return None
    standing = {e.tag for e in ctx.plan.all_elements()
                if isinstance(e, Post) and e.supported_by == tag}
    ground = ground_below_ft(ctx.plan)
    best = None
    for roof in ctx.model.roofs:
        element = ctx.plan.by_tag(roof.tag)
        if not isinstance(element, Roof):
            continue
        beams = [b for b in (ctx.plan.by_tag(r) for r in element.bearing_refs)
                 if isinstance(b, Beam)]
        if any({tag, *standing} & set(b.bearing_refs or ()) for b in beams):
            q_h = velocity_pressure_psf(basis, roof.ridge_z_m / 0.3048 - ground)
            best = q_h if best is None else max(best, q_h)
    return best

"""What stands behind a segmental unit: its drainage zone, and how near a parallel wall is.

Split out of ``segmental_wall`` (file size). Two readings, both printed on the SRW record:

* **The drainage zone** (``SegmentalWallSpec.drainage_zone``) becomes the near-heel zone of the
  two-zone trial wedge in ``srw_gravity``.
* **Confined backfill.** A wall retaining a strip ``b`` wide against a rigid face sees less
  than Coulomb only where the critical wedge cannot form inside ``b``. The published
  reductions — Frydman & Keissar (1987, centrifuge), Leshchinsky & Hu (2003) and Lawson &
  Yee (2005, limit equilibrium) — are for GRANULAR fill; Kniss et al. (2007) call the charts
  "not appropriate" for a cohesive one and found the conventional pressure at L/H 0.70. So
  nothing is credited: the record states whether the wedge reaches the face, and the most a
  planar surface restricted to the strip could take off, as a sensitivity.

Oracle: ``notes/raised_garden_srw.md`` §2b, §6b.
"""

from __future__ import annotations

import math

from typehaus.engineering.srw_gravity import DrainageZone, FreeBody, Section, trial_wedge
from typehaus.engineering.srw_tiers import Tier


def drainage_zone(spec) -> DrainageZone | None:  # type: ignore[no-untyped-def]
    zone = getattr(spec, "drainage_zone", None)
    if zone is None:
        return None
    return DrainageZone(width_ft=zone.width.feet, phi_deg=zone.friction_angle_deg)


def zone_note(spec, body: FreeBody) -> str:  # type: ignore[no-untyped-def]
    zone = spec.drainage_zone
    wedge = body.wedge
    return (f"Drainage zone: {zone.width.inches:g}\" of aggregate behind the unit at φ "
            f"{zone.friction_angle_deg:g}° ({zone.source}), graded as a two-zone trial wedge: "
            f"at {body.soil_phi_deg:.1f}° native the critical plane is {wedge.plane_deg:.2f}° "
            f"and {wedge.zone_share:.0%} of it lies in the zone, φ_eq {wedge.phi_equiv_deg:.2f}° "
            f"(length-weighted tan φ). δ stays ⅔ of the native φ. Not credited: the zone's "
            f"share of the plane's normal force beyond its length, and δ on the rock.")


def confined_note(section: Section, soil_pcf: float, body: FreeBody,
                  zone: DrainageZone | None, tier: Tier) -> str:
    """The narrow-backfill question for one parallel wall, answered and not credited."""
    height = section.height_ft
    reach = body.wedge.reach_ft
    ratio = tier.clear_ft / height if height else 0.0
    head = (f"CONFINED BACKFILL vs {tier.tag} at {soil_pcf:.0f} pcf: the strip is "
            f"{tier.clear_ft:.2f}' wide on a {height:.2f}' free body, b/H {ratio:.2f}; the "
            f"critical wedge exits {reach:.2f}' behind the heel")
    if reach <= tier.clear_ft:
        return head + " — inside the strip, so the court wall does not touch it. No reduction."
    steep = math.degrees(math.atan(height / tier.clear_ft))
    restricted = trial_wedge(height, soil_pcf, body.soil_phi_deg, section.batter_deg, zone,
                             min_plane_deg=steep).thrust_plf
    return (head + f", {reach - tier.clear_ft:.2f}' past the court face. The largest planar "
            f"wedge that exits inside the strip is {restricted:,.1f} plf against "
            f"{body.thrust_plf:,.1f} ({restricted / body.thrust_plf - 1.0:+.1%}). Not credited: "
            "the narrow-backfill charts (Leshchinsky & Hu 2003; Lawson & Yee 2005) are for "
            "granular fill, and Kniss et al. (2007) found the conventional pressure at L/H "
            "0.70 and call them not appropriate for a cohesive soil — this one is presumed.")

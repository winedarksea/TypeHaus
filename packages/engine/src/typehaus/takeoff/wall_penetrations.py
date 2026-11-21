"""``[wall_penetrations]``: the metal-wall kits, off the #142 records, billed by part.

Sleeves, boots and inlets each by product; blocks by the SF of 3/4" sheet they use (a strap
block is laminated, so its face times its plies); strut by the foot and its spring nuts each;
the panel urethane by the tube, butyl by the roll and annulus foam by the can, converted on
the standard's own figures. Priced keyed on ``product``; a strut row says ``unit = "LF"``, a
block row ``unit = "SF"``. The lineset cover stays in [linesets]' allowance.
"""

from __future__ import annotations

import math
from typing import Any

_FT = 0.3048
_SF = _FT * _FT
_IN = 0.0254


def wall_penetration_takeoff(model: Any) -> list[dict[str, Any]]:
    from typehaus.resolve.mount_blocks import penetration_standard

    standard = penetration_standard(model.plan)
    pens = list(getattr(model, "wall_penetrations", ()))
    mounts = list(getattr(model, "mount_blocks", ()))
    if standard is None or not (pens or mounts):
        return []
    rows: dict[tuple[str, str], dict[str, Any]] = {}

    def add(item: str, product: str | None, tag: str, count: int = 1, length_m: float = 0.0,
            area_m2: float = 0.0) -> None:
        if product is None:
            return
        row = rows.setdefault((item, product), {"item": item, "product": product, "count": 0,
                                                "length_ft": 0.0, "area_sf": 0.0,
                                                "tags": set()})
        row["count"] += count
        row["length_ft"] = round(row["length_ft"] + length_m / _FT, 2)
        row["area_sf"] = round(row["area_sf"] + area_m2 / _SF, 2)
        row["tags"].add(tag)

    bead = butyl = 0.0
    annuli = 0
    for pen in pens:
        if pen.sleeve_d_m and pen.sleeve_ref is None:
            add("sleeve", pen.sleeve_product, pen.run_tag, 1,
                pen.depth_m + standard.sleeve_lip.meters)
            butyl += math.pi * (pen.sleeve_d_m + 2 * _IN)  # the flange to the sheathing
            annuli += 1
        if pen.closure in ("boot", "strut_boot") and pen.boot_base_m:
            add("boot", pen.closure_product, pen.run_tag)
            butyl += math.pi * pen.boot_base_m[0]
            bead += math.pi * pen.boot_base_m[0]
        elif pen.closure == "inlet" and standard.lineset_inlet is not None:
            row = standard.lineset_inlet
            add("inlet", pen.closure_product, pen.run_tag)
            bead += row.flange_width.meters + 2 * row.flange_height.meters
    for mount in mounts:
        tag = mount.holds[0]
        if mount.kind == "strut":
            add("strut", mount.product, tag, len(mount.channels), mount.strut_lf_m)
            add("spring nut", standard.strut.spring_nut_ref, tag,
                2 * len(mount.channels) * len(mount.holds))
            continue
        height = (mount.z1_m - mount.z0_m if mount.top_z is None
                  else (sum(mount.top_z) / 2 - mount.z0_m))
        plies = 1 if mount.kind == "block" else max(1, math.ceil(
            mount.depth_m / standard.mount_block.thickness.meters - 1e-6))
        add("block" if mount.kind == "block" else "strap block", mount.product, tag, 1,
            area_m2=mount.width_m * height * plies)
        if mount.kind == "strap_block":
            row = standard.strap_block
            add("strap block screw", row.screw_ref, tag, row.screws_per_block)
        bead += mount.width_m + 2 * height if mount.kind == "block" else 0.0  # head + sides
    tubes = math.ceil(bead / standard.sealant_bead_per_tube.meters - 1e-9) if bead else 0
    rolls = math.ceil(butyl / standard.butyl_roll_length.meters - 1e-9) if butyl else 0
    cans = math.ceil(annuli / standard.annuli_per_foam_can) if annuli else 0
    add("panel sealant", standard.panel_sealant_ref, "PENETRATION-STANDARD", tubes)
    add("butyl tape", standard.butyl_ref, "PENETRATION-STANDARD", rolls)
    add("annulus foam", standard.annulus_foam_ref, "PENETRATION-STANDARD", cans)
    return [{**row, "tags": sorted(row["tags"])} for _, row in sorted(rows.items())
            if row["count"]]

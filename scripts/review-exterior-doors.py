"""Export actual resolved sill/head/jamb cuts and provenance for the selected doors.

Run with .venv/bin/python scripts/review-exterior-doors.py [--export]. Artifacts go to
out/exterior-door-review; unresolved factory sections remain visible in the review.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as PlotPolygon
from shapely.geometry import LineString, Polygon

from typehaus.emit.draw.elevation_project import solid_faces
from typehaus.resolve import resolve
from typehaus.resolve.doorway import doorway_json
from typehaus.resolve.geometry import opening_center, wall_frame
from typehaus.resolve.geometry_ir import GMesh, GPrism, GSweep
from typehaus.server.model_json import model_to_dict
from typehaus.source import load_plan

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "out/exterior-door-review"
TAGS = ("D-M-ENTRY", "D-M-BALC", "D-S-DECK-E", "D-B-PATIO")


def color(part):
    if "flashing" in part.material_key or "fluid" in (part.catalog.material_ref or ""
                                                       if part.catalog else ""):
        return "#c84e43"
    if part.key.startswith("installation:") or part.key in ("frame", "leaf", "mullion"):
        return "#41464a"
    if "finish" in part.key or "floor" in part.material_key:
        return "#c4b59c"
    return "#d9d1bd"


def render_cuts(model):
    figure, axes = plt.subplots(3, len(TAGS), figsize=(7.5 * len(TAGS), 12))
    for column, tag in enumerate(TAGS):
        opening = next(o for o in model.openings if o.tag == tag)
        wall = model.wall(opening.host_wall)
        center = opening_center(wall, opening)
        _, tangent, normal, _ = wall_frame(wall)
        sign = opening.doorway.exterior_placement.outward_sign
        base = opening.doorway.rough_opening_z_m
        station = -opening.width_m / 4 if tag != "D-M-ENTRY" else 0.0
        def local(point, center=center, tangent=tangent, sign=sign, normal=normal):
            delta = (point[0] - center[0], point[1] - center[1])
            return (sum(delta[i] * tangent[i] for i in (0, 1)),
                    sign * sum(delta[i] * normal[i] for i in (0, 1)))
        for row, name in enumerate(("Sill", "Head", "Jamb (plan cut)")):
            ax = axes[row, column]
            ax.set_title(f"{tag} — {name}")
            for element in model.geometry.elements:
                for part in element.parts:
                    for solid in part.solids:
                        if isinstance(solid, GPrism):
                            ring = Polygon([local(p) for p in solid.ring],
                                           holes=[[local(p) for p in h] for h in solid.voids])
                            if not ring.is_valid or ring.is_empty:
                                continue
                            if row == 2:
                                if not solid.z0_m < base + 1.0 < solid.z1_m:
                                    continue
                                if not ring.intersects(Polygon([
                                        (-opening.width_m/2-.14,-.23),
                                        (-opening.width_m/2+.14,-.23),
                                        (-opening.width_m/2+.14,.27),
                                        (-opening.width_m/2-.14,.27)])):
                                    continue
                                ax.add_patch(PlotPolygon([(y/.0254,x/.0254)
                                    for x,y in ring.exterior.coords], facecolor=color(part),
                                    edgecolor="#777", linewidth=.45))
                            else:
                                zlo,zhi = ((-.13,.25) if row == 0 else
                                           (opening.height_m - .25, opening.height_m + .25))
                                if solid.z1_m < base + zlo or solid.z0_m > base + zhi:
                                    continue
                                crossing = ring.intersection(LineString([(station,-1),(station,1)]))
                                for line in getattr(crossing,"geoms",(crossing,)):
                                    if line.geom_type != "LineString" or line.is_empty:
                                        continue
                                    depths=[p[1]/.0254 for p in line.coords]
                                    ax.add_patch(PlotPolygon([
                                        (min(depths),(solid.z0_m-base)/.0254),
                                        (max(depths),(solid.z0_m-base)/.0254),
                                        (max(depths),(solid.z1_m-base)/.0254),
                                        (min(depths),(solid.z1_m-base)/.0254)],facecolor=color(part),
                                        edgecolor="#777",linewidth=.45))
                        elif isinstance(solid, (GSweep, GMesh)) and row != 2:
                            # Cut boundary faces at the same station as the prism cut.
                            # Projecting the whole sweep would include off-station geometry.
                            for face in solid_faces(solid):
                                distances = [local(p)[0] - station for p in face]
                                hits = [(local(point)[1] / .0254, (point[2] - base) / .0254)
                                        for point, distance in zip(face, distances, strict=True)
                                        if abs(distance) <= 1e-9]
                                for i in range(len(face)):
                                    j = (i + 1) % len(face)
                                    a, b = distances[i], distances[j]
                                    if a * b < 0:
                                        t = a / (a - b)
                                        point = tuple(face[i][k] + t * (face[j][k] - face[i][k])
                                                      for k in (0, 1, 2))
                                        hits.append((local(point)[1] / .0254,
                                                     (point[2] - base) / .0254))
                                hits = list(dict.fromkeys(tuple(round(v, 8)
                                                                   for v in hit)
                                                          for hit in hits))
                                if len(hits) >= 2:
                                    line = hits + hits[:1] if len(hits) > 2 else hits
                                    ax.plot(*zip(*line, strict=True), color=color(part), lw=.65)
            ax.set_xlim(-9, 18 if tag == "D-B-PATIO" else 12)
            if row==0:
                ax.set_ylim(-5,10)
                report = opening.doorway.exterior_placement.installation_report
                label = ("Catalog coordination — installation incomplete" if report else
                         "Sill design envelope — factory section / structural support pending")
                ax.text(.02, .95, label, transform=ax.transAxes, va="top", fontsize=8,
                        color="#a02e27")
                if report:
                    for key, tone in (("interior_surface_z_m", "#458545"),
                                      ("exterior_surface_z_m", "#5577aa"),
                                      ("conservative_crest_z_m", "#a02e27")):
                        value = report.get(key)
                        if value is not None:
                            ax.axhline((value-base)/.0254, color=tone, ls="--", lw=.6)
            elif row==1:
                ax.set_ylim(opening.height_m / .0254 - 10, opening.height_m / .0254 + 10)
            else:
                jamb=-opening.width_m/2/.0254
                ax.set_ylim(jamb-5,jamb+5)
            ax.set_xlabel("Outward from wall axis (in)")
            ax.set_ylabel("Elevation above rough opening (in)" if row<2 else "Along opening (in)")
            ax.grid(alpha=.2)
    figure.suptitle("Structural-wall doors — actual resolved geometry; red = flashing")
    figure.tight_layout()
    figure.savefig(OUTPUT/"door-sections.png",dpi=170)
    figure.savefig(OUTPUT/"door-sections.pdf")


def write_catalog_review(model):
    from typehaus.takeoff.doors import door_installation_rows

    reports = {o.tag: o.doorway.exterior_placement.installation_report
               for o in model.openings if o.tag in TAGS and o.doorway.exterior_placement
               and o.doorway.exterior_placement.installation_report}
    (OUTPUT / "catalog-installation-report.json").write_text(json.dumps(reports, indent=2) + "\n")
    with (OUTPUT / "catalog-height-review.csv").open("w") as stream:
        writer = csv.writer(stream)
        writer.writerow(("door", "crest_above_interior_in", "crest_above_exterior_in",
                         "height_tolerance_in", "conservative_crest_above_interior_in",
                         "conservative_crest_above_exterior_in",
                         "support_member", "root_connection", "fit"))
        for tag, report in reports.items():
            allowance = (report["conservative_crest_z_m"] - report["nominal_crest_z_m"]) / .0254
            writer.writerow((tag, report["crest_above_interior_in"],
                             report["crest_above_exterior_in"],
                             allowance,
                             report["crest_above_interior_in"] + allowance,
                             report["crest_above_exterior_in"] + allowance,
                             report["support"]["member_status"],
                             report["support"]["connection_status"],
                             next(o.doorway.fit_status for o in model.openings if o.tag == tag)))
    rows = [r for r in door_installation_rows(model) if any(t in reports for t in r["tags"])]
    (OUTPUT / "catalog-installation-takeoff.json").write_text(json.dumps(rows, indent=2) + "\n")
    from typehaus.takeoff.door_trim_layout import TrimSheetStock, door_trim_sheet_layouts

    layouts = door_trim_sheet_layouts(model, {
        "captivate-graphite-sheet": TrimSheetStock(
            description="AZEK Captivate 3/4 x 48 x 96; AS03448096 substrate",
            finish="Graphite Gray", thickness_in=0.75, width_in=48, length_in=96,
            saw_kerf_in=0.125),
    })
    (OUTPUT / "catalog-trim-sheet-layout.json").write_text(json.dumps(layouts, indent=2) + "\n")
    figure, axes = plt.subplots(1, 2, figsize=(14, 6))
    study = next(o for o in model.openings if o.tag == "D-S-DECK-E")
    placement = study.doorway.exterior_placement
    base = study.doorway.rough_opening_z_m
    for axis, side in zip(axes, (-1, 1), strict=True):
        for section in placement.sections:
            if 'flashing-end-' not in section.name or not section.name.endswith(f'-{side}'):
                continue
            points = [(placement.outward_sign*x/.0254, (z-base)/.0254)
                      for x, z in section.polygon_m]
            axis.add_patch(PlotPolygon(points, alpha=.6, label=section.name))
        axis.autoscale_view()
        axis.set_aspect('equal')
        axis.set_title(f'D-S-DECK-E end {side}: envelopes, bonds unconfirmed')
        axis.set_xlabel('Outward from host axis (in)')
        axis.set_ylabel('Above rough sill (in)')
        axis.grid(alpha=.2)
        axis.legend(fontsize=6)
    figure.tight_layout()
    figure.savefig(OUTPUT / 'catalog-flashing-ends.png', dpi=150)
    figure.savefig(OUTPUT / 'catalog-flashing-ends.pdf')
    plt.close(figure)


def main():
    OUTPUT.mkdir(parents=True,exist_ok=True)
    loaded=load_plan(ROOT/"houses/catlin")
    if loaded.plan is None:
        raise RuntimeError([f.message for f in loaded.findings])
    model,findings=resolve(loaded.plan)
    errors=[f.message for f in findings if f.severity.value=="error"]
    if errors:
        raise RuntimeError(errors)
    payload=model_to_dict(model)
    (OUTPUT/"model.json").write_text(json.dumps(payload))
    report={o.tag:doorway_json(o.doorway) for o in model.openings if o.tag in TAGS}
    (OUTPUT/"doorway-report.json").write_text(json.dumps(report,indent=2))
    render_cuts(model)
    write_catalog_review(model)
    if "--export" in sys.argv:
        from typehaus.emit.gltf import emit_glb
        from typehaus.emit.ifc import emit_ifc
        emit_glb(model,OUTPUT/"catlin-exterior-doors.glb",lod="framed")
        emit_ifc(model,OUTPUT/"catlin-exterior-doors.ifc",lod="framed")
    print(OUTPUT)


if __name__=="__main__":
    main()

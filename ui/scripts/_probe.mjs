import { createServer } from "vite";
const server = await createServer({ configFile: false, server: { middlewareMode: true }, appType: "custom" });
try {
  const walls = await server.ssrLoadModule("/src/three/builders/walls.ts");
  const model = await (await fetch("http://127.0.0.1:8765/model")).json();
  const wall = model.walls.find((w) => w.tag === "W-B-BRICK");
  const openings = model.openings.filter((o) => o.host === wall.uid || o.host === wall.tag);
  const door = openings.find((o) => o.tag === "AO-B-BRICK-DOOR");
  const IN = 0.0254;
  console.log("wall z", wall.z0_m / IN, wall.z1_m / IN, "axis", JSON.stringify(wall.axis));
  console.log("door along", door.center_along_m / IN, "w", door.width_m / IN,
    "h", door.height_m / IN, "sill", door.sill_m / IN);
  const start = door.center_along_m - door.width_m / 2, end = door.center_along_m + door.width_m / 2;
  for (const ly of wall.layers) {
    if (ly.polygon.length < 3 || ly.is_cavity) continue;
    const geo = walls.createSmoothArchedWallLayerGeometry(wall, ly.polygon, openings, [0, 0], ly);
    if (!geo) { console.log(ly.material, "-> strip path"); continue; }
    const pos = geo.getAttribute("position");
    // Scene (x, z) maps back to plan (x, -z) about the centre, then project onto the axis.
    const [[sx, sy], [ex, ey]] = wall.axis;
    const len = Math.hypot(ex - sx, ey - sy);
    const ux = (ex - sx) / len, uy = (ey - sy) / len;
    const alongOf = (i) => (pos.getX(i) - sx) * ux + (-pos.getZ(i) - sy) * uy;
    let inside = 0, minY = Infinity, maxY = -Infinity;
    for (let t = 0; t < pos.count; t += 3) {
      const as = [0, 1, 2].map((k) => alongOf(t + k));
      const ys = [0, 1, 2].map((k) => pos.getY(t + k));
      const cx = (as[0] + as[1] + as[2]) / 3;
      if (cx > start + 0.02 && cx < end - 0.02) {
        inside++;
        minY = Math.min(minY, ...ys); maxY = Math.max(maxY, ...ys);
      }
    }
    if (ly.material === "brown-brick" || ly.material === "glazed-gold-brick") {
      const acrossOf = (i) => (pos.getX(i) - sx) * -uy + (-pos.getZ(i) - sy) * ux;
      let shown = 0;
      for (let t = 0; t < pos.count && shown < 8; t += 3) {
        const as = [0, 1, 2].map((k) => alongOf(t + k));
        const cx = (as[0] + as[1] + as[2]) / 3;
        if (!(cx > start + 0.02 && cx < end - 0.02)) continue;
        shown++;
        console.log("   tri", [0, 1, 2].map((k) => [
          ((alongOf(t + k)) / IN).toFixed(2),
          ((pos.getY(t + k) - wall.z0_m) / IN).toFixed(2),
          (acrossOf(t + k) / IN).toFixed(3),
        ].join("/")).join("  "));
      }
    }
    console.log(`${ly.material.padEnd(20)} band ${((ly.z0_m ?? wall.z0_m) - wall.z0_m) / IN}..${((ly.z1_m ?? wall.z1_m) - wall.z0_m) / IN}`
      + `  tris-over-door=${inside}` + (inside ? `  y=${((minY - wall.z0_m) / IN).toFixed(2)}..${((maxY - wall.z0_m) / IN).toFixed(2)}` : ""));
  }
} finally { await server.close(); }
process.exit(0);

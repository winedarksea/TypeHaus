import { createServer } from "vite";
const server = await createServer({ configFile: false, server: { middlewareMode: true }, appType: "custom" });
try {
  const walls = await server.ssrLoadModule("/src/three/builders/walls.ts");
  const model = JSON.parse(await (await import("node:fs/promises")).readFile("../houses/catlin/out/model.json", "utf8"));
  const wall = model.walls.find((w) => w.tag === "W-B-BRICK");
  const openings = model.openings.filter((o) => o.host === wall.uid || o.host === wall.tag);
  const door = openings.find((o) => o.tag === process.env.OP);
  const IN = 0.0254;
  const start = door.center_along_m - door.width_m / 2, end = door.center_along_m + door.width_m / 2;
  const [[sx, sy], [ex, ey]] = wall.axis;
  const len = Math.hypot(ex - sx, ey - sy), ux = (ex - sx) / len, uy = (ey - sy) / len;
  for (const ly of wall.layers) {
    if (ly.polygon.length < 3 || ly.is_cavity) continue;
    const geo = walls.createSmoothArchedWallLayerGeometry(wall, ly.polygon, openings, [0, 0], ly);
    if (!geo) continue;
    const pos = geo.getAttribute("position"), nrm = geo.getAttribute("normal");
    const alongOf = (i) => (pos.getX(i) - sx) * ux + (-pos.getZ(i) - sy) * uy;
    const buckets = new Map();
    for (let t = 0; t < pos.count; t += 3) {
      const ys = [0, 1, 2].map((k) => pos.getY(t + k));
      if (Math.max(...ys) - Math.min(...ys) > 1e-9) continue;
      const as = [0, 1, 2].map((k) => alongOf(t + k));
      if (Math.max(...as) < start + 1e-6 || Math.min(...as) > end - 1e-6) continue;
      const ny = nrm.getY(t);
      const key = `${((ys[0] - wall.z0_m) / IN).toFixed(2)}" ny=${ny > 0.5 ? "+1" : ny < -0.5 ? "-1" : ny.toFixed(2)}`;
      buckets.set(key, (buckets.get(key) ?? 0) + 1);
    }
    const band = `${(((ly.z0_m ?? wall.z0_m) - wall.z0_m) / IN).toFixed(1)}..${(((ly.z1_m ?? wall.z1_m) - wall.z0_m) / IN).toFixed(1)}`;
    console.log(`${ly.material.padEnd(19)} band ${band.padEnd(14)}`, JSON.stringify(Object.fromEntries([...buckets].sort())));
  }
} finally { await server.close(); }
process.exit(0);

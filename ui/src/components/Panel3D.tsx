import { useEffect, useRef } from "react";
import * as THREE from "three";
import { ALL_TRADES, useStore, type Trade } from "../state/store";
import type { Model, Roof, Solid, Floor, Stair, Wall, EnvelopeBand } from "../model/types";
import { materialColor, RESOLVED_NORDIC_PALETTE, type ResolvedNordicPalette } from "../nordic/palette";
import { buildMembers, disposeGroup } from "../three/members";
import { createPlanPrismGeometry } from "../three/planGeometry";
import { useTheme } from "../theme/theme";

// The 3D panel behind an implicit ModelViewer seam (→ 21 §3D panel). The primary path is
// glTF from ResolvedModel; until the server emits it, this builds an equivalent scene
// directly from model.json (extruded wall/solid/roof surfaces + solid instanced framing
// members), which is always available and guarantees the 3D view shows exactly what the
// resolver computed. The Nordic passes (soft lighting + edge linework) attach to the
// three.js scene, so they survive the eventual glTF route unchanged. Clicking a wall
// cross-highlights the 2D plan and surfaces its file:line provenance.

const TRADE_LABEL: Record<Trade, string> = {
  walls: "Walls", framing: "Framing", floors: "Floors", concrete: "Concrete",
  roof: "Roof", stairs: "Stairs", furniture: "Furniture",
};

type PanDirection = "left" | "right" | "up" | "down";

export function Panel3D() {
  const model = useStore((s) => s.model);
  const threeMode = useStore((s) => s.threeMode);
  const setThreeMode = useStore((s) => s.setThreeMode);
  const select = useStore((s) => s.select);
  const selection = useStore((s) => s.selection);
  const visibleTrades = useStore((s) => s.visibleTrades);
  const setTradeVisible = useStore((s) => s.setTradeVisible);
  const { theme } = useTheme();
  const mountRef = useRef<HTMLDivElement>(null);
  const api = useRef<SceneApi | null>(null);
  const renderedModel = useRef<Model | null>(null);
  const renderedTheme = useRef<string | null>(null);

  useEffect(() => {
    if (!mountRef.current) return;
    const a = createScene(mountRef.current, (uid) => select("wall", uid));
    api.current = a;
    return () => a.dispose();
  }, [select]);

  useEffect(() => {
    if (!model) return;
    const preserveView = renderedModel.current === model && renderedTheme.current !== null;
    api.current?.setModel(model, threeMode, RESOLVED_NORDIC_PALETTE[theme], preserveView);
    api.current?.highlight(selection.kind === "wall" ? selection.uid : null);
    renderedModel.current = model;
    renderedTheme.current = theme;
  }, [model, threeMode, theme]);

  useEffect(() => {
    api.current?.highlight(selection.kind === "wall" ? selection.uid : null);
  }, [selection]);

  useEffect(() => {
    for (const trade of ALL_TRADES) api.current?.setVisibility(trade, visibleTrades[trade]);
  }, [visibleTrades]);

  return (
    <div style={{ position: "absolute", inset: 0 }}>
      <div ref={mountRef} style={{ position: "absolute", inset: 0 }} />
      <div
        className="hud"
        aria-label="3D view navigation"
        style={{ bottom: 12, top: "auto", left: 12, right: "auto", display: "grid", gridTemplateColumns: "repeat(3, var(--hit))", gap: 4, padding: 4 }}
      >
        <span />
        <button className="seg-btn" aria-label="Pan view up" title="Pan up" onClick={() => api.current?.pan("up")}>↑</button>
        <span />
        <button className="seg-btn" aria-label="Pan view left" title="Pan left" onClick={() => api.current?.pan("left")}>←</button>
        <button className="seg-btn" aria-label="Reset 3D view" title="Reset view" onClick={() => api.current?.resetView()}>⌾</button>
        <button className="seg-btn" aria-label="Pan view right" title="Pan right" onClick={() => api.current?.pan("right")}>→</button>
        <span />
        <button className="seg-btn" aria-label="Pan view down" title="Pan down" onClick={() => api.current?.pan("down")}>↓</button>
        <span />
      </div>
      <div className="hud" style={{ bottom: "auto", top: 12, right: 12, left: "auto", display: "flex", gap: 6 }}>
        {(["nordic", "schematic"] as const).map((m) => (
          <button
            key={m}
            className={`seg-btn${threeMode === m ? " active" : ""}`}
            onClick={() => setThreeMode(m)}
          >
            {m}
          </button>
        ))}
      </div>
      <div className="hud" style={{ bottom: 12, top: "auto", right: 12, left: "auto", display: "flex", gap: 4, flexWrap: "wrap", maxWidth: 260 }}>
        {ALL_TRADES.map((trade) => (
          <button
            key={trade}
            className={`seg-btn${visibleTrades[trade] ? " active" : ""}`}
            onClick={() => setTradeVisible(trade, !visibleTrades[trade])}
            title={`Toggle ${TRADE_LABEL[trade]}`}
          >
            {TRADE_LABEL[trade]}
          </button>
        ))}
      </div>
    </div>
  );
}

interface SceneApi {
  setModel: (m: Model, mode: "nordic" | "schematic", palette: ResolvedNordicPalette, preserveView: boolean) => void;
  pan: (direction: PanDirection) => void;
  resetView: () => void;
  highlight: (uid: string | null) => void;
  setVisibility: (trade: Trade, visible: boolean) => void;
  dispose: () => void;
}

function createScene(mount: HTMLElement, onPick: (uid: string) => void): SceneApi {
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(RESOLVED_NORDIC_PALETTE.light.bg);
  const camera = new THREE.PerspectiveCamera(50, 1, 0.05, 500);
  const renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setPixelRatio(Math.min(2, window.devicePixelRatio));
  mount.appendChild(renderer.domElement);

  const content = new THREE.Group();
  scene.add(content);
  // One persistent THREE.Group per trade (→ WP7): created once, repopulated by setModel,
  // visibility flipped in place — never rebuilt, never re-created, so toggling a trade off
  // and back on costs nothing but a bool flip + one render.
  const tradeGroups = Object.fromEntries(
    ALL_TRADES.map((trade) => [trade, new THREE.Group()]),
  ) as Record<Trade, THREE.Group>;
  for (const trade of ALL_TRADES) content.add(tradeGroups[trade]);

  let picks: THREE.Mesh[] = [];
  const byUid = new Map<string, THREE.Material[]>();
  let highlighted: string | null = null;
  let activePalette = RESOLVED_NORDIC_PALETTE.light;

  // Lighting: soft neutral environment (Nordic). Hemisphere + a key light.
  const hemi = new THREE.HemisphereLight(0xffffff, 0xbcb6a8, 0.9);
  const key = new THREE.DirectionalLight(0xffffff, 0.7);
  key.position.set(4, 8, 6);
  scene.add(hemi, key);

  // Simple orbit: drag to rotate, wheel to dolly (no external controls dependency).
  let theta = Math.PI * 0.25;
  let phi = Math.PI * 0.32;
  let radius = 12;
  let target = new THREE.Vector3(0, 1, 0);
  let fittedTheta = theta;
  let fittedPhi = phi;
  let fittedRadius = radius;
  let fittedTarget = target.clone();
  let panStep = 1;
  let dragging = false;
  let last = [0, 0];

  const place = () => {
    camera.position.set(
      target.x + radius * Math.sin(phi) * Math.cos(theta),
      target.y + radius * Math.cos(phi),
      target.z + radius * Math.sin(phi) * Math.sin(theta),
    );
    camera.lookAt(target);
  };

  // Render-on-demand (Phase 1c): instead of an unconditional RAF loop pinning the GPU/CPU
  // while the scene is static, coalesce a single frame whenever something visibly changes —
  // orbit/dolly, resize, setModel, or a highlight toggle.
  let raf = 0;
  let renderPending = false;
  const requestRender = () => {
    if (renderPending) return;
    renderPending = true;
    raf = requestAnimationFrame(() => {
      renderPending = false;
      place();
      renderer.render(scene, camera);
    });
  };

  const el = renderer.domElement;
  const raycaster = new THREE.Raycaster();
  let downAt = [0, 0];
  el.style.touchAction = "none";
  el.addEventListener("pointerdown", (e) => {
    dragging = true;
    last = [e.clientX, e.clientY];
    downAt = [e.clientX, e.clientY];
    el.setPointerCapture(e.pointerId);
  });
  el.addEventListener("pointermove", (e) => {
    if (!dragging) return;
    theta -= (e.clientX - last[0]) * 0.008;
    phi = Math.min(Math.PI / 2 - 0.05, Math.max(0.1, phi - (e.clientY - last[1]) * 0.008));
    last = [e.clientX, e.clientY];
    requestRender();
  });
  el.addEventListener("pointerup", (e) => {
    dragging = false;
    // treat a near-zero drag as a click → raycast pick
    if (Math.hypot(e.clientX - downAt[0], e.clientY - downAt[1]) < 4) {
      const r = el.getBoundingClientRect();
      const ndc = new THREE.Vector2(
        ((e.clientX - r.left) / r.width) * 2 - 1,
        -((e.clientY - r.top) / r.height) * 2 + 1,
      );
      raycaster.setFromCamera(ndc, camera);
      const hit = raycaster.intersectObjects(picks, false)[0];
      const uid = hit?.object.userData.uid as string | undefined;
      if (uid) onPick(uid);
    }
  });
  el.addEventListener("wheel", (e) => {
    e.preventDefault();
    radius = Math.min(120, Math.max(2, radius * Math.exp(e.deltaY * 0.001)));
    requestRender();
  });

  const resize = () => {
    const w = mount.clientWidth || 1;
    const h = mount.clientHeight || 1;
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    requestRender();
  };
  const ro = new ResizeObserver(resize);
  ro.observe(mount);
  resize();

  // Dispose every mesh's geometry/material before dropping it — the previous version left
  // these leaking on every setModel() (content.clear() only detaches Object3Ds, it never
  // calls .dispose()).
  const clear = () => {
    for (const trade of ALL_TRADES) {
      disposeGroup(tradeGroups[trade]);
      tradeGroups[trade].clear();
    }
    picks = [];
    byUid.clear();
    highlighted = null;
  };

  const resetView = () => {
    theta = fittedTheta;
    phi = fittedPhi;
    radius = fittedRadius;
    target.copy(fittedTarget);
    requestRender();
  };

  const pan = (direction: PanDirection) => {
    // Translate the target in the camera's screen plane. place() refreshes its orientation
    // first so pan remains intuitive after orbiting, while the spherical camera offset stays
    // unchanged and therefore cannot alter the current rotation or zoom.
    place();
    const screenRight = new THREE.Vector3(1, 0, 0).applyQuaternion(camera.quaternion);
    const screenUp = new THREE.Vector3(0, 1, 0).applyQuaternion(camera.quaternion);
    const offset = direction === "left" ? screenRight.multiplyScalar(-panStep)
      : direction === "right" ? screenRight.multiplyScalar(panStep)
        : direction === "up" ? screenUp.multiplyScalar(panStep)
          : screenUp.multiplyScalar(-panStep);
    target.add(offset);
    requestRender();
  };

  const setModel = (m: Model, mode: "nordic" | "schematic", palette: ResolvedNordicPalette, preserveView: boolean) => {
    clear();
    activePalette = palette;
    scene.background = new THREE.Color(palette.bg);
    // Center on the plan's structural bounds.
    let cx = 0;
    let cz = 0;
    let n = 0;
    for (const w of m.walls)
      for (const p of w.axis) {
        cx += p[0];
        cz += p[1];
        n++;
      }
    if (n) {
      cx /= n;
      cz /= n;
    }
    if (!preserveView) target = new THREE.Vector3(0, 1.2, 0);

    for (const band of m.envelope_bands ?? []) buildEnvelopeBand(tradeGroups.walls, band, cx, cz, mode, palette);
    for (const w of m.walls) buildWall(tradeGroups, w, cx, cz, mode, palette, picks, byUid);
    for (const solid of m.solids ?? []) buildSolid(tradeGroups.concrete, solid, cx, cz, mode, palette);
    for (const floor of m.floors ?? []) buildFloor(tradeGroups.floors, floor, cx, cz, mode, palette);
    for (const roof of m.roofs ?? []) buildRoof(tradeGroups.roof, roof, cx, cz, mode, palette);
    for (const stair of m.stairs ?? []) buildStair(tradeGroups.stairs, stair, cx, cz, mode);
    for (const furniture of m.furniture ?? [])
      buildFurniture(tradeGroups.furniture, furniture, cx, cz, mode, palette,
        m.storeys.find((storey) => storey.tag === furniture.storey)?.elevation_m ?? 0);

    // Frame the full rendered bounds, including its vertical origin. The old target only
    // considered height, leaving models whose base was above zero visibly low in the canvas.
    const box = new THREE.Box3().setFromObject(content);
    if (!box.isEmpty() && !preserveView) {
      const sphere = box.getBoundingSphere(new THREE.Sphere());
      const verticalHalfFov = THREE.MathUtils.degToRad(camera.fov) / 2;
      const horizontalHalfFov = Math.atan(Math.tan(verticalHalfFov) * camera.aspect);
      const limitingHalfFov = Math.min(verticalHalfFov, horizontalHalfFov);
      theta = Math.PI * 0.25;
      phi = Math.PI * 0.32;
      radius = Math.max(2, sphere.radius / Math.sin(limitingHalfFov) * 1.15);
      target.copy(sphere.center);
      panStep = Math.max(0.2, sphere.radius * 0.3);
      fittedTheta = theta;
      fittedPhi = phi;
      fittedRadius = radius;
      fittedTarget.copy(target);
    }
    requestRender();
  };

  const highlight = (uid: string | null) => {
    if (highlighted && byUid.has(highlighted))
      for (const mat of byUid.get(highlighted)!)
        (mat as THREE.MeshStandardMaterial).emissive?.setHex(0x000000);
    highlighted = uid;
    if (uid && byUid.has(uid))
      for (const mat of byUid.get(uid)!)
        (mat as THREE.MeshStandardMaterial).emissive?.set(activePalette.highlight);
    requestRender();
  };

  const setVisibility = (trade: Trade, visible: boolean) => {
    tradeGroups[trade].visible = visible;
    requestRender();
  };

  return {
    setModel,
    pan,
    resetView,
    highlight,
    setVisibility,
    dispose: () => {
      cancelAnimationFrame(raf);
      ro.disconnect();
      for (const trade of ALL_TRADES) disposeGroup(tradeGroups[trade]);
      renderer.dispose();
      mount.removeChild(el);
    },
  };
}

function buildFurniture(
  parent: THREE.Group,
  furniture: NonNullable<Model["furniture"]>[number],
  cx: number,
  cz: number,
  mode: "nordic" | "schematic",
  palette: ResolvedNordicPalette,
  elevation: number,
) {
  const geometry = new THREE.BoxGeometry(
    furniture.footprint_m[0], furniture.height_m, furniture.footprint_m[1],
  );
  const material = new THREE.MeshStandardMaterial({
    color: palette.member.wood, roughness: mode === "nordic" ? 0.88 : 1, flatShading: mode === "schematic",
  });
  const mesh = new THREE.Mesh(geometry, material);
  mesh.position.set(furniture.position[0] - cx, elevation + furniture.height_m / 2,
    furniture.position[1] - cz);
  parent.add(mesh);
}

// A ToRoof wall's raked top elevation at a plan point, interpolated along the wall axis
// (mirrors emit/draw/section.py::_wall_top_at_cut). Falls back to the flat z1_m top for
// ordinary rectangular walls (top_z0_m/top_z1_m both null).
function rakedTopAt(w: Wall, x: number, y: number): number {
  if (w.top_z0_m == null && w.top_z1_m == null) return w.z1_m;
  const start = w.top_z0_m ?? w.z1_m;
  const end = w.top_z1_m ?? w.z1_m;
  const [[x0, y0], [x1, y1]] = w.axis;
  const dx = x1 - x0, dy = y1 - y0;
  const len2 = dx * dx + dy * dy;
  const t = len2 < 1e-9 ? 0 : Math.min(1, Math.max(0, ((x - x0) * dx + (y - y0) * dy) / len2));
  return start + (end - start) * t;
}

// Extrude a layer polygon between z0 and a per-vertex raked top (rather than a flat height) —
// a wall under a sloped roof (gable end, ToRoof) must stop at its actual rake, or its full
// bounding-height rectangle engulfs the roof geometry and hides it from outside (#WP-roof-hide).
function buildRakedLayerGeometry(
  polygon: [number, number][], z0: number, w: Wall, cx: number, cz: number,
): THREE.BufferGeometry {
  const n = polygon.length;
  const bottom = polygon.map(([x, y]) => new THREE.Vector3(x - cx, z0, y - cz));
  const top = polygon.map(([x, y]) => new THREE.Vector3(x - cx, rakedTopAt(w, x, y), y - cz));
  const positions: number[] = [];
  const pushTri = (a: THREE.Vector3, b: THREE.Vector3, c: THREE.Vector3) => {
    positions.push(a.x, a.y, a.z, b.x, b.y, b.z, c.x, c.y, c.z);
  };
  for (let i = 0; i < n; i++) {
    const j = (i + 1) % n;
    pushTri(bottom[i], bottom[j], top[j]);
    pushTri(bottom[i], top[j], top[i]);
  }
  for (let i = 1; i < n - 1; i++) {
    pushTri(bottom[0], bottom[i + 1], bottom[i]); // bottom cap (down-facing)
    pushTri(top[0], top[i], top[i + 1]); // top cap (up-facing)
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
  geo.computeVertexNormals();
  return geo;
}

function translatePlanRing(points: readonly [number, number][], cx: number, cz: number): [number, number][] {
  return points.map(([x, y]) => [x - cx, y - cz]);
}

// Build one wall: an extruded prism per layer polygon (→ "walls" trade) + its solid framing
// members (→ "framing" trade, WP8). World plan (x,y) maps to three (x, z); height runs
// along +Y. Centered on (cx,cz). Raked (ToRoof) walls extrude to their actual sloped top,
// not the flat bounding height, so the roof they carry stays visible from outside.
function buildWall(
  tradeGroups: Record<Trade, THREE.Group>,
  w: Wall,
  cx: number,
  cz: number,
  mode: "nordic" | "schematic",
  palette: ResolvedNordicPalette,
  picks: THREE.Mesh[],
  byUid: Map<string, THREE.Material[]>,
) {
  const raked = w.top_z0_m != null || w.top_z1_m != null;
  const h = Math.max(0.01, w.z1_m - w.z0_m);
  const mats: THREE.Material[] = [];
  for (const ly of w.layers) {
    if (ly.polygon.length < 3) continue;
    let geo: THREE.BufferGeometry;
    if (raked) {
      geo = buildRakedLayerGeometry(ly.polygon, w.z0_m, w, cx, cz);
    } else {
      const planPrism = createPlanPrismGeometry(translatePlanRing(ly.polygon, cx, cz), w.z0_m, w.z0_m + h);
      if (!planPrism) continue;
      geo = planPrism;
    }
    const mat = new THREE.MeshStandardMaterial({
      color: new THREE.Color(materialColor(ly.material, palette)),
      roughness: mode === "nordic" ? 0.85 : 1,
      metalness: 0,
      flatShading: mode === "schematic",
    });
    const mesh = new THREE.Mesh(geo, mat);
    mesh.userData.uid = w.uid;
    mesh.userData.tag = w.tag;
    tradeGroups.walls.add(mesh);
    picks.push(mesh);
    mats.push(mat);

    if (mode === "nordic") {
      const edges = new THREE.LineSegments(
        new THREE.EdgesGeometry(geo, 25),
        new THREE.LineBasicMaterial({ color: palette.edge, transparent: true, opacity: 0.35 }),
      );
      tradeGroups.walls.add(edges);
    }
  }
  buildMembers(tradeGroups.framing, w.members, cx, cz, mode);
  byUid.set(w.uid, mats);
}

function buildEnvelopeBand(parent: THREE.Group, band: EnvelopeBand, cx: number, cz: number,
  mode: "nordic" | "schematic", palette: ResolvedNordicPalette) {
  for (const layer of band.layers) {
    if (layer.polygon.length < 3) continue;
    const geometry = createPlanPrismGeometry(translatePlanRing(layer.polygon, cx, cz), band.z0_m, band.z1_m);
    if (!geometry) continue;
    parent.add(new THREE.Mesh(geometry, new THREE.MeshStandardMaterial({
      color: new THREE.Color(materialColor(layer.material, palette)), roughness: mode === "nordic" ? 0.85 : 1,
      flatShading: mode === "schematic",
    })));
  }
}


// Slabs, footings, pads: same outline-extrusion recipe as wall layers, concrete grey.
function buildSolid(parent: THREE.Group, solid: Solid, cx: number, cz: number,
  mode: "nordic" | "schematic", palette: ResolvedNordicPalette) {
  if (solid.outline.length < 3) return;
  const geo = createPlanPrismGeometry(translatePlanRing(solid.outline, cx, cz), solid.z0_m,
    Math.max(solid.z1_m, solid.z0_m + 0.01));
  if (!geo) return;
  const mat = new THREE.MeshStandardMaterial({
    color: palette.member.concrete, roughness: mode === "nordic" ? 0.9 : 1, flatShading: mode === "schematic",
  });
  parent.add(new THREE.Mesh(geo, mat));
}

function buildFloor(parent: THREE.Group, floor: Floor, cx: number, cz: number,
  mode: "nordic" | "schematic", palette: ResolvedNordicPalette) {
  if (floor.subfloor && floor.members.length) {
    const points = floor.members.flatMap((member) => [member.p0, member.p1]);
    const minX = Math.min(...points.map((point) => point[0]));
    const maxX = Math.max(...points.map((point) => point[0]));
    const minY = Math.min(...points.map((point) => point[1]));
    const maxY = Math.max(...points.map((point) => point[1]));
    const z = Math.max(...floor.members.map((member) => member.z1_m));
    const geometry = createPlanPrismGeometry(
      translatePlanRing([[minX, minY], [maxX, minY], [maxX, maxY], [minX, maxY]], cx, cz),
      z,
      z + floor.subfloor.thickness_m,
      floor.openings.map((opening) => translatePlanRing(opening, cx, cz)),
    );
    if (!geometry) return;
    parent.add(new THREE.Mesh(geometry, new THREE.MeshStandardMaterial({
      color: new THREE.Color(materialColor(floor.subfloor.material, palette)), roughness: mode === "nordic" ? 0.85 : 1,
      flatShading: mode === "schematic",
    })));
  }
  buildMembers(parent, floor.members, cx, cz, mode);
}

// Sloped quads from footprint/eave_z/ridge_z/ridge_direction — mirrors
// emit/gltf/emitter.py's _add_roof — plus the roof's own members (rafters, ridge beam).
function buildRoof(parent: THREE.Group, roof: Roof, cx: number, cz: number,
  mode: "nordic" | "schematic", palette: ResolvedNordicPalette) {
  const xs = roof.footprint.map((p) => p[0] - cx);
  const ys = roof.footprint.map((p) => p[1] - cz);
  const minx = Math.min(...xs), maxx = Math.max(...xs);
  const miny = Math.min(...ys), maxy = Math.max(...ys);
  const eave = roof.eave_z_m;
  const ridge = roof.ridge_z_m;
  const v = (x: number, y: number, z: number) => new THREE.Vector3(x, z, y);
  let triangles: THREE.Vector3[];
  if (roof.form === "shed") {
    triangles = roof.ridge_direction === "x"
      ? [v(minx, miny, eave), v(maxx, miny, eave), v(maxx, maxy, ridge),
         v(minx, miny, eave), v(maxx, maxy, ridge), v(minx, maxy, ridge)]
      : [v(minx, miny, eave), v(maxx, miny, ridge), v(maxx, maxy, ridge),
         v(minx, miny, eave), v(maxx, maxy, ridge), v(minx, maxy, eave)];
  } else if (roof.ridge_direction === "x") {
    const mid = (miny + maxy) / 2;
    const ra = v(minx, mid, ridge), rb = v(maxx, mid, ridge);
    triangles = [
      v(minx, miny, eave), v(maxx, miny, eave), rb,
      v(minx, miny, eave), rb, ra,
      ra, rb, v(maxx, maxy, eave),
      ra, v(maxx, maxy, eave), v(minx, maxy, eave),
    ];
  } else {
    const mid = (minx + maxx) / 2;
    const ra = v(mid, miny, ridge), rb = v(mid, maxy, ridge);
    triangles = [
      v(minx, miny, eave), ra, rb,
      v(minx, miny, eave), rb, v(minx, maxy, eave),
      ra, v(maxx, miny, eave), v(maxx, maxy, eave),
      ra, v(maxx, maxy, eave), rb,
    ];
  }
  const geo = new THREE.BufferGeometry().setFromPoints(triangles);
  geo.computeVertexNormals();
  const mat = new THREE.MeshStandardMaterial({
    color: palette.material.metal, roughness: mode === "nordic" ? 0.9 : 1, flatShading: mode === "schematic",
    transparent: true, opacity: 0.65, side: THREE.DoubleSide,
  });
  parent.add(new THREE.Mesh(geo, mat));
  buildMembers(parent, roof.members, cx, cz, mode);
}

function buildStair(parent: THREE.Group, stair: Stair, cx: number, cz: number,
  mode: "nordic" | "schematic") {
  buildMembers(parent, stair.members, cx, cz, mode);
}

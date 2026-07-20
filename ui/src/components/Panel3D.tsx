import { useEffect, useRef } from "react";
import * as THREE from "three";
import { ALL_TRADES, useStore, type Trade } from "../state/store";
import type { Model, Roof, Solid, Floor, Stair, Wall } from "../model/types";
import { materialColor, NORDIC_BG } from "../nordic/palette";
import { buildMembers, disposeGroup } from "../three/members";

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

export function Panel3D() {
  const model = useStore((s) => s.model);
  const threeMode = useStore((s) => s.threeMode);
  const setThreeMode = useStore((s) => s.setThreeMode);
  const select = useStore((s) => s.select);
  const selection = useStore((s) => s.selection);
  const visibleTrades = useStore((s) => s.visibleTrades);
  const setTradeVisible = useStore((s) => s.setTradeVisible);
  const mountRef = useRef<HTMLDivElement>(null);
  const api = useRef<SceneApi | null>(null);

  useEffect(() => {
    if (!mountRef.current) return;
    const a = createScene(mountRef.current, (uid) => select("wall", uid));
    api.current = a;
    return () => a.dispose();
  }, [select]);

  useEffect(() => {
    if (model) api.current?.setModel(model, threeMode);
  }, [model, threeMode]);

  useEffect(() => {
    api.current?.highlight(selection.kind === "wall" ? selection.uid : null);
  }, [selection]);

  useEffect(() => {
    for (const trade of ALL_TRADES) api.current?.setVisibility(trade, visibleTrades[trade]);
  }, [visibleTrades]);

  return (
    <div style={{ position: "absolute", inset: 0 }}>
      <div ref={mountRef} style={{ position: "absolute", inset: 0 }} />
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
  setModel: (m: Model, mode: "nordic" | "schematic") => void;
  highlight: (uid: string | null) => void;
  setVisibility: (trade: Trade, visible: boolean) => void;
  dispose: () => void;
}

function createScene(mount: HTMLElement, onPick: (uid: string) => void): SceneApi {
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(NORDIC_BG);
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

  const setModel = (m: Model, mode: "nordic" | "schematic") => {
    clear();
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
    target = new THREE.Vector3(0, 1.2, 0);

    for (const w of m.walls) buildWall(tradeGroups, w, cx, cz, mode, picks, byUid);
    for (const solid of m.solids ?? []) buildSolid(tradeGroups.concrete, solid, cx, cz, mode);
    for (const floor of m.floors ?? []) buildFloor(tradeGroups.floors, floor, cx, cz, mode);
    for (const roof of m.roofs ?? []) buildRoof(tradeGroups.roof, roof, cx, cz, mode);
    for (const stair of m.stairs ?? []) buildStair(tradeGroups.stairs, stair, cx, cz, mode);
    for (const furniture of m.furniture ?? [])
      buildFurniture(tradeGroups.furniture, furniture, cx, cz, mode,
        m.storeys.find((storey) => storey.tag === furniture.storey)?.elevation_m ?? 0);

    // frame the model
    const box = new THREE.Box3().setFromObject(content);
    const size = box.getSize(new THREE.Vector3());
    radius = Math.max(6, Math.max(size.x, size.z) * 1.4);
    target.y = size.y * 0.4;
    requestRender();
  };

  const highlight = (uid: string | null) => {
    if (highlighted && byUid.has(highlighted))
      for (const mat of byUid.get(highlighted)!)
        (mat as THREE.MeshStandardMaterial).emissive?.setHex(0x000000);
    highlighted = uid;
    if (uid && byUid.has(uid))
      for (const mat of byUid.get(uid)!)
        (mat as THREE.MeshStandardMaterial).emissive?.setHex(0x2a3d45);
    requestRender();
  };

  const setVisibility = (trade: Trade, visible: boolean) => {
    tradeGroups[trade].visible = visible;
    requestRender();
  };

  return {
    setModel,
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
  elevation: number,
) {
  const geometry = new THREE.BoxGeometry(
    furniture.footprint_m[0], furniture.height_m, furniture.footprint_m[1],
  );
  const material = new THREE.MeshStandardMaterial({
    color: 0x704c34, roughness: mode === "nordic" ? 0.88 : 1, flatShading: mode === "schematic",
  });
  const mesh = new THREE.Mesh(geometry, material);
  mesh.position.set(furniture.position[0] - cx, elevation + furniture.height_m / 2,
    furniture.position[1] - cz);
  parent.add(mesh);
}

// Build one wall: an extruded prism per layer polygon (→ "walls" trade) + its solid framing
// members (→ "framing" trade, WP8). World plan (x,y) maps to three (x, z); height runs
// along +Y. Centered on (cx,cz).
function buildWall(
  tradeGroups: Record<Trade, THREE.Group>,
  w: Wall,
  cx: number,
  cz: number,
  mode: "nordic" | "schematic",
  picks: THREE.Mesh[],
  byUid: Map<string, THREE.Material[]>,
) {
  const h = Math.max(0.01, w.z1_m - w.z0_m);
  const mats: THREE.Material[] = [];
  for (const ly of w.layers) {
    if (ly.polygon.length < 3) continue;
    const shape = new THREE.Shape();
    ly.polygon.forEach((p, i) => {
      const x = p[0] - cx;
      const y = p[1] - cz;
      if (i === 0) shape.moveTo(x, y);
      else shape.lineTo(x, y);
    });
    const geo = new THREE.ExtrudeGeometry(shape, { depth: h, bevelEnabled: false });
    geo.rotateX(-Math.PI / 2); // shape XY plane → ground XZ, extrude → +Y
    geo.translate(0, w.z0_m, 0);
    const mat = new THREE.MeshStandardMaterial({
      color: new THREE.Color(materialColor(ly.material)),
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
        new THREE.LineBasicMaterial({ color: 0x4a463d, transparent: true, opacity: 0.35 }),
      );
      tradeGroups.walls.add(edges);
    }
  }
  buildMembers(tradeGroups.framing, w.members, cx, cz, mode);
  byUid.set(w.uid, mats);
}

// Slabs, footings, pads: same outline-extrusion recipe as wall layers, concrete grey.
function buildSolid(parent: THREE.Group, solid: Solid, cx: number, cz: number,
  mode: "nordic" | "schematic") {
  if (solid.outline.length < 3) return;
  const shape = new THREE.Shape();
  solid.outline.forEach((p, i) => {
    const x = p[0] - cx;
    const y = p[1] - cz;
    if (i === 0) shape.moveTo(x, y);
    else shape.lineTo(x, y);
  });
  const h = Math.max(0.01, solid.z1_m - solid.z0_m);
  const geo = new THREE.ExtrudeGeometry(shape, { depth: h, bevelEnabled: false });
  geo.rotateX(-Math.PI / 2);
  geo.translate(0, solid.z0_m, 0);
  const mat = new THREE.MeshStandardMaterial({
    color: 0x9a9a96, roughness: mode === "nordic" ? 0.9 : 1, flatShading: mode === "schematic",
  });
  parent.add(new THREE.Mesh(geo, mat));
}

// Floors have no deck surface of their own in the resolved model — just joists + rim
// boards; render those into the "floors" trade so they're hideable for stair continuity.
function buildFloor(parent: THREE.Group, floor: Floor, cx: number, cz: number,
  mode: "nordic" | "schematic") {
  buildMembers(parent, floor.members, cx, cz, mode);
}

// Sloped quads from footprint/eave_z/ridge_z/ridge_direction — mirrors
// emit/gltf/emitter.py's _add_roof — plus the roof's own members (rafters, ridge beam).
function buildRoof(parent: THREE.Group, roof: Roof, cx: number, cz: number,
  mode: "nordic" | "schematic") {
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
    color: 0x595d63, roughness: mode === "nordic" ? 0.9 : 1, flatShading: mode === "schematic",
    transparent: true, opacity: 0.65, side: THREE.DoubleSide,
  });
  parent.add(new THREE.Mesh(geo, mat));
  buildMembers(parent, roof.members, cx, cz, mode);
}

function buildStair(parent: THREE.Group, stair: Stair, cx: number, cz: number,
  mode: "nordic" | "schematic") {
  buildMembers(parent, stair.members, cx, cz, mode);
}

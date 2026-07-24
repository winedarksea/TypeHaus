import { useEffect, useRef } from "react";
import * as THREE from "three";
import { RoomEnvironment } from "three/examples/jsm/environments/RoomEnvironment.js";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
import { ALL_TRADES, useStore, type Trade } from "../state/store";
import type { CanvasObject, CanvasObjectType, Catalog, Model, Opening, Roof, Solid, Floor, Stair, Wall } from "../model/types";
import { materialColor, RESOLVED_NORDIC_PALETTE, type ResolvedNordicPalette } from "../nordic/palette";
import { buildMembers, disposeGroup } from "../three/members";
import { applyStandingSeamWallUv, createStandingSeamMaterial, isStandingSeam } from "../three/materials";
import { aboveStructureLayers, boundaryEdges, roofOffsetter, roofPlaneTriangles } from "../three/roofGeometry";
import {
  createPlanPrismGeometry,
  createProjectedSurfaceGeometry,
  createRakedPlanPrismGeometry,
  projectPointToScene,
  type PlanCenter,
  type ProjectVertex,
} from "../three/planGeometry";
import { useTheme } from "../theme/theme";

// The 3D panel behind an implicit ModelViewer seam (→ 21 §3D panel). The primary path is
// glTF from ResolvedModel; until the server emits it, this builds an equivalent scene
// directly from model.json (extruded wall/solid/roof surfaces + solid instanced framing
// members), which is always available and guarantees the 3D view shows exactly what the
// resolver computed. The Nordic passes (soft lighting + edge linework) attach to the
// three.js scene, so they survive the eventual glTF route unchanged. Clicking a wall
// cross-highlights the 2D plan and surfaces its file:line provenance.

export const EARTH_PLANE_OPACITY = 0.28;
export const EARTH_PLANE_THICKNESS_M = 0.01;
export const EARTH_FALLBACK_HALF_SIZE_M = 50;

type PanDirection = "left" | "right" | "up" | "down";

export function Panel3D() {
  const model = useStore((s) => s.model);
  const threeMode = useStore((s) => s.threeMode);
  const select = useStore((s) => s.select);
  const selection = useStore((s) => s.selection);
  const visibleTrades = useStore((s) => s.visibleTrades);
  const { theme } = useTheme();
  const mountRef = useRef<HTMLDivElement>(null);
  const api = useRef<SceneApi | null>(null);
  const renderedModel = useRef<Model | null>(null);
  const renderedTheme = useRef<string | null>(null);

  useEffect(() => {
    if (!mountRef.current) return;
    const a = createScene(mountRef.current, (kind, uid) => select(kind, uid));
    api.current = a;
    return () => a.dispose();
  }, [select]);

  useEffect(() => {
    api.current?.setPalette(RESOLVED_NORDIC_PALETTE[theme]);
  }, [theme]);

  useEffect(() => {
    if (!model) return;
    const preserveView = renderedModel.current === model && renderedTheme.current !== null;
    api.current?.setModel(model, threeMode, RESOLVED_NORDIC_PALETTE[theme], preserveView);
    api.current?.highlight(selection.kind === "wall" || selection.kind === "canvas_object" ? selection.uid : null);
    renderedModel.current = model;
    renderedTheme.current = theme;
  }, [model, threeMode, theme]);

  useEffect(() => {
    api.current?.highlight(selection.kind === "wall" || selection.kind === "canvas_object" ? selection.uid : null);
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
      {/* Nordic/schematic switch + discipline toggles now live in the shared Views panel
          (Phase 6), reachable from the view-chip bar. */}
    </div>
  );
}

interface SceneApi {
  setModel: (m: Model, mode: "nordic" | "schematic", palette: ResolvedNordicPalette, preserveView: boolean) => void;
  setPalette: (palette: ResolvedNordicPalette) => void;
  pan: (direction: PanDirection) => void;
  resetView: () => void;
  highlight: (uid: string | null) => void;
  setVisibility: (trade: Trade, visible: boolean) => void;
  dispose: () => void;
}

function createScene(mount: HTMLElement, onPick: (kind: "wall" | "canvas_object", uid: string) => void): SceneApi {
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(RESOLVED_NORDIC_PALETTE.light.bg);
  const camera = new THREE.PerspectiveCamera(50, 1, 0.05, 500);
  const renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setPixelRatio(Math.min(2, window.devicePixelRatio));
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
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
  let sceneGeneration = 0;
  const byUid = new Map<string, THREE.Material[]>();
  let highlighted: string | null = null;
  let activePalette = RESOLVED_NORDIC_PALETTE.light;

  // Lighting: soft neutral environment (Nordic). Hemisphere + a key light.
  const hemi = new THREE.HemisphereLight(0xffffff, 0xbcb6a8, 0.9);
  const key = new THREE.DirectionalLight(0xffffff, 0.7);
  key.position.set(4, 8, 6);
  key.castShadow = true;
  key.shadow.bias = -0.0001;
  key.shadow.mapSize.set(2048, 2048);
  scene.add(hemi, key, key.target);

  // Painted metal is only metal if there is something to reflect. RoomEnvironment ships
  // inside the `three` package, so the PWA keeps working offline — no HDRI download.
  const pmrem = new THREE.PMREMGenerator(renderer);
  const environment = pmrem.fromScene(new RoomEnvironment(), 0.04);
  scene.environment = environment.texture;

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
      const kind = hit?.object.userData.selectionKind as "wall" | "canvas_object" | undefined;
      if (uid && kind) onPick(kind, uid);
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
    sceneGeneration++;
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

    const center: PlanCenter = [cx, cz];
    for (const w of m.walls) {
      const wallOpenings = m.openings.filter((opening) => opening.host === w.tag);
      buildWall(tradeGroups, w, wallOpenings, center, mode, palette, picks, byUid);
      for (const opening of wallOpenings) {
        const isDoubleSwing = m.catalog?.door_types.find((dt) => dt.tag === opening.type_ref)?.operation === "double_swing";
        buildOpening(tradeGroups.openings, opening, w, center, mode, palette, isDoubleSwing);
      }
    }
    buildEarth(tradeGroups.earth, m, center, mode);
    for (const solid of m.solids ?? []) buildSolid(tradeGroups.concrete, solid, center, mode, palette);
    for (const floor of m.floors ?? []) buildFloor(tradeGroups.floors, floor, center, mode, palette);
    for (const roof of m.roofs ?? []) buildRoof(tradeGroups.roof, roof, center, mode, palette, m.catalog);
    for (const stair of m.stairs ?? []) buildStair(tradeGroups.stairs, stair, center, mode);
    const types = new Map((m.catalog?.canvas_object_types ?? []).map((type) => [type.tag, type]));
    for (const item of m.canvas_objects ?? []) {
      // Hosted openings retain their dedicated cut/fill meshes above. The normalized
      // record is for shared inspection and interchange, not a second 3D proxy.
      if (item.domain === "opening") continue;
      if (!item.position_m) continue;
      const group = item.domain === "plumbing" ? tradeGroups.plumbing
        : item.domain === "electrical" ? tradeGroups.electrical
          : item.domain === "mechanical" ? tradeGroups.mechanical : tradeGroups.furniture;
      const type = types.get(item.type ?? "");
      const fallback = buildCanvasObject(group, item, type, center, mode, palette,
        item.z_m ?? m.storeys.find((storey) => storey.tag === item.storey)?.elevation_m ?? 0, picks, byUid);
      if (type?.model_glb && fallback) {
        const generation = sceneGeneration;
        new GLTFLoader().load(type.model_glb, (gltf) => {
          if (generation !== sceneGeneration || !item.position_m) {
            disposeGroup(gltf.scene);
            return;
          }
          group.remove(fallback);
          fallback.geometry.dispose();
          (fallback.material as THREE.Material).dispose();
          picks = picks.filter((mesh) => mesh !== fallback);
          const visual = gltf.scene;
          visual.position.copy(projectPointToScene(item.position_m,
            item.z_m ?? m.storeys.find((storey) => storey.tag === item.storey)?.elevation_m ?? 0, center));
          visual.rotation.y = -((item.rotation ?? 0) * Math.PI / 180);
          const materials: THREE.Material[] = [];
          visual.traverse((node) => {
            if (!(node instanceof THREE.Mesh)) return;
            node.castShadow = true;
            node.receiveShadow = true;
            node.userData.uid = item.uid;
            node.userData.selectionKind = "canvas_object";
            picks.push(node);
            const material = node.material;
            materials.push(...(Array.isArray(material) ? material : [material]));
          });
          byUid.set(item.uid, materials);
          group.add(visual);
          requestRender();
        });
      }
    }

    // Frame the full rendered bounds, including its vertical origin. The old target only
    // considered height, leaving models whose base was above zero visibly low in the canvas.
    const box = new THREE.Box3().setFromObject(content);
    if (!box.isEmpty()) {
      // Fit the sun's orthographic shadow frustum to the building, otherwise the default
      // 5m box clips every house and the shadow map resolution is wasted on empty space.
      const bounds = box.getBoundingSphere(new THREE.Sphere());
      const cam = key.shadow.camera;
      cam.left = -bounds.radius; cam.right = bounds.radius;
      cam.top = bounds.radius; cam.bottom = -bounds.radius;
      cam.near = 0.1; cam.far = bounds.radius * 6;
      cam.updateProjectionMatrix();
      key.target.position.copy(bounds.center);
      key.position.copy(bounds.center).add(
        new THREE.Vector3(0.6, 1.1, 0.45).normalize().multiplyScalar(bounds.radius * 2.5),
      );
      key.target.updateMatrixWorld();
    }
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

  const setPalette = (palette: ResolvedNordicPalette) => {
    activePalette = palette;
    scene.background = new THREE.Color(palette.bg);
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
    setPalette,
    pan,
    resetView,
    highlight,
    setVisibility,
    dispose: () => {
      cancelAnimationFrame(raf);
      ro.disconnect();
      for (const trade of ALL_TRADES) disposeGroup(tradeGroups[trade]);
      environment.dispose();
      pmrem.dispose();
      renderer.dispose();
      mount.removeChild(el);
    },
  };
}

export function earthOutline(model: Model, center: PlanCenter): [number, number][] {
  const parcel = model.site?.parcel;
  if (parcel && parcel.length >= 3) return parcel.map(([x, y]) => [x, y]);
  const [cx, cz] = center;
  const half = EARTH_FALLBACK_HALF_SIZE_M;
  return [[cx - half, cz - half], [cx + half, cz - half],
    [cx + half, cz + half], [cx - half, cz + half]];
}

export function earthElevation(model: Model): number {
  return model.site?.grade_m ?? 0;
}

function buildEarth(parent: THREE.Group, model: Model, center: PlanCenter, mode: "nordic" | "schematic") {
  const outline = earthOutline(model, center);
  const grade = earthElevation(model);
  const geometry = createPlanPrismGeometry(
    outline, grade - EARTH_PLANE_THICKNESS_M, grade,
    [], center,
  );
  if (!geometry) return;
  const material = new THREE.MeshStandardMaterial({
    color: 0x806040,
    transparent: true,
    opacity: EARTH_PLANE_OPACITY,
    depthWrite: false,
    side: THREE.DoubleSide,
    roughness: mode === "nordic" ? 0.95 : 1,
    flatShading: mode === "schematic",
  });
  parent.add(new THREE.Mesh(geometry, material));
}

function buildCanvasObject(
  parent: THREE.Group,
  item: CanvasObject,
  type: CanvasObjectType | undefined,
  center: PlanCenter,
  mode: "nordic" | "schematic",
  palette: ResolvedNordicPalette,
  elevation: number,
  picks: THREE.Mesh[],
  byUid: Map<string, THREE.Material[]>,
): THREE.Mesh | null {
  if (!item.position_m) return null;
  const [width, depth] = type?.footprint_m ?? [0.45, 0.45];
  const height = type?.height_m ?? 0.25;
  const color = item.domain === "electrical" ? 0xd69e2e
    : item.domain === "plumbing" ? 0x4299e1 : item.domain === "mechanical" ? 0x718096 : palette.member.wood;
  const material = new THREE.MeshStandardMaterial({ color, roughness: mode === "nordic" ? 0.82 : 1,
    flatShading: mode === "schematic" });
  // Keep a configured primitive visible while a potentially large GLB loads.
  const mesh = new THREE.Mesh(canvasObjectFallbackGeometry(
    item.model_primitive ?? type?.model_primitive, width, height, depth,
  ), material);
  mesh.position.copy(projectPointToScene(item.position_m, elevation + height / 2, center));
  mesh.rotation.y = -((item.rotation ?? 0) * Math.PI / 180);
  mesh.userData.uid = item.uid;
  mesh.userData.selectionKind = "canvas_object";
  parent.add(mesh);
  picks.push(mesh);
  byUid.set(item.uid, [material]);
  return mesh;
}

export function canvasObjectFallbackGeometry(
  primitive: string | null | undefined,
  width: number,
  height: number,
  depth: number,
): THREE.BufferGeometry {
  switch (primitive?.toLowerCase()) {
    case "cylinder":
      return new THREE.CylinderGeometry(Math.max(width, depth) / 2, Math.max(width, depth) / 2, height, 24);
    case "sphere":
      return new THREE.SphereGeometry(Math.max(width, height, depth) / 2, 24, 16);
    default:
      return new THREE.BoxGeometry(width, height, depth);
  }
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
// Build one wall: an extruded prism per layer polygon (→ "walls" trade) + its solid framing
// members (→ "framing" trade, WP8). World plan (x,y) maps to three (x, z); height runs
// along +Y. Centered on (cx,cz). Raked (ToRoof) walls extrude to their actual sloped top,
// not the flat bounding height, so the roof they carry stays visible from outside.
function buildWall(
  tradeGroups: Record<Trade, THREE.Group>,
  w: Wall,
  openings: Opening[],
  center: PlanCenter,
  mode: "nordic" | "schematic",
  palette: ResolvedNordicPalette,
  picks: THREE.Mesh[],
  byUid: Map<string, THREE.Material[]>,
) {
  const mats: THREE.Material[] = [];
  for (const ly of w.layers) {
    if (ly.polygon.length < 3) continue;
    // Cavity fill shares its host structure layer's polygon — extruding it would only
    // z-fight with the studs it lives between.
    if (ly.is_cavity) continue;
    const seam = ly.function === "cladding" && isStandingSeam(ly.material);
    const mat = seam
      ? createStandingSeamMaterial(mode, [
        Math.hypot(w.axis[1][0] - w.axis[0][0], w.axis[1][1] - w.axis[0][1]),
        Math.max(0.1, w.z1_m - w.z0_m),
      ], 0xE8E8E2, true)
      : new THREE.MeshStandardMaterial({
        color: new THREE.Color(materialColor(ly.material, palette)),
        roughness: mode === "nordic" ? 0.85 : 1,
        metalness: 0,
        flatShading: mode === "schematic",
      });
    mats.push(mat);
    for (const piece of wallLayerPieces(w, ly.polygon, openings)) {
      let geo: THREE.BufferGeometry | null;
      if (piece.topIsRaked) {
        geo = createRakedPlanPrismGeometry(piece.polygon, piece.z0_m,
          (point) => rakedTopAt(w, point[0], point[1]), center);
      } else {
        geo = createPlanPrismGeometry(piece.polygon, piece.z0_m, piece.z1_m, [], center);
      }
      if (!geo) continue;
      if (seam) applyStandingSeamWallUv(geo, w.axis, center);
      const mesh = new THREE.Mesh(geo, mat);
      mesh.castShadow = true;
      mesh.receiveShadow = true;
      mesh.userData.uid = w.uid;
      mesh.userData.selectionKind = "wall";
      mesh.userData.tag = w.tag;
      tradeGroups.walls.add(mesh);
      picks.push(mesh);

      if (mode === "nordic") {
        tradeGroups.walls.add(new THREE.LineSegments(
          new THREE.EdgesGeometry(geo, 25),
          new THREE.LineBasicMaterial({ color: palette.edge, transparent: true, opacity: 0.35 }),
        ));
      }
    }
  }
  buildMembers(tradeGroups.framing, w.members, center, mode);
  byUid.set(w.uid, mats);
}

export interface WallLayerPiece {
  polygon: [number, number][];
  z0_m: number;
  z1_m: number;
  topIsRaked: boolean;
}

// Split an arbitrary junction-solved layer polygon at opening jamb stations. Clipping the
// actual ring (instead of rebuilding its local bounds) preserves mitered and butted ends.
export function wallLayerPieces(wall: Wall, polygon: readonly [number, number][], openings: Opening[]): WallLayerPiece[] {
  const [[x0, y0], [x1, y1]] = wall.axis;
  const length = Math.hypot(x1 - x0, y1 - y0);
  if (length < 1e-9 || polygon.length < 3) return [];
  const direction: [number, number] = [(x1 - x0) / length, (y1 - y0) / length];
  const normal: [number, number] = [-direction[1], direction[0]];
  const local = polygon.map(([x, y]) => {
    const px = x - x0, py = y - y0;
    return [px * direction[0] + py * direction[1], px * normal[0] + py * normal[1]] as const;
  });
  const minAlong = Math.min(...local.map(([along]) => along));
  const maxAlong = Math.max(...local.map(([along]) => along));
  const relevant = openings.map((opening) => ({
    opening,
    start: Math.max(minAlong, opening.center_along_m - opening.width_m / 2),
    end: Math.min(maxAlong, opening.center_along_m + opening.width_m / 2),
  })).filter(({ start, end }) => end - start > 1e-9);
  const boundaries = Array.from(new Set([minAlong, maxAlong, ...relevant.flatMap(({ start, end }) => [start, end])]))
    .sort((a, b) => a - b);
  const point = (along: number, across: number): [number, number] => [
    x0 + direction[0] * along + normal[0] * across,
    y0 + direction[1] * along + normal[1] * across,
  ];
  const clip = (
    ring: readonly (readonly [number, number])[],
    boundary: number,
    keepGreater: boolean,
  ): [number, number][] => {
    const output: [number, number][] = [];
    const inside = ([along]: readonly [number, number]) =>
      keepGreater ? along >= boundary - 1e-9 : along <= boundary + 1e-9;
    for (let index = 0; index < ring.length; index++) {
      const current = ring[index], next = ring[(index + 1) % ring.length];
      const currentInside = inside(current), nextInside = inside(next);
      if (currentInside) output.push([current[0], current[1]]);
      if (currentInside !== nextInside) {
        const denominator = next[0] - current[0];
        if (Math.abs(denominator) > 1e-12) {
          const fraction = (boundary - current[0]) / denominator;
          output.push([boundary, current[1] + (next[1] - current[1]) * fraction]);
        }
      }
    }
    return output;
  };
  const ring = (start: number, end: number): [number, number][] =>
    clip(clip(local, start, true), end, false).map(([along, across]) => point(along, across));
  const raked = wall.top_z0_m != null || wall.top_z1_m != null;
  const pieces: WallLayerPiece[] = [];
  for (let index = 0; index < boundaries.length - 1; index++) {
    const start = boundaries[index], end = boundaries[index + 1];
    const active = relevant.find(({ start: openingStart, end: openingEnd }) =>
      (start + end) / 2 >= openingStart && (start + end) / 2 <= openingEnd)?.opening;
    const strip = ring(start, end);
    if (strip.length < 3) continue;
    if (!active) {
      pieces.push({ polygon: strip, z0_m: wall.z0_m, z1_m: wall.z1_m, topIsRaked: raked });
      continue;
    }
    const openingBottom = wall.z0_m + active.sill_m;
    const openingTop = openingBottom + active.height_m;
    if (openingBottom > wall.z0_m + 1e-9)
      pieces.push({ polygon: strip, z0_m: wall.z0_m, z1_m: openingBottom, topIsRaked: false });
    const minTop = Math.min(...strip.map(([x, y]) => rakedTopAt(wall, x, y)));
    if (minTop > openingTop + 1e-9)
      pieces.push({ polygon: strip, z0_m: openingTop, z1_m: wall.z1_m, topIsRaked: raked });
  }
  return pieces;
}

function buildOpening(parent: THREE.Group, opening: Opening, wall: Wall, center: PlanCenter,
  mode: "nordic" | "schematic", palette: ResolvedNordicPalette, isDoubleSwing: boolean) {
  if (opening.kind === "rough_opening") return;
  const [[x0, y0], [x1, y1]] = wall.axis;
  const length = Math.hypot(x1 - x0, y1 - y0);
  if (length < 1e-9) return;
  const direction: [number, number] = [(x1 - x0) / length, (y1 - y0) / length];
  const position: [number, number] = [x0 + direction[0] * opening.center_along_m, y0 + direction[1] * opening.center_along_m];
  const availableHeight = Math.max(0, Math.min(opening.height_m,
    rakedTopAt(wall, x0 + direction[0] * (opening.center_along_m - opening.width_m / 2), y0 + direction[1] * (opening.center_along_m - opening.width_m / 2)) - wall.z0_m - opening.sill_m,
    rakedTopAt(wall, x0 + direction[0] * (opening.center_along_m + opening.width_m / 2), y0 + direction[1] * (opening.center_along_m + opening.width_m / 2)) - wall.z0_m - opening.sill_m));
  if (availableHeight <= 1e-9) return;
  const rotation = -Math.atan2(direction[1], direction[0]);
  const frameWidth = Math.min(0.075, opening.width_m / 4, availableHeight / 4);
  const depth = 0.08;
  const frameMaterial = new THREE.MeshStandardMaterial({ color: palette.member.wood, roughness: mode === "nordic" ? 0.85 : 1, flatShading: mode === "schematic" });
  const addBox = (width: number, height: number, thickness: number, along: number, elevation: number, material: THREE.Material) => {
    const mesh = new THREE.Mesh(new THREE.BoxGeometry(width, height, thickness), material);
    mesh.position.copy(projectPointToScene([position[0] + direction[0] * along, position[1] + direction[1] * along], elevation, center));
    mesh.rotation.y = rotation;
    parent.add(mesh);
  };
  const midElevation = wall.z0_m + opening.sill_m + availableHeight / 2;
  addBox(frameWidth, availableHeight, depth, -opening.width_m / 2 + frameWidth / 2, midElevation, frameMaterial);
  addBox(frameWidth, availableHeight, depth, opening.width_m / 2 - frameWidth / 2, midElevation, frameMaterial);
  addBox(opening.width_m, frameWidth, depth, 0, wall.z0_m + opening.sill_m + availableHeight - frameWidth / 2, frameMaterial);
  addBox(opening.width_m, frameWidth, depth, 0, wall.z0_m + opening.sill_m + frameWidth / 2, frameMaterial);
  const panelHeight = Math.max(0.01, availableHeight - 2 * frameWidth);
  if (opening.kind === "door" && isDoubleSwing) {
    // Two leaves meeting at a center mullion, matching the 2D French-door symbol.
    const mullionWidth = Math.min(frameWidth, (opening.width_m - 2 * frameWidth) / 6);
    const leafWidth = Math.max(0.01, (opening.width_m - 2 * frameWidth - mullionWidth) / 2);
    const panelElevation = wall.z0_m + opening.sill_m + frameWidth + panelHeight / 2;
    addBox(mullionWidth, availableHeight, depth, 0, midElevation, frameMaterial);
    addBox(leafWidth, panelHeight, 0.045, -mullionWidth / 2 - leafWidth / 2, panelElevation, frameMaterial);
    addBox(leafWidth, panelHeight, 0.045, mullionWidth / 2 + leafWidth / 2, panelElevation, frameMaterial);
  } else if (opening.kind === "door") {
    addBox(Math.max(0.01, opening.width_m - 2 * frameWidth), panelHeight, 0.045, 0,
      wall.z0_m + opening.sill_m + frameWidth + panelHeight / 2, frameMaterial);
  } else {
    const glassMaterial = new THREE.MeshStandardMaterial({ color: 0x8fb7c9, transparent: true, opacity: 0.48,
      roughness: 0.2, metalness: 0.05, flatShading: mode === "schematic", depthWrite: false });
    addBox(Math.max(0.01, opening.width_m - 2 * frameWidth), panelHeight, 0.015, 0,
      wall.z0_m + opening.sill_m + frameWidth + panelHeight / 2, glassMaterial);
  }
}

// Slabs, footings, pads: same outline-extrusion recipe as wall layers, concrete grey.
function buildSolid(parent: THREE.Group, solid: Solid, center: PlanCenter,
  mode: "nordic" | "schematic", palette: ResolvedNordicPalette) {
  if (solid.outline.length < 3) return;
  const geo = createPlanPrismGeometry(solid.outline, solid.z0_m, Math.max(solid.z1_m, solid.z0_m + 0.01), solid.voids ?? [], center);
  if (!geo) return;
  const mat = new THREE.MeshStandardMaterial({
    color: palette.member.concrete, roughness: mode === "nordic" ? 0.9 : 1, flatShading: mode === "schematic",
  });
  parent.add(new THREE.Mesh(geo, mat));
}

function buildFloor(parent: THREE.Group, floor: Floor, center: PlanCenter,
  mode: "nordic" | "schematic", palette: ResolvedNordicPalette) {
  if (floor.subfloor && floor.members.length) {
    const points = floor.members.flatMap((member) => [member.p0, member.p1]);
    const minX = Math.min(...points.map((point) => point[0]));
    const maxX = Math.max(...points.map((point) => point[0]));
    const minY = Math.min(...points.map((point) => point[1]));
    const maxY = Math.max(...points.map((point) => point[1]));
    const z = Math.max(...floor.members.map((member) => member.z1_m));
    const geometry = createPlanPrismGeometry(
      [[minX, minY], [maxX, minY], [maxX, maxY], [minX, maxY]],
      z,
      z + floor.subfloor.thickness_m,
      floor.openings,
      center,
    );
    if (!geometry) return;
    parent.add(new THREE.Mesh(geometry, new THREE.MeshStandardMaterial({
      color: new THREE.Color(materialColor(floor.subfloor.material, palette)), roughness: mode === "nordic" ? 0.85 : 1,
      flatShading: mode === "schematic",
    })));
  }
  buildMembers(parent, floor.members, center, mode);
}

// Sloped quads from footprint/eave_z/ridge_z/ridge_direction — mirrors
// emit/gltf/emitter.py's _add_roof — thickened into the authored assembly, plus the
// roof's own members (rafters, ridge beam).
function buildRoof(parent: THREE.Group, roof: Roof, center: PlanCenter,
  mode: "nordic" | "schematic", palette: ResolvedNordicPalette, catalog?: Catalog) {
  const triangles = roofPlaneTriangles(roof);
  const offsetAt = roofOffsetter(triangles);
  const perimeter = boundaryEdges(triangles);
  const assembly = catalog?.assemblies.find((a) => a.tag === roof.assembly);
  // eave_z_m/ridge_z_m is the rafter *top*, so the stack starts at zero and grows up.
  const layers = aboveStructureLayers(assembly);
  const stack = layers.length ? layers
    : [{ name: "roofing", function: "cladding", material: "standing-seam", thickness_m: 0.05 }];

  let base = 0;
  for (const layer of stack) {
    const top = base + layer.thickness_m;
    const faces: ProjectVertex[][] = [];
    for (const tri of triangles) {
      faces.push([offsetAt(tri[0], top), offsetAt(tri[1], top), offsetAt(tri[2], top)]);
      faces.push([offsetAt(tri[0], base), offsetAt(tri[2], base), offsetAt(tri[1], base)]);
    }
    // Close the eave and rake so the layer stack reads as real thickness from outside.
    for (const [a, b] of perimeter) {
      faces.push([offsetAt(a, base), offsetAt(b, base), offsetAt(b, top)]);
      faces.push([offsetAt(a, base), offsetAt(b, top), offsetAt(a, top)]);
    }
    const geo = createProjectedSurfaceGeometry(faces, center);
    const seam = layer.function === "cladding" && isStandingSeam(layer.material);
    const mat = seam
      ? createStandingSeamMaterial(mode, [Math.sqrt(roof.surface_area_m2), Math.sqrt(roof.surface_area_m2)])
      : new THREE.MeshStandardMaterial({
        color: new THREE.Color(materialColor(layer.material, palette)),
        roughness: mode === "nordic" ? 0.9 : 1,
        flatShading: mode === "schematic",
        side: THREE.DoubleSide,
      });
    const mesh = new THREE.Mesh(geo, mat);
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    parent.add(mesh);
    base = top;
  }
  buildMembers(parent, roof.members, center, mode);
}

function buildStair(parent: THREE.Group, stair: Stair, center: PlanCenter,
  mode: "nordic" | "schematic") {
  buildMembers(parent, stair.members, center, mode);
}

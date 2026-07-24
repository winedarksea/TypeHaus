import { useEffect, useRef } from "react";
import * as THREE from "three";
import { RoomEnvironment } from "three/examples/jsm/environments/RoomEnvironment.js";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
import { ALL_SELECTION_KINDS, ALL_TRADES, useStore, type SelectionKind, type Trade } from "../state/store";
import type { CanvasObject, CanvasObjectType, Catalog, FootingBedding, MaterialSpec, Model, Opening, Roof, Solid, Floor, Stair, Wall } from "../model/types";
import { authoredAppearance, materialColor, RESOLVED_NORDIC_PALETTE, type ResolvedNordicPalette } from "../nordic/palette";
import { buildMembers, disposeGroup } from "../three/members";
import { createSolidMaterial } from "../three/solidMaterials";
import { applyDeckBoardUv, applyMasonryWallUv, applyStandingSeamWallUv, createDeckBoardMaterial, createMasonryMaterial, createStandingSeamMaterial, isAluminumDeckBoard, isMasonry, isStandingSeam, masonryStyleFor, masonryTileSizeM } from "../three/materials";
import { aboveStructureLayers, boundaryEdges, roofOffsetter, roofPlaneTriangles } from "../three/roofGeometry";
import {
  createPlanPrismGeometry,
  createProjectedSurfaceGeometry,
  createRakedPlanPrismGeometry,
  geographicBearingToSceneDirection,
  geographicSoutheastSceneAzimuthRadians,
  projectPlanRotationToSceneRadians,
  projectPointToScene,
  type PlanCenter,
  type ProjectVertex,
} from "../three/planGeometry";
import { useTheme } from "../theme/theme";

// The 3D panel behind an implicit ModelViewer seam (→ 21 §3D panel).
//
// Two scene sources cooperate. The always-available baseline rebuilds the scene directly from
// model.json (extruded wall/solid/roof surfaces + solid instanced framing members), so the
// 3D view shows exactly what the resolver computed and works offline in the Pyodide PWA where
// the glb may be absent. On top of that, setModel asks the engine for its whole-house glb
// (server /model.glb, or the Pyodide engine's glb artifact). When that glb carries per-object
// trade metadata, setWholeHouseGlb can promote it to the PRIMARY scene, distributed across the
// same trade groups so selection, highlight and the trade/role toggles keep working (see the
// emitter contract on setWholeHouseGlb). The emitter now writes per-object nodes, but promotion
// stays gated off (WHOLE_HOUSE_GLB_PRIMARY) until it reaches visual parity with this baseline —
// flat-extruded tops and palette-only wall finishes still lag the model.json render path — so
// the glb is discarded and the model.json baseline stands, unchanged. The Nordic passes (soft lighting
// + edge linework) attach to the three.js scene, so they survive either route. Clicking a wall
// cross-highlights the 2D plan and surfaces its file:line provenance.

export const EARTH_PLANE_OPACITY = 0.28;
export const EARTH_PLANE_THICKNESS_M = 0.01;
export const EARTH_FALLBACK_HALF_SIZE_M = 50;
// Arch tessellation for one continuous viewer mesh; no internal wall-piece seams are emitted.
// The segment count is derived per arch from its radius (archSoffitSegmentCount) so that a
// soffit facet never strays further than this from the true circle, whatever the arch's size.
export const ARCH_SOFFIT_CHORD_TOLERANCE_M = 0.0005;
export const ARCH_SOFFIT_MIN_SEGMENT_COUNT = 24;
export const ARCH_SOFFIT_MAX_SEGMENT_COUNT = 192;
// A vertex counts as being on the soffit circle within this distance of it. The samples are
// computed from the circle, so the only slack needed is ExtrudeGeometry's float32 storage
// (~3e-7 m at house coordinates); anything beyond was clipped away by the wall top.
const ARCH_SOFFIT_RING_TOLERANCE_M = 1e-5;
// ExtrudeGeometry gives its front/back caps normals along the sweep axis and its swept side
// walls normals in the shape plane; only the latter can belong to an arch soffit.
const ARCH_SOFFIT_SWEPT_FACE_MAX_AXIAL_NORMAL = 0.5;
// Junction resolution splits a layer ring's straight edges at every crossing wall. A vertex
// this far off the chord between its neighbours is a real corner; anything closer is padding.
export const COLLINEAR_VERTEX_TOLERANCE_M = 1e-6;

// Whether a fully-tagged whole-house glb may take over from the model.json baseline scene.
// Held OFF until the glTF emitter reaches visual parity with the model.json render path: it
// still (a) extrudes walls flat between z0..z1 rather than raking gable/ToRoof tops to the roof
// slope, and (b) ships flat palette colors instead of the procedural standing-seam / CMU wall
// finishes. Promoting it before then silently downgrades those envelope details, so the glb —
// though now correctly per-object tagged (its identity metadata is still emitted and consumed
// for anything that reads it) — stays a secondary artifact until the emitter closes those gaps.
export const WHOLE_HOUSE_GLB_PRIMARY = false;

type PanDirection = "left" | "right" | "up" | "down";

// How a whole-house glb node maps back to an interactive element. A node earns an assignment
// via glTF `extras` (GLTFLoader copies these onto object.userData) or, as a fallback, a
// "<trade>|<kind>|<uid>" node name. `kind`/`uid` are optional: untagged envelope geometry only
// needs a trade (to land in the right visibility group), while a selectable node also carries
// its model uid so picking and highlight resolve to the same record model.json uses. The `kind`
// vocabulary is the shared SelectionKind (→ state/store.ts, emit/gltf/emitter.py).
export interface GlbNodeAssignment {
  trade: Trade;
  uid: string | null;
  kind: SelectionKind | null;
}

export function wholeHouseGlbAssignment(
  name: string | undefined,
  userData: Record<string, unknown> | undefined,
): GlbNodeAssignment | null {
  const parts = (name ?? "").split("|");
  const tradeRaw = typeof userData?.trade === "string" ? userData.trade : parts[0];
  if (!tradeRaw || !(ALL_TRADES as readonly string[]).includes(tradeRaw)) return null;
  const kindRaw = typeof userData?.kind === "string" ? userData.kind : parts[1];
  const kind = (ALL_SELECTION_KINDS as readonly string[]).includes(kindRaw)
    ? kindRaw as SelectionKind : null;
  const uidRaw = typeof userData?.uid === "string" ? userData.uid : parts[2];
  return { trade: tradeRaw as Trade, uid: uidRaw || null, kind };
}

// Make every mesh a builder just added to `parent` resolve to one model element: snapshot
// parent.children.length before building, pass it here afterwards. Framing members are merged
// into shared instanced/merged draw calls (→ three/members.ts) and carry no identity of their
// own, so a click on a joist, a tread or a rafter deliberately selects the floor / stair / roof
// that owns it. Nordic edge overlays are LineSegments, so they stay out of the raycast set.
function registerSelectable(
  parent: THREE.Object3D,
  firstChildIndex: number,
  uid: string,
  kind: SelectionKind,
  picks: THREE.Mesh[],
  byUid: Map<string, THREE.Material[]>,
) {
  // Deduped: an opening's frame material is shared by half a dozen boxes, and the highlight
  // pass would otherwise set the same emissive over and over.
  const materials = new Set(byUid.get(uid) ?? []);
  for (let index = firstChildIndex; index < parent.children.length; index++) {
    const child = parent.children[index];
    if (!(child instanceof THREE.Mesh)) continue;
    child.userData.uid = uid;
    child.userData.selectionKind = kind;
    picks.push(child);
    const material = child.material;
    for (const one of Array.isArray(material) ? material : [material]) materials.add(one);
  }
  if (materials.size) byUid.set(uid, [...materials]);
}

export function Panel3D() {
  const model = useStore((s) => s.model);
  const threeMode = useStore((s) => s.threeMode);
  const select = useStore((s) => s.select);
  const selection = useStore((s) => s.selection);
  const visibleTrades = useStore((s) => s.visibleTrades);
  const client = useStore((s) => s.client);
  const { theme } = useTheme();
  const mountRef = useRef<HTMLDivElement>(null);
  const compassRef = useRef<SVGSVGElement>(null);
  const api = useRef<SceneApi | null>(null);
  const renderedModel = useRef<Model | null>(null);
  const renderedTheme = useRef<string | null>(null);

  useEffect(() => {
    if (!mountRef.current) return;
    const a = createScene(mountRef.current, compassRef.current, (kind, uid) => select(kind, uid));
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
    // The uid index only holds what the 3D builders registered, so a plan-only selection
    // (a room) simply clears the previous highlight rather than needing a kind test here.
    api.current?.highlight(selection.uid);
    renderedModel.current = model;
    renderedTheme.current = theme;
    // Ask the engine for its whole-house glb and, when it carries per-object metadata, promote
    // it to the primary scene. Any failure (monolithic/older glb, or offline without a glb)
    // silently keeps the model.json baseline built above. setWholeHouseGlb is guarded by the
    // scene generation, so a load that resolves after the next setModel is dropped.
    let cancelled = false;
    client.getArtifact("glb")
      .then((blob) => { if (!cancelled) api.current?.setWholeHouseGlb(blob); })
      .catch(() => { /* keep the model.json baseline */ });
    return () => { cancelled = true; };
  }, [model, threeMode, theme, client]);

  useEffect(() => {
    api.current?.highlight(selection.uid);
  }, [selection]);

  useEffect(() => {
    for (const trade of ALL_TRADES) api.current?.setVisibility(trade, visibleTrades[trade]);
  }, [visibleTrades]);

  return (
    <div style={{ position: "absolute", inset: 0 }}>
      <div ref={mountRef} style={{ position: "absolute", inset: 0 }} />
      <svg
        ref={compassRef}
        className="hud"
        aria-label="Geographic orientation compass"
        viewBox="0 0 72 72"
        style={{ top: 96, bottom: "auto", left: 76, width: 72, height: 72, padding: 0, pointerEvents: "none" }}
      >
        <circle cx="36" cy="36" r="27" fill="var(--panel)" fillOpacity="0.82"
          stroke="var(--line)" strokeWidth="1" />
        <circle cx="36" cy="36" r="2" fill="var(--muted)" />
        {(["N", "E", "S", "W"] as const).map((label, index) => (
          <text key={label} data-compass-bearing={index * 90} x="36" y="15"
            textAnchor="middle" dominantBaseline="middle" fontSize="11"
            fontWeight={label === "N" ? 800 : 600}
            fill={label === "N" ? "var(--accent)" : "var(--ink)"}>
            {label}
          </text>
        ))}
      </svg>
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
  setWholeHouseGlb: (blob: Blob) => void;
  setPalette: (palette: ResolvedNordicPalette) => void;
  pan: (direction: PanDirection) => void;
  resetView: () => void;
  highlight: (uid: string | null) => void;
  setVisibility: (trade: Trade, visible: boolean) => void;
  dispose: () => void;
}

export function compassBearingScreenDirection(
  camera: THREE.Camera,
  target: THREE.Vector3,
  bearingDegrees: number,
  trueNorthDegrees: number,
): readonly [x: number, y: number] {
  camera.updateMatrixWorld(true);
  const projectedTarget = target.clone().project(camera);
  const projectedDirection = target.clone()
    .add(geographicBearingToSceneDirection(bearingDegrees, trueNorthDegrees))
    .project(camera);
  const dx = projectedDirection.x - projectedTarget.x;
  const dy = projectedTarget.y - projectedDirection.y;
  const length = Math.hypot(dx, dy);
  return length < 1e-9 ? [0, -1] : [dx / length, dy / length];
}

function createScene(
  mount: HTMLElement,
  compass: SVGSVGElement | null,
  onPick: (kind: SelectionKind, uid: string) => void,
): SceneApi {
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
  let trueNorthDegrees = 0;
  let fittedTheta = theta;
  let fittedPhi = phi;
  let fittedRadius = radius;
  let fittedTarget = target.clone();
  let panStep = 1;
  let dragging = false;
  let panning = false; // orbit vs. screen-pan for the active pointer drag
  let last = [0, 0];

  const updateCompass = () => {
    if (!compass) return;
    for (const label of compass.querySelectorAll<SVGTextElement>("[data-compass-bearing]")) {
      const bearing = Number(label.dataset.compassBearing);
      const [dx, dy] = compassBearingScreenDirection(camera, target, bearing, trueNorthDegrees);
      label.setAttribute("x", String(36 + dx * 21));
      label.setAttribute("y", String(36 + dy * 21));
    }
  };

  const place = () => {
    camera.position.set(
      target.x + radius * Math.sin(phi) * Math.cos(theta),
      target.y + radius * Math.cos(phi),
      target.z + radius * Math.sin(phi) * Math.sin(theta),
    );
    camera.lookAt(target);
    updateCompass();
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

  // Eased camera move (reset view): interpolate orbit angles / dolly / target over a short
  // ease-in-out so the reset glides instead of snapping. Any user interaction cancels it.
  let tween = 0;
  const stopTween = () => { if (tween) { cancelAnimationFrame(tween); tween = 0; } };
  const animateTo = (toTheta: number, toPhi: number, toRadius: number, toTarget: THREE.Vector3) => {
    stopTween();
    const fromTheta = theta, fromPhi = phi, fromRadius = radius;
    const fromTarget = target.clone();
    const start = performance.now();
    const duration = 320;
    const tick = () => {
      const raw = Math.min(1, (performance.now() - start) / duration);
      const eased = raw < 0.5 ? 2 * raw * raw : 1 - Math.pow(-2 * raw + 2, 2) / 2;
      theta = fromTheta + (toTheta - fromTheta) * eased;
      phi = fromPhi + (toPhi - fromPhi) * eased;
      radius = fromRadius + (toRadius - fromRadius) * eased;
      target.copy(fromTarget).lerp(toTarget, eased);
      place();
      renderer.render(scene, camera);
      tween = raw < 1 ? requestAnimationFrame(tick) : 0;
    };
    tween = requestAnimationFrame(tick);
  };

  const el = renderer.domElement;
  const raycaster = new THREE.Raycaster();
  const groundPlane = new THREE.Plane();
  let downAt = [0, 0];
  el.style.touchAction = "none";

  // Where the pointer ray meets the horizontal plane through the current target — the anchor
  // for cursor-centric zoom and the reference depth for screen-space panning.
  const pointerGroundPoint = (clientX: number, clientY: number): THREE.Vector3 | null => {
    const r = el.getBoundingClientRect();
    const ndc = new THREE.Vector2(((clientX - r.left) / r.width) * 2 - 1, -((clientY - r.top) / r.height) * 2 + 1);
    place();
    raycaster.setFromCamera(ndc, camera);
    groundPlane.set(new THREE.Vector3(0, 1, 0), -target.y);
    const hit = new THREE.Vector3();
    return raycaster.ray.intersectPlane(groundPlane, hit) ? hit : null;
  };

  el.addEventListener("contextmenu", (e) => e.preventDefault()); // right-drag pans, no menu
  el.addEventListener("pointerdown", (e) => {
    stopTween();
    dragging = true;
    // Middle/right button or a held modifier pans; plain left-drag orbits (matches most
    // 3D tools and keeps single-button/trackpad orbit as the default).
    panning = e.button === 1 || e.button === 2 || e.shiftKey || e.metaKey;
    last = [e.clientX, e.clientY];
    downAt = [e.clientX, e.clientY];
    el.setPointerCapture(e.pointerId);
  });
  el.addEventListener("pointermove", (e) => {
    if (!dragging) return;
    const dx = e.clientX - last[0];
    const dy = e.clientY - last[1];
    if (panning) {
      // Move the target in the screen plane so the grabbed point tracks the cursor. Scale by
      // world-units-per-pixel at the target depth, so pan speed feels constant at any zoom.
      const height = mount.clientHeight || 1;
      const worldPerPixel = (2 * radius * Math.tan(THREE.MathUtils.degToRad(camera.fov) / 2)) / height;
      const screenRight = new THREE.Vector3(1, 0, 0).applyQuaternion(camera.quaternion);
      const screenUp = new THREE.Vector3(0, 1, 0).applyQuaternion(camera.quaternion);
      target.add(screenRight.multiplyScalar(-dx * worldPerPixel));
      target.add(screenUp.multiplyScalar(dy * worldPerPixel));
    } else {
      theta -= dx * 0.008;
      phi = Math.min(Math.PI / 2 - 0.05, Math.max(0.1, phi - dy * 0.008));
    }
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
      const kind = hit?.object.userData.selectionKind as SelectionKind | undefined;
      if (uid && kind) onPick(kind, uid);
    }
  });
  el.addEventListener("wheel", (e) => {
    e.preventDefault();
    stopTween();
    // Gentler, exponent-based dolly with a firm clamp; zoom homes on the point under the
    // cursor (the old wheel kept the target fixed, so zooming in drifted off whatever you
    // were inspecting).
    const anchor = pointerGroundPoint(e.clientX, e.clientY);
    const nextRadius = Math.min(120, Math.max(1.5, radius * Math.exp(e.deltaY * 0.0012)));
    if (anchor) {
      const zoomInFraction = THREE.MathUtils.clamp(1 - nextRadius / radius, 0, 0.6);
      target.lerp(anchor, zoomInFraction);
    }
    radius = nextRadius;
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
    animateTo(fittedTheta, fittedPhi, fittedRadius, fittedTarget);
  };

  // The framing bounds must exclude the translucent site sheet: the earth spans the whole
  // parcel (or a 50 m fallback), so folding it into the fit shrank the building to a speck
  // and left the default/reset zoom far too wide.
  const buildingBox = (): THREE.Box3 => {
    const box = new THREE.Box3();
    for (const trade of ALL_TRADES) {
      if (trade === "earth") continue;
      box.expandByObject(tradeGroups[trade]);
    }
    return box;
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
    const nextTrueNorthDegrees = m.site?.true_north_deg ?? 0;
    const trueNorthChanged = nextTrueNorthDegrees !== trueNorthDegrees;
    trueNorthDegrees = nextTrueNorthDegrees;
    if (trueNorthChanged) {
      fittedTheta = geographicSoutheastSceneAzimuthRadians(trueNorthDegrees);
    }
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
      buildWall(tradeGroups, w, wallOpenings, center, mode, palette, picks, byUid,
        m.catalog?.materials);
      for (const opening of wallOpenings) {
        const isDoubleSwing = m.catalog?.door_types.find((dt) => dt.tag === opening.type_ref)?.operation === "double_swing";
        buildOpening(tradeGroups.openings, opening, w, center, mode, palette, isDoubleSwing, picks, byUid);
      }
    }
    // The site sheet is context, not an element: it has no uid in model.json, so it stays out
    // of the raycast set and a click through it falls to whatever building geometry is behind.
    buildEarth(tradeGroups.earth, m, center, mode);
    for (const solid of m.solids ?? []) buildSolid(tradeGroups.concrete, solid, center, mode, palette, m.catalog, picks, byUid);
    for (const bedding of m.footing_beddings ?? []) buildFootingBedding(tradeGroups.concrete, bedding, center, mode, picks, byUid);
    for (const floor of m.floors ?? []) buildFloor(tradeGroups.floors, floor, center, mode, palette, picks, byUid);
    for (const roof of m.roofs ?? []) buildRoof(tradeGroups.roof, roof, center, mode, palette, m.catalog, picks, byUid);
    for (const stair of m.stairs ?? []) buildStair(tradeGroups.stairs, stair, center, mode, picks, byUid);
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
          visual.rotation.y = projectPlanRotationToSceneRadians(item.rotation ?? 0);
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

    // Frame the building bounds (earth excluded, or the site sheet dominates), including its
    // vertical origin. The old target only considered height, leaving models whose base was
    // above zero visibly low in the canvas.
    const box = buildingBox();
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
      theta = geographicSoutheastSceneAzimuthRadians(trueNorthDegrees);
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

  // Promote the engine's whole-house glb to the primary scene when it carries per-object trade
  // metadata; otherwise leave the model.json baseline that setModel built. Async and guarded by
  // the scene generation captured at call time, so a load resolving after the next setModel is
  // dropped. Emitter contract to make the glb primary (see the module header): every renderable
  // node declares its trade + element via glTF `extras`
  // { trade: <Trade>, uid?: string, kind?: "wall"|"canvas_object" } or a "<trade>|<kind>|<uid>"
  // node name. A single untagged node (today's color-bucketed "building" mesh) is treated as
  // unstructured and discarded, so nothing regresses until the emitter opts in.
  const setWholeHouseGlb = (blob: Blob) => {
    const generation = sceneGeneration;
    blob.arrayBuffer().then((buffer) => {
      if (generation !== sceneGeneration) return;
      new GLTFLoader().parse(buffer, "", (gltf) => {
        if (generation !== sceneGeneration) { disposeGroup(gltf.scene); return; }
        applyWholeHouseGlb(gltf.scene);
      }, () => { /* parse failure → keep the model.json baseline */ });
    }).catch(() => { /* read failure → keep the model.json baseline */ });
  };

  const applyWholeHouseGlb = (root: THREE.Object3D) => {
    // Gated off until the emitter reaches parity (see WHOLE_HOUSE_GLB_PRIMARY): promoting the glb
    // today drops raked wall tops and the procedural standing-seam/CMU finishes. Keep the richer
    // model.json baseline that setModel built.
    if (!WHOLE_HOUSE_GLB_PRIMARY) { disposeGroup(root); return; }
    // Classify first: only take over when every renderable node maps to a trade. Walk up from
    // each mesh so a tagged parent covers its (often untagged) child primitives.
    const tagged: { mesh: THREE.Mesh; assignment: GlbNodeAssignment }[] = [];
    let renderable = 0;
    let unstructured = false;
    root.traverse((node) => {
      if (unstructured || !(node instanceof THREE.Mesh)) return;
      renderable++;
      let assignment: GlbNodeAssignment | null = null;
      for (let o: THREE.Object3D | null = node; o && !assignment; o = o.parent) {
        assignment = wholeHouseGlbAssignment(o.name, o.userData);
      }
      if (!assignment) { unstructured = true; return; }
      tagged.push({ mesh: node, assignment });
    });
    if (renderable === 0 || unstructured) { disposeGroup(root); return; }

    // Structured glb → take over. Bump the generation so any pending per-item furniture loaders
    // from the superseded model.json scene are dropped, then replace every trade group's
    // contents with the glb's nodes (re-parented in place, world transform baked).
    sceneGeneration++;
    const selectedUid = highlighted; // re-apply against the rebuilt materials below
    for (const trade of ALL_TRADES) {
      disposeGroup(tradeGroups[trade]);
      tradeGroups[trade].clear();
    }
    picks = [];
    byUid.clear();
    highlighted = null;
    root.updateMatrixWorld(true);
    for (const { mesh, assignment } of tagged) {
      const world = mesh.matrixWorld.clone();
      const group = tradeGroups[assignment.trade];
      group.add(mesh); // trade groups sit at the world origin, so world == local below
      world.decompose(mesh.position, mesh.quaternion, mesh.scale);
      mesh.castShadow = true;
      mesh.receiveShadow = true;
      if (assignment.uid) {
        const materials = Array.isArray(mesh.material) ? mesh.material : [mesh.material];
        byUid.set(assignment.uid, [...(byUid.get(assignment.uid) ?? []), ...materials]);
        if (assignment.kind) {
          mesh.userData.uid = assignment.uid;
          mesh.userData.selectionKind = assignment.kind;
          picks.push(mesh);
        }
      }
    }
    disposeGroup(root); // drop any leftover empty container nodes
    highlight(selectedUid); // restore the current selection's emissive against the new materials
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
    setWholeHouseGlb,
    setPalette,
    pan,
    resetView,
    highlight,
    setVisibility,
    dispose: () => {
      cancelAnimationFrame(raf);
      stopTween();
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

// Holes punched in the site sheet so the translucent earth stops at the building footprint
// instead of bleeding up through interior floors. One cut per plan footprint is enough, so
// only the ground storey's rooms contribute — stacked upper storeys would otherwise pile
// overlapping holes onto the same plan area (rooms on one storey partition it, never overlap).
export function earthVoids(model: Model): [number, number][][] {
  const rooms = model.rooms ?? [];
  if (!rooms.length) return [];
  const storeys = model.storeys ?? [];
  const elevationOf = (tag: string) => storeys.find((s) => s.tag === tag)?.elevation_m ?? 0;
  const groundElevation = Math.min(...rooms.map((room) => elevationOf(room.storey)));
  return rooms
    .filter((room) => elevationOf(room.storey) === groundElevation && room.clear_face.length >= 3)
    .map((room) => room.clear_face.map(([x, y]) => [x, y] as [number, number]));
}

function buildEarth(parent: THREE.Group, model: Model, center: PlanCenter, mode: "nordic" | "schematic") {
  const outline = earthOutline(model, center);
  const grade = earthElevation(model);
  const geometry = createPlanPrismGeometry(
    outline, grade - EARTH_PLANE_THICKNESS_M, grade,
    earthVoids(model), center,
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
  mesh.rotation.y = projectPlanRotationToSceneRadians(item.rotation ?? 0);
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
  materials?: MaterialSpec[],
) {
  const mats: THREE.Material[] = [];
  for (const ly of w.layers) {
    if (ly.polygon.length < 3) continue;
    // Cavity fill shares its host structure layer's polygon — extruding it would only
    // z-fight with the studs it lives between.
    if (ly.is_cavity) continue;
    const seam = ly.function === "cladding" && isStandingSeam(ly.material);
    // Masonry (brick/CMU/stone) gets coursing + recessed mortar, not a flat fill — a brick
    // veneer or CMU wythe otherwise read like painted drywall. The style (module + mortar +
    // jitter) comes from the material's authored `finish`, so CMU reads as 16"×8" grey block
    // and white brick as whitewash over grey mortar; only a material that declares nothing
    // falls back to guessing from its tag.
    const appearance = authoredAppearance(ly.material, materials);
    const masonryStyle = !seam && isMasonry(ly.material)
      ? masonryStyleFor(ly.material, appearance?.finish) : null;
    const mat = seam
      ? createStandingSeamMaterial(mode, [
        Math.hypot(w.axis[1][0] - w.axis[0][0], w.axis[1][1] - w.axis[0][1]),
        Math.max(0.1, w.z1_m - w.z0_m),
      ], 0xE8E8E2, true)
      : masonryStyle
        ? createMasonryMaterial(mode, masonryStyle,
          materialColor(ly.material, palette, materials), appearance?.color)
        : new THREE.MeshStandardMaterial({
          color: new THREE.Color(materialColor(ly.material, palette, materials)),
          roughness: mode === "nordic" ? 0.85 : 1,
          metalness: 0,
          flatShading: mode === "schematic",
        });
    mats.push(mat);
    const smoothArchGeometry = createSmoothArchedWallLayerGeometry(w, ly.polygon, openings, center);
    const geometries: (THREE.BufferGeometry | null)[] = smoothArchGeometry
      ? [smoothArchGeometry]
      : wallLayerPieces(w, ly.polygon, openings).map((piece) => piece.topIsRaked
        ? createRakedPlanPrismGeometry(piece.polygon, piece.z0_m,
          (point) => rakedTopAt(w, point[0], point[1]), center)
        : createPlanPrismGeometry(piece.polygon, piece.z0_m, piece.z1_m, [], center));
    for (const geo of geometries) {
      if (!geo) continue;
      if (seam) applyStandingSeamWallUv(geo, w.axis, center);
      else if (masonryStyle) applyMasonryWallUv(geo, w.axis, center, masonryTileSizeM(masonryStyle));
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

// Drop vertices that sit on the straight line between their neighbours. Junction resolution
// splits a wall layer's long edges at every crossing wall, so an authored rectangle serializes
// as five, six or eight points (the 16" sunken-garden arch wall arrives as six). Anything that
// needs to *recognise* a rectangle has to reduce first. Mirrors `_without_collinear_vertices`
// in packages/engine/src/typehaus/emit/gltf/emitter.py — keep the two in step.
export function withoutCollinearVertices(
  polygon: readonly (readonly [number, number])[],
  toleranceM: number = COLLINEAR_VERTEX_TOLERANCE_M,
): [number, number][] {
  const ring: [number, number][] = [];
  for (const [x, y] of polygon) {
    const last = ring[ring.length - 1];
    if (!last || Math.hypot(x - last[0], y - last[1]) > toleranceM) ring.push([x, y]);
  }
  while (ring.length > 1 && Math.hypot(ring[0][0] - ring[ring.length - 1][0],
    ring[0][1] - ring[ring.length - 1][1]) <= toleranceM) ring.pop();
  if (ring.length < 3) return ring;
  const corners: [number, number][] = [];
  for (let index = 0; index < ring.length; index++) {
    const [px, py] = ring[(index - 1 + ring.length) % ring.length];
    const [cx, cy] = ring[index];
    const [nextX, nextY] = ring[(index + 1) % ring.length];
    const spanX = nextX - px, spanY = nextY - py;
    const span = Math.hypot(spanX, spanY);
    // Perpendicular distance, in metres, of this vertex from the chord between its neighbours.
    const offset = span < toleranceM
      ? Math.hypot(cx - px, cy - py)
      : Math.abs((cx - px) * spanY - (cy - py) * spanX) / span;
    if (offset > toleranceM) corners.push([cx, cy]);
  }
  return corners;
}

// Segments for a half-circle soffit sampled at even angular steps. One step's mid-chord sagitta
// is r·(1 − cos(π/2n)), so inverting it ties tessellation to the arch's actual size instead of a
// flat guess: an 8'-wide garden arch and a small niche head come out equally smooth. Mirrors
// `_arch_soffit_segment_count` in the glTF emitter.
export function archSoffitSegmentCount(radiusM: number): number {
  if (!(radiusM > ARCH_SOFFIT_CHORD_TOLERANCE_M)) return ARCH_SOFFIT_MIN_SEGMENT_COUNT;
  const halfStep = Math.acos(Math.max(-1, 1 - ARCH_SOFFIT_CHORD_TOLERANCE_M / radiusM));
  return Math.min(ARCH_SOFFIT_MAX_SEGMENT_COUNT,
    Math.max(ARCH_SOFFIT_MIN_SEGMENT_COUNT, Math.ceil(Math.PI / (2 * halfStep))));
}

// One soffit sample as (offset from the arch centreline, height above the springline). The arc
// is walked by *angle*: stepping evenly in x collapses near the springlines, where a semicircle
// turns vertical, so the last step alone dropped ~40 cm on the catlin arches — the striping.
// Mirrors `_arch_soffit_sample` in the glTF emitter.
export function archSoffitSample(
  segment: number, segmentCount: number, radiusM: number,
): { offsetM: number; heightM: number } {
  const angle = Math.PI * segment / segmentCount;
  return { offsetM: -radiusM * Math.cos(angle), heightM: radiusM * Math.sin(angle) };
}

interface ArchSoffitCylinder { centerAlongM: number; springlineM: number; radiusM: number }

// ExtrudeGeometry sweeps every hole edge as its own detached quad, so the soffit ships per-facet
// normals and shades as N flat strips however finely it is tessellated. Overwrite just the swept
// soffit ring with the analytic cylinder normal; jambs, wall ends and the front/back caps keep
// their extruded normals, so the prism's corners stay crisp. Runs in ExtrudeGeometry's local
// frame (shape in XY, sweep along Z), before the layer is placed into the scene.
function applySmoothArchSoffitNormals(
  geometry: THREE.BufferGeometry, soffits: readonly ArchSoffitCylinder[],
): void {
  if (soffits.length === 0) return;
  const position = geometry.getAttribute("position");
  const normal = geometry.getAttribute("normal");
  if (!position || !normal) return;
  for (let index = 0; index < position.count; index++) {
    if (Math.abs(normal.getZ(index)) > ARCH_SOFFIT_SWEPT_FACE_MAX_AXIAL_NORMAL) continue;
    const along = position.getX(index), elevation = position.getY(index);
    for (const { centerAlongM, springlineM, radiusM } of soffits) {
      const dx = along - centerAlongM, dy = elevation - springlineM;
      const distance = Math.hypot(dx, dy);
      if (dy < -ARCH_SOFFIT_RING_TOLERANCE_M ||
        Math.abs(distance - radiusM) > ARCH_SOFFIT_RING_TOLERANCE_M) continue;
      // Replace the facet's direction only — its outward sense stays whatever the sweep
      // established, so the void keeps facing into the opening.
      const sign = normal.getX(index) * dx + normal.getY(index) * dy < 0 ? -1 : 1;
      normal.setXYZ(index, sign * dx / distance, sign * dy / distance, 0);
      break;
    }
  }
  normal.needsUpdate = true;
}

// A concrete arch should read as one continuous cast surface. Extruding a Shape with opening
// holes gives the soffit a single smooth mesh; the strip fallback below is retained for raked
// and junction-mitered wall layers whose non-rectangular plan footprint cannot be swept safely.
export function createSmoothArchedWallLayerGeometry(
  wall: Wall, polygon: readonly [number, number][], openings: Opening[], center: PlanCenter,
): THREE.BufferGeometry | null {
  if (!openings.some((opening) => (opening.arch_rise_m ?? 0) > 1e-9) ||
      wall.top_z0_m != null || wall.top_z1_m != null) return null;
  const [[sx, sy], [ex, ey]] = wall.axis;
  const length = Math.hypot(ex - sx, ey - sy);
  if (length < 1e-9) return null;
  const ux = (ex - sx) / length, uy = (ey - sy) / length;
  const nx = -uy, ny = ux;
  // A padded ring is still a rectangle; only its *corners* decide whether it can be swept.
  const footprint = withoutCollinearVertices(polygon);
  if (footprint.length !== 4) return null;
  const local = footprint.map(([x, y]) => [
    (x - sx) * ux + (y - sy) * uy,
    (x - sx) * nx + (y - sy) * ny,
  ] as const);
  const alongs = local.map(([along]) => along), acrosses = local.map(([, across]) => across);
  const minAlong = Math.min(...alongs), maxAlong = Math.max(...alongs);
  const minAcross = Math.min(...acrosses), maxAcross = Math.max(...acrosses);
  const corners = new Set(local.map(([along, across]) => `${along.toFixed(8)},${across.toFixed(8)}`));
  if (corners.size !== 4 || ![
    [minAlong, minAcross], [minAlong, maxAcross], [maxAlong, minAcross], [maxAlong, maxAcross],
  ].every(([along, across]) => corners.has(`${along.toFixed(8)},${across.toFixed(8)}`))) return null;

  const shape = new THREE.Shape();
  shape.moveTo(minAlong, wall.z0_m);
  shape.lineTo(maxAlong, wall.z0_m);
  shape.lineTo(maxAlong, wall.z1_m);
  shape.lineTo(minAlong, wall.z1_m);
  shape.closePath();
  const soffits: ArchSoffitCylinder[] = [];
  for (const opening of openings) {
    const start = Math.max(minAlong, opening.center_along_m - opening.width_m / 2);
    const end = Math.min(maxAlong, opening.center_along_m + opening.width_m / 2);
    const bottom = Math.max(wall.z0_m, wall.z0_m + opening.sill_m);
    if (end - start <= 1e-9 || bottom >= wall.z1_m - 1e-9) continue;
    const hole = new THREE.Path();
    const archRise = opening.arch_rise_m ?? 0;
    if (archRise <= 1e-9) {
      const top = Math.min(wall.z1_m, bottom + opening.height_m);
      hole.moveTo(start, bottom); hole.lineTo(start, top); hole.lineTo(end, top); hole.lineTo(end, bottom);
    } else {
      const radiusM = opening.width_m / 2;
      const springlineM = bottom + Math.max(0, opening.height_m - archRise);
      const segmentCount = archSoffitSegmentCount(radiusM);
      hole.moveTo(start, bottom);
      hole.lineTo(start, Math.min(wall.z1_m, springlineM));
      for (let segment = 0; segment <= segmentCount; segment++) {
        const { offsetM, heightM } = archSoffitSample(segment, segmentCount, radiusM);
        hole.lineTo(opening.center_along_m + offsetM, Math.min(wall.z1_m, springlineM + heightM));
      }
      hole.lineTo(end, bottom);
      soffits.push({ centerAlongM: opening.center_along_m, springlineM, radiusM });
    }
    hole.closePath();
    shape.holes.push(hole);
  }
  const geometry = new THREE.ExtrudeGeometry(shape, {
    depth: maxAcross - minAcross, bevelEnabled: false, curveSegments: 1,
  });
  applySmoothArchSoffitNormals(geometry, soffits);
  // Extrude from the maximum-across face toward the minimum-across face. This keeps
  // the local-to-scene matrix right-handed while mapping project north to scene -Z.
  geometry.applyMatrix4(new THREE.Matrix4().set(
    ux, 0, -nx, sx + nx * maxAcross - center[0],
    0, 1, 0, 0,
    -uy, 0, ny, center[1] - sy - ny * maxAcross,
    0, 0, 0, 1,
  ));
  return geometry;
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
    const archRise = active.arch_rise_m ?? 0;
    if (archRise > 1e-9) {
      const springline = openingBottom + Math.max(0, active.height_m - archRise);
      const radius = active.width_m / 2;
      // Angular steps here too: even-x strips leave a ~40 cm riser at each springline.
      const segmentCount = archSoffitSegmentCount(radius);
      for (let segment = 0; segment < segmentCount; segment++) {
        const segmentStart = active.center_along_m + archSoffitSample(segment, segmentCount, radius).offsetM;
        const segmentEnd = active.center_along_m + archSoffitSample(segment + 1, segmentCount, radius).offsetM;
        const clippedStart = Math.max(start, segmentStart);
        const clippedEnd = Math.min(end, segmentEnd);
        if (clippedEnd - clippedStart <= 1e-9) continue;
        const midpoint = (clippedStart + clippedEnd) / 2;
        const offset = midpoint - active.center_along_m;
        const curve = radius * radius - offset * offset;
        const soffit = springline + Math.sqrt(Math.max(0, curve));
        if (wall.z1_m > soffit + 1e-9)
          pieces.push({ polygon: ring(clippedStart, clippedEnd), z0_m: soffit,
            z1_m: wall.z1_m, topIsRaked: raked });
      }
      continue;
    }
    const minTop = Math.min(...strip.map(([x, y]) => rakedTopAt(wall, x, y)));
    if (minTop > openingTop + 1e-9)
      pieces.push({ polygon: strip, z0_m: openingTop, z1_m: wall.z1_m, topIsRaked: raked });
  }
  return pieces;
}

export function buildOpening(parent: THREE.Group, opening: Opening, wall: Wall, center: PlanCenter,
  mode: "nordic" | "schematic", palette: ResolvedNordicPalette, isDoubleSwing: boolean,
  picks: THREE.Mesh[], byUid: Map<string, THREE.Material[]>) {
  if (opening.kind === "rough_opening") return;
  const firstChildIndex = parent.children.length;
  const [[x0, y0], [x1, y1]] = wall.axis;
  const length = Math.hypot(x1 - x0, y1 - y0);
  if (length < 1e-9) return;
  const direction: [number, number] = [(x1 - x0) / length, (y1 - y0) / length];
  const position: [number, number] = [x0 + direction[0] * opening.center_along_m, y0 + direction[1] * opening.center_along_m];
  const availableHeight = Math.max(0, Math.min(opening.height_m,
    rakedTopAt(wall, x0 + direction[0] * (opening.center_along_m - opening.width_m / 2), y0 + direction[1] * (opening.center_along_m - opening.width_m / 2)) - wall.z0_m - opening.sill_m,
    rakedTopAt(wall, x0 + direction[0] * (opening.center_along_m + opening.width_m / 2), y0 + direction[1] * (opening.center_along_m + opening.width_m / 2)) - wall.z0_m - opening.sill_m));
  if (availableHeight <= 1e-9) return;
  const rotation = Math.atan2(direction[1], direction[0]);
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
  // Frame, leaf/mullion and glazing are one door or window: clicking any of them selects the
  // opening record, which the Inspector already knows how to edit.
  registerSelectable(parent, firstChildIndex, opening.uid, "opening", picks, byUid);
}

// Every resolved prism that is not a wall, floor or roof: slabs, footings and pads, but also
// 6x6 posts, beams, guard rails, dowels, thermal breaks, connectors, sump pits, vent risers,
// fascia, gutters and flashings. Same outline-extrusion recipe as wall layers; the finish comes
// from the solid's authored assembly when it has one, else its category (→ three/solidMaterials.ts).
//
// Plank decking is the one case the category palette cannot express: an aluminium deck slab
// needs a UV-framed procedural board finish, not a flat colour, so it is resolved first.
export function buildSolid(parent: THREE.Group, solid: Solid, center: PlanCenter,
  mode: "nordic" | "schematic", palette: ResolvedNordicPalette, catalog: Catalog | undefined,
  picks: THREE.Mesh[], byUid: Map<string, THREE.Material[]>) {
  if (solid.outline.length < 3) return;
  const geo = createPlanPrismGeometry(solid.outline, solid.z0_m, Math.max(solid.z1_m, solid.z0_m + 0.01), solid.voids ?? [], center);
  if (!geo) return;
  const deckBoards = catalog?.assemblies.find((a) => a.tag === solid.assembly)?.layers
    .some((layer) => isAluminumDeckBoard(layer.material));
  if (deckBoards) applyDeckBoardUv(geo, center);
  const firstChildIndex = parent.children.length;
  const mesh = new THREE.Mesh(geo,
    deckBoards ? createDeckBoardMaterial(mode) : createSolidMaterial(solid, catalog, mode, palette));
  mesh.castShadow = true;
  mesh.receiveShadow = true;
  parent.add(mesh);
  registerSelectable(parent, firstChildIndex, solid.uid, "solid", picks, byUid);
}

// Compacted washed-stone footing bed: a below-grade gravel prism under a strip footing.
// Rendered granular (flat-shaded, high roughness) so it reads as aggregate, not concrete.
export const FOOTING_BEDDING_COLOR = 0x8b8478;

export function buildFootingBedding(parent: THREE.Group, bedding: FootingBedding, center: PlanCenter,
  mode: "nordic" | "schematic", picks: THREE.Mesh[], byUid: Map<string, THREE.Material[]>) {
  if (bedding.outline.length < 3 || bedding.z1_m <= bedding.z0_m) return;
  const geo = createPlanPrismGeometry(bedding.outline, bedding.z0_m, bedding.z1_m, [], center);
  if (!geo) return;
  const firstChildIndex = parent.children.length;
  const mat = new THREE.MeshStandardMaterial({
    color: FOOTING_BEDDING_COLOR,
    roughness: 1,
    metalness: 0,
    flatShading: true, // faceted normals read as loose aggregate in both shading modes
  });
  const mesh = new THREE.Mesh(geo, mat);
  mesh.castShadow = true;
  mesh.receiveShadow = true;
  parent.add(mesh);
  if (mode === "nordic") {
    parent.add(new THREE.LineSegments(
      new THREE.EdgesGeometry(geo, 20),
      new THREE.LineBasicMaterial({ color: 0x5c574d, transparent: true, opacity: 0.4 }),
    ));
  }
  registerSelectable(parent, firstChildIndex, bedding.uid, "footing_bedding", picks, byUid);
}

export function buildFloor(parent: THREE.Group, floor: Floor, center: PlanCenter,
  mode: "nordic" | "schematic", palette: ResolvedNordicPalette,
  picks: THREE.Mesh[], byUid: Map<string, THREE.Material[]>) {
  const firstChildIndex = parent.children.length;
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
  registerSelectable(parent, firstChildIndex, floor.uid, "floor", picks, byUid);
}

// Sloped quads from footprint/eave_z/ridge_z/ridge_direction — mirrors
// emit/gltf/emitter.py's _add_roof — thickened into the authored assembly, plus the
// roof's own members (rafters, ridge beam).
export function buildRoof(parent: THREE.Group, roof: Roof, center: PlanCenter,
  mode: "nordic" | "schematic", palette: ResolvedNordicPalette, catalog: Catalog | undefined,
  picks: THREE.Mesh[], byUid: Map<string, THREE.Material[]>) {
  const firstChildIndex = parent.children.length;
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
  registerSelectable(parent, firstChildIndex, roof.uid, "roof", picks, byUid);
}

// A stair is nothing but its generated members (stringers, treads, risers), so its whole
// framing bucket is what a click has to land on.
export function buildStair(parent: THREE.Group, stair: Stair, center: PlanCenter,
  mode: "nordic" | "schematic", picks: THREE.Mesh[], byUid: Map<string, THREE.Material[]>) {
  const firstChildIndex = parent.children.length;
  buildMembers(parent, stair.members, center, mode);
  registerSelectable(parent, firstChildIndex, stair.uid, "stair", picks, byUid);
}

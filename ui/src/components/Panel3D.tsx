import { useEffect, useRef } from "react";
import * as THREE from "three";
import { RoomEnvironment } from "three/examples/jsm/environments/RoomEnvironment.js";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
import { useStore } from "../state/store";
import { ALL_TRADES, DEFAULT_EARTH_OPACITY, type SelectionKind, type Trade } from "../state/vocabulary";
import { ALL_LAYER_VISIBILITY_GROUPS, type LayerVisibilityGroup } from "../model/visibility";
import type { Model } from "../model/types";
import type { EngineClient } from "../engine/EngineClient";
import { RESOLVED_NORDIC_PALETTE, type ResolvedNordicPalette } from "../nordic/palette";
import { disposeGroup } from "../three/members";
import { locateMember } from "../model/memberIdentity";
import { buildMemberHighlight, resolveMemberPickUid } from "../three/memberPicking";
import {
  clampDollyRadius, frameRadiusForBounds, normalizedWheelDeltaPx, pinchDollyRadius,
  VIEW_FIT_POLAR_ANGLE, VIEW_PAN_STEP_FRACTION, WHEEL_DOLLY_SENSITIVITY, type PanDirection,
} from "../three/cameraFraming";
import {
  wholeHouseGlbAssignment, WHOLE_HOUSE_GLB_PRIMARY, type GlbNodeAssignment,
} from "../three/wholeHouseGlb";
import { isRenderedInScene } from "../three/builders/registry";
import { planCenterOf, populateScene, type SceneRegistry } from "../three/builders/scene";
import { applyEarthOpacity } from "../three/builders/site";
import {
  geographicBearingToSceneDirection,
  geographicSoutheastSceneAzimuthRadians,
  type PlanCenter,
} from "../three/planGeometry";
import { useTheme } from "../theme/theme";
import { ZoomControls } from "./ZoomControls";

// The 3D panel behind an implicit ModelViewer seam (→ 21 §3D panel).
//
// Two scene sources cooperate. The always-available baseline rebuilds the scene directly from
// model.json (extruded wall/solid/roof surfaces + solid instanced framing members), so the
// 3D view shows exactly what the resolver computed and works offline in the Pyodide PWA where
// the glb may be absent. On top of that, setModel asks the engine for its whole-house glb
// (server /model.glb, or the Pyodide engine's glb artifact). When that glb carries per-object
// trade metadata, setWholeHouseGlb can promote it to the PRIMARY scene, distributed across the
// same trade groups so selection, highlight and the trade/role toggles keep working (see the
// emitter contract on setWholeHouseGlb). Why promotion stays gated off is explained at
// WHOLE_HOUSE_GLB_PRIMARY's definition (three/wholeHouseGlb.ts) — the model.json baseline stands,
// unchanged. The Nordic passes (soft lighting + edge linework) attach to the three.js scene, so
// they survive either route. Clicking a wall cross-highlights the 2D plan and surfaces its
// file:line provenance.

// Scratch vectors for the pointer handlers below, which run once per pointermove: three.js
// object construction is not free at that rate, and members.ts already keeps module scratch
// (`_m`, `_color`) for the same reason. Each is consumed before the next event can start.
const _right = new THREE.Vector3();
const _up = new THREE.Vector3();
const _ndc = new THREE.Vector2();
const _hit = new THREE.Vector3();
const PLANE_UP = new THREE.Vector3(0, 1, 0);

// `compact` is the 300x220 floating preview (→ Preview3D). The pan/zoom cluster is 206px wide
// there, which leaves the preview previewing its own chrome, so that surface goes without: it is
// a companion to the plan, not somewhere a view gets composed, and the pane it mirrors has the
// full controls. Drag and pinch still work in it.
export function Panel3D({ compact = false }: { compact?: boolean }) {
  const model = useStore((s) => s.model);
  const threeMode = useStore((s) => s.threeMode);
  const select = useStore((s) => s.select);
  const selection = useStore((s) => s.selection);
  const visibleTrades = useStore((s) => s.visibleTrades);
  const visibleLayerGroups = useStore((s) => s.visibleLayerGroups);
  const earthOpacity = useStore((s) => s.earthOpacity);
  const client = useStore((s) => s.client);
  const { theme } = useTheme();
  const mountRef = useRef<HTMLDivElement>(null);
  const compassRef = useRef<SVGSVGElement>(null);
  const api = useRef<SceneApi | null>(null);
  // Which engine client this panel has already framed a building for (→ preserveView below).
  const framedForClient = useRef<EngineClient | null>(null);

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
    // Re-frame the camera only when this is a different *building*, not a different model
    // object: every reload/edit re-parses model.json into a fresh object, and content hash /
    // revision also change on edits the view should survive. The engine client is what is
    // replaced when another house is opened (state/store.ts openOfflineHouse / init), so it is
    // the thing that means the old framing is meaningless. A remount (2D↔3D, split) starts with
    // a null ref and therefore frames, as it must.
    const preserveView = framedForClient.current === client;
    api.current?.setModel(model, threeMode, RESOLVED_NORDIC_PALETTE[theme], preserveView);
    // The uid index only holds what the 3D builders registered, so a plan-only selection
    // (a room) simply clears the previous highlight rather than needing a kind test here.
    api.current?.highlight(selection.uid);
    framedForClient.current = client;
    // Ask the engine for its whole-house glb and, when it carries per-object metadata, promote
    // it to the primary scene. Any failure (monolithic/older glb, or offline without a glb)
    // silently keeps the model.json baseline built above. setWholeHouseGlb is guarded by the
    // scene generation, so a load that resolves after the next setModel is dropped.
    //
    // Gated on the same flag applyWholeHouseGlb bails on: fetching and parsing the whole-house
    // glb (server-side emit_glb + a full GLTFLoader.parse of megabytes of geometry) is pure
    // waste while promotion is off, since applyWholeHouseGlb would just dispose the result. The
    // promotion path stays whole for whoever flips the flag; it just isn't paid for while it's off.
    if (!WHOLE_HOUSE_GLB_PRIMARY) return;
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

  useEffect(() => {
    for (const group of ALL_LAYER_VISIBILITY_GROUPS) {
      api.current?.setLayerGroupVisibility(group, visibleLayerGroups[group]);
    }
  }, [visibleLayerGroups]);

  // Retarget the site sheet's material in place. Deliberately not a setModel dependency: a
  // slider drag would otherwise rebuild every wall, stick and placeable per frame.
  useEffect(() => {
    api.current?.setEarthOpacity(earthOpacity);
  }, [earthOpacity]);

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
      {/* Pan and zoom are one cluster: a flex box owns the corner, so neither has to know how
          wide the other is (→ styles/shell.css .canvas-nav-controls). */}
      {!compact && <div className="canvas-nav-controls">
        <div
          className="hud"
          aria-label="3D view navigation"
          style={{ display: "grid", gridTemplateColumns: "repeat(3, var(--hit))", gap: 4, padding: 4 }}
        >
          <span />
          <button className="seg-btn" aria-label="Pan view up" title="Pan up" onClick={() => api.current?.pan("up")}>↑</button>
          <span />
          <button className="seg-btn" aria-label="Pan view left" title="Pan left" onClick={() => api.current?.pan("left")}>←</button>
          <button className="seg-btn" aria-label="Reset 3D view"
            title="Frame the whole model (three-quarter view)"
            onClick={() => api.current?.resetView()}>⌾</button>
          <button className="seg-btn" aria-label="Pan view right" title="Pan right" onClick={() => api.current?.pan("right")}>→</button>
          <span />
          <button className="seg-btn" aria-label="Pan view down" title="Pan down" onClick={() => api.current?.pan("down")}>↓</button>
          <span />
        </div>
        <ZoomControls label="3D view zoom" onZoom={(factor) => api.current?.zoomBy(factor)} />
      </div>}
      {/* Nordic/schematic switch + discipline toggles live in the shared Views panel (Phase 6). */}
    </div>
  );
}

interface SceneApi {
  setModel: (m: Model, mode: "nordic" | "schematic", palette: ResolvedNordicPalette, preserveView: boolean) => void;
  setWholeHouseGlb: (blob: Blob) => void;
  setPalette: (palette: ResolvedNordicPalette) => void;
  pan: (direction: PanDirection) => void;
  zoomBy: (factor: number) => void;
  resetView: () => void;
  highlight: (uid: string | null) => void;
  setVisibility: (trade: Trade, visible: boolean) => void;
  setLayerGroupVisibility: (group: LayerVisibilityGroup, visible: boolean) => void;
  setEarthOpacity: (opacity: number) => void;
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
  // Without tone mapping three hard-clips anything over 1.0, and a Regal White (#E8E8E2,
  // albedo 0.91) wall under this light rig lands well past it: the whole envelope rendered at
  // a flat 255 and swallowed the standing-seam shading, leaving only the few seams that
  // happened to fall on a dark lobe of the finish's waviness — irregular grey streaks on
  // white. Neutral rather than ACES: ACES adds a contrast/saturation shift that warms and
  // darkens near-white architectural surfaces, which is the one thing this palette can't take.
  renderer.toneMapping = THREE.NeutralToneMapping;
  renderer.toneMappingExposure = 1;
  // Repeated world-scaled maps (seam, masonry, deck boards) are viewed at grazing angles on
  // every wall; at the default anisotropy of 1 their mips smear unevenly and the module reads
  // as moiré. Set before any texture is constructed — the maps are built lazily in setModel.
  THREE.Texture.DEFAULT_ANISOTROPY = renderer.capabilities.getMaxAnisotropy();
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

  // A picked framing member cannot be highlighted through the uid index: its material is shared with
  // every other stick in the same draw call. It gets a throwaway outline in this group instead,
  // which sits outside the trade groups so the view-fit bounds never see it.
  const memberHighlightGroup = new THREE.Group();
  content.add(memberHighlightGroup);
  // Drop the current member outline, if any. Cheap and idempotent — called on every highlight
  // change and on every scene clear.
  const clearMemberHighlight = () => {
    disposeGroup(memberHighlightGroup);
    memberHighlightGroup.clear();
  };

  // The raycast set and the uid -> materials index, together: the async furniture loader
  // in populateScene *replaces* the pick list, so it has to be reachable by reference.
  const registry: SceneRegistry = { picks: [], byUid: new Map() };
  let sceneGeneration = 0;
  let highlighted: string | null = null;
  // What `highlight` needs to rebuild a member outline: the model the scene was built from and
  // the plan centre it was projected around.
  let highlightSourceModel: Model | null = null;
  let highlightPlanCenter: PlanCenter = [0, 0];
  let activePalette = RESOLVED_NORDIC_PALETTE.light;
  // Layer-group visibility lives on the meshes, which setModel rebuilds — unlike the trade
  // groups, which persist. Remembering the hidden set here is what lets a rebuild land with
  // the user's per-layer filter still applied.
  const hiddenLayerGroups = new Set<LayerVisibilityGroup>();
  // Ground opacity is remembered here for the same reason: the sheet is one of the meshes a
  // rebuild throws away, so populateScene reads this rather than the default.
  let earthOpacity = DEFAULT_EARTH_OPACITY;

  // Lighting: soft neutral environment (Nordic). Hemisphere + a key light.
  //
  // The budget is set against a white cladding face: hemisphere + key + environment together
  // have to land it comfortably under 1.0, or tone mapping is compressing an already-blown
  // surface and the seam finish has nothing to modulate. The key carries proportionally more
  // of the budget than the hemisphere, because a normal map is only visible in *directional*
  // light — under pure ambient the seam ridges vanish however much headroom they have.
  const hemi = new THREE.HemisphereLight(0xffffff, 0xbcb6a8, 0.8);
  const key = new THREE.DirectionalLight(0xffffff, 0.9);
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
  // RoomEnvironment is bright enough to be a third full light source. Dial it back to what it
  // is actually here for — feeding the clearcoat on painted metal — instead of a unit of flat
  // irradiance on top of the two lights above.
  scene.environmentIntensity = 0.6;

  // Simple orbit: drag to rotate, wheel or pinch to dolly (no external controls dependency).
  let theta = Math.PI * 0.25;
  let phi = Math.PI * 0.32;
  let radius = 12;
  let target = new THREE.Vector3(0, 1, 0);
  let trueNorthDegrees = 0;
  // (right, down) pan-button clicks applied on top of the whole-building fit — see setModel's
  // `m.project?.default_view_pan`.
  let defaultViewPan: [number, number] = [0, 0];
  // Set once the operator orbits/dollies/pans. A resize re-frames only while this is false, so
  // dragging the split divider never yanks a view someone has just composed.
  let viewAdjustedByUser = false;
  let dragging = false;
  let panning = false; // orbit vs. screen-pan for the active pointer drag
  let last = [0, 0];
  // Every pointer currently down, so a second finger reads as a pinch instead of fighting the
  // first one over the orbit. Same bookkeeping as the plan canvas (→ plan/usePanZoom.ts): the
  // two views should not speak different dialects of the same gesture.
  const pointers = new Map<number, [number, number]>();
  let pinch: { span: number; radius: number } | null = null;
  let tapCandidate = false; // a lone pointer that has not yet become a drag or a pinch

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
    _ndc.set(((clientX - r.left) / r.width) * 2 - 1, -((clientY - r.top) / r.height) * 2 + 1);
    place();
    raycaster.setFromCamera(_ndc, camera);
    groundPlane.set(PLANE_UP, -target.y);
    return raycaster.ray.intersectPlane(groundPlane, _hit) ? _hit : null;
  };

  el.addEventListener("contextmenu", (e) => e.preventDefault()); // right-drag pans, no menu
  const pinchSpan = (): number => {
    const [a, b] = [...pointers.values()];
    return Math.hypot(a[0] - b[0], a[1] - b[1]);
  };
  el.addEventListener("pointerdown", (e) => {
    stopTween();
    pointers.set(e.pointerId, [e.clientX, e.clientY]);
    el.setPointerCapture(e.pointerId);
    if (pointers.size === 2) {
      // Second finger down: the gesture is a pinch from here on. Ending the drag also withdraws
      // the tap, so spreading two fingers never selects whatever the first one landed on.
      pinch = { span: pinchSpan(), radius };
      dragging = false;
      tapCandidate = false;
      return;
    }
    if (pointers.size > 2) return; // a third finger neither orbits nor re-scales the pinch
    dragging = true;
    tapCandidate = true;
    // Middle/right button or a held modifier pans; plain left-drag orbits (matches most
    // 3D tools and keeps single-button/trackpad orbit as the default).
    panning = e.button === 1 || e.button === 2 || e.shiftKey || e.metaKey;
    last = [e.clientX, e.clientY];
    downAt = [e.clientX, e.clientY];
  });
  el.addEventListener("pointermove", (e) => {
    if (!pointers.has(e.pointerId)) return;
    pointers.set(e.pointerId, [e.clientX, e.clientY]);
    if (pinch && pointers.size === 2) {
      radius = pinchDollyRadius(pinch.radius, pinch.span, pinchSpan());
      viewAdjustedByUser = true;
      requestRender();
      return;
    }
    if (!dragging) return;
    const dx = e.clientX - last[0];
    const dy = e.clientY - last[1];
    if (panning) {
      // Move the target in the screen plane so the grabbed point tracks the cursor. Scale by
      // world-units-per-pixel at the target depth, so pan speed feels constant at any zoom.
      const height = mount.clientHeight || 1;
      const worldPerPixel = (2 * radius * Math.tan(THREE.MathUtils.degToRad(camera.fov) / 2)) / height;
      const screenRight = _right.set(1, 0, 0).applyQuaternion(camera.quaternion);
      const screenUp = _up.set(0, 1, 0).applyQuaternion(camera.quaternion);
      target.add(screenRight.multiplyScalar(-dx * worldPerPixel));
      target.add(screenUp.multiplyScalar(dy * worldPerPixel));
    } else {
      theta -= dx * 0.008;
      phi = Math.min(Math.PI / 2 - 0.05, Math.max(0.1, phi - dy * 0.008));
    }
    last = [e.clientX, e.clientY];
    viewAdjustedByUser = true;
    requestRender();
  });
  // Forget a pointer however it ends. `pointercancel` matters as much as `pointerup` now that
  // there is a map to keep straight: an interrupted touch that is never deleted leaves the panel
  // convinced a finger is still down, and every later gesture reads as a pinch.
  const forgetPointer = (e: PointerEvent) => {
    pointers.delete(e.pointerId);
    if (pointers.size < 2) pinch = null;
    // Still pinching, but possibly between a different pair of fingers now. Re-anchor on the
    // survivors at the current distance, or the span would appear to jump and take the zoom
    // with it the moment a third finger leaves.
    else if (pinch) pinch = { span: pinchSpan(), radius };
    if (pointers.size === 0) dragging = false;
    if (el.hasPointerCapture(e.pointerId)) el.releasePointerCapture(e.pointerId);
  };
  el.addEventListener("pointercancel", (e) => {
    tapCandidate = false;
    forgetPointer(e);
  });
  el.addEventListener("pointerup", (e) => {
    const wasTap = tapCandidate && pointers.size === 1;
    tapCandidate = false;
    forgetPointer(e);
    // treat a near-zero drag as a click → raycast pick
    if (wasTap && Math.hypot(e.clientX - downAt[0], e.clientY - downAt[1]) < 4) {
      const r = el.getBoundingClientRect();
      _ndc.set(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1);
      raycaster.setFromCamera(_ndc, camera);
      // Only pick what is actually on screen. `intersectObjects(..., false)` tests the meshes
      // directly, bypassing three's own visibility walk, so a hidden trade or a hidden assembly
      // layer would otherwise still intercept a click aimed at what it was hiding.
      const hit = raycaster.intersectObjects(registry.picks.filter(isRenderedInScene), false)[0];
      if (!hit) return;
      // A framing bucket resolves the hit's instanceId / faceIndex back to the one member it
      // drew there; anything else carries its element identity on the mesh itself.
      const memberPick = resolveMemberPickUid(hit.object, hit.instanceId, hit.faceIndex);
      if (memberPick) {
        onPick("member", memberPick);
        return;
      }
      const uid = hit.object.userData.uid as string | undefined;
      const kind = hit.object.userData.selectionKind as SelectionKind | undefined;
      if (uid && kind) onPick(kind, uid);
    }
  });
  el.addEventListener("wheel", (e) => {
    e.preventDefault();
    stopTween();
    // Exponent-based dolly over a *normalized, clamped* delta: a line-mode mouse notch and a
    // pixel-mode trackpad flick otherwise differ by more than an order of magnitude. Zoom
    // homes on the point under the cursor, so zooming in tracks whatever you were inspecting.
    const anchor = pointerGroundPoint(e.clientX, e.clientY);
    const step = normalizedWheelDeltaPx(e.deltaY, e.deltaMode);
    const nextRadius = clampDollyRadius(radius * Math.exp(step * WHEEL_DOLLY_SENSITIVITY));
    if (anchor) {
      const zoomInFraction = THREE.MathUtils.clamp(1 - nextRadius / radius, 0, 0.6);
      target.lerp(anchor, zoomInFraction);
    }
    radius = nextRadius;
    viewAdjustedByUser = true;
    requestRender();
  }, { passive: false }); // preventDefault above is the only thing stopping browser page zoom

  // Safari/iPadOS answers a trackpad or touch pinch with its own `gesture*` events, which
  // `touch-action: none` does not suppress. Left alone they zoom the *page* — the document
  // scaling out from under a canvas that was already handling the same fingers.
  for (const name of ["gesturestart", "gesturechange", "gestureend"]) {
    el.addEventListener(name, (e) => e.preventDefault());
  }

  const resize = () => {
    const w = mount.clientWidth || 1;
    const h = mount.clientHeight || 1;
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    // A pane that changes shape (2D → split → 3D, or the window itself) changes what "framed"
    // means. Re-fit while the view is still the computed one; leave a composed view alone.
    if (!viewAdjustedByUser) applyFraming(false);
    requestRender();
  };
  const ro = new ResizeObserver(resize);

  // Dispose every mesh's geometry/material before dropping it: content.clear() only detaches
  // Object3Ds, it never calls .dispose(), so skipping this leaks on every setModel().
  const clear = () => {
    sceneGeneration++;
    for (const trade of ALL_TRADES) {
      disposeGroup(tradeGroups[trade]);
      tradeGroups[trade].clear();
    }
    clearMemberHighlight();
    registry.picks = [];
    registry.byUid.clear();
    highlighted = null;
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

  // The screen-space basis pan() derives from camera.quaternion (line ~583 below), rederived
  // for an arbitrary orbit state rather than the live camera — lets defaultViewPan reproduce
  // N pan-button clicks against a framing that hasn't been applied to the camera yet.
  const screenBasisFor = (orbitTheta: number, orbitPhi: number, orbitRadius: number, orbitTarget: THREE.Vector3) => {
    const eye = new THREE.Vector3(
      orbitTarget.x + orbitRadius * Math.sin(orbitPhi) * Math.cos(orbitTheta),
      orbitTarget.y + orbitRadius * Math.cos(orbitPhi),
      orbitTarget.z + orbitRadius * Math.sin(orbitPhi) * Math.sin(orbitTheta),
    );
    const m = new THREE.Matrix4().lookAt(eye, orbitTarget, camera.up);
    const q = new THREE.Quaternion().setFromRotationMatrix(m);
    return {
      screenRight: new THREE.Vector3(1, 0, 0).applyQuaternion(q),
      screenUp: new THREE.Vector3(0, 1, 0).applyQuaternion(q),
    };
  };

  // Compute the framing that shows the whole building from a three-quarter viewpoint, at the
  // pane's *current* aspect. Reset recomputes rather than replaying a snapshot, so a view fitted
  // in the narrow split pane still frames correctly once the panel goes full width.
  const buildingFraming = (): { theta: number; phi: number; radius: number; target: THREE.Vector3 } | null => {
    const box = buildingBox();
    if (box.isEmpty()) return null;
    const fitTheta = geographicSoutheastSceneAzimuthRadians(trueNorthDegrees);
    const fitTarget = box.getCenter(new THREE.Vector3());
    const fitRadius = frameRadiusForBounds(
      box, fitTarget, fitTheta, VIEW_FIT_POLAR_ANGLE,
      THREE.MathUtils.degToRad(camera.fov), camera.aspect,
    );
    const [rightClicks, downClicks] = defaultViewPan;
    if (rightClicks || downClicks) {
      const { screenRight, screenUp } = screenBasisFor(fitTheta, VIEW_FIT_POLAR_ANGLE, fitRadius, fitTarget);
      const panStep = fitRadius * VIEW_PAN_STEP_FRACTION;
      // Matches pan()'s own signs: right adds screenRight, down subtracts screenUp.
      fitTarget.addScaledVector(screenRight, panStep * rightClicks)
        .addScaledVector(screenUp, -panStep * downClicks);
    }
    return { theta: fitTheta, phi: VIEW_FIT_POLAR_ANGLE, radius: fitRadius, target: fitTarget };
  };

  const applyFraming = (animate: boolean) => {
    const framing = buildingFraming();
    if (!framing) return;
    viewAdjustedByUser = false;
    if (animate) {
      animateTo(framing.theta, framing.phi, framing.radius, framing.target);
      return;
    }
    theta = framing.theta;
    phi = framing.phi;
    radius = framing.radius;
    target.copy(framing.target);
  };

  const resetView = () => applyFraming(true);

  // Observe only now that `resize` can safely call back into the framing helpers above.
  ro.observe(mount);
  resize();

  const pan = (direction: PanDirection) => {
    // Translate the target in the camera's screen plane. place() refreshes its orientation
    // first so pan remains intuitive after orbiting, while the spherical camera offset stays
    // unchanged and therefore cannot alter the current rotation or zoom.
    place();
    const panStep = radius * VIEW_PAN_STEP_FRACTION;
    const screenRight = _right.set(1, 0, 0).applyQuaternion(camera.quaternion);
    const screenUp = _up.set(0, 1, 0).applyQuaternion(camera.quaternion);
    const offset = direction === "left" ? screenRight.multiplyScalar(-panStep)
      : direction === "right" ? screenRight.multiplyScalar(panStep)
        : direction === "up" ? screenUp.multiplyScalar(panStep)
          : screenUp.multiplyScalar(-panStep);
    target.add(offset);
    viewAdjustedByUser = true;
    requestRender();
  };

  // Button zoom. The wheel homes on the cursor, but a button press has no cursor to home on, so
  // this dollies straight down the current sightline and leaves the composed angle and centre
  // exactly where they were. Eased like resetView rather than snapped — a jump cut here reads
  // as the model moving rather than the camera.
  const zoomBy = (factor: number) => {
    const next = clampDollyRadius(radius * factor);
    if (next === radius) return; // already at a clamp: nothing to animate
    viewAdjustedByUser = true;
    // target.clone(): animateTo lerps `target` toward the vector it is handed, so handing it
    // the live target would have it interpolating toward itself as it mutates.
    animateTo(theta, phi, next, target.clone());
  };

  const setModel =(m: Model, mode: "nordic" | "schematic", palette: ResolvedNordicPalette, preserveView: boolean) => {
    clear();
    activePalette = palette;
    scene.background = new THREE.Color(palette.bg);
    trueNorthDegrees = m.site?.true_north_deg ?? 0;
    defaultViewPan = m.project?.default_view_pan ?? [0, 0];
    if (!preserveView) target = new THREE.Vector3(0, 1.2, 0);

    const center = planCenterOf(m);
    highlightSourceModel = m;
    highlightPlanCenter = center;
    populateScene({
      tradeGroups, model: m, center, mode, palette, earthOpacity, registry,
      generation: sceneGeneration, currentGeneration: () => sceneGeneration, requestRender,
    });

    // Frame the building bounds (earth excluded, or the site sheet dominates), including its
    // vertical origin, so a model whose base sits above zero is not left low in the canvas.
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
    if (!preserveView) applyFraming(false);
    applyLayerVisibility(); // the rebuild dropped the meshes the filter was applied to
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
    // Gated off by decision, not by missing geometry parity (see WHOLE_HOUSE_GLB_PRIMARY):
    // promoting the glb would trade the procedural standing-seam/CMU finishes for the export's
    // flat portable colours. Keep the richer model.json baseline that setModel built.
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
    registry.picks = [];
    registry.byUid.clear();
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
        registry.byUid.set(assignment.uid, [...(registry.byUid.get(assignment.uid) ?? []), ...materials]);
        if (assignment.kind) {
          mesh.userData.uid = assignment.uid;
          mesh.userData.selectionKind = assignment.kind;
          registry.picks.push(mesh);
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
    if (highlighted && registry.byUid.has(highlighted))
      for (const mat of registry.byUid.get(highlighted)!)
        (mat as THREE.MeshStandardMaterial).emissive?.setHex(0x000000);
    clearMemberHighlight();
    highlighted = uid;
    if (uid && registry.byUid.has(uid))
      for (const mat of registry.byUid.get(uid)!)
        (mat as THREE.MeshStandardMaterial).emissive?.set(activePalette.highlight);
    // A member uid names one stick inside a shared bucket; outline it rather than tinting the
    // bucket's material, which would light every stud in the wall.
    const located = uid && highlightSourceModel ? locateMember(highlightSourceModel, uid) : null;
    if (located) {
      const outline = buildMemberHighlight(located.member, highlightPlanCenter, activePalette.highlight);
      if (outline) memberHighlightGroup.add(outline);
    }
    requestRender();
  };

  const setVisibility = (trade: Trade, visible: boolean) => {
    tradeGroups[trade].visible = visible;
    requestRender();
  };

  // Apply the remembered per-layer filter to whatever is in the scene right now. Cheap enough
  // to run on every rebuild: one traversal, one bool per tagged object, no geometry work.
  const applyLayerVisibility = () => {
    content.traverse((object) => {
      const group = object.userData.layerGroup as LayerVisibilityGroup | undefined;
      if (group) object.visible = !hiddenLayerGroups.has(group);
    });
  };

  // Retarget the live material rather than rebuilding: a drag is many events a second, and the
  // remembered value above means a rebuild mid-drag (an edit, a theme flip) does not snap the
  // ground back to the default.
  const setEarthOpacity = (opacity: number) => {
    earthOpacity = Math.min(1, Math.max(0, opacity));
    tradeGroups.earth.traverse((object) => {
      if (!(object instanceof THREE.Mesh) || !object.userData.earthSheet) return;
      for (const material of Array.isArray(object.material) ? object.material : [object.material]) {
        applyEarthOpacity(material, earthOpacity);
      }
    });
    requestRender();
  };

  const setLayerGroupVisibility = (group: LayerVisibilityGroup, visible: boolean) => {
    if (visible) hiddenLayerGroups.delete(group);
    else hiddenLayerGroups.add(group);
    applyLayerVisibility();
    requestRender();
  };

  return {
    setModel,
    setWholeHouseGlb,
    setPalette,
    pan,
    zoomBy,
    resetView,
    highlight,
    setVisibility,
    setLayerGroupVisibility,
    setEarthOpacity,
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


// Pan / zoom / tap gesture handling for the SVG floorplan, plus the once-per-storey fit.
// Split from components/Canvas2D.tsx along its documented seam: pointer bookkeeping lives
// here (pan vs. pinch vs. tap discrimination, post-pan click suppression); what a *tap*
// means is the tool dispatch's business, reached through the `onTap` callback.
import { useLayoutEffect, useRef } from "react";
import type { MutableRefObject, RefObject } from "react";
import { useStore } from "../../state/store";
import type { Model, Vec2, Wall } from "../../model/types";
import { clampScale } from "./PlanChrome";
import { TAP_PX } from "./canvasTypes";

export interface PanZoomHandlers {
  /** Zoom about the viewport centre. Factor > 1 means *further away*, as in the 3D panel. */
  zoomBy: (factor: number) => void;
  onPointerDown: (e: React.PointerEvent) => void;
  onPointerMove: (e: React.PointerEvent) => void;
  onPointerUp: (e: React.PointerEvent) => void;
  onClickCapture: (e: React.MouseEvent<SVGSVGElement>) => void;
}

export function usePanZoom(args: {
  svgRef: RefObject<SVGSVGElement>;
  model: Model;
  activeStorey: string | null;
  wallsOnStorey: Wall[];
  unproject: (clientX: number, clientY: number) => Vec2;
  onTap: (world: Vec2, screen: Vec2) => void;
  // Written on every pointer move so ortho-lock reads the live shift state without
  // re-subscribing; owned by the caller because the rubber-band memo reads it too.
  shiftRef: MutableRefObject<boolean>;
  setCursor: (world: Vec2 | null) => void;
}): PanZoomHandlers {
  const { svgRef, model, activeStorey, wallsOnStorey, unproject, onTap, shiftRef, setCursor } = args;
  const view = useStore((s) => s.view);
  const setView = useStore((s) => s.setView);
  const tool = useStore((s) => s.tool);

  const pointers = useRef<Map<number, Vec2>>(new Map());
  const pinch = useRef<{ dist: number; scale: number } | null>(null);
  const panLast = useRef<Vec2 | null>(null);
  const gesture = useRef<{ x: number; y: number; moved: boolean } | null>(null);
  const suppressPostPanClick = useRef(false);
  const fittedStorey = useRef<string | null>(null);

  // The authored model is in metres, while screen dimensions are only known after the
  // SVG enters its pane.  Fit once per storey so a fresh single-pane view starts with
  // the whole floor visible rather than an arbitrary 120 px/m slice near the origin.
  useLayoutEffect(() => {
    if (!activeStorey || fittedStorey.current === activeStorey) return;
    const svg = svgRef.current;
    if (!svg) return;

    const points: Vec2[] = [
      ...wallsOnStorey.flatMap((wall) => [wall.axis[0], wall.axis[1],
        ...wall.layers.flatMap((layer) => layer.polygon)]),
      ...model.rooms.filter((room) => room.storey === activeStorey)
        .flatMap((room) => room.clear_face),
    ];
    if (!points.length) return;

    const fit = () => {
      const { width, height } = svg.getBoundingClientRect();
      if (width <= 0 || height <= 0) return;
      const xs = points.map(([x]) => x);
      const ys = points.map(([, y]) => y);
      const spanX = Math.max(0.1, Math.max(...xs) - Math.min(...xs));
      const spanY = Math.max(0.1, Math.max(...ys) - Math.min(...ys));
      const padding = 64;
      const scale = clampScale(Math.min((width - padding * 2) / spanX, (height - padding * 2) / spanY));
      setView({
        scale,
        tx: width / 2 - ((Math.min(...xs) + Math.max(...xs)) / 2) * scale,
        ty: height / 2 + ((Math.min(...ys) + Math.max(...ys)) / 2) * scale,
      });
      fittedStorey.current = activeStorey;
    };

    const observer = new ResizeObserver(fit);
    observer.observe(svg);
    fit();
    return () => observer.disconnect();
  }, [activeStorey, model.rooms, setView, svgRef, wallsOnStorey]);

  // Scale about a point in viewport coordinates, keeping the world point under it fixed.
  // Reads the live view out of the store rather than the closed-over render value, so the same
  // function can serve a native listener that is only subscribed once.
  const zoomAbout = (factor: number, cx: number, cy: number) => {
    const current = useStore.getState().view;
    const scale = clampScale(current.scale * factor);
    const wx = (cx - current.tx) / current.scale;
    const wy = (current.ty - cy) / current.scale;
    setView({ scale, tx: cx - wx * scale, ty: cy + wy * scale });
  };

  // The wheel is a *native*, explicitly non-passive listener rather than React's `onWheel`.
  // React attaches wheel at the root passively, so preventDefault() from a synthetic handler is
  // ignored — and a trackpad pinch, which arrives here as ctrl+wheel, fell through to the
  // browser and zoomed the page instead of the plan. Safari's own `gesture*` pinch events need
  // the same treatment; `touch-action: none` does not cover them.
  useLayoutEffect(() => {
    const svg = svgRef.current;
    if (!svg) return;
    const onWheel = (e: WheelEvent) => {
      e.preventDefault();
      const rect = svg.getBoundingClientRect();
      zoomAbout(Math.exp(-e.deltaY * 0.0015), e.clientX - rect.left, e.clientY - rect.top);
    };
    const swallow = (e: Event) => e.preventDefault();
    svg.addEventListener("wheel", onWheel, { passive: false });
    for (const name of ["gesturestart", "gesturechange", "gestureend"]) {
      svg.addEventListener(name, swallow);
    }
    return () => {
      svg.removeEventListener("wheel", onWheel);
      for (const name of ["gesturestart", "gesturechange", "gestureend"]) {
        svg.removeEventListener(name, swallow);
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [svgRef]);

  // A button press has no cursor to zoom about, so it works on the middle of the pane. Factor
  // is inverted on the way in: the shared control speaks in dolly distance (up = further away),
  // the plan in pixels per metre.
  const zoomBy = (factor: number) => {
    const rect = svgRef.current?.getBoundingClientRect();
    if (!rect) return;
    zoomAbout(1 / factor, rect.width / 2, rect.height / 2);
  };

  const onPointerDown = (e: React.PointerEvent) => {
    if (e.pointerType === "mouse" && e.button !== 0) return;
    // Capturing on the viewport (instead of the pressed wall/image child) keeps the
    // gesture alive after the pointer leaves that child or the SVG bounds.
    e.currentTarget.setPointerCapture(e.pointerId);
    pointers.current.set(e.pointerId, [e.clientX, e.clientY]);
    if (pointers.current.size === 2) {
      const [a, b] = [...pointers.current.values()];
      pinch.current = { dist: Math.hypot(a[0] - b[0], a[1] - b[1]), scale: view.scale };
      gesture.current = null;
    } else {
      panLast.current = [e.clientX, e.clientY];
      gesture.current = { x: e.clientX, y: e.clientY, moved: false };
    }
  };

  const onPointerMove = (e: React.PointerEvent) => {
    shiftRef.current = e.shiftKey;
    // Rubber-band / snap preview follows the bare pointer for the wall tool (desktop hover).
    if (tool === "wall") setCursor(unproject(e.clientX, e.clientY));
    if (!pointers.current.has(e.pointerId)) return;
    pointers.current.set(e.pointerId, [e.clientX, e.clientY]);
    if (pointers.current.size === 2 && pinch.current) {
      const [a, b] = [...pointers.current.values()];
      const dist = Math.hypot(a[0] - b[0], a[1] - b[1]);
      setView({ scale: clampScale((pinch.current.scale * dist) / pinch.current.dist) });
      return;
    }
    if (gesture.current) {
      const moved = Math.hypot(e.clientX - gesture.current.x, e.clientY - gesture.current.y);
      if (moved > TAP_PX) gesture.current.moved = true;
    }
    if (panLast.current && (!gesture.current || gesture.current.moved)) {
      const dx = e.clientX - panLast.current[0];
      const dy = e.clientY - panLast.current[1];
      panLast.current = [e.clientX, e.clientY];
      const currentView = useStore.getState().view;
      setView({ tx: currentView.tx + dx, ty: currentView.ty + dy });
    }
  };

  const onPointerUp = (e: React.PointerEvent) => {
    const wasTap = gesture.current && !gesture.current.moved;
    const wasPan = gesture.current?.moved ?? false;
    pointers.current.delete(e.pointerId);
    if (pointers.current.size < 2) pinch.current = null;
    if (pointers.current.size === 0) panLast.current = null;
    if (wasTap && pointers.current.size === 0) {
      onTap(unproject(e.clientX, e.clientY), [
        e.clientX - e.currentTarget.getBoundingClientRect().left,
        e.clientY - e.currentTarget.getBoundingClientRect().top,
      ]);
    }
    if (wasPan) {
      // Native click follows pointerup.  Let the event finish, then clear the guard
      // so a drag across geometry never becomes an accidental selection.
      suppressPostPanClick.current = true;
      window.setTimeout(() => { suppressPostPanClick.current = false; }, 0);
    }
    if (e.currentTarget.hasPointerCapture(e.pointerId)) {
      e.currentTarget.releasePointerCapture(e.pointerId);
    }
    gesture.current = null;
  };

  const onClickCapture = (e: React.MouseEvent<SVGSVGElement>) => {
    if (!suppressPostPanClick.current) return;
    e.preventDefault();
    e.stopPropagation();
  };

  return { zoomBy, onPointerDown, onPointerMove, onPointerUp, onClickCapture };
}

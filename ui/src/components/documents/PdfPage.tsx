import { useEffect, useRef, useState } from "react";
import { Icon } from "../../icons/Icon";

/**
 * One page of the permit set, rendered to a canvas by pdf.js.
 *
 * Why not `<iframe src=blob>` and let the browser's viewer do it: on iPad Safari a native
 * PDF embed renders page one and stops — no scroll, no pager — and the iPad is the target
 * form factor for reading a drawing on site (decision #14). A canvas render is the same on
 * every device, and it is the only way the sheet list can *drive* the page.
 *
 * pdf.js is a lazy `import()` inside the component and a named chunk in vite.config.ts, so
 * it stays out of the entry bundle. The worker URL is a `?url` import rather than a
 * `new URL(…, import.meta.url)`: under `base: "./"` the latter resolves against the chunk's
 * own location and breaks when the app is served from `/app/`.
 */

// The type surface we actually use, hand-declared: `pdfjs-dist`'s own types would have to be
// imported eagerly to be referenced, which is exactly what the lazy chunk is avoiding.
interface RenderTask { promise: Promise<void>; cancel: () => void }
interface PdfPageProxy {
  getViewport(options: { scale: number }): { width: number; height: number };
  render(options: { canvasContext: CanvasRenderingContext2D; viewport: unknown }): RenderTask;
  cleanup(): void;
}
interface PdfDocumentProxy {
  numPages: number;
  getPage(page: number): Promise<PdfPageProxy>;
  destroy(): Promise<void>;
}

const ZOOM_STEPS = [0.5, 0.75, 1, 1.5, 2, 3, 4];

// iOS caps a canvas at roughly 16.7 megapixels and, past it, silently hands back a blank
// bitmap rather than throwing. A 24x36 sheet at 4x on a 3x-DPR display is well over that, so
// the device-pixel scale is clamped down until the canvas fits — the page renders slightly
// softer instead of white.
const MAX_CANVAS_PIXELS = 15_000_000;

export function PdfPage({ blob, page, label }: {
  blob: Blob | null;
  /** 1-based, from the sheet manifest. */
  page: number;
  /** Accessible name for the canvas — the sheet number and title. */
  label: string;
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const docRef = useRef<PdfDocumentProxy | null>(null);
  const taskRef = useRef<RenderTask | null>(null);
  const [zoom, setZoom] = useState(1);
  const [error, setError] = useState<string | null>(null);
  const [ready, setReady] = useState(false);

  // One `getDocument` per blob. Re-parsing the whole set on every page turn is what made an
  // early version take a second per sheet on a 40-page catlin print.
  useEffect(() => {
    let live = true;
    setReady(false);
    setError(null);
    if (!blob) return;
    void (async () => {
      try {
        const pdfjs = await import("pdfjs-dist");
        const workerUrl = (await import("pdfjs-dist/build/pdf.worker.min.mjs?url")).default;
        pdfjs.GlobalWorkerOptions.workerSrc = workerUrl;
        const data = await blob.arrayBuffer();
        const doc = await pdfjs.getDocument({ data }).promise;
        if (!live) { void doc.destroy(); return; }
        docRef.current = doc as unknown as PdfDocumentProxy;
        setReady(true);
      } catch (err) {
        if (live) setError(err instanceof Error ? err.message : String(err));
      }
    })();
    return () => {
      live = false;
      const doc = docRef.current;
      docRef.current = null;
      if (doc) void doc.destroy();
    };
  }, [blob]);

  // Render whenever the page or the zoom changes, cancelling whatever was still drawing:
  // pdf.js throws if two renders share a canvas, and paging fast is exactly how a reader
  // finds a sheet.
  useEffect(() => {
    const doc = docRef.current;
    const canvas = canvasRef.current;
    if (!ready || !doc || !canvas) return;
    let live = true;
    void (async () => {
      taskRef.current?.cancel();
      taskRef.current = null;
      const index = Math.min(Math.max(page, 1), doc.numPages);
      let pageProxy: PdfPageProxy;
      try {
        pageProxy = await doc.getPage(index);
      } catch {
        return; // the document was destroyed under us — a new blob is already loading
      }
      if (!live) return;
      const base = pageProxy.getViewport({ scale: 1 });
      const dpr = Math.min(window.devicePixelRatio || 1, 3);
      const wanted = zoom * dpr;
      const pixels = base.width * base.height * wanted * wanted;
      const scale = pixels > MAX_CANVAS_PIXELS
        ? wanted * Math.sqrt(MAX_CANVAS_PIXELS / pixels)
        : wanted;
      const viewport = pageProxy.getViewport({ scale });
      canvas.width = Math.floor(viewport.width);
      canvas.height = Math.floor(viewport.height);
      // CSS size is the *zoom* size; the canvas backing store is the device-pixel size, so
      // the sheet stays crisp without the layout knowing about DPR at all.
      canvas.style.width = `${Math.floor(base.width * zoom)}px`;
      canvas.style.height = `${Math.floor(base.height * zoom)}px`;
      const ctx = canvas.getContext("2d");
      if (!ctx) return;
      const task = pageProxy.render({ canvasContext: ctx, viewport });
      taskRef.current = task;
      try {
        await task.promise;
      } catch {
        /* cancelled by the next render — not an error */
      } finally {
        if (taskRef.current === task) taskRef.current = null;
        pageProxy.cleanup();
      }
    })();
    return () => { live = false; };
  }, [ready, page, zoom]);

  useEffect(() => () => { taskRef.current?.cancel(); }, []);

  const step = (delta: 1 | -1) => setZoom((current) => {
    const index = ZOOM_STEPS.indexOf(current);
    const from = index >= 0 ? index
      : ZOOM_STEPS.findIndex((z) => z > current) - (delta === 1 ? 1 : 0);
    const next = ZOOM_STEPS[Math.min(Math.max(from + delta, 0), ZOOM_STEPS.length - 1)];
    return next ?? current;
  });

  if (error) {
    return <div className="doc-pdf-empty" role="alert">Could not open the drawing set: {error}</div>;
  }

  return (
    <>
      <div className="doc-chip-row">
        <button className="btn icon-btn" onClick={() => step(-1)} title="Zoom out"
          disabled={zoom <= ZOOM_STEPS[0]}>
          <Icon name="zoom-out" size={18} />
        </button>
        <span className="doc-meta" aria-live="polite">{Math.round(zoom * 100)}%</span>
        <button className="btn icon-btn" onClick={() => step(1)} title="Zoom in"
          disabled={zoom >= ZOOM_STEPS[ZOOM_STEPS.length - 1]}>
          <Icon name="zoom-in" size={18} />
        </button>
      </div>
      <div
        className="doc-pdf-scroll"
        // Ctrl/⌘+wheel is the browser's zoom gesture on a document, and a trackpad pinch
        // arrives as exactly that. Plain wheel keeps scrolling the sheet.
        onWheel={(event) => {
          if (!event.ctrlKey && !event.metaKey) return;
          event.preventDefault();
          step(event.deltaY < 0 ? 1 : -1);
        }}
      >
        {ready
          ? <canvas ref={canvasRef} className="doc-pdf-canvas" role="img" aria-label={label} />
          : <div className="doc-pdf-empty">Opening the drawing set…</div>}
      </div>
    </>
  );
}

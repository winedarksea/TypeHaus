// The M2 EngineClient implementation: fetch + WebSocket against `haus serve`
// (server/app.py). Same-origin relative paths — the Vite dev proxy and the wheel-served
// production build both route these to the engine (→ 21 §EngineClient boundary).

import type { Finding, Model } from "../model/types";
import {
  type BuildResult,
  type DetailIndexEntry,
  type EngineBom,
  type DetailPayload,
  EngineError,
  type EngineArtifact,
  type EngineClient,
  type EngineEvent,
  type HistoryResult,
  type MacroRequest,
  type MacroResult,
  type PatchOp,
  type PatchResult,
  type PreviewGeometry,
  RevisionConflict,
  type UnderlayCalibration,
} from "./EngineClient";

const ARTIFACT_PATHS: Record<EngineArtifact, string> = {
  ifc: "/model.ifc",
  glb: "/model.glb",
};

async function readError(res: Response): Promise<string> {
  try {
    const body = (await res.json()) as { error?: string };
    return body.error ?? res.statusText;
  } catch {
    return res.statusText;
  }
}

export class HttpEngineClient implements EngineClient {
  constructor(private readonly base = "") {}

  private url(path: string): string {
    return `${this.base}${path}`;
  }

  async getModel(): Promise<Model> {
    const res = await fetch(this.url("/model"));
    if (!res.ok) throw new EngineError(await readError(res), res.status);
    return (await res.json()) as Model;
  }

  async getChecks(): Promise<Finding[]> {
    const res = await fetch(this.url("/checks"));
    if (!res.ok) throw new EngineError(await readError(res), res.status);
    const body = (await res.json()) as { findings: Finding[] };
    return body.findings;
  }

  async getDetailIndex(): Promise<DetailIndexEntry[]> {
    const res = await fetch(this.url("/details"));
    if (!res.ok) throw new EngineError(await readError(res), res.status);
    const body = (await res.json()) as { details: DetailIndexEntry[] };
    return body.details;
  }

  async getDetail(key: string): Promise<DetailPayload> {
    const res = await fetch(this.url(`/detail?key=${encodeURIComponent(key)}`));
    if (!res.ok) throw new EngineError(await readError(res), res.status);
    return (await res.json()) as DetailPayload;
  }

  async getBom(): Promise<EngineBom> {
    const res = await fetch(this.url("/bom"));
    if (!res.ok) throw new EngineError(await readError(res), res.status);
    return (await res.json()) as EngineBom;
  }

  async appendDetailNote(key: string, text: string): Promise<string> {
    const res = await fetch(this.url("/detail/notes"), {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ key, text }),
    });
    if (!res.ok) throw new EngineError(await readError(res), res.status);
    const body = (await res.json()) as { notes_markdown: string };
    return body.notes_markdown;
  }

  async patchPlan(ops: PatchOp[], revision: string): Promise<PatchResult> {
    const res = await fetch(this.url("/plan"), {
      method: "PATCH",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ ops, revision }),
    });
    if (res.status === 409) throw new RevisionConflict(await readError(res));
    if (!res.ok) throw new EngineError(await readError(res), res.status);
    return (await res.json()) as PatchResult;
  }

  async runMacro(request: MacroRequest, revision: string): Promise<MacroResult> {
    const res = await fetch(this.url("/macro"), {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ ...request, revision }),
    });
    if (res.status === 409) throw new RevisionConflict(await readError(res));
    if (!res.ok) throw new EngineError(await readError(res), res.status);
    return (await res.json()) as MacroResult;
  }

  async previewMacro(request: MacroRequest, rehearse = false): Promise<PreviewGeometry> {
    const res = await fetch(this.url("/macro/preview"), {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(rehearse ? { ...request, rehearse: true } : request),
    });
    if (!res.ok) throw new EngineError(await readError(res), res.status);
    return (await res.json()) as PreviewGeometry;
  }

  async build(): Promise<BuildResult> {
    const res = await fetch(this.url("/build"), { method: "POST" });
    if (!res.ok) throw new EngineError(await readError(res), res.status);
    return (await res.json()) as BuildResult;
  }

  async undo(): Promise<HistoryResult> {
    return this.history("/undo");
  }

  async redo(): Promise<HistoryResult> {
    return this.history("/redo");
  }

  private async history(path: string): Promise<HistoryResult> {
    const res = await fetch(this.url(path), { method: "POST" });
    if (!res.ok) throw new EngineError(await readError(res), res.status);
    return (await res.json()) as HistoryResult;
  }

  async getArtifact(kind: EngineArtifact): Promise<Blob> {
    const path = ARTIFACT_PATHS[kind];
    if (!path) throw new EngineError(`unknown artifact ${kind}`, 400);
    const res = await fetch(this.url(path));
    if (!res.ok) throw new EngineError(await readError(res), res.status);
    return await res.blob();
  }

  async calibrateUnderlay(calibration: UnderlayCalibration): Promise<void> {
    const res = await fetch(this.url("/underlays/calibrate"), {
      method: "PUT",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(calibration),
    });
    if (!res.ok) throw new EngineError(await readError(res), res.status);
  }

  events(onEvent: (e: EngineEvent) => void, onStatus?: (up: boolean) => void): () => void {
    let closed = false;
    let ws: WebSocket | null = null;
    let retry: ReturnType<typeof setTimeout> | null = null;

    const wsUrl = () => {
      const proto = location.protocol === "https:" ? "wss:" : "ws:";
      const host = this.base ? this.base.replace(/^https?:/, proto) : `${proto}//${location.host}`;
      return `${host}/events`;
    };

    const connect = () => {
      if (closed) return;
      ws = new WebSocket(wsUrl());
      ws.onopen = () => onStatus?.(true);
      ws.onmessage = (ev) => {
        try {
          onEvent(JSON.parse(ev.data) as EngineEvent);
        } catch {
          /* ignore malformed frames */
        }
      };
      ws.onclose = () => {
        onStatus?.(false);
        if (!closed) retry = setTimeout(connect, 1500);
      };
      ws.onerror = () => ws?.close();
    };

    connect();
    return () => {
      closed = true;
      if (retry) clearTimeout(retry);
      ws?.close();
    };
  }
}

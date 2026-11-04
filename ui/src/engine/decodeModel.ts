import type { Model } from "../model/types";
import { bootMark } from "./bootMarks";

// The one decode of model.json bytes: `GET /model`'s body and the worker's `model` reply are
// the same bytes (server/model_payload.py), so both clients and the snapshot read them here.
export function decodeModel(bytes: ArrayBuffer | Uint8Array): Model {
  return decodeJson(bytes) as Model;
}

export function decodeJson(bytes: ArrayBuffer | Uint8Array): unknown {
  const t0 = performance.now();
  const out: unknown = JSON.parse(new TextDecoder("utf-8", { fatal: true }).decode(bytes));
  bootMark("modelParse", performance.now() - t0);
  return out;
}

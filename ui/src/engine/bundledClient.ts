import type { Model } from "../model/types";
import { loadModelSnapshot } from "./modelSnapshot";
import { loadBundledHouse } from "./openHouse";
import { PyodideEngineClient } from "./PyodideEngineClient";

// Constructing the client starts Pyodide immediately; its house promise resolves in parallel.
export function createBundledClient(
  onSnapshot?: (model: Model, client: PyodideEngineClient) => void,
): PyodideEngineClient {
  const house = loadBundledHouse();
  const client = new PyodideEngineClient(house.then((opened) => opened.files));
  if (onSnapshot) {
    void loadModelSnapshot().then((model) => onSnapshot(model, client)).catch(() => undefined);
  }
  return client;
}

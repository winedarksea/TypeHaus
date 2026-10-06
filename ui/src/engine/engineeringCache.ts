import type { EngineClient } from "./EngineClient";
import type { EngineeringCalculations } from "./engineeringTypes";

const cache = new WeakMap<EngineClient, {
  revision: string; payload: Promise<EngineeringCalculations>;
}>();

/** Coalesce in-flight requests; reopening also re-reads preferences and signoffs. */
export function loadEngineeringCalculations(
  client: EngineClient, revision: string,
): Promise<EngineeringCalculations> {
  const hit = cache.get(client);
  if (hit?.revision === revision) return hit.payload;
  const payload = client.getEngineeringCalculations();
  cache.set(client, { revision, payload });
  const evict = () => {
    if (cache.get(client)?.payload === payload) cache.delete(client);
  };
  void payload.then(evict, evict);
  return payload;
}

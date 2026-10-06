import type { EngineClient } from "./EngineClient";
import type { EngineeringCalculations } from "./engineeringTypes";
import { loadEngineeringCalculations } from "./engineeringCache";

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

function deferred() {
  let resolve!: (payload: EngineeringCalculations) => void;
  let reject!: (error: Error) => void;
  const promise = new Promise<EngineeringCalculations>((accept, fail) => { resolve = accept; reject = fail; });
  return { promise, resolve, reject };
}

export async function runEngineeringCacheTests() {
  const requests: ReturnType<typeof deferred>[] = [];
  const client = { getEngineeringCalculations: () => {
    const pending = deferred();
    requests.push(pending);
    return pending.promise;
  } } as unknown as EngineClient;
  const first = loadEngineeringCalculations(client, "r1");
  assert(loadEngineeringCalculations(client, "r1") === first, "same-revision concurrent reads coalesce");
  const second = loadEngineeringCalculations(client, "r2");
  requests[0].reject(new Error("superseded failure"));
  await first.catch(() => undefined);
  assert(loadEngineeringCalculations(client, "r2") === second, "an old rejection cannot evict a newer request");
  requests[1].resolve({ revision: "r2", files: {}, families: [] });
  await second;
  const fresh = loadEngineeringCalculations(client, "r2");
  assert(fresh !== second, "reopening re-reads preferences and signoffs even without a plan edit");
  requests[2].reject(new Error("failed"));
  await fresh.catch(() => undefined);
  const retry = loadEngineeringCalculations(client, "r2");
  assert(retry !== fresh, "a failed computation can be retried");
  requests[3].resolve({ revision: "r3", files: {}, families: [] });
  await retry;
  const afterMismatch = loadEngineeringCalculations(client, "r2");
  assert(afterMismatch !== retry, "a response for another revision is never reused");
  requests[4].resolve({ revision: "r2", files: {}, families: [] });
  await afterMismatch;
}

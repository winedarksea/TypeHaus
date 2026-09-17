// An input bound to an authoritative value: it shows the model's value until the user types,
// then holds the draft until the commit handler calls reset(). An edit from anywhere else — a
// drag, an arrow nudge, an agent editing the file — shows up in an untouched field at once
// instead of waiting for the panel to remount.
import { useCallback, useState } from "react";

export function useSyncedField(authoritative: string): [
  string, (value: string) => void, { dirty: boolean; reset: () => void },
] {
  const [draft, setDraft] = useState<string | null>(null);
  const reset = useCallback(() => setDraft(null), []);
  return [draft ?? authoritative, setDraft, { dirty: draft !== null, reset }];
}

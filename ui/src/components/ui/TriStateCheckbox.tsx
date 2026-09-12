// A checkbox that can also say "some of them": a group header over chips that are partly on.
// The DOM has the state (`indeterminate`) but not the attribute, so it is set by ref.
import { useEffect, useRef } from "react";

export function TriStateCheckbox({ state, onChange, label }: {
  state: "on" | "off" | "mixed";
  onChange: (checked: boolean) => void;
  label: string;
}) {
  const ref = useRef<HTMLInputElement>(null);
  useEffect(() => {
    if (ref.current) ref.current.indeterminate = state === "mixed";
  }, [state]);
  return (
    <input
      ref={ref}
      type="checkbox"
      aria-label={label}
      checked={state === "on"}
      // A mixed group turns fully on: the isolation gesture is "show me all of this".
      onChange={(e) => onChange(state === "mixed" ? true : e.target.checked)}
    />
  );
}

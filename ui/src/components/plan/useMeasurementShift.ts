import { useEffect, useState, type MutableRefObject } from "react";

// Keyboard events must refresh the tape even when the pointer stays still.
export function useMeasurementShift(active: boolean, shiftRef: MutableRefObject<boolean>) {
  const [pressed, setPressed] = useState(false);
  useEffect(() => {
    if (!active) return;
    const updateShift = (event: KeyboardEvent) => {
      shiftRef.current = event.shiftKey;
      setPressed(event.shiftKey);
    };
    const clearShift = () => {
      shiftRef.current = false;
      setPressed(false);
    };
    window.addEventListener("keydown", updateShift);
    window.addEventListener("keyup", updateShift);
    window.addEventListener("blur", clearShift);
    return () => {
      window.removeEventListener("keydown", updateShift);
      window.removeEventListener("keyup", updateShift);
      window.removeEventListener("blur", clearShift);
    };
  }, [active, shiftRef]);
  return [pressed, setPressed] as const;
}

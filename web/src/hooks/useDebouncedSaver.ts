import { useEffect, useRef } from "react";

export function useDebouncedSaver<T>(value: T, delayMs: number, fn: (v: T)=>void) {
  const timer = useRef<any>(null);
  useEffect(()=>{
    if (timer.current) clearTimeout(timer.current);
    timer.current = setTimeout(()=> fn(value), delayMs);
    return ()=> timer.current && clearTimeout(timer.current);
  }, [value, delayMs, fn]);
}

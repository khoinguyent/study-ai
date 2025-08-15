import { useLayoutEffect, useState } from "react";

export function useHeaderHeight(defaultH = 64) {
  const [h, setH] = useState(defaultH);

  useLayoutEffect(() => {
    const el = document.querySelector("[data-app-header]") as HTMLElement | null;
    const compute = () => setH(el?.getBoundingClientRect().height ?? defaultH);

    compute();
    const ro = el ? new ResizeObserver(compute) : null;
    window.addEventListener("resize", compute);

    if (el) ro?.observe(el);
    return () => {
      window.removeEventListener("resize", compute);
      ro?.disconnect();
    };
  }, [defaultH]);

  return h;
}

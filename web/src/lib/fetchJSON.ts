export async function fetchJSON<T>(
  url: string,
  init: RequestInit,
  attempts = 3,
  timeoutMs = 6000
): Promise<T> {
  let lastErr: any;
  for (let i = 0; i < attempts; i++) {
    const ctrl = new AbortController();
    const t = setTimeout(() => ctrl.abort(), timeoutMs);
    try {
      const res = await fetch(url, { ...init, signal: ctrl.signal });
      clearTimeout(t);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return (await res.json()) as T;
    } catch (e) {
      lastErr = e;
      if (i === attempts - 1) break;
      const backoff = 150 * 2 ** i + Math.random() * 50;
      await new Promise(r => setTimeout(r, backoff));
    }
  }
  throw lastErr;
}



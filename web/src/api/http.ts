import authService from "../services/auth";

export async function fetchJSON<T>(
  url: string,
  init: RequestInit = {},
  opts?: { withCredentials?: boolean }
): Promise<T> {
  const token = authService.getToken();
  const res = await fetch(url, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(init.headers || {}),
    },
    credentials: opts?.withCredentials ? "include" : init.credentials,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`${res.status} ${res.statusText} ${text}`);
  }
  return (await res.json()) as T;
}

import authService from "../services/auth";

export async function fetchJSON<T>(
  url: string,
  init: RequestInit = {},
  opts?: { withCredentials?: boolean }
): Promise<T> {
  const token = authService.getToken();
  const requestId = Math.random().toString(36).substring(2, 15);
  
  console.log('🌐 [HTTP] Making request:', {
    timestamp: new Date().toISOString(),
    requestId,
    url,
    method: init.method || 'GET',
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token.substring(0, 10)}...` } : {}),
      ...(init.headers || {}),
    },
    body: init.body ? (typeof init.body === 'string' ? init.body.substring(0, 200) + '...' : '[Binary/FormData]') : undefined,
    userAgent: navigator.userAgent
  });

  const startTime = Date.now();
  
  try {
    const res = await fetch(url, {
      ...init,
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...(init.headers || {}),
      },
      credentials: opts?.withCredentials ? "include" : init.credentials,
    });
    
    const responseTime = Date.now() - startTime;
    
    if (!res.ok) {
      const text = await res.text().catch(() => "");
      console.error('❌ [HTTP] Request failed:', {
        timestamp: new Date().toISOString(),
        requestId,
        url,
        status: res.status,
        statusText: res.statusText,
        responseTime: `${responseTime}ms`,
        errorText: text.substring(0, 200) + (text.length > 200 ? '...' : ''),
        headers: Object.fromEntries(res.headers.entries())
      });
      throw new Error(`${res.status} ${res.statusText} ${text}`);
    }
    
    const responseData = await res.json() as T;
    
    console.log('✅ [HTTP] Request successful:', {
      timestamp: new Date().toISOString(),
      requestId,
      url,
      status: res.status,
      responseTime: `${responseTime}ms`,
      responseSize: JSON.stringify(responseData).length,
      responsePreview: JSON.stringify(responseData).substring(0, 200) + (JSON.stringify(responseData).length > 200 ? '...' : ''),
      headers: Object.fromEntries(res.headers.entries())
    });
    
    return responseData;
  } catch (error) {
    const responseTime = Date.now() - startTime;
    console.error('💥 [HTTP] Request error:', {
      timestamp: new Date().toISOString(),
      requestId,
      url,
      responseTime: `${responseTime}ms`,
      error: error instanceof Error ? error.message : String(error),
      stack: error instanceof Error ? error.stack : undefined
    });
    throw error;
  }
}

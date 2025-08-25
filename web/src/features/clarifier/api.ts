import type { StartReq, StartResp, IngestReq, IngestResp } from './types';

export type ClarifierApiOpts = { apiBase?: string; token?: string };

const auth = (t?: string): Record<string, string> => (t ? { Authorization: `Bearer ${t}` } : {});

export async function startClarifier(req: StartReq, opts: ClarifierApiOpts): Promise<StartResp> {
  const url = `${opts.apiBase ?? ''}/clarifier/start`;
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...auth(opts.token) },
    body: JSON.stringify(req)
  });
  
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  
  return response.json();
}

export async function ingestClarifier(req: IngestReq, opts: ClarifierApiOpts): Promise<IngestResp> {
  const url = `${opts.apiBase ?? ''}/clarifier/ingest`;
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...auth(opts.token) },
    body: JSON.stringify(req)
  });
  
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  
  return response.json();
}

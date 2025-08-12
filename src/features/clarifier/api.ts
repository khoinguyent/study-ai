import { fetchJSON } from '../../api/fetchJSON';
import type { StartReq, StartResp, IngestReq, IngestResp } from './types';

export type ClarifierApiOpts = { apiBase?: string; token?: string };

const auth = (t?: string) => (t ? { Authorization: `Bearer ${t}` } : {});

export async function startClarifier(req: StartReq, opts: ClarifierApiOpts): Promise<StartResp> {
  const url = `${opts.apiBase ?? ''}/clarifier/start`;
  return fetchJSON<StartResp>(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...auth(opts.token) },
    body: JSON.stringify(req)
  });
}

export async function ingestClarifier(req: IngestReq, opts: ClarifierApiOpts): Promise<IngestResp> {
  const url = `${opts.apiBase ?? ''}/clarifier/ingest`;
  return fetchJSON<IngestResp>(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...auth(opts.token) },
    body: JSON.stringify(req)
  });
}


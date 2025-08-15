export type QuizState = "queued" | "running" | "completed" | "failed";
const RANK: Record<QuizState, number> = { queued: 0, running: 1, completed: 2, failed: 2 };

const buffers = new Map<string, { t: any; last: any }>();

export const jobKey = (x: { job_id?: string; quiz_id?: string }) =>
  x.quiz_id || x.job_id || "unknown";

export function coalesceByJob<T extends { job_id?: string; quiz_id?: string; status: QuizState }>(
  e: T,
  ms = 180,
  cb: (x: T) => void,
) {
  const key = jobKey(e);
  const buf = buffers.get(key) ?? { t: null, last: null as T | null };
  if (!buf.last || RANK[e.status] >= RANK[buf.last.status as QuizState]) buf.last = e;
  clearTimeout(buf.t as any);
  buf.t = setTimeout(() => {
    cb(buf.last as T);
    buffers.delete(key);
  }, ms);
  buffers.set(key, buf);
}

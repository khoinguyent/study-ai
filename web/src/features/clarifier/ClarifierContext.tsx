import React, { createContext, useCallback, useContext, useMemo, useReducer } from 'react';
import { startClarifier, ingestClarifier } from './api';
import type {
  ClarifierCallbacks, ClarifierEvent, ClarifierMessage, ClarifierState, FlowId, StartReq
} from './types';

const randId = () => Math.random().toString(36).slice(2);

type ProviderProps = {
  sessionId: string;
  userId: string;
  subjectId: string;
  docIds: string[];
  flow?: FlowId;
  apiBase?: string;
  token?: string;
  children: React.ReactNode;
  callbacks?: ClarifierCallbacks;
};

type Ctx = ClarifierState & {
  sendText: (text: string) => Promise<void>;
  restart: () => Promise<void>;
};

const ClarifierCtx = createContext<Ctx | null>(null);

function reducer(state: ClarifierState, ev: ClarifierEvent): ClarifierState {
  switch (ev.type) {
    case 'START_REQUEST':
      return { ...state, ready: false, error: null, messages: [], done: false };
    case 'START_SUCCESS':
      return {
        ...state,
        ready: true,
        error: null,
        messages: [...state.messages, { id: randId(), text: ev.payload.nextPrompt, quick: ev.payload.quick, ts: Date.now() }]
      };
    case 'START_FAILURE':
      return { ...state, ready: false, error: ev.error };
    case 'INGEST_REQUEST':
      return { ...state, sending: true, error: null };
    case 'INGEST_SUCCESS': {
      const msgs: ClarifierMessage[] = [];
      if (ev.payload.redirect && ev.payload.message) {
        msgs.push({ id: randId(), text: ev.payload.message, ts: Date.now() });
      }
      if (ev.payload.done) {
        msgs.push({ id: randId(), text: ev.payload.nextPrompt ?? 'Perfect! I\'m generating your questions now.', ts: Date.now() });
      } else if (ev.payload.nextPrompt) {
        msgs.push({ id: randId(), text: ev.payload.nextPrompt, quick: ev.payload.ui?.quick, ts: Date.now() });
      } else {
        msgs.push({ id: randId(), text: 'Please choose from the options above or type your choice.', ts: Date.now() });
      }
      return {
        ...state,
        sending: false,
        done: !!ev.payload.done,
        stage: ev.payload.stage ?? state.stage,
        filled: ev.payload.filled ?? state.filled,
        messages: [...state.messages, ...msgs],
      };
    }
    case 'INGEST_FAILURE':
      return { ...state, sending: false, error: ev.error };
    case 'PUSH_BOT':
      return { ...state, messages: [...state.messages, { id: randId(), text: ev.text, quick: ev.quick, ts: Date.now() }] };
    case 'RESET':
      return { ...state, ready: false, done: false, messages: [], error: null, stage: undefined, filled: undefined };
    default:
      return state;
  }
}

export function ClarifierProvider({
  sessionId, userId, subjectId, docIds,
  apiBase, token, flow = 'quiz_setup',
  children, callbacks
}: ProviderProps) {
  const [state, dispatch] = useReducer(reducer, {
    sessionId, userId, subjectId, docIds, apiBase, token, flow,
    ready: false, done: false, sending: false, error: null, messages: []
  });

  const start = useCallback(async () => {
    dispatch({ type: 'START_REQUEST' });
    try {
      const payload: StartReq = { sessionId, userId, subjectId, docIds, flow };
      const res = await startClarifier(payload, { apiBase, token });
      dispatch({ type: 'START_SUCCESS', payload: { nextPrompt: res.nextPrompt, quick: res.ui?.quick } });
    } catch (e: any) {
      const msg = `Failed to start: ${e.message ?? String(e)}`;
      dispatch({ type: 'START_FAILURE', error: msg });
      callbacks?.onError?.(msg);
    }
  }, [sessionId, userId, subjectId, docIds, apiBase, token, flow, callbacks]);

  const sendText = useCallback(async (text: string) => {
    if (!text.trim() || state.sending || state.done) return;
    dispatch({ type: 'INGEST_REQUEST', text });
    try {
      const res = await ingestClarifier({ sessionId, text }, { apiBase, token });
      dispatch({ type: 'INGEST_SUCCESS', payload: res });
      if (res.stage) callbacks?.onStageChange?.(res.stage, res.filled);
      if (res.done) callbacks?.onDone?.(res.filled);
    } catch (e: any) {
      const msg = `Send failed: ${e.message ?? String(e)}`;
      dispatch({ type: 'INGEST_FAILURE', error: msg });
      callbacks?.onError?.(msg);
    }
  }, [state.sending, state.done, sessionId, apiBase, token, callbacks]);

  const restart = useCallback(async () => {
    dispatch({ type: 'RESET' });
    await start();
  }, [start]);

  // auto-start on first mount
  React.useEffect(() => { start(); }, [start]);

  const value: Ctx = useMemo(() => ({ ...state, sendText, restart }), [state, sendText, restart]);

  return <ClarifierCtx.Provider value={value}>{children}</ClarifierCtx.Provider>;
}

export function useClarifier(): Ctx {
  const ctx = useContext(ClarifierCtx);
  if (!ctx) throw new Error('useClarifier must be used within ClarifierProvider');
  return ctx;
}

import { create } from 'zustand';

export type ClarifierParams = {
  sessionId: string;
  userId: string;
  subjectId: string;
  docIds: string[];
  apiBase?: string;
  token?: string;
  flow?: 'quiz_setup' | 'doc_summary' | 'doc_highlights' | 'doc_conclusion';
};

type ClarifierUIState = {
  isOpen: boolean;
  params?: ClarifierParams;
  open: (p: ClarifierParams) => void;
  close: () => void;
};

export const useClarifierUI = create<ClarifierUIState>((set) => ({
  isOpen: false,
  params: undefined,
  open: (params) => set({ isOpen: true, params }),
  close: () => set({ isOpen: false, params: undefined }),
}));



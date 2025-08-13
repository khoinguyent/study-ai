import { create } from "zustand";
import { persist } from "zustand/middleware";

type LaunchCtx = {
  userId?: string;
  subjectId?: string;
  docIds: string[];
};

type SelState = LaunchCtx & {
  setUser: (id?: string) => void;
  setSubject: (id?: string) => void;
  setDocs: (ids: string[]) => void;
  setLaunchCtx: (ctx: LaunchCtx) => void;
  clear: () => void;
};

export const useSelection = create<SelState>()(
  persist(
    (set) => ({
      userId: undefined,
      subjectId: undefined,
      docIds: [],
      setUser: (userId) => set({ userId }),
      setSubject: (subjectId) => set({ subjectId }),
      setDocs: (docIds) => set({ docIds }),
      setLaunchCtx: (ctx) => set(ctx),
      clear: () => set({ subjectId: undefined, docIds: [] }),
    }),
    { name: "studyai-selection" }
  )
);

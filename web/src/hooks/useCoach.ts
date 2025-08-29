import { useEffect, useRef, useState } from "react";

export type CoachMsg = { id: string; role: "bot" | "user"; text: string; ts: number };

export function useCoach(totalQs: number) {
  const [msgs, setMsgs] = useState<CoachMsg[]>([]);
  const milestones = useRef({ half: false, start: false, submitted: false });

  useEffect(()=>{
    // initial encouragement
    if (!milestones.current.start) {
      milestones.current.start = true;
      pushBot("🎯 Let's do this! Read carefully, trust your knowledge, and take it one question at a time.");
      pushBot(`You have ${totalQs} question${totalQs!==1?"s":""}. I believe in you! 💪`);
    }
    // eslint-disable-next-line
  }, [totalQs]);

  const pushBot = (text: string) => setMsgs(m => [...m, {id: Math.random().toString(36).slice(2), role:"bot", text, ts: Date.now()}]);
  const pushUser = (text: string) => setMsgs(m => [...m, {id: Math.random().toString(36).slice(2), role:"user", text, ts: Date.now()}]);

  const onProgress = (answeredCount: number) => {
    if (!milestones.current.half && answeredCount >= Math.ceil(totalQs/2)) {
      milestones.current.half = true;
      pushBot("Nice! You're halfway there. Keep the momentum going 🚀");
    }
  };

  const onSubmit = (score: number, max: number) => {
    if (!milestones.current.submitted) {
      milestones.current.submitted = true;
      const pct = Math.round((score / Math.max(1,max)) * 100);
      pushBot(`✅ Submitted! Score: ${score}/${max} (${pct}%). Proud of your effort—review and keep improving! 🌟`);
    }
  };

  return { msgs, pushBot, pushUser, onProgress, onSubmit };
}

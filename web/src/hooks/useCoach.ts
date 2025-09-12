import { useEffect, useRef, useState } from "react";

export type CoachMsg = { id: string; role: "bot" | "user"; text: string; ts: number };

// Feedback message arrays for different performance levels
const LOW_SCORE_MESSAGES = [
  "Don't worry—every quiz is a learning opportunity! Take some time to review the material and try again when you're ready. You've got this! 💪",
  "Every expert was once a beginner! This quiz shows you exactly what to focus on. Review the material and come back stronger! 🌱",
  "Learning is a journey, not a destination. Use this as a guide to identify areas for improvement. You're making progress! 📚",
  "Don't be discouraged! Every mistake is a chance to learn something new. Take a break, review, and try again! 🚀",
  "Remember: even the greatest minds had to start somewhere. This quiz is just one step in your learning journey! 💡",
  "It's okay to not know everything yet! This quiz helps you see what to study more. Keep going—you're doing great! 🌟"
];

const MEDIUM_SCORE_MESSAGES = [
  "Good effort! You're on the right track. A bit more practice will help you master this topic. Keep studying! 📚",
  "Nice work! You're getting there. A little more review and you'll have this topic down pat! 🎯",
  "Solid performance! You clearly understand the basics. A few more practice sessions and you'll be an expert! 🔥",
  "Well done! You're making good progress. Keep up the momentum and you'll master this in no time! ⚡",
  "Great job! You're building a strong foundation. A bit more practice will take you to the next level! 🏗️",
  "Excellent progress! You're halfway to mastery. Keep studying and you'll get there! 🎓"
];

const HIGH_SCORE_MESSAGES = [
  "Excellent work! You really know your stuff! Congratulations on such a great performance! 🌟",
  "Outstanding! You've clearly mastered this material. Your hard work is paying off! 🏆",
  "Fantastic job! You're absolutely crushing it! This level of understanding is impressive! 🚀",
  "Amazing performance! You've got this topic down to a science. Well done! 🧠",
  "Incredible work! Your dedication to learning really shows. You should be proud! 🎉",
  "Brilliant! You've demonstrated excellent understanding. Keep up the fantastic work! ✨"
];

const INITIAL_MESSAGES = [
  "Ready to tackle {count} question{plural}? Take a deep breath and let's begin! 🌟",
  "Let's dive into these {count} question{plural}! I'm here to cheer you on every step of the way! 💪",
  "Time to show what you know! {count} question{plural} await—you've got this! 🎯",
  "Here we go! {count} question{plural} of knowledge coming your way. Trust yourself! 🚀",
  "Let's make this quiz count! {count} question{plural} to demonstrate your skills! ⭐",
  "Ready for the challenge? These {count} question{plural} are no match for you! 🔥"
];

const HALFWAY_MESSAGES = [
  "Nice! You're halfway there. Keep the momentum going 🚀",
  "Great progress! You're doing amazing—keep it up! 💪",
  "You're crushing it! The finish line is in sight! 🎯",
  "Excellent work so far! You're on fire! 🔥",
  "Keep going strong! You're doing fantastic! ⚡",
  "Amazing pace! You've got this in the bag! 🌟"
];

// Helper function to get random message from array
const getRandomMessage = (messages: string[]): string => {
  return messages[Math.floor(Math.random() * messages.length)];
};

// Helper function to format initial message with count
const formatInitialMessage = (totalQs: number): string => {
  const message = getRandomMessage(INITIAL_MESSAGES);
  const plural = totalQs !== 1 ? "s" : "";
  return message.replace("{count}", totalQs.toString()).replace("{plural}", plural);
};

export function useCoach(totalQs: number) {
  const [msgs, setMsgs] = useState<CoachMsg[]>([]);
  const milestones = useRef({ half: false, start: false, submitted: false });

  useEffect(()=>{
    // initial encouragement - only when we have actual questions
    if (!milestones.current.start && totalQs > 0) {
      milestones.current.start = true;
      pushBot("🎯 Let's do this! Read carefully, trust your knowledge, and take it one question at a time.");
      pushBot(formatInitialMessage(totalQs));
    }
    // eslint-disable-next-line
  }, [totalQs]);

  const pushBot = (text: string) => setMsgs(m => [...m, {id: Math.random().toString(36).slice(2), role:"bot", text, ts: Date.now()}]);
  const pushUser = (text: string) => setMsgs(m => [...m, {id: Math.random().toString(36).slice(2), role:"user", text, ts: Date.now()}]);

  const onProgress = (answeredCount: number) => {
    if (!milestones.current.half && answeredCount >= Math.ceil(totalQs/2)) {
      milestones.current.half = true;
      pushBot(getRandomMessage(HALFWAY_MESSAGES));
    }
  };

  const onSubmit = (score: number, max: number) => {
    if (!milestones.current.submitted) {
      milestones.current.submitted = true;
      const pct = Math.round((score / Math.max(1,max)) * 100);
      
      let feedbackMessage: string;
      if (pct < 50) {
        feedbackMessage = getRandomMessage(LOW_SCORE_MESSAGES);
      } else if (pct >= 50 && pct < 80) {
        feedbackMessage = getRandomMessage(MEDIUM_SCORE_MESSAGES);
      } else {
        feedbackMessage = getRandomMessage(HIGH_SCORE_MESSAGES);
      }
      
      pushBot(`✅ Submitted! Score: ${score}/${max} (${pct}%). ${feedbackMessage}`);
    }
  };

  return { msgs, pushBot, pushUser, onProgress, onSubmit };
}

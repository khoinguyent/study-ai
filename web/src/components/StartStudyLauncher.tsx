"use client";

import React from "react";
import { useNavigate } from "react-router-dom";
import LeftClarifierSheet, { ClarifierResult } from "./LeftClarifierSheet";

export default function StartStudyLauncher({
  selectedDocIds,
}: {
  selectedDocIds: string[];
}) {
  const [open, setOpen] = React.useState(false);
  const navigate = useNavigate();

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 text-white font-semibold hover:bg-blue-500"
      >
        ▶ Start Study Session
      </button>

      <LeftClarifierSheet
        open={open}
        onClose={() => setOpen(false)}
        maxQuestions={50}
        suggested={15}
        onConfirm={(r: ClarifierResult) => {
          // TODO: call backend later; for now persist and go
          localStorage.setItem("questionCount", String(r.questionCount));
          localStorage.setItem("questionTypes", JSON.stringify(r.questionTypes));
          localStorage.setItem("difficulty", r.difficulty);
          localStorage.setItem("docIds", JSON.stringify(selectedDocIds));
          navigate("/study-session");
        }}
      />
    </>
  );
}

export type QuestionType =
  | "single_choice"
  | "multiple_choice"
  | "true_false"
  | "fill_blank"
  | "short_answer";

export type Choice = { id: string; text: string };

export type QuestionBase = {
  id: string;
  type: QuestionType;
  prompt: string;
  points?: number;
  explanation?: string;        // revealed after submit
};

export type SingleChoiceQ = QuestionBase & {
  type: "single_choice";
  options: Choice[];
  correctChoiceIds?: string[]; // server sends after submit
};

export type MultipleChoiceQ = QuestionBase & {
  type: "multiple_choice";
  options: Choice[];
  correctChoiceIds?: string[];
};

export type TrueFalseQ = QuestionBase & {
  type: "true_false";
  trueLabel?: string;
  falseLabel?: string;
  correct?: boolean;           // after submit
};

export type FillBlankQ = QuestionBase & {
  type: "fill_blank";
  blanks: number;              // number of blanks in prompt
  labels?: string[];           // optional labels per blank
  correctValues?: string[];    // after submit
};

export type ShortAnswerQ = QuestionBase & {
  type: "short_answer";
  minWords?: number;
  rubric?: string;
};

export type Question =
  | SingleChoiceQ
  | MultipleChoiceQ
  | TrueFalseQ
  | FillBlankQ
  | ShortAnswerQ;

export type QuizPayload = {
  sessionId: string;
  quizId: string;
  questions: Question[];
};

export type AnswerMap = {
  [questionId: string]:
    | { kind: "single"; choiceId: string | null }
    | { kind: "multiple"; choiceIds: string[] }
    | { kind: "boolean"; value: boolean | null }
    | { kind: "blanks"; values: string[] }      // length = blanks
    | { kind: "text"; value: string };
};

export type SubmitResult = {
  scorePercent: number;
  correctCount: number;
  total: number;
  // The graded questions with explanations/correct answers included
  graded: Question[];
};

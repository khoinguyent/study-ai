export type Option = { id: string; text: string; isCorrect?: boolean };

export type Question =
  | {
      id: string;
      type: "single_choice";
      prompt: string;
      options: Option[];                 // exactly one isCorrect
      explanation?: string;
      points?: number;
    }
  | {
      id: string;
      type: "multiple_choice";
      prompt: string;
      options: Option[];                 // >=1 isCorrect
      explanation?: string;
      points?: number;
    }
  | {
      id: string;
      type: "true_false";
      prompt: string;
      correct: boolean;                  // true or false
      trueLabel?: string;
      falseLabel?: string;
      explanation?: string;
      points?: number;
    }
  | {
      id: string;
      type: "fill_blank";
      prompt: string;
      blanks: number;
      labels?: string[];
      correctValues?: string[];          // case-insensitive compare
      explanation?: string;
      points?: number;
    }
  | {
      id: string;
      type: "short_answer";
      prompt: string;
      expected?: string[];               // optional keywords
      explanation?: string;
      points?: number;
      minWords?: number;
      rubric?: string;
    };

export type Answer =
  | { kind: "single"; choiceId: string | null }
  | { kind: "multiple"; choiceIds: string[] }
  | { kind: "boolean"; value: boolean | null }
  | { kind: "blanks"; values: string[] }
  | { kind: "text"; value: string };

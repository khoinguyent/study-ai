import type { QuestionType, ApiQuestionType } from "../types";

export const toApiType: Record<QuestionType, ApiQuestionType> = {
  mcq: "mcq",
  truefalse: "true_false",
  fill_blank: "fill_in_blank",
  short: "short_answer",
};

export const fromApiType: Record<ApiQuestionType, QuestionType> = {
  mcq: "mcq",
  true_false: "truefalse",
  fill_in_blank: "fill_blank",
  short_answer: "short",
};

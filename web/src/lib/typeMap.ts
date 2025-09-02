import type { QuestionType, ApiQuestionType } from "../types";

export const toApiType: Record<QuestionType, ApiQuestionType> = {
  single_choice: "mcq",
  multiple_choice: "mcq",
  true_false: "true_false",
  fill_blank: "fill_in_blank",
  short_answer: "short_answer",
};

export const fromApiType: Record<ApiQuestionType, QuestionType> = {
  mcq: "single_choice",
  true_false: "true_false",
  fill_in_blank: "fill_blank",
  short_answer: "short_answer",
};

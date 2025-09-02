// User related types
export interface User {
  id: string;
  username: string;
  email: string;
  created_at: string;
  updated_at?: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  name: string;
  email: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

// Subject/Category related types
export interface Subject {
  id: string;
  name: string;
  description?: string;
  icon?: string;
  color_theme?: string;
  user_id: string;
  document_count: number;
  avg_score: number;
  created_at: string;
  updated_at?: string;
  categories?: Category[];
}

export interface Category {
  id: string;
  name: string;
  description?: string;
  subject_id: string;
  user_id: string;
  document_count: number;
  avg_score: number;
  created_at: string;
  updated_at?: string;
  documents?: Document[];
}

export interface SubjectCreate {
  name: string;
  description?: string;
  icon?: string;
  color_theme?: string;
}

export interface CategoryCreate {
  name: string;
  description?: string;
  subject_id: string;
}

// Document related types
export interface Document {
  id: string;
  title: string;
  filename: string;
  file_path?: string;
  file_size: number;
  mime_type: string;
  category_id: string;
  user_id: string;
  status: 'processing' | 'completed' | 'ready' | 'failed';
  created_at: string;
  updated_at: string;
}

// Quiz related types
export interface Quiz {
  id: string;
  title: string;
  category_id: string;
  user_id: string;
  questions: Question[] | string;
  status: 'processing' | 'completed' | 'ready' | 'failed';
  created_at: string;
  updated_at: string;
}

export interface Question {
  id: string;
  type: QuestionType;           // REQUIRED: Standardized type field
  prompt: string;               // The question text (renamed from 'question')
  options?: QuestionOption[];
  answer?: string | boolean;     // Legacy field for backward compatibility
  explanation?: string;
  points?: number;              // Points for this question
  // Additional fields for specific question types
  correctChoiceId?: string;     // For single choice questions
  correctChoiceIds?: string[];  // For multiple choice questions
  correct?: boolean;            // For true/false questions
  blanks?: number;              // For fill in the blank questions
  labels?: string[];            // For fill in the blank questions
  correctValues?: string[];     // For fill in the blank questions
  minWords?: number;            // For short answer questions
  rubric?: string;              // For short answer questions
}

export interface QuestionOption {
  id: string;
  text: string;                  // Option text (renamed from 'content')
  content?: string;             // Legacy field for backward compatibility
  isCorrect?: boolean;
}

// API Response types
export interface ApiResponse<T> {
  data: T;
  message?: string;
  status: string;
}

export interface ApiError {
  detail: string;
  status_code: number;
}

// Dashboard stats
export interface DashboardStats {
  documentSets: number;
  documents: number;
  avgScore: number;
}

// Component props types
export interface ProtectedRouteProps {
  children: React.ReactNode;
}

export interface PublicRouteProps {
  children: React.ReactNode;
}

// Question and Budget types
export type QuestionType = 
  | "single_choice"    // Multiple choice with one correct answer
  | "multiple_choice"  // Multiple choice with multiple correct answers
  | "true_false"       // True/False questions
  | "fill_blank"       // Fill in the blank questions
  | "short_answer";    // Short answer questions

// Legacy type for backward compatibility
export type LegacyQuestionType = "mcq" | "short" | "truefalse" | "fill_blank";

// Percentages (0..100) per selected type; sum must be 100 across selected types
export type QuestionMix = Partial<Record<QuestionType, number>>;

export type Difficulty = "easy" | "medium" | "hard" | "mixed";

export interface QuestionTypeConfig {
  type: QuestionType;
  label: string;
  count: number;
  maxCount?: number;
}

export interface BudgetEstimate {
  maxQuestions: number;
  perQuestionCost: number;
  totalCost: number;
  notes?: string;
  breakdown?: {
    evidence?: string;
    cost?: string;
    policy?: string;
    lengthGuard?: string;
  };
}

// Quiz Generation types
export type ApiQuestionType = "mcq" | "true_false" | "fill_in_blank" | "short_answer";

export interface GenerateQuizRequest {
  docIds: string[];
  numQuestions: number;
  questionTypes: ApiQuestionType[];
  difficulty: "easy" | "medium" | "hard";
  language?: "auto" | string;
}

export interface GenerateQuizResponse {
  job_id: string;
  quiz_id: string;
  session_id?: string;  // Added by API Gateway after session creation
  message?: string;
  status: string;  // Backend always returns this
  quiz?: any;
} 
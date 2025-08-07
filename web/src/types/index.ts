// User related types
export interface User {
  id: string;
  name: string;
  email: string;
  created_at: string;
  updated_at: string;
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

// Category/Subject related types
export interface Category {
  id: string;
  name: string;
  description?: string;
  user_id: string;
  document_count?: number;
  avg_score?: number;
  created_at: string;
  updated_at: string;
}

export interface CategoryCreate {
  name: string;
  description?: string;
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
  status: 'processing' | 'completed' | 'failed';
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
  status: 'processing' | 'completed' | 'failed';
  created_at: string;
  updated_at: string;
}

export interface Question {
  id: string;
  question: string;
  options: QuestionOption[];
  correct_answer: number;
  explanation?: string;
}

export interface QuestionOption {
  text: string;
  is_correct: boolean;
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
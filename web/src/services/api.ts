import {
  User,
  LoginRequest,
  RegisterRequest,
  AuthResponse,
  Subject,
  Category,
  SubjectCreate,
  CategoryCreate,
  Document,
  Quiz,
  ApiResponse,
  ApiError
} from '../types';
import authService from './auth'; // Import the new auth service

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

class ApiService {
  private getAuthHeaders(): HeadersInit {
    return authService.getAuthHeaders(); // Use authService to get headers
  }

  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      const errorData: ApiError = await response.json();
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }
    return response.json();
  }

  // Auth endpoints
  async login(credentials: LoginRequest): Promise<AuthResponse> {
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(credentials),
    });
    return this.handleResponse<AuthResponse>(response);
  }

  async register(userData: RegisterRequest): Promise<AuthResponse> {
    const response = await fetch(`${API_BASE_URL}/auth/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(userData),
    });
    return this.handleResponse<AuthResponse>(response);
  }

  async getCurrentUser(): Promise<User> {
    const response = await fetch(`${API_BASE_URL}/auth/me`, {
      headers: this.getAuthHeaders(),
    });
    return this.handleResponse<User>(response);
  }

  // Subjects endpoints
  async getSubjects(): Promise<Subject[]> {
    const response = await fetch(`${API_BASE_URL}/subjects`, {
      headers: this.getAuthHeaders(),
    });
    return this.handleResponse<Subject[]>(response);
  }

  async createSubject(subjectData: SubjectCreate): Promise<Subject> {
    const response = await fetch(`${API_BASE_URL}/subjects`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(subjectData),
    });
    return this.handleResponse<Subject>(response);
  }

  async getSubject(id: string): Promise<Subject> {
    const response = await fetch(`${API_BASE_URL}/subjects/${id}`, {
      headers: this.getAuthHeaders(),
    });
    return this.handleResponse<Subject>(response);
  }

  async updateSubject(id: string, subjectData: Partial<SubjectCreate>): Promise<Subject> {
    const response = await fetch(`${API_BASE_URL}/subjects/${id}`, {
      method: 'PUT',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(subjectData),
    });
    return this.handleResponse<Subject>(response);
  }

  async deleteSubject(id: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/subjects/${id}`, {
      method: 'DELETE',
      headers: this.getAuthHeaders(),
    });
    if (!response.ok) {
      throw new Error(`Failed to delete subject: ${response.status}`);
    }
  }

  // Categories endpoints
  async getCategories(subjectId?: string): Promise<Category[]> {
    const url = subjectId 
      ? `${API_BASE_URL}/subjects/${subjectId}/categories`
      : `${API_BASE_URL}/categories`;
    
    const response = await fetch(url, {
      headers: this.getAuthHeaders(),
    });
    return this.handleResponse<Category[]>(response);
  }

  async createCategory(categoryData: CategoryCreate): Promise<Category> {
    const response = await fetch(`${API_BASE_URL}/categories`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(categoryData),
    });
    return this.handleResponse<Category>(response);
  }

  async getCategory(id: string): Promise<Category> {
    const response = await fetch(`${API_BASE_URL}/categories/${id}`, {
      headers: this.getAuthHeaders(),
    });
    return this.handleResponse<Category>(response);
  }

  async updateCategory(id: string, categoryData: Partial<CategoryCreate>): Promise<Category> {
    const response = await fetch(`${API_BASE_URL}/categories/${id}`, {
      method: 'PUT',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(categoryData),
    });
    return this.handleResponse<Category>(response);
  }

  async deleteCategory(id: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/categories/${id}`, {
      method: 'DELETE',
      headers: this.getAuthHeaders(),
    });
    if (!response.ok) {
      throw new Error(`Failed to delete category: ${response.status}`);
    }
  }

  // Documents endpoints
  async getDocuments(categoryId?: string): Promise<Document[]> {
    const url = categoryId 
      ? `${API_BASE_URL}/documents?category_id=${categoryId}`
      : `${API_BASE_URL}/documents`;
    
    const response = await fetch(url, {
      headers: this.getAuthHeaders(),
    });
    return this.handleResponse<Document[]>(response);
  }

  async getCategoryDocuments(categoryId: string, page: number = 1, pageSize: number = 10): Promise<{
    documents: Document[];
    total_count: number;
    page: number;
    page_size: number;
    has_more: boolean;
  }> {
    const response = await fetch(
      `${API_BASE_URL}/categories/${categoryId}/documents?page=${page}&page_size=${pageSize}`,
      {
        headers: this.getAuthHeaders(),
      }
    );
    return this.handleResponse(response);
  }

  async uploadDocument(file: File, categoryId: string): Promise<Document> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('category_id', categoryId);

    const response = await fetch(`${API_BASE_URL}/upload`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authService.getToken()}`, // Use authService to get token
      },
      body: formData,
    });
    return this.handleResponse<Document>(response);
  }

  async uploadDocuments(formData: FormData): Promise<Document[]> {
    const token = authService.getToken();
    const headers: HeadersInit = {
      'Authorization': `Bearer ${token}`,
    };
    
    const response = await fetch(`${API_BASE_URL}/upload-multiple`, {
      method: 'POST',
      headers,
      body: formData,
    });
    return this.handleResponse<Document[]>(response);
  }

  async deleteDocument(id: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/documents/${id}`, {
      method: 'DELETE',
      headers: this.getAuthHeaders(),
    });
    if (!response.ok) {
      throw new Error(`Failed to delete document: ${response.status}`);
    }
  }

  async downloadDocument(documentId: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/documents/${documentId}/download`, {
      method: 'GET',
      headers: this.getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error(`Failed to download document: ${response.status}`);
    }

    // Get filename from Content-Disposition header
    const contentDisposition = response.headers.get('Content-Disposition');
    let filename = 'download';
    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename=([^;]+)/);
      if (filenameMatch) {
        filename = filenameMatch[1].replace(/"/g, '');
      }
    }

    // Create blob and download
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  }

  // Quiz endpoints
  async generateQuiz(categoryId: string, numQuestions: number = 5): Promise<Quiz> {
    const response = await fetch(`${API_BASE_URL}/quiz/generate/category`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify({
        category_id: categoryId,
        num_questions: numQuestions
      }),
    });
    return this.handleResponse<Quiz>(response);
  }

  async getQuiz(id: string): Promise<Quiz> {
    const response = await fetch(`${API_BASE_URL}/quiz/${id}`, {
      headers: this.getAuthHeaders(),
    });
    return this.handleResponse<Quiz>(response);
  }

  async getQuizzes(categoryId?: string): Promise<Quiz[]> {
    const url = categoryId
      ? `${API_BASE_URL}/quiz?category_id=${categoryId}`
      : `${API_BASE_URL}/quiz`;

    const response = await fetch(url, {
      headers: this.getAuthHeaders(),
    });
    return this.handleResponse<Quiz[]>(response);
  }

  // Health check
  async healthCheck(): Promise<{ status: string }> {
    const response = await fetch(`${API_BASE_URL}/health`);
    return this.handleResponse<{ status: string }>(response);
  }
}

export const apiService = new ApiService();
export default apiService; 
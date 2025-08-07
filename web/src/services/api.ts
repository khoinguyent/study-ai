import { 
  User, 
  LoginRequest, 
  RegisterRequest, 
  AuthResponse, 
  Category, 
  CategoryCreate,
  Document,
  Quiz,
  ApiResponse,
  ApiError 
} from '../types';

const API_BASE_URL = process.env.REACT_APP_API_URL || '';

class ApiService {
  private getAuthHeaders(): HeadersInit {
    const token = localStorage.getItem('token');
    return {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` })
    };
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

  // Categories/Subjects endpoints
  async getCategories(): Promise<Category[]> {
    const response = await fetch(`${API_BASE_URL}/subjects`, {
      headers: this.getAuthHeaders(),
    });
    return this.handleResponse<Category[]>(response);
  }

  async createCategory(categoryData: CategoryCreate): Promise<Category> {
    const response = await fetch(`${API_BASE_URL}/subjects`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(categoryData),
    });
    return this.handleResponse<Category>(response);
  }

  async getCategory(id: string): Promise<Category> {
    const response = await fetch(`${API_BASE_URL}/subjects/${id}`, {
      headers: this.getAuthHeaders(),
    });
    return this.handleResponse<Category>(response);
  }

  async updateCategory(id: string, categoryData: Partial<CategoryCreate>): Promise<Category> {
    const response = await fetch(`${API_BASE_URL}/subjects/${id}`, {
      method: 'PUT',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(categoryData),
    });
    return this.handleResponse<Category>(response);
  }

  async deleteCategory(id: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/subjects/${id}`, {
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

  async uploadDocument(file: File, categoryId: string): Promise<Document> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('category_id', categoryId);

    const response = await fetch(`${API_BASE_URL}/documents/upload`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
      },
      body: formData,
    });
    return this.handleResponse<Document>(response);
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
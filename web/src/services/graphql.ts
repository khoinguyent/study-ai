const GRAPHQL_ENDPOINT = `/graphql`;

export interface GraphQLRequest {
  query: string;
  variables?: Record<string, any>;
}

export interface GraphQLResponse<T = any> {
  data?: T;
  errors?: Array<{
    message: string;
    locations?: Array<{
      line: number;
      column: number;
    }>;
    path?: Array<string | number>;
  }>;
}

class GraphQLClient {
  private endpoint: string;

  constructor(endpoint: string) {
    this.endpoint = endpoint;
  }

  async request<T = any>(request: GraphQLRequest): Promise<T> {
    const token = localStorage.getItem('study_ai_token');
    
    const response = await fetch(this.endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { 'Authorization': `Bearer ${token}` } : {})
      },
      body: JSON.stringify(request)
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const result: GraphQLResponse<T> = await response.json();

    if (result.errors && result.errors.length > 0) {
      throw new Error(result.errors[0].message);
    }

    if (!result.data) {
      throw new Error('No data returned from GraphQL query');
    }

    return result.data;
  }

  // Dashboard query
  async getDashboardData(userId: string) {
    const query = `
      query GetDashboard($userId: String!) {
        dashboard(userId: $userId) {
          stats {
            totalSubjects
            totalCategories
            totalDocuments
            avgScore
          }
          subjects {
            id
            name
            description
            icon
            colorTheme
            totalDocuments
            avgScore
            createdAt
            updatedAt
            categories {
              id
              name
              description
              totalDocuments
              avgScore
              createdAt
              updatedAt
              documents {
                id
                name
                filename
                contentType
                fileSize
                status
                s3Url
                createdAt
                updatedAt
              }
            }
          }
        }
      }
    `;

    return this.request({
      query,
      variables: { userId }
    });
  }

  // Subjects only query
  async getSubjects(userId: string) {
    const query = `
      query GetSubjects($userId: String!) {
        subjects(userId: $userId) {
          id
          name
          description
          icon
          colorTheme
          totalDocuments
          avgScore
          createdAt
          updatedAt
          categories {
            id
            name
            description
            totalDocuments
            avgScore
            createdAt
            updatedAt
            documents {
              id
              name
              filename
              contentType
              fileSize
              status
              s3Url
              createdAt
              updatedAt
            }
          }
        }
      }
    `;

    return this.request({
      query,
      variables: { userId }
    });
  }

  // Stats only query
  async getStats(userId: string) {
    const query = `
      query GetStats($userId: String!) {
        stats(userId: $userId) {
          totalSubjects
          totalCategories
          totalDocuments
          avgScore
        }
      }
    `;

    return this.request({
      query,
      variables: { userId }
    });
  }
}

// Export a singleton instance
export const graphqlClient = new GraphQLClient(GRAPHQL_ENDPOINT);

// Export types for the response data
export interface Document {
  id: string;
  name: string;
  filename: string;
  contentType: string;
  fileSize: number;
  status: string;
  s3Url: string;
  createdAt: string;
  updatedAt?: string;
}

export interface Category {
  id: string;
  name: string;
  description: string;
  totalDocuments: number;
  avgScore: number;
  createdAt: string;
  updatedAt?: string;
  documents: Document[];
}

export interface Subject {
  id: string;
  name: string;
  description: string;
  icon?: string;
  colorTheme?: string;
  totalDocuments: number;
  avgScore: number;
  createdAt: string;
  updatedAt?: string;
  categories: Category[];
}

export interface DashboardStats {
  totalSubjects: number;
  totalCategories: number;
  totalDocuments: number;
  avgScore: number;
}

export interface DashboardData {
  stats: DashboardStats;
  subjects: Subject[];
}

import { QueryRequest, QueryResponse, ChatSession } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

class APIService {
  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.statusText}`);
    }

    return response.json();
  }

  async sendMessage(request: QueryRequest): Promise<QueryResponse> {
    return this.request<QueryResponse>('/chat', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async getSessions(): Promise<ChatSession[]> {
    return this.request<ChatSession[]>('/sessions');
  }

  async createSession(title: string): Promise<ChatSession> {
    return this.request<ChatSession>('/sessions', {
      method: 'POST',
      body: JSON.stringify({ title }),
    });
  }

  async deleteSession(sessionId: string): Promise<void> {
    await this.request(`/sessions/${sessionId}`, {
      method: 'DELETE',
    });
  }

  async updateSession(sessionId: string, updates: Partial<ChatSession>): Promise<ChatSession> {
    return this.request<ChatSession>(`/sessions/${sessionId}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
  }

  async getHealthCheck(): Promise<{ status: string }> {
    return this.request<{ status: string }>('/health');
  }

  async uploadFile(file: File): Promise<{ url: string; metadata: any }> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE_URL}/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Upload failed: ${response.statusText}`);
    }

    return response.json();
  }

  async getDataStatistics(): Promise<any> {
    return this.request<any>('/data/statistics');
  }

  async searchData(query: string, options: any = {}): Promise<any> {
    const params = new URLSearchParams({
      query,
      ...options
    });
    
    return this.request<any>(`/data/search?${params}`);
  }

  async startScraping(options: any = {}): Promise<any> {
    return this.request<any>('/data/scrape', {
      method: 'POST',
      body: JSON.stringify(options),
    });
  }

  // Real-time data methods
  async getRealTimeWeatherData(location?: { lat: number; lon: number }): Promise<any> {
    const params = location ? `?lat=${location.lat}&lon=${location.lon}` : '';
    return this.request<any>(`/data/weather/realtime${params}`);
  }

  async getRealTimeOceanData(location?: { lat: number; lon: number }): Promise<any> {
    const params = location ? `?lat=${location.lat}&lon=${location.lon}` : '';
    return this.request<any>(`/data/ocean/realtime${params}`);
  }

  async getSatelliteStatus(): Promise<any> {
    return this.request<any>('/data/satellites/status');
  }
}

export const apiService = new APIService();
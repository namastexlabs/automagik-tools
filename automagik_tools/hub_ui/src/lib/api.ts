import { clearUserInfo } from './auth';

const TOKEN_STORAGE_KEY = 'hub_access_token';
const API_BASE_URL = '/api';

// Token management (WorkOS AuthKit)
export function getAccessToken(): string | null {
  return localStorage.getItem(TOKEN_STORAGE_KEY);
}

export function setAccessToken(token: string): void {
  localStorage.setItem(TOKEN_STORAGE_KEY, token);
}

export function removeAccessToken(): void {
  localStorage.removeItem(TOKEN_STORAGE_KEY);
  clearUserInfo();
}

export function isAuthenticated(): boolean {
  return !!getAccessToken();
}

// API client helper
async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getAccessToken();

  if (!token && !endpoint.includes('/health') && !endpoint.includes('/info')) {
    throw new Error('Not authenticated. Please login.');
  }

  const url = `${API_BASE_URL}${endpoint}`;

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...options.headers as Record<string, string>,
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    if (response.status === 401 || response.status === 403) {
      removeAccessToken();
      window.location.href = '/login';
      throw new Error('Authentication failed');
    }

    const error = await response.text();
    throw new Error(error || `Request failed with status ${response.status}`);
  }

  return response.json();
}

// Tool types
export interface Tool {
  tool_name: string;
  display_name: string;
  description: string;
  category: string;
  auth_type: string;
  config_schema: Record<string, any>;
  required_oauth?: string[];
}

export interface UserTool {
  tool_name: string;
  config: Record<string, any>;
  enabled: boolean;
  created_at: string;
  updated_at: string;
}

export interface ToolConfig {
  [key: string]: any;
}

// API methods
export const api = {
  // Test authentication
  async testAuth(): Promise<boolean> {
    try {
      await apiRequest('/user/tools');
      return true;
    } catch (error) {
      console.error('[API] Auth test failed:', error);
      return false;
    }
  },

  // Tool Catalogue API
  catalogue: {
    async list(): Promise<Tool[]> {
      return apiRequest('/tools/catalogue');
    },

    async getMetadata(toolName: string): Promise<Tool> {
      return apiRequest(`/tools/${toolName}/metadata`);
    },

    async getSchema(toolName: string): Promise<{
      tool_name: string;
      config_schema: Record<string, any>;
      auth_type: string;
      required_oauth: string[];
    }> {
      return apiRequest(`/tools/${toolName}/schema`);
    },
  },

  // User Tools API
  tools: {
    async list(): Promise<UserTool[]> {
      return apiRequest('/user/tools');
    },

    async get(toolName: string): Promise<UserTool> {
      return apiRequest(`/user/tools/${toolName}`);
    },

    async configure(toolName: string, config: ToolConfig): Promise<{
      status: string;
      message: string;
      tool: string;
    }> {
      return apiRequest(`/user/tools/${toolName}`, {
        method: 'POST',
        body: JSON.stringify({ config }),
      });
    },

    async update(toolName: string, config: ToolConfig): Promise<{
      status: string;
      message: string;
      tool: string;
    }> {
      return apiRequest(`/user/tools/${toolName}`, {
        method: 'PUT',
        body: JSON.stringify({ config }),
      });
    },

    async delete(toolName: string): Promise<{
      status: string;
      message: string;
      tool: string;
    }> {
      return apiRequest(`/user/tools/${toolName}`, {
        method: 'DELETE',
      });
    },

    async test(toolName: string, config: ToolConfig): Promise<{
      status: string;
      message: string;
      valid: boolean;
    }> {
      return apiRequest(`/user/tools/${toolName}/test`, {
        method: 'POST',
        body: JSON.stringify({ config }),
      });
    },
  },

  // Tool Lifecycle API
  lifecycle: {
    async getStatus(toolName: string): Promise<{
      tool: string;
      status: string;
      message: string;
    }> {
      return apiRequest(`/user/tools/${toolName}/status`);
    },

    async start(toolName: string): Promise<{
      status: string;
      message: string;
      tool: string;
    }> {
      return apiRequest(`/user/tools/${toolName}/start`, {
        method: 'POST',
      });
    },

    async stop(toolName: string): Promise<{
      status: string;
      message: string;
      tool: string;
    }> {
      return apiRequest(`/user/tools/${toolName}/stop`, {
        method: 'POST',
      });
    },

    async refresh(toolName: string): Promise<{
      status: string;
      message: string;
      tool: string;
    }> {
      return apiRequest(`/user/tools/${toolName}/refresh`, {
        method: 'POST',
      });
    },
  },

  // Credentials API
  credentials: {
    async list(): Promise<Array<{
      tool_name: string;
      provider: string;
      created_at: string;
    }>> {
      return apiRequest('/user/credentials');
    },

    async get(toolName: string, provider: string): Promise<Record<string, any>> {
      return apiRequest(`/user/credentials/${toolName}?provider=${provider}`);
    },

    async store(
      toolName: string,
      provider: string,
      secrets: Record<string, any>
    ): Promise<{
      status: string;
      message: string;
    }> {
      return apiRequest(`/user/credentials/${toolName}`, {
        method: 'POST',
        body: JSON.stringify({ provider, secrets }),
      });
    },

    async delete(toolName: string, provider: string): Promise<{
      status: string;
      message: string;
    }> {
      return apiRequest(`/user/credentials/${toolName}?provider=${provider}`, {
        method: 'DELETE',
      });
    },
  },

  // Workspace API
  workspace: {
    async get(): Promise<{
      id: string;
      name: string;
      slug: string;
      owner_id: string;
      settings: Record<string, any>;
      stats: {
        tools: { total: number; enabled: number };
        configs: number;
        credentials: number;
        audit_events_30d: number;
      };
    }> {
      return apiRequest('/workspace');
    },

    async updateSettings(settings: Record<string, any>): Promise<{
      id: string;
      name: string;
      settings: Record<string, any>;
    }> {
      return apiRequest('/workspace/settings', {
        method: 'PUT',
        body: JSON.stringify(settings),
      });
    },
  },

  // Audit Logs API
  auditLogs: {
    async list(options?: {
      category?: string;
      action?: string;
      limit?: number;
      offset?: number;
    }): Promise<Array<{
      id: string;
      action: string;
      category: string;
      actor: { id: string | null; email: string | null; type: string };
      target: { type: string; id: string | null; name: string | null } | null;
      workspace_id: string;
      success: boolean;
      error_message: string | null;
      occurred_at: string;
      metadata: Record<string, any> | null;
    }>> {
      const params = new URLSearchParams();
      if (options?.category) params.append('category', options.category);
      if (options?.action) params.append('action', options.action);
      if (options?.limit) params.append('limit', options.limit.toString());
      if (options?.offset) params.append('offset', options.offset.toString());

      const query = params.toString();
      return apiRequest(`/audit-logs${query ? `?${query}` : ''}`);
    },
  },

  // Admin API (Super Admin Only)
  admin: {
    async listWorkspaces(options?: {
      limit?: number;
      offset?: number;
    }): Promise<Array<{
      id: string;
      name: string;
      slug: string;
      owner_id: string;
      created_at: string;
    }>> {
      const params = new URLSearchParams();
      if (options?.limit) params.append('limit', options.limit.toString());
      if (options?.offset) params.append('offset', options.offset.toString());

      const query = params.toString();
      return apiRequest(`/admin/workspaces${query ? `?${query}` : ''}`);
    },

    async listAllAuditLogs(options?: {
      workspace_id?: string;
      category?: string;
      action?: string;
      limit?: number;
      offset?: number;
    }): Promise<Array<{
      id: string;
      action: string;
      category: string;
      actor: { id: string | null; email: string | null; type: string };
      target: { type: string; id: string | null; name: string | null } | null;
      workspace_id: string;
      success: boolean;
      error_message: string | null;
      occurred_at: string;
      metadata: Record<string, any> | null;
    }>> {
      const params = new URLSearchParams();
      if (options?.workspace_id) params.append('workspace_id', options.workspace_id);
      if (options?.category) params.append('category', options.category);
      if (options?.action) params.append('action', options.action);
      if (options?.limit) params.append('limit', options.limit.toString());
      if (options?.offset) params.append('offset', options.offset.toString());

      const query = params.toString();
      return apiRequest(`/admin/audit-logs${query ? `?${query}` : ''}`);
    },
  },

  // Health & Info
  async health(): Promise<{ status: string }> {
    const response = await fetch('/api/health');
    return response.json();
  },

  async info(): Promise<{
    name: string;
    version: string;
    auth_provider: string;
    features: string[];
  }> {
    return apiRequest('/info');
  },
};

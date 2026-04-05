// API工具函数，用于与后端API进行交互

const API_BASE_URL = 'http://localhost:8000/api';

// 通用请求函数
async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.error || `HTTP error! status: ${response.status}`);
  }

  return response.json();
}

// 聊天相关API
export const chatApi = {
  // 发送消息并获取响应
  sendMessage: (message: string) => {
    return request<{
      response: string;
      emotion: string;
      timestamp: string;
    }>('/chat', {
      method: 'POST',
      body: JSON.stringify({ message }),
    });
  },
};

// 记忆相关API
export const memoryApi = {
  // 获取核心记忆
  getCoreMemory: () => {
    return request<{
      memories: Array<{
        id: string;
        content: string;
        importance: number;
        timestamp: string;
      }>;
    }>('/memory/core');
  },

  // 添加核心记忆
  addCoreMemory: (content: string, importance: number) => {
    return request<{
      id: string;
      status: string;
    }>('/memory/core', {
      method: 'POST',
      body: JSON.stringify({ content, importance }),
    });
  },

  // 获取事件记忆
  getEpisodicMemory: () => {
    return request<{
      events: Array<{
        id: string;
        content: string;
        timestamp: string;
        emotion: string;
      }>;
    }>('/memory/episodic');
  },

  // 获取工作记忆
  getWorkingMemory: () => {
    return request<{
      items: Array<{
        id: string;
        content: string;
        timestamp: string;
      }>;
    }>('/memory/working');
  },
};

// 设置相关API
export const settingsApi = {
  // 获取系统设置
  getSettings: () => {
    return request<{
      settings: {
        llmProvider: string;
        apiKey: string;
        modelName: string;
        enableProactivity: boolean;
        enableWorldTick: boolean;
        enableNpcBrain: boolean;
        theme: string;
        fontSize: string;
      };
    }>('/settings');
  },

  // 更新系统设置
  updateSettings: (settings: any) => {
    return request<{
      status: string;
    }>('/settings', {
      method: 'POST',
      body: JSON.stringify({ settings }),
    });
  },

  // 控制主动消息
  setProactive: (enabled: boolean) => {
    return request<{
      status: string;
    }>('/proactive', {
      method: 'POST',
      body: JSON.stringify({ enabled }),
    });
  },
};

// 系统状态API
export const statusApi = {
  // 获取系统状态
  getStatus: () => {
    return request<{
      status: string;
      emotion: string;
      worldState: {
        time: string;
        weather: string;
        location: string;
      };
      proactiveStatus: {
        enabled: boolean;
        task_active: boolean;
        check_interval: number;
        context: string;
      };
    }>('/status');
  },

  // 健康检查
  healthCheck: () => {
    return request<{
      status: string;
    }>('/health');
  },
};
// 设置状态管理
import { create } from 'zustand';
import { settingsApi, statusApi } from '../utils/api';

interface Settings {
  llmProvider: string;
  apiKey: string;
  modelName: string;
  enableProactivity: boolean;
  enableWorldTick: boolean;
  enableNpcBrain: boolean;
  theme: string;
  fontSize: string;
}

interface SystemStatus {
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
}

interface SettingsState {
  settings: Settings;
  systemStatus: SystemStatus | null;
  isLoading: boolean;
  error: string | null;
  
  fetchSettings: () => Promise<void>;
  updateSettings: (newSettings: Partial<Settings>) => Promise<void>;
  setProactive: (enabled: boolean) => Promise<void>;
  fetchSystemStatus: () => Promise<void>;
  toggleTheme: () => Promise<void>;
  clearError: () => void;
}

const defaultSettings: Settings = {
  llmProvider: 'OpenAI',
  apiKey: '',
  modelName: 'gpt-3.5-turbo',
  enableProactivity: false,
  enableWorldTick: true,
  enableNpcBrain: false,
  theme: 'light',
  fontSize: 'medium',
};

export const useSettingsStore = create<SettingsState>((set, get) => ({
  settings: defaultSettings,
  systemStatus: null,
  isLoading: false,
  error: null,
  
  fetchSettings: async () => {
    set({ isLoading: true, error: null });
    try {
      const response = await settingsApi.getSettings();
      set({ settings: response.settings, isLoading: false });
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : '获取设置失败',
        isLoading: false 
      });
    }
  },
  
  updateSettings: async (newSettings) => {
    set({ isLoading: true, error: null });
    try {
      const currentSettings = get().settings;
      const updatedSettings = { ...currentSettings, ...newSettings };
      await settingsApi.updateSettings(updatedSettings);
      set({ settings: updatedSettings, isLoading: false });
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : '更新设置失败',
        isLoading: false 
      });
    }
  },
  
  setProactive: async (enabled) => {
    set({ isLoading: true, error: null });
    try {
      await settingsApi.setProactive(enabled);
      // 更新本地设置
      const currentSettings = get().settings;
      set({ 
        settings: { ...currentSettings, enableProactivity: enabled },
        isLoading: false 
      });
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : '更新主动消息设置失败',
        isLoading: false 
      });
    }
  },
  
  fetchSystemStatus: async () => {
    set({ isLoading: true, error: null });
    try {
      const response = await statusApi.getStatus();
      set({ systemStatus: response, isLoading: false });
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : '获取系统状态失败',
        isLoading: false 
      });
    }
  },
  
  toggleTheme: async () => {
    const currentTheme = get().settings.theme;
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    await get().updateSettings({ theme: newTheme });
    
    // 更新文档主题
    document.documentElement.classList.toggle('dark', newTheme === 'dark');
  },
  
  clearError: () => set({ error: null }),
}));
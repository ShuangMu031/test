// 记忆状态管理
import { create } from 'zustand';
import { memoryApi } from '../utils/api';

interface CoreMemoryItem {
  id: string;
  content: string;
  importance: number;
  timestamp: string;
}

interface EpisodicMemoryItem {
  id: string;
  content: string;
  timestamp: string;
  emotion: string;
}

interface WorkingMemoryItem {
  id: string;
  content: string;
  timestamp: string;
}

interface MemoryState {
  coreMemory: CoreMemoryItem[];
  episodicMemory: EpisodicMemoryItem[];
  workingMemory: WorkingMemoryItem[];
  isLoading: boolean;
  error: string | null;
  
  fetchCoreMemory: () => Promise<void>;
  addCoreMemory: (content: string, importance: number) => Promise<void>;
  fetchEpisodicMemory: () => Promise<void>;
  fetchWorkingMemory: () => Promise<void>;
  clearError: () => void;
}

export const useMemoryStore = create<MemoryState>((set) => ({
  coreMemory: [],
  episodicMemory: [],
  workingMemory: [],
  isLoading: false,
  error: null,
  
  fetchCoreMemory: async () => {
    set({ isLoading: true, error: null });
    try {
      const response = await memoryApi.getCoreMemory();
      set({ coreMemory: response.memories, isLoading: false });
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : '获取核心记忆失败',
        isLoading: false 
      });
    }
  },
  
  addCoreMemory: async (content, importance) => {
    set({ isLoading: true, error: null });
    try {
      await memoryApi.addCoreMemory(content, importance);
      // 添加成功后重新获取核心记忆
      const response = await memoryApi.getCoreMemory();
      set({ coreMemory: response.memories, isLoading: false });
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : '添加核心记忆失败',
        isLoading: false 
      });
    }
  },
  
  fetchEpisodicMemory: async () => {
    set({ isLoading: true, error: null });
    try {
      const response = await memoryApi.getEpisodicMemory();
      set({ episodicMemory: response.events, isLoading: false });
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : '获取事件记忆失败',
        isLoading: false 
      });
    }
  },
  
  fetchWorkingMemory: async () => {
    set({ isLoading: true, error: null });
    try {
      const response = await memoryApi.getWorkingMemory();
      set({ workingMemory: response.items, isLoading: false });
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : '获取工作记忆失败',
        isLoading: false 
      });
    }
  },
  
  clearError: () => set({ error: null }),
}));
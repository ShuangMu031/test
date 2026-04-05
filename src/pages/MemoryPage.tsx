// 记忆管理页面 - 技术展示页
import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useMemoryStore } from '../store/memoryStore';
import MemoryCard from '../components/MemoryCard';
import { ArrowLeft } from 'lucide-react';

const MemoryPage: React.FC = () => {
  const { 
    coreMemory, 
    episodicMemory, 
    workingMemory, 
    isLoading, 
    error, 
    fetchCoreMemory, 
    addCoreMemory, 
    fetchEpisodicMemory, 
    fetchWorkingMemory, 
    clearError 
  } = useMemoryStore();
  
  const [activeTab, setActiveTab] = useState<'core' | 'episodic' | 'working'>('core');
  const [newMemory, setNewMemory] = useState('');
  const [importance, setImportance] = useState(5);

  // 初始化获取记忆数据
  useEffect(() => {
    fetchCoreMemory();
    fetchEpisodicMemory();
    fetchWorkingMemory();
  }, [fetchCoreMemory, fetchEpisodicMemory, fetchWorkingMemory]);

  // 清除错误
  useEffect(() => {
    if (error) {
      const timer = setTimeout(clearError, 5000);
      return () => clearTimeout(timer);
    }
  }, [error, clearError]);

  // 添加核心记忆
  const handleAddMemory = () => {
    if (newMemory.trim()) {
      addCoreMemory(newMemory, importance);
      setNewMemory('');
      setImportance(5);
    }
  };

  // 渲染记忆列表
  const renderMemoryList = () => {
    switch (activeTab) {
      case 'core':
        return (
          <>
            {/* 添加核心记忆表单 */}
            <div className="bg-white/5 backdrop-blur-md rounded-xl p-4 mb-6 border border-white/10">
              <h3 className="text-sm font-medium text-gray-300 mb-3">
                添加核心记忆
              </h3>
              <div className="space-y-3">
                <textarea
                  value={newMemory}
                  onChange={(e) => setNewMemory(e.target.value)}
                  placeholder="输入记忆内容..."
                  className="w-full p-3 rounded-lg bg-white/5 border border-white/10 text-white focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                  rows={3}
                />
                <div className="flex items-center gap-2">
                  <label className="text-sm text-gray-400">
                    重要性:
                  </label>
                  <input
                    type="range"
                    min="1"
                    max="10"
                    value={importance}
                    onChange={(e) => setImportance(Number(e.target.value))}
                    className="w-40"
                  />
                  <span className="text-sm text-gray-400">
                    {importance}
                  </span>
                </div>
                <button
                  onClick={handleAddMemory}
                  disabled={!newMemory.trim() || isLoading}
                  className={`w-full py-2 rounded-lg ${newMemory.trim() && !isLoading 
                    ? 'bg-gradient-to-r from-blue-500 to-blue-700 text-white hover:shadow-lg hover:shadow-blue-500/20' 
                    : 'bg-gray-600 text-gray-400 cursor-not-allowed'}`}
                >
                  {isLoading ? '添加中...' : '添加记忆'}
                </button>
              </div>
            </div>

            {/* 核心记忆列表 */}
            {coreMemory.length === 0 ? (
              <div className="text-center py-16 text-gray-400">
                暂无核心记忆
              </div>
            ) : (
              coreMemory.map((memory) => (
                <MemoryCard
                  key={memory.id}
                  id={memory.id}
                  content={memory.content}
                  timestamp={memory.timestamp}
                  type="core"
                  importance={memory.importance}
                />
              ))
            )}
          </>
        );
      case 'episodic':
        return episodicMemory.length === 0 ? (
          <div className="text-center py-16 text-gray-400">
            暂无事件记忆
          </div>
        ) : (
          episodicMemory.map((memory) => (
            <MemoryCard
              key={memory.id}
              id={memory.id}
              content={memory.content}
              timestamp={memory.timestamp}
              type="episodic"
              emotion={memory.emotion}
            />
          ))
        );
      case 'working':
        return workingMemory.length === 0 ? (
          <div className="text-center py-16 text-gray-400">
            暂无工作记忆
          </div>
        ) : (
          workingMemory.map((memory) => (
            <MemoryCard
              key={memory.id}
              id={memory.id}
              content={memory.content}
              timestamp={memory.timestamp}
              type="working"
            />
          ))
        );
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen p-8">
      <div className="max-w-4xl mx-auto">
        {/* 返回按钮 */}
        <Link to="/" className="inline-flex items-center gap-2 text-sm text-gray-400 hover:text-white mb-6">
          <ArrowLeft className="w-4 h-4" />
          <span>返回首页</span>
        </Link>

        {/* 页面标题 */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold mb-2">记忆管理</h1>
          <p className="text-sm text-gray-400">技术展示页面 - 三层记忆系统的管理界面</p>
        </div>

        {/* 错误提示 */}
        {error && (
          <div className="bg-red-900/30 text-red-300 p-3 rounded-lg mb-6 border border-red-500/30">
            {error}
          </div>
        )}

        {/* 标签页 */}
        <div className="flex border-b border-white/10 mb-6">
          <button
            onClick={() => setActiveTab('core')}
            className={`px-4 py-2 font-medium ${activeTab === 'core' 
              ? 'text-blue-400 border-b-2 border-blue-400' 
              : 'text-gray-400 hover:text-white'}`}
          >
            核心记忆
          </button>
          <button
            onClick={() => setActiveTab('episodic')}
            className={`px-4 py-2 font-medium ${activeTab === 'episodic' 
              ? 'text-blue-400 border-b-2 border-blue-400' 
              : 'text-gray-400 hover:text-white'}`}
          >
            事件记忆
          </button>
          <button
            onClick={() => setActiveTab('working')}
            className={`px-4 py-2 font-medium ${activeTab === 'working' 
              ? 'text-blue-400 border-b-2 border-blue-400' 
              : 'text-gray-400 hover:text-white'}`}
          >
            工作记忆
          </button>
        </div>

        {/* 记忆列表 */}
        {renderMemoryList()}
      </div>
    </div>
  );
};

export default MemoryPage;
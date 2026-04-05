// 主应用组件
import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { useSettingsStore } from './store/settingsStore';
import Home from './pages/Home';
import ChatPage from './pages/ChatPage';
import MemoryPage from './pages/MemoryPage';
import SettingsPage from './pages/SettingsPage';
import { Home as HomeIcon, MessageSquare, Brain, Settings } from 'lucide-react';

const App: React.FC = () => {
  const { settings, fetchSettings } = useSettingsStore();

  // 初始化获取设置
  useEffect(() => {
    fetchSettings();
  }, [fetchSettings]);

  // 应用主题
  useEffect(() => {
    document.documentElement.classList.toggle('dark', settings.theme === 'dark');
  }, [settings.theme]);

  return (
    <Router>
      <div className="min-h-screen">
        {/* 侧边导航栏 */}
        <div className="fixed left-0 top-0 bottom-0 w-64 bg-white/10 dark:bg-gray-900/80 backdrop-blur-lg border-r border-gray-200/20 dark:border-gray-800/50 flex flex-col items-center py-6 gap-6 z-20">
          <Link to="/" className="flex flex-col items-center gap-1 p-2 rounded-lg hover:bg-gray-100/20 dark:hover:bg-gray-800/30 transition-colors">
            <HomeIcon className="w-6 h-6 text-gray-700 dark:text-gray-300" />
            <span className="text-xs text-gray-600 dark:text-gray-400">首页</span>
          </Link>
          <Link to="/chat/service" className="flex flex-col items-center gap-1 p-2 rounded-lg hover:bg-gray-100/20 dark:hover:bg-gray-800/30 transition-colors">
            <MessageSquare className="w-6 h-6 text-gray-700 dark:text-gray-300" />
            <span className="text-xs text-gray-600 dark:text-gray-400">客服场景</span>
          </Link>
          <Link to="/chat/game" className="flex flex-col items-center gap-1 p-2 rounded-lg hover:bg-gray-100/20 dark:hover:bg-gray-800/30 transition-colors">
            <MessageSquare className="w-6 h-6 text-gray-700 dark:text-gray-300" />
            <span className="text-xs text-gray-600 dark:text-gray-400">游戏场景</span>
          </Link>
          <Link to="/chat/companion" className="flex flex-col items-center gap-1 p-2 rounded-lg hover:bg-gray-100/20 dark:hover:bg-gray-800/30 transition-colors">
            <MessageSquare className="w-6 h-6 text-gray-700 dark:text-gray-300" />
            <span className="text-xs text-gray-600 dark:text-gray-400">陪伴场景</span>
          </Link>
          <Link to="/memory" className="flex flex-col items-center gap-1 p-2 rounded-lg hover:bg-gray-100/20 dark:hover:bg-gray-800/30 transition-colors">
            <Brain className="w-6 h-6 text-gray-700 dark:text-gray-300" />
            <span className="text-xs text-gray-600 dark:text-gray-400">记忆管理</span>
          </Link>
          <Link to="/settings" className="flex flex-col items-center gap-1 p-2 rounded-lg hover:bg-gray-100/20 dark:hover:bg-gray-800/30 transition-colors">
            <Settings className="w-6 h-6 text-gray-700 dark:text-gray-300" />
            <span className="text-xs text-gray-600 dark:text-gray-400">设置</span>
          </Link>
        </div>

        {/* 主内容区 */}
        <div className="ml-64">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/chat/:scene" element={<ChatPage />} />
            <Route path="/memory" element={<MemoryPage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Routes>
        </div>
      </div>
    </Router>
  );
};

export default App;
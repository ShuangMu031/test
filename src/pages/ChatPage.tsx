// 聊天页面
import React, { useEffect, useRef, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useChatStore } from '../store/chatStore';
import { useSettingsStore } from '../store/settingsStore';
import MessageList from '../components/chat/MessageList';
import InputArea from '../components/chat/InputArea';
import ConversationStatusMini from '../components/status/ConversationStatusMini';
import BrainFlowBoard from '../components/workbench/BrainFlowBoard';
import BrainInspector from '../components/workbench/BrainInspector';
import PhaseTimeline from '../components/workbench/PhaseTimeline';
import TraceDrawer from '../components/workbench/TraceDrawer';
import { BrainName } from '../types/trace';

const ChatPage: React.FC = () => {
  const { scene = 'service' } = useParams<{ scene: string }>();
  const { 
    messages, 
    inputValue, 
    isLoading, 
    error, 
    currentTrace, 
    selectedBrain, 
    setInputValue, 
    setSelectedBrain, 
    sendMessage, 
    clearError 
  } = useChatStore();
  
  const { 
    systemStatus, 
    settings, 
    fetchSystemStatus, 
    setProactive 
  } = useSettingsStore();
  
  const [isTraceDrawerOpen, setIsTraceDrawerOpen] = useState(false);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // 滚动到底部
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // 发送消息
  const handleSend = () => {
    if (inputValue.trim()) {
      sendMessage({
        message: inputValue,
        scene: scene as 'service' | 'game' | 'companion',
        traceEnabled: true,
        debug: true
      });
    }
  };

  // 切换主动消息
  const handleToggleProactive = () => {
    setProactive(!settings.enableProactivity);
  };

  // 选择脑
  const handleSelectBrain = (brainName: BrainName) => {
    setSelectedBrain(brainName);
  };

  // 初始化和定期获取系统状态
  useEffect(() => {
    fetchSystemStatus();
    const interval = setInterval(fetchSystemStatus, 30000); // 每30秒更新一次状态
    return () => clearInterval(interval);
  }, [fetchSystemStatus]);

  // 消息变化时滚动到底部
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // 清除错误
  useEffect(() => {
    if (error) {
      const timer = setTimeout(clearError, 5000);
      return () => clearTimeout(timer);
    }
  }, [error, clearError]);

  // 场景配置
  const sceneConfig = {
    service: {
      name: '客服场景',
      color: 'from-blue-500 to-blue-700',
      borderColor: 'border-blue-500/30',
      welcome: '我可以协助处理咨询、售后和问题定位',
      placeholder: '请输入你的问题或订单信息'
    },
    game: {
      name: '游戏场景',
      color: 'from-purple-500 to-purple-700',
      borderColor: 'border-purple-500/30',
      welcome: '当前世界状态已加载，可继续推进剧情',
      placeholder: '输入剧情指令或角色对话'
    },
    companion: {
      name: '情景陪伴',
      color: 'from-green-500 to-green-700',
      borderColor: 'border-green-500/30',
      welcome: '我会先理解你的感受，再慢慢陪你聊',
      placeholder: '写下你现在的感受或想说的话'
    }
  };

  const currentScene = sceneConfig[scene as keyof typeof sceneConfig] || sceneConfig.service;

  return (
    <div className="flex flex-col h-screen">
      {/* 顶部场景切换条 */}
      <div className="bg-white/10 backdrop-blur-md border-b border-white/10 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link to="/chat/service" className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${scene === 'service' ? 'bg-gradient-to-r from-blue-500 to-blue-700 text-white' : 'bg-white/5 hover:bg-white/10'}`}>
              客服
            </Link>
            <Link to="/chat/game" className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${scene === 'game' ? 'bg-gradient-to-r from-purple-500 to-purple-700 text-white' : 'bg-white/5 hover:bg-white/10'}`}>
              游戏
            </Link>
            <Link to="/chat/companion" className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${scene === 'companion' ? 'bg-gradient-to-r from-green-500 to-green-700 text-white' : 'bg-white/5 hover:bg-white/10'}`}>
              情景陪伴
            </Link>
          </div>
          <div className="flex items-center gap-2">
            <button
              className="px-3 py-1 rounded-md text-xs bg-gray-800/50 hover:bg-gray-700/50 transition-colors"
              onClick={() => setIsTraceDrawerOpen(true)}
            >
              Trace 数据
            </button>
          </div>
        </div>
        
        {/* Phase 时间线 */}
        <div className="mt-4">
          <PhaseTimeline trace={currentTrace} />
        </div>
      </div>

      {/* 主内容区 */}
      <div className="flex flex-1 overflow-hidden">
        {/* 聊天主区 */}
        <div className="w-1/3 flex flex-col overflow-hidden border-r border-white/10">
          {/* 消息列表 */}
          <div className="flex-1 overflow-y-auto">
            <div className="max-w-md mx-auto">
              {/* 欢迎消息 */}
              {messages.length === 0 && (
                <div className="text-center py-16">
                  <div className={`inline-block p-3 rounded-full bg-gradient-to-r ${currentScene.color} mb-4`}>
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                    </svg>
                  </div>
                  <h2 className="text-2xl font-bold mb-2">
                    你好！
                  </h2>
                  <p className="text-gray-400">
                    {currentScene.welcome}
                  </p>
                </div>
              )}

              {/* 消息气泡 */}
              <MessageList messages={messages} />

              {/* 错误提示 */}
              {error && (
                <div className="bg-red-900/30 text-red-300 p-3 rounded-lg mb-4 border border-red-500/30">
                  {error}
                </div>
              )}

              {/* 滚动到底部的参考元素 */}
              <div ref={messagesEndRef} />
            </div>
          </div>

          {/* 输入区域 */}
          <div className="p-4 border-t border-white/10">
            <div className="max-w-md mx-auto">
              <InputArea
                value={inputValue}
                onChange={setInputValue}
                onSend={handleSend}
                isLoading={isLoading}
                placeholder={currentScene.placeholder}
                scene={scene}
              />
            </div>
          </div>
        </div>

        {/* 中间六脑流图 */}
        <div className="w-1/3 flex flex-col overflow-hidden border-r border-white/10">
          <BrainFlowBoard
            trace={currentTrace}
            selectedBrain={selectedBrain}
            onSelectBrain={handleSelectBrain}
          />
        </div>

        {/* 右侧脑详情检查器 */}
        <div className="w-1/3 flex flex-col overflow-hidden">
          {/* 系统状态摘要 */}
          {systemStatus && (
            <div className="p-4 border-b border-white/10">
              <ConversationStatusMini
                emotion={systemStatus.emotion}
                worldState={systemStatus.worldState}
                proactiveEnabled={settings.enableProactivity}
                onToggleProactive={handleToggleProactive}
              />
            </div>
          )}
          
          {/* 脑详情 */}
          <BrainInspector
            trace={currentTrace}
            selectedBrain={selectedBrain}
          />
        </div>
      </div>

      {/* Trace 抽屉 */}
      <TraceDrawer
        isOpen={isTraceDrawerOpen}
        onClose={() => setIsTraceDrawerOpen(false)}
        trace={currentTrace}
      />
    </div>
  );
};

export default ChatPage;
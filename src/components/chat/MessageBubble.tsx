// 消息气泡组件
import React from 'react';
import { Message } from '../../store/chatStore';

interface MessageBubbleProps {
  content: string;
  isUser: boolean;
  timestamp: string;
  emotion?: string;
  scene?: string;
}

const MessageBubble: React.FC<MessageBubbleProps> = ({ content, isUser, timestamp, emotion, scene = 'service' }) => {
  // 根据场景获取助手名称
  const getAssistantName = (scene: string) => {
    const assistantNameMap = {
      service: '客服助手',
      game: '世界助手',
      companion: '陪伴助手'
    };
    return assistantNameMap[scene as keyof typeof assistantNameMap] || '助手';
  };

  // 根据情绪获取对应的表情和颜色
  const getEmotionInfo = (emotion?: string) => {
    switch (emotion) {
      case 'happy':
        return { emoji: '😊', color: 'text-yellow-500' };
      case 'sad':
        return { emoji: '😢', color: 'text-blue-500' };
      case 'excited':
        return { emoji: '🤗', color: 'text-pink-500' };
      case 'calm':
        return { emoji: '😌', color: 'text-green-500' };
      default:
        return { emoji: '😐', color: 'text-gray-500' };
    }
  };

  // 根据场景获取颜色
  const getSceneColor = (scene: string) => {
    const sceneColorMap = {
      service: 'from-blue-500 to-blue-700',
      game: 'from-purple-500 to-purple-700',
      companion: 'from-green-500 to-green-700'
    };
    return sceneColorMap[scene as keyof typeof sceneColorMap] || 'from-blue-500 to-blue-700';
  };

  const emotionInfo = getEmotionInfo(emotion);
  const assistantName = getAssistantName(scene);
  const sceneColor = getSceneColor(scene);

  return (
    <div 
      className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4 items-start gap-3`}
    >
      {!isUser && (
        <div className={`w-8 h-8 rounded-full bg-gradient-to-r ${sceneColor} flex items-center justify-center`}>
          <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
          </svg>
        </div>
      )}
      <div 
        className={`max-w-[80%] rounded-2xl p-4 ${isUser 
          ? 'bg-gradient-to-r from-blue-500 to-blue-700 text-white' 
          : 'bg-white/5 dark:bg-gray-800/50 text-white border border-white/10'}`}
      >
        <div className="flex items-center gap-2 mb-1">
          <span className={`text-sm font-medium ${isUser ? 'text-blue-100' : 'text-gray-300'}`}>
            {isUser ? 'You' : assistantName}
          </span>
          {!isUser && emotion && (
            <span className={`text-sm ${emotionInfo.color}`}>
              {emotionInfo.emoji}
            </span>
          )}
          <span className={`text-xs ${isUser ? 'text-blue-200' : 'text-gray-400'}`}>
            {new Date(timestamp).toLocaleTimeString()}
          </span>
        </div>
        <div className="text-sm whitespace-pre-wrap">
          {content}
        </div>
      </div>
      {isUser && (
        <div className="w-8 h-8 rounded-full bg-gradient-to-r from-gray-500 to-gray-700 flex items-center justify-center">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
          </svg>
        </div>
      )}
    </div>
  );
};

export default MessageBubble;
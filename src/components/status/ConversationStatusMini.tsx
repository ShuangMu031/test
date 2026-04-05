// 系统状态摘要组件
import React from 'react';
import { Sun, Moon, Cloud, CloudRain, CloudSnow, Wind } from 'lucide-react';

interface ConversationStatusMiniProps {
  emotion: string;
  worldState: {
    time: string;
    weather: string;
    location: string;
  };
  proactiveEnabled: boolean;
  onToggleProactive: () => void;
}

const ConversationStatusMini: React.FC<ConversationStatusMiniProps> = ({ 
  emotion, 
  worldState, 
  proactiveEnabled, 
  onToggleProactive 
}) => {
  // 根据情绪获取对应的表情和颜色
  const getEmotionInfo = (emotion: string) => {
    switch (emotion) {
      case 'happy':
        return { emoji: '😊', color: 'text-yellow-400', label: '开心' };
      case 'sad':
        return { emoji: '😢', color: 'text-blue-400', label: '难过' };
      case 'excited':
        return { emoji: '🤗', color: 'text-pink-400', label: '兴奋' };
      case 'calm':
        return { emoji: '😌', color: 'text-green-400', label: '平静' };
      default:
        return { emoji: '😐', color: 'text-gray-400', label: '中性' };
    }
  };

  // 根据天气获取对应的图标
  const getWeatherIcon = (weather: string) => {
    switch (weather) {
      case 'sunny':
        return <Sun className="w-4 h-4 text-yellow-400" />;
      case 'cloudy':
        return <Cloud className="w-4 h-4 text-gray-400" />;
      case 'rainy':
        return <CloudRain className="w-4 h-4 text-blue-400" />;
      case 'snowy':
        return <CloudSnow className="w-4 h-4 text-blue-300" />;
      case 'windy':
        return <Wind className="w-4 h-4 text-gray-400" />;
      default:
        return <Sun className="w-4 h-4 text-yellow-400" />;
    }
  };

  const emotionInfo = getEmotionInfo(emotion);

  return (
    <div className="space-y-3">
      {/* 情绪状态 */}
      <div className="flex items-center justify-between">
        <span className="text-sm text-gray-400">当前情绪</span>
        <div className="flex items-center gap-2">
          <span className={`text-lg ${emotionInfo.color}`}>{emotionInfo.emoji}</span>
          <span className="text-sm font-medium text-white">{emotionInfo.label}</span>
        </div>
      </div>

      {/* 世界状态 */}
      <div className="flex items-center justify-between">
        <span className="text-sm text-gray-400">世界状态</span>
        <div className="flex items-center gap-2">
          {getWeatherIcon(worldState.weather)}
          <span className="text-sm font-medium text-white">{worldState.weather}</span>
        </div>
      </div>

      {/* 主动交互 */}
      <div className="flex items-center justify-between">
        <span className="text-sm text-gray-400">主动交互</span>
        <button
          onClick={onToggleProactive}
          className={`relative inline-flex h-5 w-10 items-center rounded-full transition-colors ${proactiveEnabled ? 'bg-green-500' : 'bg-gray-600'}`}
        >
          <span
            className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${proactiveEnabled ? 'translate-x-5' : 'translate-x-1'}`}
          />
        </button>
      </div>
    </div>
  );
};

export default ConversationStatusMini;
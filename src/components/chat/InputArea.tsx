// 输入区域组件
import React from 'react';
import { Send, Smile } from 'lucide-react';

interface InputAreaProps {
  value: string;
  onChange: (value: string) => void;
  onSend: () => void;
  isLoading: boolean;
  placeholder?: string;
  scene?: string;
}

const InputArea: React.FC<InputAreaProps> = ({ 
  value, 
  onChange, 
  onSend, 
  isLoading,
  placeholder = '输入消息...',
  scene = 'service'
}) => {
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      onSend();
    }
  };

  // 根据场景获取标签颜色
  const getSceneColor = (scene: string) => {
    const sceneColorMap = {
      service: 'bg-blue-500/20 text-blue-400',
      game: 'bg-purple-500/20 text-purple-400',
      companion: 'bg-green-500/20 text-green-400'
    };
    return sceneColorMap[scene as keyof typeof sceneColorMap] || 'bg-blue-500/20 text-blue-400';
  };

  // 根据场景获取标签文本
  const getSceneLabel = (scene: string) => {
    const sceneLabelMap = {
      service: '客服',
      game: '游戏',
      companion: '陪伴'
    };
    return sceneLabelMap[scene as keyof typeof sceneLabelMap] || '场景';
  };

  const sceneColor = getSceneColor(scene);
  const sceneLabel = getSceneLabel(scene);

  return (
    <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-2xl p-4 shadow-lg">
      <div className="flex items-center gap-3">
        <div className={`px-2 py-1 rounded-full text-xs font-medium ${sceneColor}`}>
          {sceneLabel}
        </div>
        <button 
          className="p-2 rounded-full hover:bg-white/10 transition-colors"
          disabled={isLoading}
        >
          <Smile className="w-5 h-5 text-gray-400" />
        </button>
        <div className="flex-1 relative">
          <textarea
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={placeholder}
            className="w-full p-3 rounded-full bg-white/5 border border-white/10 text-white focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
            rows={1}
            disabled={isLoading}
          />
        </div>
        <button
          onClick={onSend}
          disabled={!value.trim() || isLoading}
          className={`p-3 rounded-full ${value.trim() && !isLoading 
            ? 'bg-gradient-to-r from-blue-500 to-blue-700 text-white hover:shadow-lg hover:shadow-blue-500/20' 
            : 'bg-gray-600 text-gray-400 cursor-not-allowed'}`}
        >
          {isLoading ? (
            <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
          ) : (
            <Send className="w-5 h-5" />
          )}
        </button>
      </div>
    </div>
  );
};

export default InputArea;
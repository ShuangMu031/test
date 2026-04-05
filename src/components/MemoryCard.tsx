// 记忆卡片组件
import React from 'react';

interface MemoryCardProps {
  id: string;
  content: string;
  timestamp: string;
  type: 'core' | 'episodic' | 'working';
  emotion?: string;
  importance?: number;
  onEdit?: (id: string) => void;
  onDelete?: (id: string) => void;
}

const MemoryCard: React.FC<MemoryCardProps> = ({ 
  id, 
  content, 
  timestamp, 
  type, 
  emotion, 
  importance, 
  onEdit, 
  onDelete 
}) => {
  // 获取记忆类型的标签和颜色
  const getTypeInfo = (type: string) => {
    switch (type) {
      case 'core':
        return { label: '核心记忆', color: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200' };
      case 'episodic':
        return { label: '事件记忆', color: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' };
      case 'working':
        return { label: '工作记忆', color: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200' };
      default:
        return { label: '记忆', color: 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200' };
    }
  };

  // 根据情绪获取对应的表情
  const getEmotionEmoji = (emotion?: string) => {
    switch (emotion) {
      case 'happy':
        return '😊';
      case 'sad':
        return '😢';
      case 'excited':
        return '🤗';
      case 'calm':
        return '😌';
      default:
        return '😐';
    }
  };

  const typeInfo = getTypeInfo(type);

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-4 mb-4 border border-gray-200 dark:border-gray-700">
      <div className="flex justify-between items-start mb-2">
        <span className={`px-2 py-1 rounded-full text-xs font-medium ${typeInfo.color}`}>
          {typeInfo.label}
        </span>
        <div className="flex gap-2">
          {onEdit && (
            <button 
              className="text-gray-500 hover:text-blue-500 dark:text-gray-400 dark:hover:text-blue-400"
              onClick={() => onEdit(id)}
            >
              编辑
            </button>
          )}
          {onDelete && (
            <button 
              className="text-gray-500 hover:text-red-500 dark:text-gray-400 dark:hover:text-red-400"
              onClick={() => onDelete(id)}
            >
              删除
            </button>
          )}
        </div>
      </div>
      
      <div className="mb-3">
        <p className="text-sm text-gray-600 dark:text-gray-300 line-clamp-3">
          {content}
        </p>
      </div>
      
      <div className="flex justify-between items-center text-xs text-gray-500 dark:text-gray-400">
        <span>{new Date(timestamp).toLocaleString()}</span>
        <div className="flex items-center gap-2">
          {emotion && (
            <span>{getEmotionEmoji(emotion)}</span>
          )}
          {importance && (
            <span>重要性: {importance}</span>
          )}
        </div>
      </div>
    </div>
  );
};

export default MemoryCard;
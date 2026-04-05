import React from 'react';
import { BrainTraceView } from '../../types/trace';
import { brainThemes } from '../../utils/brainTheme';

interface BrainNodeCardProps {
  brain: BrainTraceView;
  isSelected: boolean;
  onSelect: (brainName: string) => void;
}

const BrainNodeCard: React.FC<BrainNodeCardProps> = ({ brain, isSelected, onSelect }) => {
  const theme = brainThemes[brain.brain_name];
  
  return (
    <div
      className={`relative rounded-xl p-4 transition-all duration-300 cursor-pointer
        ${isSelected ? 'ring-2 ring-offset-2' : 'hover:shadow-lg'}
        ${brain.has_error ? 'bg-red-900/30 border border-red-500/50' : 'bg-white/5 dark:bg-gray-800/50 border border-white/10'}
        ${isSelected ? `ring-${theme.primary}` : ''}`}
      style={{
        borderLeftColor: theme.primary,
        borderLeftWidth: '4px'
      }}
      onClick={() => onSelect(brain.brain_name)}
    >
      <div className="flex justify-between items-start mb-2">
        <h3 className="text-sm font-semibold text-white flex items-center gap-2">
          <span className="w-2 h-2 rounded-full" style={{ backgroundColor: theme.primary }}></span>
          {brain.display_name}
        </h3>
        <div className="flex items-center gap-2">
          <span className="text-xs px-2 py-1 rounded-full bg-gray-700/50 text-gray-300">
            {brain.duration_ms}ms
          </span>
          {brain.has_error && (
            <span className="text-xs px-2 py-1 rounded-full bg-red-900/50 text-red-300">
              错误
            </span>
          )}
        </div>
      </div>
      
      <p className="text-xs text-gray-300 mb-3 line-clamp-2">
        {brain.conclusion}
      </p>
      
      {brain.key_fields && Object.keys(brain.key_fields).length > 0 && (
        <div className="space-y-1">
          {Object.entries(brain.key_fields).slice(0, 3).map(([key, value]) => (
            <div key={key} className="flex justify-between items-center">
              <span className="text-xs text-gray-400">{key}</span>
              <span className="text-xs text-white">{String(value)}</span>
            </div>
          ))}
          {Object.keys(brain.key_fields).length > 3 && (
            <div className="text-xs text-gray-400">+{Object.keys(brain.key_fields).length - 3} 更多</div>
          )}
        </div>
      )}
      
      {brain.influence_target && brain.influence_target.length > 0 && (
        <div className="mt-3 pt-2 border-t border-white/10">
          <div className="text-xs text-gray-400 mb-1">影响目标</div>
          <div className="flex flex-wrap gap-1">
            {brain.influence_target.map((target) => (
              <span key={target} className="text-xs px-2 py-0.5 rounded-full bg-gray-700/50 text-gray-300">
                {target}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default BrainNodeCard;
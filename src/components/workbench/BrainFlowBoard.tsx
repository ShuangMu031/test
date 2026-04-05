import React from 'react';
import { TurnTrace, BrainName } from '../../types/trace';
import BrainNodeCard from './BrainNodeCard';
import { brainThemes } from '../../utils/brainTheme';

interface BrainFlowBoardProps {
  trace: TurnTrace | null;
  selectedBrain: BrainName | null;
  onSelectBrain: (brainName: BrainName) => void;
}

const defaultBrainOrder: BrainName[] = ['emotion', 'memory', 'world', 'npc', 'behavior', 'supervisor'];

const BrainFlowBoard: React.FC<BrainFlowBoardProps> = ({ trace, selectedBrain, onSelectBrain }) => {
  if (!trace || !trace.brain_views) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center text-gray-400">
          <p className="text-sm">暂无六脑决策数据</p>
          <p className="text-xs mt-1">发送消息后将显示决策流</p>
        </div>
      </div>
    );
  }

  // 按默认顺序排序脑视图
  const orderedBrains = defaultBrainOrder
    .map(brainName => trace.brain_views?.find(brain => brain.brain_name === brainName))
    .filter((brain): brain is typeof brain => brain !== undefined);

  return (
    <div className="flex-1 overflow-y-auto p-4">
      <h2 className="text-sm font-semibold text-white mb-4">六脑决策流</h2>
      
      <div className="space-y-6">
        {orderedBrains.map((brain, index) => (
          <div key={brain.brain_name} className="relative">
            <BrainNodeCard
              brain={brain}
              isSelected={selectedBrain === brain.brain_name}
              onSelect={(brainName) => onSelectBrain(brainName as BrainName)}
            />
            
            {/* 连接线 */}
            {index < orderedBrains.length - 1 && (
              <div className="absolute bottom-0 left-1/2 transform -translate-x-1/2 -translate-y-1/2">
                <div className="w-0.5 h-6 bg-gray-700"></div>
              </div>
            )}
          </div>
        ))}
      </div>
      
      {trace.decision_tensions && trace.decision_tensions.length > 0 && (
        <div className="mt-6 p-4 rounded-xl bg-amber-900/30 border border-amber-500/50">
          <h3 className="text-sm font-semibold text-amber-300 mb-2">决策冲突</h3>
          <div className="space-y-2">
            {trace.decision_tensions.map((tension, index) => (
              <div key={index} className="text-xs text-gray-300">
                {JSON.stringify(tension)}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default BrainFlowBoard;
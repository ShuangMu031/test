import React from 'react';
import { TurnTrace } from '../../types/trace';

interface PhaseTimelineProps {
  trace: TurnTrace | null;
}

const phases = [
  { key: 'context_collected', label: '收集上下文' },
  { key: 'brains_completed', label: '六脑执行' },
  { key: 'policy_checked', label: '策略检查' },
  { key: 'plan_compiled', label: '计划编译' },
  { key: 'executed', label: '执行' },
  { key: 'responded', label: '生成回复' },
  { key: 'committed', label: '提交' }
];

const PhaseTimeline: React.FC<PhaseTimelineProps> = ({ trace }) => {
  const completedPhases = trace?.timeline || [];
  const currentPhase = completedPhases[completedPhases.length - 1];

  return (
    <div className="flex items-center gap-1 py-2 px-4 bg-gray-900/50 rounded-lg">
      {phases.map((phase, index) => {
        const isCompleted = completedPhases.includes(phase.key);
        const isCurrent = phase.key === currentPhase;
        
        return (
          <React.Fragment key={phase.key}>
            <div className="flex flex-col items-center">
              <div className={`w-3 h-3 rounded-full transition-all duration-300
                ${isCompleted ? 'bg-green-500' : 'bg-gray-700'}
                ${isCurrent ? 'ring-2 ring-green-400 ring-offset-2 ring-offset-gray-900' : ''}`}
              ></div>
              <span className={`text-xs mt-1 transition-all duration-300
                ${isCompleted ? 'text-green-400' : 'text-gray-400'}
                ${isCurrent ? 'font-medium' : ''}`}
              >
                {phase.label}
              </span>
            </div>
            
            {index < phases.length - 1 && (
              <div className={`w-8 h-0.5 transition-all duration-300
                ${completedPhases.includes(phases[index + 1].key) ? 'bg-green-500' : 'bg-gray-700'}`}
              ></div>
            )}
          </React.Fragment>
        );
      })}
    </div>
  );
};

export default PhaseTimeline;
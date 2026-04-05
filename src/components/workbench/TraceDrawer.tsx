import React, { useState } from 'react';
import { TurnTrace } from '../../types/trace';

interface TraceDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  trace: TurnTrace | null;
}

const TraceDrawer: React.FC<TraceDrawerProps> = ({ isOpen, onClose, trace }) => {
  const [activeTab, setActiveTab] = useState('decisionChain');
  
  if (!isOpen) return null;
  
  if (!trace) {
    return (
      <div className="fixed inset-0 bg-black/50 z-50 flex items-end justify-center">
        <div className="bg-gray-900 border-t border-gray-700 w-full max-h-[70vh] overflow-hidden flex flex-col">
          <div className="p-4 border-b border-gray-800 flex justify-between items-center">
            <h2 className="text-sm font-semibold text-white">Trace 数据</h2>
            <button
              className="text-gray-400 hover:text-white transition-colors"
              onClick={onClose}
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <div className="flex-1 p-4 flex items-center justify-center">
            <div className="text-center text-gray-400">
              <p className="text-sm">暂无 Trace 数据</p>
            </div>
          </div>
        </div>
      </div>
    );
  }
  
  const tabs = [
    { key: 'decisionChain', label: '决策链' },
    { key: 'warnings', label: '警告' },
    { key: 'memoryCommit', label: '记忆提交' },
    { key: 'fullTrace', label: '完整 Trace' }
  ];
  
  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-end justify-center">
      <div className="bg-gray-900 border-t border-gray-700 w-full max-h-[70vh] overflow-hidden flex flex-col">
        {/* 头部 */}
        <div className="p-4 border-b border-gray-800 flex justify-between items-center">
          <h2 className="text-sm font-semibold text-white">Trace 数据</h2>
          <button
            className="text-gray-400 hover:text-white transition-colors"
            onClick={onClose}
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        {/* 标签页导航 */}
        <div className="flex gap-2 p-4 border-b border-gray-800 overflow-x-auto">
          {tabs.map(tab => (
            <button
              key={tab.key}
              className={`px-3 py-1 rounded-md text-xs whitespace-nowrap transition-all duration-300
                ${activeTab === tab.key 
                  ? 'bg-white/10 text-white font-medium' 
                  : 'bg-gray-800/50 text-gray-400 hover:bg-gray-700/50'}`}
              onClick={() => setActiveTab(tab.key)}
            >
              {tab.label}
            </button>
          ))}
        </div>
        
        {/* 标签页内容 */}
        <div className="flex-1 p-4 overflow-y-auto">
          {/* 决策链 */}
          {activeTab === 'decisionChain' && (
            <div className="space-y-3">
              <div className="p-3 rounded-lg bg-white/5 border border-white/10">
                <h3 className="text-sm font-medium text-white mb-2">决策步骤</h3>
                {trace.decision_chain && trace.decision_chain.steps && trace.decision_chain.steps.length > 0 ? (
                  <ol className="list-decimal list-inside space-y-1 text-xs text-gray-300">
                    {trace.decision_chain.steps.map((step, index) => (
                      <li key={index}>{step}</li>
                    ))}
                  </ol>
                ) : (
                  <p className="text-xs text-gray-400">无决策步骤</p>
                )}
              </div>
              
              <div className="p-3 rounded-lg bg-white/5 border border-white/10">
                <h3 className="text-sm font-medium text-white mb-2">总体信息</h3>
                <div className="space-y-2 text-xs">
                  <div className="flex justify-between">
                    <span className="text-gray-400">主导脑</span>
                    <span className="text-white">{trace.dominant_brain}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">最终动作</span>
                    <span className="text-white">{trace.final_action}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">模型档位</span>
                    <span className="text-white">{trace.model_tier}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">总执行时间</span>
                    <span className="text-white">{trace.total_duration_ms}ms</span>
                  </div>
                </div>
              </div>
            </div>
          )}
          
          {/* 警告 */}
          {activeTab === 'warnings' && (
            <div className="p-3 rounded-lg bg-white/5 border border-white/10">
              <h3 className="text-sm font-medium text-white mb-2">警告信息</h3>
              {trace.warnings && trace.warnings.length > 0 ? (
                <ul className="list-disc list-inside space-y-1 text-xs text-amber-300">
                  {trace.warnings.map((warning, index) => (
                    <li key={index}>{warning}</li>
                  ))}
                </ul>
              ) : (
                <p className="text-xs text-gray-400">无警告信息</p>
              )}
            </div>
          )}
          
          {/* 记忆提交 */}
          {activeTab === 'memoryCommit' && (
            <div className="p-3 rounded-lg bg-white/5 border border-white/10">
              <h3 className="text-sm font-medium text-white mb-2">记忆提交</h3>
              {trace.memory_commit && Object.keys(trace.memory_commit).length > 0 ? (
                <div className="space-y-2 text-xs">
                  {Object.entries(trace.memory_commit).map(([key, value]) => (
                    <div key={key} className="flex flex-col">
                      <span className="text-gray-400">{key}</span>
                      <span className="text-white">{typeof value === 'object' ? JSON.stringify(value) : String(value)}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-gray-400">无记忆提交</p>
              )}
            </div>
          )}
          
          {/* 完整 Trace */}
          {activeTab === 'fullTrace' && (
            <div className="p-3 rounded-lg bg-white/5 border border-white/10">
              <h3 className="text-sm font-medium text-white mb-2">完整 Trace 数据</h3>
              <pre className="text-xs text-gray-300 overflow-x-auto max-h-[40vh]">
                {JSON.stringify(trace, null, 2)}
              </pre>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default TraceDrawer;
import React, { useState } from 'react';
import { TurnTrace, BrainName } from '../../types/trace';
import { brainThemes } from '../../utils/brainTheme';

interface BrainInspectorProps {
  trace: TurnTrace | null;
  selectedBrain: BrainName | null;
}

const BrainInspector: React.FC<BrainInspectorProps> = ({ trace, selectedBrain }) => {
  const [activeTab, setActiveTab] = useState('overview');
  
  if (!trace || !selectedBrain) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center text-gray-400">
          <p className="text-sm">请选择一个脑查看详细信息</p>
        </div>
      </div>
    );
  }
  
  const brain = trace.brain_views.find(b => b.brain_name === selectedBrain);
  if (!brain) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center text-gray-400">
          <p className="text-sm">未找到脑数据</p>
        </div>
      </div>
    );
  }
  
  const theme = brainThemes[brain.brain_name];
  
  const tabs = [
    { key: 'overview', label: '概览' },
    { key: 'keyFields', label: '关键字段' },
    { key: 'monologue', label: '独白' },
    { key: 'actions', label: '动作' },
    { key: 'interactions', label: '交互' },
    { key: 'toolCalls', label: '工具调用' },
    { key: 'telemetry', label: '遥测' },
    { key: 'raw', label: '原始数据' }
  ];
  
  return (
    <div className="flex-1 overflow-y-auto p-4">
      <h2 className="text-sm font-semibold text-white mb-4">脑详情检查器</h2>
      
      {/* 标签页导航 */}
      <div className="flex gap-2 mb-4 overflow-x-auto pb-2">
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
      <div className="space-y-4">
        {/* 概览 */}
        {activeTab === 'overview' && (
          <div className="space-y-3">
            <div className="p-3 rounded-lg bg-white/5 border border-white/10">
              <h3 className="text-sm font-medium text-white mb-2">基本信息</h3>
              <div className="space-y-2 text-xs">
                <div className="flex justify-between">
                  <span className="text-gray-400">脑名称</span>
                  <span className="text-white">{brain.display_name}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">触发状态</span>
                  <span className={`${brain.triggered ? 'text-green-400' : 'text-gray-400'}`}>
                    {brain.triggered ? '已触发' : '未触发'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">执行时间</span>
                  <span className="text-white">{brain.duration_ms}ms</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">错误状态</span>
                  <span className={`${brain.has_error ? 'text-red-400' : 'text-green-400'}`}>
                    {brain.has_error ? '有错误' : '正常'}
                  </span>
                </div>
              </div>
            </div>
            
            <div className="p-3 rounded-lg bg-white/5 border border-white/10">
              <h3 className="text-sm font-medium text-white mb-2">结论</h3>
              <p className="text-xs text-gray-300">{brain.conclusion}</p>
            </div>
            
            {brain.influence_target && brain.influence_target.length > 0 && (
              <div className="p-3 rounded-lg bg-white/5 border border-white/10">
                <h3 className="text-sm font-medium text-white mb-2">影响目标</h3>
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
        )}
        
        {/* 关键字段 */}
        {activeTab === 'keyFields' && (
          <div className="p-3 rounded-lg bg-white/5 border border-white/10">
            <h3 className="text-sm font-medium text-white mb-2">关键字段</h3>
            {brain.key_fields && Object.keys(brain.key_fields).length > 0 ? (
              <div className="space-y-2 text-xs">
                {Object.entries(brain.key_fields).map(([key, value]) => (
                  <div key={key} className="flex flex-col">
                    <span className="text-gray-400">{key}</span>
                    <span className="text-white">{typeof value === 'object' ? JSON.stringify(value) : String(value)}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-gray-400">无关键字段</p>
            )}
          </div>
        )}
        
        {/* 独白 */}
        {activeTab === 'monologue' && (
          <div className="p-3 rounded-lg bg-white/5 border border-white/10">
            <h3 className="text-sm font-medium text-white mb-2">独白</h3>
            <p className="text-xs text-gray-300">{brain.monologue || '无独白'}</p>
          </div>
        )}
        
        {/* 动作 */}
        {activeTab === 'actions' && (
          <div className="p-3 rounded-lg bg-white/5 border border-white/10">
            <h3 className="text-sm font-medium text-white mb-2">动作</h3>
            {brain.actions && brain.actions.length > 0 ? (
              <ul className="list-disc list-inside space-y-1 text-xs text-gray-300">
                {brain.actions.map((action, index) => (
                  <li key={index}>{action}</li>
                ))}
              </ul>
            ) : (
              <p className="text-xs text-gray-400">无动作</p>
            )}
          </div>
        )}
        
        {/* 交互 */}
        {activeTab === 'interactions' && (
          <div className="p-3 rounded-lg bg-white/5 border border-white/10">
            <h3 className="text-sm font-medium text-white mb-2">交互</h3>
            {brain.interactions && brain.interactions.length > 0 ? (
              <ul className="list-disc list-inside space-y-1 text-xs text-gray-300">
                {brain.interactions.map((interaction, index) => (
                  <li key={index}>{interaction}</li>
                ))}
              </ul>
            ) : (
              <p className="text-xs text-gray-400">无交互</p>
            )}
          </div>
        )}
        
        {/* 工具调用 */}
        {activeTab === 'toolCalls' && (
          <div className="p-3 rounded-lg bg-white/5 border border-white/10">
            <h3 className="text-sm font-medium text-white mb-2">工具调用</h3>
            {brain.tool_calls && brain.tool_calls.length > 0 ? (
              <ul className="list-disc list-inside space-y-1 text-xs text-gray-300">
                {brain.tool_calls.map((toolCall, index) => (
                  <li key={index}>{toolCall}</li>
                ))}
              </ul>
            ) : (
              <p className="text-xs text-gray-400">无工具调用</p>
            )}
          </div>
        )}
        
        {/* 遥测 */}
        {activeTab === 'telemetry' && (
          <div className="p-3 rounded-lg bg-white/5 border border-white/10">
            <h3 className="text-sm font-medium text-white mb-2">遥测数据</h3>
            {brain.telemetry && Object.keys(brain.telemetry).length > 0 ? (
              <div className="space-y-2 text-xs">
                {Object.entries(brain.telemetry).map(([key, value]) => (
                  <div key={key} className="flex justify-between">
                    <span className="text-gray-400">{key}</span>
                    <span className="text-white">{typeof value === 'object' ? JSON.stringify(value) : String(value)}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-gray-400">无遥测数据</p>
            )}
          </div>
        )}
        
        {/* 原始数据 */}
        {activeTab === 'raw' && (
          <div className="p-3 rounded-lg bg-white/5 border border-white/10">
            <h3 className="text-sm font-medium text-white mb-2">原始数据</h3>
            <pre className="text-xs text-gray-300 overflow-x-auto">
              {JSON.stringify(brain, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
};

export default BrainInspector;
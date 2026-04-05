// 开发设置页面
import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useSettingsStore } from '../store/settingsStore';
import SettingItem from '../components/SettingItem';
import { Sun, Moon, ChevronDown, ChevronUp, ArrowLeft } from 'lucide-react';

const SettingsPage: React.FC = () => {
  const { 
    settings, 
    isLoading, 
    error, 
    fetchSettings, 
    updateSettings, 
    toggleTheme, 
    clearError 
  } = useSettingsStore();
  
  const [showAdvanced, setShowAdvanced] = useState(false);

  // 初始化获取设置
  useEffect(() => {
    fetchSettings();
  }, [fetchSettings]);

  // 清除错误
  useEffect(() => {
    if (error) {
      const timer = setTimeout(clearError, 5000);
      return () => clearTimeout(timer);
    }
  }, [error, clearError]);

  // LLM提供商选项
  const llmProviderOptions = [
    { label: 'OpenAI', value: 'OpenAI' },
    { label: 'SiliconFlow', value: 'SiliconFlow' },
    { label: 'Ollama', value: 'Ollama' },
  ];

  // 字体大小选项
  const fontSizeOptions = [
    { label: '小', value: 'small' },
    { label: '中', value: 'medium' },
    { label: '大', value: 'large' },
  ];

  return (
    <div className="min-h-screen p-8">
      <div className="max-w-4xl mx-auto">
        {/* 返回按钮 */}
        <Link to="/" className="inline-flex items-center gap-2 text-sm text-gray-400 hover:text-white mb-6">
          <ArrowLeft className="w-4 h-4" />
          <span>返回首页</span>
        </Link>

        {/* 页面标题 */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold mb-2">开发设置</h1>
          <p className="text-sm text-gray-400">配置应用的基本设置和高级选项</p>
        </div>

        {/* 错误提示 */}
        {error && (
          <div className="bg-red-900/30 text-red-300 p-3 rounded-lg mb-6 border border-red-500/30">
            {error}
          </div>
        )}

        {/* 基本设置卡片 */}
        <div className="bg-white/5 backdrop-blur-md rounded-xl p-6 border border-white/10 mb-6">
          <h2 className="text-lg font-medium mb-4">基本设置</h2>
          
          {/* 主题设置 */}
          <div className="flex justify-between items-center mb-6">
            <label className="text-sm font-medium text-gray-300">
              主题
            </label>
            <button
              onClick={toggleTheme}
              className="p-2 rounded-full hover:bg-white/10 transition-colors"
            >
              {settings.theme === 'light' ? (
                <Moon className="w-5 h-5 text-gray-400" />
              ) : (
                <Sun className="w-5 h-5 text-gray-400" />
              )}
            </button>
          </div>
          
          {/* 字体大小 */}
          <SettingItem
            label="字体大小"
            type="select"
            value={settings.fontSize}
            onChange={(value) => updateSettings({ fontSize: value as string })}
            options={fontSizeOptions}
            description="调整界面字体大小"
          />
          
          {/* 主动消息开关 */}
          <SettingItem
            label="启用主动消息"
            type="toggle"
            value={settings.enableProactivity}
            onChange={(value) => updateSettings({ enableProactivity: value as boolean })}
            description="允许AI主动发送消息"
          />
        </div>

        {/* 高级设置卡片 */}
        <div className="bg-white/5 backdrop-blur-md rounded-xl border border-white/10 mb-6">
          {/* 高级设置标题 */}
          <button
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="w-full p-6 flex justify-between items-center text-left"
          >
            <h2 className="text-lg font-medium">高级设置</h2>
            {showAdvanced ? (
              <ChevronUp className="w-5 h-5 text-gray-400" />
            ) : (
              <ChevronDown className="w-5 h-5 text-gray-400" />
            )}
          </button>
          
          {/* 高级设置内容 */}
          {showAdvanced && (
            <div className="px-6 pb-6 space-y-4">
              <SettingItem
                label="LLM 提供商"
                type="select"
                value={settings.llmProvider}
                onChange={(value) => updateSettings({ llmProvider: value as string })}
                options={llmProviderOptions}
                description="选择使用的LLM服务提供商"
              />
              
              <SettingItem
                label="API 密钥"
                type="input"
                value={settings.apiKey}
                onChange={(value) => updateSettings({ apiKey: value as string })}
                placeholder="输入API密钥"
                description="根据选择的提供商输入对应的API密钥"
              />
              
              <SettingItem
                label="模型名称"
                type="input"
                value={settings.modelName}
                onChange={(value) => updateSettings({ modelName: value as string })}
                placeholder="输入模型名称"
                description="例如: gpt-3.5-turbo, gpt-4等"
              />
              
              <SettingItem
                label="启用世界状态更新"
                type="toggle"
                value={settings.enableWorldTick}
                onChange={(value) => updateSettings({ enableWorldTick: value as boolean })}
                description="启用世界状态的自动更新"
              />
              
              <SettingItem
                label="启用NPC系统"
                type="toggle"
                value={settings.enableNpcBrain}
                onChange={(value) => updateSettings({ enableNpcBrain: value as boolean })}
                description="启用NPC管理和交互功能"
              />
            </div>
          )}
        </div>

        {/* 保存状态 */}
        {isLoading && (
          <div className="text-center py-4 text-gray-400">
            保存中...
          </div>
        )}
      </div>
    </div>
  );
};

export default SettingsPage;
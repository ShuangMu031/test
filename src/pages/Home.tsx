import React from 'react';
import { Link } from 'react-router-dom';
import { MessageSquare, Gamepad2, Heart, Brain, Globe, Zap, Eye, Code } from 'lucide-react';

const Home: React.FC = () => {
  return (
    <div className="min-h-screen px-8 py-16">
      {/* 顶部品牌区 */}
      <div className="text-center mb-16">
        <h1 className="text-4xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-500 mb-2">
          Emotional World
        </h1>
        <p className="text-xl text-gray-400">情绪交互与世界驱动 Agent</p>
      </div>

      {/* 中间主视觉区 */}
      <div className="text-center mb-24 max-w-4xl mx-auto">
        <h2 className="text-5xl font-bold mb-6">
          探索 AI 与人类的
          <span className="block bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-green-400">
            情感连接
          </span>
        </h2>
        <p className="text-xl text-gray-400 mb-10">
          基于情绪识别、三层记忆和世界状态的智能 Agent，为你带来更真实、更有温度的交互体验
        </p>
        <div className="flex justify-center gap-4">
          <Link 
            to="/chat/service" 
            className="px-8 py-3 bg-gradient-to-r from-blue-500 to-blue-700 rounded-full font-medium hover:shadow-lg hover:shadow-blue-500/30 transition-all"
          >
            进入演示
          </Link>
          <Link 
            to="/memory" 
            className="px-8 py-3 bg-transparent border border-gray-500 rounded-full font-medium hover:bg-white/10 transition-all"
          >
            查看架构
          </Link>
        </div>
      </div>

      {/* 三场景卡片区 */}
      <div className="mb-24">
        <h3 className="text-3xl font-bold text-center mb-12">应用场景</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* 客服场景 */}
          <Link to="/chat/service" className="group">
            <div className="bg-gradient-to-br from-blue-900/30 to-blue-700/20 backdrop-blur-md border border-blue-500/30 rounded-2xl p-8 hover:shadow-xl hover:shadow-blue-500/20 hover:-translate-y-2 transition-all group-hover:border-blue-400/50">
              <div className="bg-blue-500/20 rounded-full w-16 h-16 flex items-center justify-center mb-6 group-hover:bg-blue-500/30 transition-colors">
                <MessageSquare className="w-8 h-8 text-blue-400" />
              </div>
              <h4 className="text-xl font-semibold mb-3 text-blue-400">客服场景</h4>
              <p className="text-gray-400">
                智能处理咨询、售后和问题定位，提供专业、高效的客户服务体验
              </p>
            </div>
          </Link>

          {/* 游戏对话 */}
          <Link to="/chat/game" className="group">
            <div className="bg-gradient-to-br from-purple-900/30 to-purple-700/20 backdrop-blur-md border border-purple-500/30 rounded-2xl p-8 hover:shadow-xl hover:shadow-purple-500/20 hover:-translate-y-2 transition-all group-hover:border-purple-400/50">
              <div className="bg-purple-500/20 rounded-full w-16 h-16 flex items-center justify-center mb-6 group-hover:bg-purple-500/30 transition-colors">
                <Gamepad2 className="w-8 h-8 text-purple-400" />
              </div>
              <h4 className="text-xl font-semibold mb-3 text-purple-400">游戏对话</h4>
              <p className="text-gray-400">
                基于世界状态的游戏剧情推进，提供沉浸式的游戏交互体验
              </p>
            </div>
          </Link>

          {/* 情景陪伴 */}
          <Link to="/chat/companion" className="group">
            <div className="bg-gradient-to-br from-green-900/30 to-green-700/20 backdrop-blur-md border border-green-500/30 rounded-2xl p-8 hover:shadow-xl hover:shadow-green-500/20 hover:-translate-y-2 transition-all group-hover:border-green-400/50">
              <div className="bg-green-500/20 rounded-full w-16 h-16 flex items-center justify-center mb-6 group-hover:bg-green-500/30 transition-colors">
                <Heart className="w-8 h-8 text-green-400" />
              </div>
              <h4 className="text-xl font-semibold mb-3 text-green-400">情景陪伴</h4>
              <p className="text-gray-400">
                理解你的感受，提供情感支持和陪伴，成为你的心灵伙伴
              </p>
            </div>
          </Link>
        </div>
      </div>

      {/* 能力亮点区 */}
      <div className="mb-24">
        <h3 className="text-3xl font-bold text-center mb-12">核心能力</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
          {/* 情绪识别 */}
          <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-xl p-6 hover:shadow-lg hover:shadow-blue-500/10 hover:-translate-y-1 transition-all">
            <div className="bg-blue-500/20 rounded-full w-12 h-12 flex items-center justify-center mb-4">
              <Heart className="w-6 h-6 text-blue-400" />
            </div>
            <h4 className="text-lg font-semibold mb-2">情绪识别</h4>
            <p className="text-sm text-gray-400">
              实时分析用户情绪，提供相应的情感回应
            </p>
          </div>

          {/* 三层记忆 */}
          <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-xl p-6 hover:shadow-lg hover:shadow-purple-500/10 hover:-translate-y-1 transition-all">
            <div className="bg-purple-500/20 rounded-full w-12 h-12 flex items-center justify-center mb-4">
              <Brain className="w-6 h-6 text-purple-400" />
            </div>
            <h4 className="text-lg font-semibold mb-2">三层记忆</h4>
            <p className="text-sm text-gray-400">
              核心记忆、事件记忆、工作记忆，构建完整的记忆体系
            </p>
          </div>

          {/* 世界状态 */}
          <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-xl p-6 hover:shadow-lg hover:shadow-green-500/10 hover:-translate-y-1 transition-all">
            <div className="bg-green-500/20 rounded-full w-12 h-12 flex items-center justify-center mb-4">
              <Globe className="w-6 h-6 text-green-400" />
            </div>
            <h4 className="text-lg font-semibold mb-2">世界状态</h4>
            <p className="text-sm text-gray-400">
              模拟真实世界状态，影响 Agent 的行为和决策
            </p>
          </div>

          {/* 主动交互 */}
          <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-xl p-6 hover:shadow-lg hover:shadow-yellow-500/10 hover:-translate-y-1 transition-all">
            <div className="bg-yellow-500/20 rounded-full w-12 h-12 flex items-center justify-center mb-4">
              <Zap className="w-6 h-6 text-yellow-400" />
            </div>
            <h4 className="text-lg font-semibold mb-2">主动交互</h4>
            <p className="text-sm text-gray-400">
              基于世界状态和用户情绪，主动发起有意义的对话
            </p>
          </div>

          {/* 可观测追踪 */}
          <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-xl p-6 hover:shadow-lg hover:shadow-red-500/10 hover:-translate-y-1 transition-all">
            <div className="bg-red-500/20 rounded-full w-12 h-12 flex items-center justify-center mb-4">
              <Eye className="w-6 h-6 text-red-400" />
            </div>
            <h4 className="text-lg font-semibold mb-2">可观测追踪</h4>
            <p className="text-sm text-gray-400">
              完整的行为追踪和决策过程可视化，提高系统透明度
            </p>
          </div>
        </div>
      </div>

      {/* 底部演示说明区 */}
      <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-2xl p-8">
        <h3 className="text-2xl font-bold mb-6">演示说明</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div>
            <h4 className="text-lg font-semibold mb-3 flex items-center">
              <Code className="w-5 h-5 mr-2 text-blue-400" />
              当前版本支持
            </h4>
            <ul className="space-y-2 text-gray-400">
              <li className="flex items-center">
                <span className="w-2 h-2 bg-green-400 rounded-full mr-2"></span>
                三场景切换（客服、游戏、陪伴）
              </li>
              <li className="flex items-center">
                <span className="w-2 h-2 bg-green-400 rounded-full mr-2"></span>
                情绪识别与响应
              </li>
              <li className="flex items-center">
                <span className="w-2 h-2 bg-green-400 rounded-full mr-2"></span>
                三层记忆管理
              </li>
              <li className="flex items-center">
                <span className="w-2 h-2 bg-green-400 rounded-full mr-2"></span>
                世界状态模拟
              </li>
            </ul>
          </div>
          <div>
            <h4 className="text-lg font-semibold mb-3 flex items-center">
              <Code className="w-5 h-5 mr-2 text-purple-400" />
              后续计划
            </h4>
            <ul className="space-y-2 text-gray-400">
              <li className="flex items-center">
                <span className="w-2 h-2 bg-blue-400 rounded-full mr-2"></span>
                接入后端 API，实现完整功能
              </li>
              <li className="flex items-center">
                <span className="w-2 h-2 bg-blue-400 rounded-full mr-2"></span>
                增加更多场景和角色
              </li>
              <li className="flex items-center">
                <span className="w-2 h-2 bg-blue-400 rounded-full mr-2"></span>
                优化情绪识别算法
              </li>
              <li className="flex items-center">
                <span className="w-2 h-2 bg-blue-400 rounded-full mr-2"></span>
                增加多模态交互支持
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Home;
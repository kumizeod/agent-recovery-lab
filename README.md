# 🥣 Soup Detector | 海龟汤侦探

> 探索逻辑的迷宫，还原故事的真相。一款由大语言模型（LLM）驱动的侧向思维（Lateral Thinking）情景推理解谜游戏。

## ✨ 核心特性

- **🫧 物理引擎气泡池**：基于原生 JavaScript 打造的 Bubble Physics Engine，支持中心引力、碰撞排斥、阻尼衰减与平滑缩放，提供丝滑的关键词挑选体验。
- **🤖 双引擎无缝驱动**：
  - **LLM 动态生成与智能裁判**：支持自定义接入 DeepSeek、OpenAI、SiliconFlow、LM Studio 等任何兼容 OpenAI 格式的接口，根据所选关键词实时创作独一无二的汤面并担任问答裁判。
  - **内置精选离线题库**：无需配置 API Key 亦可直接开玩，内置「清汤（逻辑推理）」「红汤（悬疑惊悚）」「黑汤（人性反转）」经典谜题与智能本地裁判。
- **🔍 沉浸式双模式推理**：
  - **提问模式**：提出只能用「是 / 否 / 无关 / 部分正确」回答的问题，系统自动记录关键线索并计算真相还原度。
  - **猜谜模式**：当你锁定核心诡计时，直接提交完整真相结案。
- **🎨 暗黑磨砂玻璃美学**：响应式 Glassmorphism UI 设计，完美适配桌面端与移动端，纯静态前端架构，支持一键部署至 GitHub Pages 或 Vercel。

## 🚀 快速开始

1. **直接部署或本地运行**：
   - 本项目为纯前端单页应用（无需配置后端数据库），直接双击打开 `index.html` 或启用 GitHub Pages 即可访问。
2. **配置 API（可选）**：
   - 点击右上角 **「API 设置」**，填入您的 `API Base URL`、`API Key` 以及生成/裁判模型名称（配置仅保存在本地浏览器 `localStorage` 中）。
3. **开始游戏**：
   - 在首页选择汤底风格（清汤 / 红汤 / 黑汤），从物理气泡池中点击挑选 1–4 个关键词，点击 **「生成汤面 · 开始推理」**。

## 🤖 推荐模型配置

| 角色 | 推荐模型 | 说明 |
| :--- | :--- | :--- |
| **故事生成模型 (Story)** | `deepseek-reasoner` / `deepseek-chat` / `gpt-4o` | 负责根据关键词构建逻辑严密、反转精彩的汤面与汤底。 |
| **裁判问答模型 (Judge)** | `deepseek-chat` / `gpt-4o-mini` | 负责快速、准确地判定玩家的提问（是 / 否 / 无关）与真相还原度。 |

## 🛠️ 技术栈

- **前端核心**：HTML5, CSS3 (CSS Variables, Glassmorphism, Flexbox/Grid), Vanilla JavaScript
- **物理交互**：Custom Bubble Physics Engine (`requestAnimationFrame` 2D 碰撞与引力模拟)
- **图标与字体**：Iconify, Noto Sans SC, Noto Serif SC, JetBrains Mono

## 📄 开源协议

本项目采用 [MIT License](LICENSE) 开源协议。

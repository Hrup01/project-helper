# Project Helper - 项目学习助手

> 帮助开发者快速理解和分析 GitHub 开源仓库的智能工具

## 📖 项目简介

Project Helper 是一个全栈 Web 应用，专为开发者设计，能够快速理解和分析不熟悉的 GitHub 代码仓库。它会自动克隆仓库、扫描源码、识别技术栈，并生成适合初学者阅读的完整分析报告。同时提供智能问答助手，让您能够通过对话方式深入了解源码细节。

### ✨ 核心功能

- **🔍 自动分析**：克隆 GitHub 仓库，扫描目录结构、依赖配置和源码文件
- **📊 智能报告**：生成通俗易懂的中文 Markdown 分析报告，包含技术栈、目录结构、核心模块、数据流等
- **💬 源码问答**：基于 AI Agent 的交互式问答，可自主读取文件、搜索代码并给出准确回答
- **⚡ 实时进度**：通过 SSE（Server-Sent Events）实时推送分析进度到浏览器
- **💾 缓存机制**：SQLite 数据库缓存已完成的分析报告，避免重复分析
- **🎯 面向初学者**：报告内容通俗易懂，附带阅读建议和二次开发指导

## 🛠️ 技术栈

### 后端
- **语言**：Python
- **Web 框架**：FastAPI
- **AI 框架**：LangChain
- **数据库**：SQLite
- **AI 客户端**：OpenAI-compatible DeepSeek client
- **其他工具**：Git（仓库克隆）、pydantic（数据验证）

### 前端
- **框架**：Vue 3（Composition API）
- **构建工具**：Vite
- **UI 图标**：Lucide Icons
- **Markdown 渲染**：marked.js
- **语法高亮**：highlight.js（GitHub Dark 主题）
- **HTTP 客户端**：原生 Fetch API + EventSource（SSE）

## 🚀 快速开始

### 环境要求

- Python 3.10+
- Node.js 16+
- Git
- DeepSeek API Key（可选，用于 AI 增强分析）

### 后端启动

```
powershell
# 进入后端目录
cd backend

# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境（Windows PowerShell）
.venv\Scripts\Activate.ps1

# 安装依赖
pip install -r requirements.txt

# 复制环境变量配置文件
copy .env.example .env

# 编辑 .env 文件，设置 DEEPSEEK_API_KEY（可选但推荐）
# DEEPSEEK_API_KEY=your_api_key_here

# 启动后端服务
uvicorn app.main:app --reload --port 8000
```
后端服务将在 `http://localhost:8000` 运行，访问 `http://localhost:8000/docs` 可查看 API 文档。

### 前端启动

```
powershell
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```
前端服务通常在 `http://localhost:5173` 运行，浏览器会自动打开或手动访问该地址。

## 📋 使用说明

### 1. 分析仓库

1. 在输入框中输入 GitHub 仓库地址（必须是 HTTPS 格式），例如：
   - `https://github.com/vuejs/vue`
   - `https://github.com/tiangolo/fastapi`
2. （可选）勾选"重新分析"强制刷新已有缓存
3. 点击"分析项目"按钮

### 2. 查看分析报告

分析完成后，右侧会显示完整的 Markdown 报告，包含：

- **项目概述**：仓库基本信息和文件统计
- **技术栈**：识别的编程语言、框架和库
- **目录结构**：主要文件夹及其用途说明
- **核心模块入口**：关键文件列表和行数
- **数据流和执行流**：理解项目的建议路径
- **设计模式观察**：架构和分层信号
- **可用脚本**：package.json 中的 scripts（如适用）
- **阅读建议**：分阶段的学习路线

### 3. 源码问答

完成一次分析后，可在右侧聊天面板提问，例如：

- "入口文件在哪里？"
- "请求流程怎么走？"
- "这个模块怎么修改？"
- "主要使用了哪些设计模式？"

Agent 会自主调用工具读取相关文件、搜索代码，并给出基于源码的回答。

## ⚙️ 配置说明

### 环境变量（backend/.env）

```
bash
# DeepSeek API Key（可选）
# 配置后将启用 AI 增强的深度分析和智能问答
# 未配置时仍可使用本地静态分析功能
DEEPSEEK_API_KEY=your_api_key_here

# 其他可选配置
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-chat
```
### 数据存储

- **克隆的仓库**：`backend/data/repos/`
- **SQLite 数据库**：`backend/data/project_helper.db`
  - 存储项目元数据、分析报告、聊天历史

## 🔌 API 接口

### POST /api/analyze
提交仓库分析任务

**请求体**：
```
json
{
  "repo_url": "https://github.com/vuejs/vue",
  "force": false
}
```
**响应**：
```
json
{
  "project_id": "vuejs_vue",
  "status": "queued",
  "cached": false
}
```
### GET /api/analyze/{project_id}/events
获取分析进度的 SSE 事件流

**事件类型**：
- `progress`：进度更新
- `cached`：命中缓存
- `done`：分析完成
- `error`：发生错误

### GET /api/projects/{project_id}
获取项目信息和报告

### POST /api/projects/{project_id}/chat
发起源码问答

**请求体**：
```
json
{
  "question": "入口文件在哪里？"
}
```
**响应**：SSE 流式返回答案

## 🏗️ 项目结构

```

project-helper/
├── backend/                    # 后端服务
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py            # FastAPI 应用入口
│   │   ├── analyzer.py        # 仓库分析引擎
│   │   ├── chat.py            # 问答 Agent
│   │   ├── scanner.py         # 源码扫描器
│   │   ├── tools.py           # Agent 工具集
│   │   ├── llm.py             # LLM 客户端封装
│   │   ├── models.py          # Pydantic 数据模型
│   │   ├── database.py        # SQLite 数据库管理
│   │   ├── repository.py      # Git 仓库操作
│   │   ├── config.py          # 配置管理
│   │   └── utils.py           # 工具函数
│   ├── data/                   # 数据存储
│   │   ├── repos/             # 克隆的仓库
│   │   └── project_helper.db  # SQLite 数据库
│   ├── tests/                  # 单元测试
│   ├── requirements.txt       # Python 依赖
│   ├── .env.example           # 环境变量模板
│   └── pytest.ini             # 测试配置
├── frontend/                   # 前端应用
│   ├── src/
│   │   ├── App.vue            # 主组件
│   │   ├── main.js            # 应用入口
│   │   └── styles.css         # 全局样式
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
└── README.md
```
## 🧪 测试

运行后端单元测试：

```
powershell
cd backend
pytest
```
## 💡 工作原理

### 分析流程

1. **仓库克隆**：使用 Git 克隆或更新目标仓库到本地
2. **源码扫描**：
   - 识别文件类型和扩展名分布
   - 解析目录结构和文件大小
   - 提取 package.json、requirements.txt 等配置文件
   - 统计代码行数和模块分布
3. **报告生成**：
   - **本地模式**：基于扫描结果生成本地分析报告
   - **AI 模式**：调用 DeepSeek LLM 生成深度分析报告
4. **缓存存储**：将报告和元数据存入 SQLite 数据库

### 问答流程

1. 用户提出问题
2. Agent 调用工具：
   - `list_files()`：列出项目文件
   - `search_code(query)`：搜索相关代码
   - `read_file(path)`：读取具体文件内容
3. 结合工具结果和历史上下文生成回答
4. 流式返回答案到前端

## 🎯 应用场景

- 👶 **新手学习**：快速理解新接触的项目结构和核心逻辑
- 🔧 **二次开发**：了解现有项目的技术栈和模块划分
- 📚 **技术调研**：评估开源项目的质量和可维护性
- 🎓 **教学辅助**：为学生讲解复杂项目的架构设计
- 💼 **团队协作**：新成员快速上手团队项目

## ⚠️ 注意事项

- 仅支持 GitHub HTTPS 仓库地址（`https://github.com/...`）
- 大型仓库的分析可能需要较长时间
- 配置 `DEEPSEEK_API_KEY` 可获得更深入的 AI 分析
- 克隆的仓库存储在 `backend/data/repos`，注意磁盘空间
- 前端默认允许来自 `localhost:5173` 的跨域请求

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 🙏 致谢

感谢以下开源项目：

- [FastAPI](https://fastapi.tiangolo.com/) - 高性能 Web 框架
- [Vue 3](https://vuejs.org/) - 渐进式 JavaScript 框架
- [LangChain](https://langchain.com/) - LLM 应用开发框架
- [DeepSeek](https://www.deepseek.com/) - AI 模型服务
- [marked](https://marked.js.org/) - Markdown 解析器
- [highlight.js](https://highlightjs.org/) - 语法高亮库

---

**Made with ❤️ for developers**
```

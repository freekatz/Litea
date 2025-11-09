# Litea: Literature with a cup of tea!

Litea 是一款面向科研人员的自托管文献检索与智能推送助手，聚焦于以下能力:

- 多来源文献检索，当前默认接入 arXiv，并预留扩展接口以快速支持 PyPaperBot 生态中的更多源。
- 基于多智能体（CrewAI）的文献筛选与总结工作流，支持不同模型供应商（OpenAI、DeepSeek、Doubao、Qwen 等）的灵活配置。
- **MCP (Model Context Protocol) 集成**：邮件推送和飞书群机器人通知基于统一的 MCP 协议实现，易于扩展更多通知渠道。
- 任务化的文献追踪与推送，支持定时运行、多渠道通知（邮件、飞书）以及结果的结构化存储。
- SQLite 持久化记录检索历史、筛选结果、总结内容，可平滑迁移到 MySQL/PostgreSQL 等数据库。
- 现代化的 Vue 3 + Tailwind 前端界面，包含任务配置、历史浏览与分析页。
- **简单身份认证**：基于 JWT 的 admin 账户认证，密码保存在 .env 中，token 30天过期。

## 目录

- [项目结构](#项目结构)
- [快速开始](#快速开始)
- [环境变量](#环境变量)
- [开发工作流](#开发工作流)
- [后端架构概览](#后端架构概览)
- [前端功能概览](#前端功能概览)
- [扩展规划](#扩展规划)

## 项目结构

```
Litea/
├── backend/
│   ├── app/
│   │   ├── api/            # aiohttp 路由与接口
│   │   ├── config.py       # Pydantic Settings & 业务配置
│   │   ├── db/             # SQLAlchemy 模型与仓库
│   │   ├── services/       # AI、检索、通知、任务编排等服务
│   │   │   ├── mcp/        # MCP (Model Context Protocol) 工具
│   │   │   │   ├── base.py          # MCP 基础类和协议
│   │   │   │   ├── email_tool.py    # 邮件推送 MCP 工具
│   │   │   │   └── feishu_tool.py   # 飞书 Webhook MCP 工具
│   │   │   ├── ai/         # AI agents (filtering, summarization, keywords)
│   │   │   ├── retrieval/  # 文献检索服务
│   │   │   └── tasks/      # 任务运行器与调度
│   │   ├── schemas/        # Pydantic Schema
│   │   └── utils/
│   ├── pyproject.toml
│   └── ...
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── layouts/
│   │   ├── router/
│   │   ├── stores/
│   │   ├── views/
│   │   └── services/
│   ├── package.json
│   └── ...
└── README.md
```

## 快速开始

### 先决条件

- Python 3.10+
- Node.js 18+ / npm 9+
- （可选）Zotero API Key、SMTP 服务账号、飞书Webhook

### 后端启动

```bash
cd backend

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，配置 AI providers、Email 等

# 安装依赖（使用 poetry 或 pip）
pip install -e .

# 初始化数据库
python init_db.py

# 启动服务（默认端口 6060）
python -m app.main

# 启动并后台运行
screen -S backend
python -m app.main
```

后端 API 运行在 http://localhost:6060

### 前端启动

```bash
cd frontend

# 安装依赖
npm install

# 开发模式（热重载）
npm run dev

# 生产构建
npm run build
npm run preview

# 启动并后台运行
screen -S frontend
npm run preview
```

前端开发服务器运行在 http://localhost:3000，自动代理 API 请求到后端。

## 环境变量

在 `backend` 目录复制 `.env.example` 为 `.env` 并按需填写：

### 认证配置
- `AUTH__ADMIN_PASSWORD`：管理员密码
- `AUTH__JWT_SECRET`：JWT 签名密钥（生产环境务必修改）
- `AUTH__JWT_EXPIRE_DAYS`：JWT 过期天数（默认30天）

### AI 配置
- `AI__PROVIDERS__*`：配置多个模型提供商（名称、Base URL、API Key、模型 ID 等）

### 通知配置
- `EMAIL__*`：邮件推送 SMTP 信息、模板配置（主题、展示模式、显示区块）
- `FEISHU__*`：飞书群机器人配置（在任务中配置具体的 Webhook URL）

### 其他配置
- `SCHEDULER__TIMEZONE`：任务调度时区
- `ZOTERO__*`：Zotero API Key、库 ID/类型。未配置时不会执行写入操作


## 开发工作流

1. **任务配置**：在前端创建任务，配置 Prompt、关键词策略、检索来源、模型、调度与通知方式。
2. **关键词建议**：点击“AI 重新建议关键词”触发 `/api/tasks/keywords/suggest`，自动合并到任务关键词列表。
3. **手动运行**：保存后点击“立即运行”调用 `/api/tasks/{id}/run`，由后端完成检索→筛选→总结→持久化→通知。
4. **调度运行**：后续将集成 APScheduler 根据 Cron/时间段自动执行任务。

## 后端架构概览

- **AIOHTTP**：提供 RESTful API
- **JWT 认证**：基于 PyJWT 的简单身份验证，保护所有 API 端点
- **SQLAlchemy + SQLite**：任务、关键词、来源、运行记录、文献与总结的实体建模
- **MCP (Model Context Protocol)**：
  - 统一的工具协议用于通知推送
  - `EmailTool`：邮件推送，支持 HTML 模板和批量发送
  - `FeishuTool`：飞书群机器人 Webhook 推送，支持富文本卡片
  - 易于扩展更多渠道（钉钉、企业微信、Slack 等）
- **CrewAI 多智能体**：`FilteringAgentService` 与 `SummarizationAgentService` 分别编排文献筛选和总结
- **ProviderRegistry**：统一管理不同厂商模型的调用配置，便于扩展 OpenAI、DeepSeek、Doubao、Qwen 等
- **RetrievalRegistry**：当前实现 `ArxivRetrievalSource`，利用 PyPaperBot 检索文献；保留扩展接口
- **ZoteroClient**：基于 PyZotero，仅执行新增操作，避免误删用户已有条目

## 前端功能概览

- **登录认证**：首次访问需要使用 admin 账户登录，token 自动保存并附加到所有 API 请求
- **任务看板**：
  - 左侧任务列表，支持运行、停止、复制、编辑、归档操作
  - 右侧配置表单（基础信息、关键词策略、检索来源、AI 策略、调度与推送）
  - 通知推送配置：支持邮件和飞书两种渠道，可同时启用多个
- **文献列表**：
  - 显示 AI Summary（黄色渐变背景）和原始摘要
  - 支持按来源、评分、关键词筛选
  - 时间趋势图表和统计分析
- **历史与分析**：提供占位视图，后续补充实际数据可视化（趋势、关键词云、运行历史）
- **Pinia Store**：`config` 与 `tasks` store 管理全局配置及任务数据，Axios 封装 API 调用
- **Tailwind UI**：根据学术审美设计，专注信息密度与可读性

## 扩展规划

- 增加更多文献来源（CrossRef、Semantic Scholar 等）以及检索参数模板
- 扩展更多通知渠道（钉钉、企业微信、Slack、Discord）基于 MCP 协议
- 引入历史分析视图（检索量趋势、关键词云、筛选率等），并支持导出分享页面
- 集成任务调度管理界面，支持启停、历史运行记录、失败重试等
- 提供 Alembic 迁移脚本，为 MySQL/PostgreSQL 迁移铺平道路
- 增强身份认证：支持多用户、角色权限、OAuth 登录等

## 新功能亮点 (v0.2)

### MCP 集成
- 基于 Model Context Protocol 实现统一的通知工具接口
- 邮件推送：支持 HTML 富文本、批量接收人、自定义主题模板
- 飞书推送：支持群机器人 Webhook、富文本卡片、文献列表展示
- 易于扩展：新增通知渠道只需实现 `MCPTool` 基类

### UI 优化
- GitHub 入口：标题栏右上角添加 GitHub 链接
- AI Summary 展示：文献列表中显著展示 AI 生成的摘要
- 归档任务优化：归档任务时文献列表标题不再显示任务名
- 通知配置面板：任务表单中新增通知推送配置区域

### 代码清理
- 删除空目录和未使用的代码
- 更新 .gitignore 忽略编译产物和缓存文件
- 整理项目结构，提高代码可维护性

欢迎 Issue/PR，一起完善 Litea！

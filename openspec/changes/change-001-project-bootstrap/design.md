## Context

Battery-RAG Agent 目前只有产品级规格和一个空仓库。为了让后续登录、RAG、Agent、数据模型和异步任务等能力可以稳定增量开发，需要先搭建一个明确的 monorepo 工程骨架，并统一前端、后端、基础设施和环境配置的边界。

这次 change 是跨模块的基础设施搭建，涉及前端应用、后端服务、本地依赖容器、环境变量规范和项目文档，因此需要先在设计层明确结构和约束，避免后续 change 反复调整目录和运行方式。

主要约束：

- 只做工程骨架，不实现登录、RAG、Agent 或具体业务流程。
- 前端必须使用 Next.js + React + Tailwind CSS。
- 后端必须使用 FastAPI，并暴露基础 health check。
- 本地依赖服务必须至少包含 PostgreSQL、Redis 和 Qdrant。
- 结构应适合后续扩展为多用户、RAG、Agent 和异步任务系统。

## Goals / Non-Goals

**Goals:**

- 建立清晰的 monorepo 目录结构，分离 `frontend`、`backend` 和根级基础设施配置。
- 提供一个可启动的前端占位应用，包含 landing page 和 dashboard 占位页。
- 提供一个可启动的后端占位服务，包含健康检查接口。
- 定义本地开发基础设施入口，包括 `docker-compose`、`.env.example` 和基础 README。
- 为后续业务 change 保留稳定的扩展位，例如 API 路由、服务层、数据库迁移、异步任务和前端应用路由。

**Non-Goals:**

- 用户注册、登录、权限控制实现。
- 文档上传、知识库构建、RAG 检索或 Agent 工作流。
- 实际数据库 schema、向量索引 schema 或任务执行逻辑。
- 生产级 CI/CD、监控、计费或部署编排。

## Decisions

### Decision: Use a monorepo with top-level `frontend/`, `backend/`, and infra files

选择 monorepo 是因为当前项目前后端会紧密协同演进，并共享同一套产品规格、环境变量约定和本地依赖。把前端、后端和基础设施放在同一仓库中，可以降低早期迭代成本，并让 OpenSpec change 更容易跨层管理。

备选方案：

- 分仓库管理前后端：不利于早期快速联动，且会增加环境同步成本。
- 单目录混合前后端：不利于长期维护和职责边界清晰化。

### Decision: Keep frontend shell intentionally thin but route-ready

前端只提供 landing page 和 dashboard 占位页面，但目录结构需要为后续 App Router、项目页、认证页和业务子页面预留扩展空间。这样可以避免后续为了增加业务路由再重构项目根结构。

备选方案：

- 只保留单首页：更简单，但无法验证后续多页面布局和导航结构。
- 现在就加入完整产品信息架构：会把本次 change 推向业务实现，超出范围。

### Decision: Keep backend shell service-oriented from day one

后端虽然只提供 health check，但目录结构应从一开始保留 API 路由、核心配置、服务层和未来数据库接入入口。这样可以让后续认证、文档、聊天和 Agent 模块直接增量接入，而不是先做一个临时脚本式 FastAPI 项目再迁移。

备选方案：

- 极简单文件 FastAPI：启动最快，但会在后续业务开发时立刻失去可维护性。
- 过度设计完整企业模板：成本过高，不适合此阶段。

### Decision: Use Docker Compose only for shared dependencies, not necessarily full app boot in this change

本次 change 必须为 PostgreSQL、Redis、Qdrant 提供容器依赖，但不强制要求前后端在 Compose 内完整运行。这样可以优先把数据库和基础中间件标准化，同时给后续选择前端/后端本地直跑还是容器运行保留空间。

备选方案：

- 前后端与依赖一起全部容器化：更统一，但会增加脚手架复杂度和调试成本。
- 不引入 Compose：后续每位开发者环境不一致，且不利于数据库与向量库稳定联调。

### Decision: Centralize configuration with a root `.env.example`

使用根目录 `.env.example` 作为开发配置样例的单一入口，有助于统一前后端和依赖服务的环境变量命名约定。后续如果需要拆分前后端局部环境文件，也应从根级样例派生。

备选方案：

- 前后端各自维护独立样例：短期可行，但会让共享基础配置分散。
- 现在就引入复杂配置层：不必要。

### Decision: Document what is explicitly not included

脚手架类 change 很容易被误解为“顺手实现一点业务逻辑”。因此设计上必须明确：本次只定义工程结构、占位页面、健康检查和基础运行方式，不做身份、RAG、Agent 或实际数据流程。

## Risks / Trade-offs

- [脚手架过薄，后续仍需补结构] → 通过在目录层面为 API、服务层、页面路由和任务系统预留明确扩展位来降低返工风险。
- [脚手架过厚，偏离本次范围] → 通过规格明确禁止登录、RAG、Agent 和真实业务逻辑进入本 change。
- [环境变量设计过早固化] → 先定义最小共享配置集合，允许后续 change 扩展但避免破坏已有命名。
- [Compose 只覆盖依赖服务，运行方式存在两套入口] → README 需要明确“依赖服务由 Compose 提供，应用可本地启动”的开发模型。

## Migration Plan

这是一个新仓库初始化 change，不涉及线上迁移或数据回滚。

落地顺序应为：

1. 建立目录结构和应用骨架。
2. 增加前端占位页面与后端健康检查。
3. 增加 `docker-compose` 和 `.env.example`。
4. 增加 README 说明。

如果需要回滚，只需移除本次新增的工程骨架文件。

## Open Questions

- 根目录是否同时引入统一的 JavaScript 包管理 workspace 配置，还是先只保留独立前后端目录。
- 前端占位页面是否需要在本次就包含全局布局和导航骨架。
- 后端是否在本次同时预留 Alembic、SQLAlchemy 等目录，即使暂不接入数据库。

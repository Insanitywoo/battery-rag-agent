## Why

Battery-RAG Agent 已经明确了产品级 Source of Truth，但仓库还没有可执行的工程骨架。现在先建立统一的 monorepo、前后端占位应用、基础容器依赖和环境配置，可以把后续登录、RAG、Agent 等能力放到稳定的项目结构里推进，避免后面一边做业务一边返工工程基础。

## What Changes

- 创建面向前后端协作的 monorepo 项目结构，作为后续所有业务能力的承载基础。
- 引入 `frontend` Web 应用骨架，技术栈为 Next.js + React + Tailwind CSS，并提供 landing page 与 dashboard 占位页面。
- 引入 `backend` API 服务骨架，技术栈为 FastAPI，并提供基础 health check 接口。
- 增加本地开发基础设施配置，使用 `docker-compose` 启动 PostgreSQL、Redis 和 Qdrant。
- 增加基础环境变量样例文件 `.env.example`，统一前后端和基础设施的配置入口。
- 增加基础 `README`，说明项目定位、目录结构和启动方式。
- 明确本次 change 只完成工程脚手架，不实现登录、RAG、Agent 或业务工作流。

## Capabilities

### New Capabilities
- `project-scaffold`: 定义 Battery-RAG Agent 的 monorepo 目录结构、共享工程约束和本地开发入口。
- `frontend-shell`: 定义前端占位应用的页面骨架与最小路由结构。
- `backend-shell`: 定义 FastAPI 服务骨架与基础健康检查能力。
- `local-dev-infra`: 定义本地开发依赖服务、环境变量样例和基础运行文档。

### Modified Capabilities
- None.

## Impact

- Affected code: `frontend/`, `backend/`, repo root bootstrap files, and local infrastructure config.
- Affected systems: local development workflow, containerized dependencies, frontend and backend app startup paths.
- Dependencies introduced: Next.js, React, Tailwind CSS, FastAPI, Docker Compose services for PostgreSQL, Redis, and Qdrant.
- No breaking API or data model changes are introduced because this change creates scaffolding only.

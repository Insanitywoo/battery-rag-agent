## Why

Battery-RAG Agent 目前只有工程脚手架和占位页面，还没有用户身份和项目归属能力。为了让后续文档上传、RAG 知识库和 Agent 工作流建立在可靠的多用户隔离基础上，现在需要先补齐用户认证和个人科研项目管理这一层。

## What Changes

- 增加后端用户注册、登录、JWT access token 鉴权、密码哈希存储和当前用户信息接口。
- 增加后端科研项目管理接口，包括创建项目、查询当前用户项目列表、查询项目详情和删除项目。
- 增加以 `owner_id` 或 `user_id` 为核心的项目归属与访问校验约束，确保项目级数据隔离。
- 增加前端登录页、注册页、登录后 Dashboard 页面、项目列表页和创建项目表单。
- 增加前后端对认证流程的最小集成，但不实现第三方登录、邮箱验证、找回密码、文档上传、RAG、Agent 或付费系统。
- **BREAKING**: 现有前端与后端“仅占位壳、不实现认证或业务工作流”的约束将被收窄，只在已明确的认证和项目工作区范围内放开。

## Capabilities

### New Capabilities
- `user-authentication`: 定义用户注册、登录、JWT 鉴权、密码哈希和当前用户信息能力。
- `user-project-workspace`: 定义当前登录用户的科研项目创建、查询、详情和删除能力，以及 owner 级访问隔离。
- `frontend-auth-workspace`: 定义前端登录、注册、登录后 dashboard、项目列表和创建项目表单的最小工作区体验。

### Modified Capabilities
- `backend-shell`: 变更“后端仅提供 health check、不包含业务能力”的要求，使后端壳层允许在本 change 中引入认证和项目 API。
- `frontend-shell`: 变更“前端只允许占位页面、不包含登录或业务流程”的要求，使前端壳层允许在本 change 中引入认证页和个人项目工作区页面。

## Impact

- Affected code: `backend/` auth and project modules, database-related backend wiring, `frontend/` auth and workspace pages, shared environment configuration, and root documentation.
- Affected APIs: new auth endpoints and project workspace endpoints protected by JWT.
- Affected systems: backend persistence model, frontend session handling, project ownership checks, and local environment configuration for JWT secrets and database access.
- Dependencies likely introduced or activated: password hashing library, JWT library, relational persistence libraries, and frontend request/state handling for authenticated flows.

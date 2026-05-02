## Context

Battery-RAG Agent 已经具备前后端脚手架、Docker 依赖服务和 OpenSpec 主规格，但当前系统仍然是匿名占位壳，没有用户身份、项目归属和受保护 API。后续的文档上传、知识库构建、RAG、Agent 任务和导出结果都需要建立在明确的用户所有权和项目隔离基础上，因此认证与个人科研工作区是下一步最关键的基础能力。

这次 change 是一个跨前后端、数据模型和安全边界的增量：

- 后端需要从单个 health check 扩展到受保护 API；
- 系统需要落地用户实体和项目实体；
- 前端需要从纯占位页面扩展到登录、注册和个人工作区页面；
- 安全要求需要从“不要暴露密钥”提升到“基于 JWT 的受保护接口和 owner 级访问控制”。

主要约束：

- 密码必须哈希存储，不能明文落库；
- JWT secret 必须来源于环境变量；
- 所有项目必须绑定 `owner_id` 或 `user_id`；
- 用户只能访问自己的项目；
- 本次不实现第三方登录、邮箱验证、找回密码、付费、文档上传、RAG、Agent 或 Skills。

## Goals / Non-Goals

**Goals:**

- 提供最小但完整的用户注册、登录和当前用户识别闭环。
- 提供基于 JWT access token 的受保护后端 API。
- 提供用户级科研项目工作区，包括创建、列表、详情和删除。
- 让前端具备最小可用的认证入口和登录后工作区视图。
- 为后续任何项目级资源建立统一的 `owner_id` / `user_id` 数据隔离模式。

**Non-Goals:**

- 第三方 OAuth、邮箱验证或密码找回。
- 刷新 token、复杂会话管理或多设备登录策略。
- 文档上传、知识库、RAG 检索、Agent 任务或导出能力。
- 计费、订阅、团队协作或管理员后台。

## Decisions

### Decision: Introduce relational persistence for users and projects now

认证和项目管理是明确的关系型领域，因此本 change 应正式接入 PostgreSQL 作为后端持久层，并定义 `User` 与 `Project` 两个核心实体。这样后续文档、聊天、任务和导出都可以直接以用户和项目为上层归属。

备选方案：

- 暂时用内存存储：实现快，但无法支撑真实登录和 owner 校验。
- 暂时用 SQLite：虽然可行，但当前项目已经标准化了 PostgreSQL，本地与后续部署一致性更重要。

### Decision: Use hashed passwords with a dedicated password hashing library

密码将通过专门的密码哈希库处理，而不是自定义哈希逻辑。这样可以减少安全错误，并使注册与登录验证流程具备可维护性和可升级性。

备选方案：

- 手写哈希流程：风险高，不接受。
- 明文或可逆加密存储：违反安全要求，不接受。

### Decision: Use environment-backed JWT signing with an HttpOnly Cookie access-token flow

本阶段只实现 access token，不引入 refresh token。JWT 签名 secret 必须来自环境变量，以保证本地开发和部署配置一致，并避免密钥进入前端或仓库。

access token 的持久化策略在本 change 中明确固定为：

- 登录成功后由后端通过 `Set-Cookie` 写入 HttpOnly Cookie；
- 前端不得把 token 写入 `localStorage` 或 `sessionStorage`；
- 前端访问受保护 API 时使用 `credentials: "include"`；
- 后端认证依赖从 Cookie 中读取 `access_token`；
- logout 接口负责清除该 Cookie；
- 开发环境 `COOKIE_SECURE=false`，生产环境 `COOKIE_SECURE=true`；
- `COOKIE_SAMESITE` 默认 `lax`。

备选方案：

- 硬编码 JWT secret：违反安全要求。
- 本 change 同时引入 refresh token：复杂度更高，不是当前最小可行范围。
- 将 token 保存在 `localStorage` 或 `sessionStorage`：暴露面更大，不采用。

### Decision: Use owner-bound authorization at the project API boundary

项目相关 API 的核心安全边界是：先识别当前用户，再按 `owner_id` 校验项目归属。所有项目查询、详情、删除逻辑都必须以当前用户为过滤条件或显式校验前置条件，避免通过项目 ID 横向访问他人资源。

备选方案：

- 只在前端隐藏其他项目：不构成安全边界。
- 仅在业务服务末端补校验：容易遗漏，风险高。

### Decision: Extend the existing frontend shell into a minimal authenticated workspace

前端不再只是静态占位，而是增加注册页、登录页、登录后 dashboard、项目列表页和创建项目表单。这样后续文档、聊天和 Agent 页面可以建立在真实用户工作区之上。

备选方案：

- 仅实现后端 API，不做前端页面：不利于尽早验证用户体验和端到端流程。
- 一次性实现完整产品导航：会超出当前 change 范围。

### Decision: Keep the session model minimal and bounded

本 change 的目标是“用户能登录并操作自己的项目”，不是完整账户系统。因此只引入最小认证流、基于 HttpOnly Cookie 的 access token、基础受保护页面和 API 调用约束，避免在邮箱验证、密码重置或多端会话上过度设计。

## Risks / Trade-offs

- [认证流过于简单，后续需要扩展] → 保持接口和依赖边界清晰，为 refresh token、邮箱验证和更复杂会话策略预留扩展空间。
- [项目 owner 校验遗漏导致越权] → 在 API 依赖和服务层双重落实当前用户与项目归属检查，并为越权路径设计测试场景。
- [前端会话处理选择不当带来安全负担] → 明确采用 HttpOnly Cookie 持久化 access token，禁止前端将 token 写入 `localStorage` 或 `sessionStorage`，并确保任何密钥都不进入前端代码或仓库。
- [数据库接入会放大实现工作量] → 仅引入 `User` 与 `Project` 的最小模型，避免把后续文档和 RAG 相关表提前带入本 change。

## Migration Plan

这是在已有脚手架上的首次业务能力扩展，不涉及线上数据迁移。

落地顺序建议为：

1. 接入数据库层和基础配置。
2. 实现用户模型、认证模型和密码/JWT 基础设施。
3. 实现注册、登录、当前用户接口。
4. 实现项目模型与 owner 校验下的项目 API。
5. 实现前端登录、注册和个人工作区页面。
6. 联调前后端并验证未授权、越权、正常访问三类路径。

如果需要回滚，可移除本次新增的认证、项目和前端工作区模块，并恢复到纯脚手架状态。

## Open Questions

- 项目删除是否需要软删除，为后续文档和任务资源保留恢复空间。
- 是否在本 change 中同步引入数据库迁移工具，还是先以最小 schema 初始化为主。

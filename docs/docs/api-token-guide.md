# API Token 使用指南

> 为脚本、CLI、第三方系统集成提供**永久有效**的 API 访问凭证。与登录 JWT（7 天过期）并存，适用于 OpenAPI 调用场景。

---

## 功能说明

| 项 | 说明 |
| --- | --- |
| 格式 | `aix_` + 随机字符串，如 `aix_k7Hx9mP2nQ4rS6tU8vW0xY2zA4bC6dE8fGhIjKl` |
| 有效期 | 永久（`expires_at = NULL`） |
| 绑定账号 | 仅可绑定 `role=admin` 的用户 |
| 作用范围 | 所有 `@check_token` 鉴权接口（含 `POST /chat/answer`） |
| 管理接口 | 仅接受登录 JWT，**不接受** API Token |
| 存储 | 数据库仅存 SHA-256 哈希，明文仅在创建时返回一次 |

---

## 管理 Token

### Web 管理界面

1. 管理员登录 Web
2. 进入 **系统设置 → API Token**
3. 点击 **创建 Token**，填写名称与绑定管理员
4. 在弹窗中**复制并保存完整明文**（关闭后无法再次查看）
5. 列表仅显示 `token_prefix`（如前 12 位 `aix_k7Hx9mP`）

支持操作：启用 / 禁用 / 删除。泄露或遗失时请禁用或删除后重新创建。

### 管理 API（需 JWT）

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/user/api_token/add` | 创建 Token |
| POST | `/user/api_token/list` | 分页列表 |
| POST | `/user/api_token/enable` | 启用 |
| POST | `/user/api_token/disable` | 禁用 |
| POST | `/user/api_token/delete` | 删除 |

---

## curl 调用示例

以下示例假设后端直连地址为 `http://127.0.0.1:8088`。若经前端代理（Vite `2048` 或 Docker `18080`），路径前加 `/api` 前缀。

### 1. 登录获取 JWT（用于创建 Token）

```bash
curl -s -X POST 'http://127.0.0.1:8088/user/login' \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"123456"}'
```

```bash
export JWT_TOKEN="<响应 data.token>"
```

### 2. 创建 API Token

```bash
curl -s -X POST 'http://127.0.0.1:8088/user/api_token/add' \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -H 'Content-Type: application/json' \
  -d '{"name":"integration-demo","user_id":1}'
```

将响应中的 `data.token` 保存为环境变量：

```bash
export API_TOKEN="aix_xxxxxxxx..."
```

> **注意**：数据库中的 `token_hash` 与 `token_prefix` **不能**拼成可用 Token，必须使用创建时返回的完整明文。

### 3. 验证 Token

```bash
curl -s -X GET 'http://127.0.0.1:8088/datasource/list' \
  -H "Authorization: Bearer ${API_TOKEN}"
```

### 4. 调用主聊天接口（SSE）

**智能问答（COMMON_QA）**

```bash
curl -N -X POST 'http://127.0.0.1:8088/chat/answer' \
  -H "Authorization: Bearer ${API_TOKEN}" \
  -H 'Content-Type: application/json' \
  -d '{
    "query": "你好，请介绍一下你自己",
    "qa_type": "COMMON_QA",
    "chat_id": "curl-demo-chat-001",
    "uuid": "curl-demo-uuid-001",
    "file_list": []
  }'
```

**数据问答（DATABASE_QA）**

```bash
curl -N -X POST 'http://127.0.0.1:8088/chat/answer' \
  -H "Authorization: Bearer ${API_TOKEN}" \
  -H 'Content-Type: application/json' \
  -d '{
    "query": "有哪些数据表？",
    "qa_type": "DATABASE_QA",
    "chat_id": "curl-demo-chat-002",
    "uuid": "curl-demo-uuid-002",
    "datasource_id": 1,
    "file_list": []
  }'
```

`-N` 用于实时输出 SSE 流。`datasource_id` 请替换为实际数据源 ID。

### 经前端代理访问

```bash
curl -N -X POST 'http://127.0.0.1:2048/api/chat/answer' \
  -H "Authorization: Bearer ${API_TOKEN}" \
  -H 'Content-Type: application/json' \
  -d '{"query":"你好","qa_type":"COMMON_QA","chat_id":"demo","uuid":"demo-uuid","file_list":[]}'
```

---

## CLI 使用

CLI 请求路径带 `/api` 前缀，请使用 **Web 代理地址**（非直连后端 8088）：

```bash
# 永久 API Token 登录
aix-db-cli login --token aix_xxxxxxxx --url http://127.0.0.1:2048

# 或 Docker 部署
aix-db-cli login --token aix_xxxxxxxx --url http://localhost:18080

aix-db-cli datasources
aix-db-cli chat "有哪些数据表？" --datasource 1 --stream
```

浏览器登录（JWT，7 天有效）方式不变：`aix-db-cli login --url http://...`

---

## 数据库迁移

新环境由 `docker/init_sql.sql` 自动建表。存量环境执行：

```bash
# 建表（若尚未创建）
psql "$SQLALCHEMY_DATABASE_URI" -f scripts/migrations/001_add_t_api_token.sql

# 补全表注释（可选）
psql "$SQLALCHEMY_DATABASE_URI" -f scripts/migrations/002_t_api_token_comments.sql
```

表名：`t_api_token`。字段说明见 `docker/init_sql.sql` 或迁移脚本中的 `COMMENT ON`。

---

## 环境变量

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `JWT_SECRET_KEY` | 见 `.env.example` | JWT 签名密钥（与 API Token 无关） |
| `API_TOKEN_MAX_PER_USER` | `10` | 每个管理员最多可创建的 Token 数量 |

---

## 常见问题

### 为什么不能用 token_hash + token_prefix 调用 API？

`token_hash` 是完整明文的 SHA-256，`token_prefix` 仅用于列表展示。服务端校验 `SHA256(请求中的完整明文) == token_hash`，哈希不可逆，前缀也不足以还原明文。

### API Token 调管理接口返回 403？

设计如此。创建 / 列表 / 启用 / 禁用 / 删除 Token 必须使用登录 JWT，防止泄露的 API Token 被用来签发更多 Token。

### 禁用或删除后多久失效？

立即失效。再次请求将返回 `code: 401`（部分接口 HTTP 状态码仍为 200，以响应体 `code` 为准）。

### 管理员 Token 访问数据源需要授权吗？

`DATABASE_QA` 时，管理员账号（`role=admin`）可访问所有数据源，无需 `t_datasource_auth` 授权。

---

## 相关源码

| 路径 | 说明 |
| --- | --- |
| `services/auth_service.py` | `resolve_token()` / `resolve_user_payload_from_token()` 统一鉴权 |
| `services/user_service.py` | `get_user_info(request)` 优先复用 `request.state.user_payload` |
| `common/agent_util.py` | `get_user_id(user_payload)` Agent 层取用户 ID |
| `services/api_token_service.py` | Token CRUD |
| `controllers/api_token_api.py` | 管理 API |
| `common/token_decorator.py` | `@check_token` |
| `common/jwt_only_decorator.py` | `@check_jwt_token`（管理接口） |
| `web/src/views/system/config/api-token-config.vue` | 管理页面 |

更多鉴权链路见 [源码理解指南 - 认证与 API Token](./source-code-guide.md#13-认证与-api-token)。

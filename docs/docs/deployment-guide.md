# 部署与开发指南

> 涵盖 Docker 快速部署、本地开发、环境变量与常见问题。部署后系统配置见 [配置说明](./index.md)。

---

## 一、快速体验（Docker）

```bash
git clone https://github.com/qinlei131479/Ai-Chat-DB.git
cd Ai-Chat-DB/docker
cp .env.template .env
docker-compose up -d
```

或在项目根目录使用 Makefile：

```bash
make up
```

### 访问地址

| 服务 | 地址 | 说明 |
| --- | --- | --- |
| Web 管理界面 | http://localhost:18080 | 默认账号 `admin` / 密码 `123456` |
| 后端 API | http://localhost:18088 | Swagger：http://localhost:18088/docs |
| PostgreSQL | `localhost:15432` | 库名 `aix_db`，用户 `aix_db`，密码 `1` |

### 首次使用

1. 登录 Web 界面
2. **系统设置 → 模型配置**：添加并设为默认大语言模型（必填）
3. **系统设置 → 库表配置**：添加业务数据源
4. 切换到 **数据问答** 模式开始查询

---

## 二、本地开发

### 环境要求

- Python 3.12
- PostgreSQL（本地或 Docker 映射）
- Node.js >= 18.12（前端）
- [uv](https://docs.astral.sh/uv/)（推荐，Python 依赖管理）

### ① 克隆与配置

```bash
git clone https://github.com/qinlei131479/Ai-Chat-DB.git
cd Ai-Chat-DB
cp .env.example .env
```

### ② 准备 PostgreSQL

确保本机 PostgreSQL 已启动，并存在数据库 `aix_db`：

```
postgresql+psycopg2://postgres:postgres@127.0.0.1:5432/aix_db
```

若使用 Docker Compose 仅提供 PostgreSQL（映射端口 `15432`）：

```
postgresql+psycopg2://aix_db:1@127.0.0.1:15432/aix_db
```

### ③ 安装 Python 依赖

```bash
# 推荐：uv
uv venv --python 3.12
source .venv/bin/activate
uv sync

# 或 pip
pip install -r requirements.txt
```

### ④ 启动后端

```bash
python serv.py
```

后端地址：http://localhost:8088

首次启动时，若数据库中无 `admin` 用户，会自动创建（账号 `admin`，密码 `123456`）。

### ⑤ 启动前端

```bash
cd web
npm install
npm run dev
```

### 可选能力

| 能力 | 条件 |
| --- | --- |
| 表格问答 | `MINIO_ENABLED=true` + MinIO 服务 |
| MCP 工具（智能问答） | 配置 `MCP_HUB_COMMON_QA_GROUP_URL` + mcp-hub |
| Langfuse 追踪 | 配置 `LANGFUSE_*` 变量 |

更多架构细节见 [源码理解指南](./source-code-guide.md)。

---

## 三、环境变量

> 完整模板见项目根目录 `.env.example` 文件

### 核心服务

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `SERVER_PORT` | `8088` | 后端 API 端口 |
| `SERVER_WORKERS` | `1` | Uvicorn 工作进程数 |
| `SQLALCHEMY_DATABASE_URI` | `postgresql+psycopg2://postgres:postgres@127.0.0.1:5432/aix_db` | 应用元数据库（PostgreSQL） |

### 文件存储（表格问答 / 部分 Skill）

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `MINIO_ENABLED` | `false` | 是否启用 MinIO |
| `MINIO_ENDPOINT` | `127.0.0.1:9000` | MinIO 地址 |
| `MINIO_ACCESS_KEY` | `admin` | 访问密钥 |
| `MINIO_SECRET_KEY` | `admin123` | 秘密密钥 |
| `MINIO_DEFAULT_BUCKET` | `filedata` | 默认存储桶 |

> **表格问答**（`FILEDATA_QA`）和部分 Skill 文件能力依赖 MinIO。本地开发默认关闭，启用时需设为 `MINIO_ENABLED=true` 并启动 MinIO。

### 认证

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `JWT_SECRET_KEY` | 见 `.env.example` | 登录 JWT 签名密钥 |
| `API_TOKEN_MAX_PER_USER` | `10` | 每个管理员可创建的 API Token 上限 |

API Token 用于脚本、CLI、OpenAPI 集成，永久有效。管理入口：**系统设置 → API Token**。详见 [API Token 使用指南](./api-token-guide.md)。

存量环境若缺少 `t_api_token` 表：

```bash
psql "$SQLALCHEMY_DATABASE_URI" -f scripts/migrations/001_add_t_api_token.sql
psql "$SQLALCHEMY_DATABASE_URI" -f scripts/migrations/002_t_api_token_comments.sql
```

### MCP 工具（仅智能问答）

| 变量 | 说明 |
| --- | --- |
| `MCP_HUB_COMMON_QA_GROUP_URL` | 外部 mcp-hub 地址，仅 `COMMON_QA` 使用；未配置时降级为 LLM + Skill |

### 链路追踪（可选）

| 变量 | 说明 |
| --- | --- |
| `LANGFUSE_TRACING_ENABLED` | 设为 `true` 启用 |
| `LANGFUSE_SECRET_KEY` | Langfuse Secret Key |
| `LANGFUSE_PUBLIC_KEY` | Langfuse Public Key |
| `LANGFUSE_BASE_URL` | Langfuse 服务地址 |

### 向量检索 / Text2SQL

| 变量 | 说明 |
| --- | --- |
| `EMBEDDING_ENABLED` | 是否启用 Embedding |
| `DEFAULT_EMBEDDING_MODEL` | 本地回退模型 |
| `TABLE_RETURN_COUNT` | 表结构检索返回数量 |

### 前端构建

| 变量 | 说明 |
| --- | --- |
| `VITE_ENABLE_PAGE_AGENT` | PageAgent 开关，修改后需重新构建前端 |

---

## 四、常见问题

### 登录失败 / 默认密码是什么？

- **Docker 部署**：`admin` / `123456`（由 `docker/init_sql.sql` 初始化）
- **本地开发**：首次启动 `python serv.py` 时自动创建 `admin` / `123456`

### 为什么聊天没有响应？

1. 是否在 **系统设置 → 模型配置** 中配置了默认大语言模型？所有 Agent 从数据库表 `t_ai_model` 读取模型，不读 `.env` 中的 API Key。
2. 数据问答是否已选择数据源？
3. 查看后端日志是否有 API 调用错误。

### 表格问答无法上传文件？

表格问答（`FILEDATA_QA`）依赖 MinIO 存储文件。请在 `.env` 中设置：

```bash
MINIO_ENABLED=true
MINIO_ENDPOINT=127.0.0.1:9000
```

并确保 MinIO 服务已启动。Docker 镜像内置 MinIO（端口 9000/9001）。

### MCP 多智能体不生效？

MCP 工具**仅智能问答**（`COMMON_QA`）使用，需配置：

```bash
MCP_HUB_COMMON_QA_GROUP_URL=<your-mcp-hub-url>
```

未配置时自动降级为 LLM + Skill，界面上无 MCP 工具调用。

### 表关系数据存在哪里？

表关系由数据源管理中的 ER 图编辑并保存到 PostgreSQL `t_datasource.table_relation`（JSONB）。Text2SQL 和深度问数均从此字段读取。

### 前端 API 为什么带 `/api/` 前缀？

前端通过 Vite 开发代理或 nginx 将 `/api/*` 重写为后端路径。后端实际为 FastAPI，路由如 `/chat/answer`，不含 `/api` 前缀。

### 支持哪些数据库？

管理界面默认可选：MySQL、PostgreSQL、Oracle、SQL Server、ClickHouse、达梦、Doris、StarRocks。

后端 `common/datasource_util.py` 还支持 Kingbase、AWS Redshift、Elasticsearch（前端表单默认注释隐藏，可按需启用）。

CSV / Excel 仅用于表格问答文件上传，不是 SQL 数据源类型。

### 已有数据库如何升级反馈字段？

若数据库在 `rating` 字段引入前已创建，请执行：

```sql
ALTER TABLE t_user_qa_record ADD COLUMN IF NOT EXISTS rating VARCHAR(10);
```

### 如何用 curl / 脚本调用聊天接口？

1. 在 **系统设置 → API Token** 创建永久 Token（或使用 JWT 调 `POST /user/api_token/add`）
2. 请求头：`Authorization: Bearer aix_...`（完整明文，不是数据库中的 `token_hash`）
3. `POST /chat/answer` 发起 SSE 聊天

完整示例见 [API Token 使用指南](./api-token-guide.md)。

### API Token 明文丢失了怎么办？

数据库只存哈希，无法从 `token_hash` 或 `token_prefix` 恢复。请在管理页禁用/删除旧 Token 后重新创建。

### 四种问答模式分别用什么技术？

| 模式 | qa_type | 引擎 |
| --- | --- | --- |
| 智能问答 | `COMMON_QA` | DeepAgents + Skills + MCP（可选） |
| 数据问答 | `DATABASE_QA` | LangGraph Text2SQL |
| 表格问答 | `FILEDATA_QA` | LangGraph + DuckDB |
| 深度问数 | `REPORT_QA` | DeepAgents + SQL 工具 + Skills |

更多细节见 [源码理解指南](./source-code-guide.md)。

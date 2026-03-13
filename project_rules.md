# Ai-Chat-DB (Aix-DB) 项目分析总结

## 一、项目概述

**Ai-Chat-DB**（也称为 **Aix-DB**）是一个基于大语言模型（LLM）和 RAG 技术的智能数据分析系统，实现对话式数据分析（ChatBI），支持自然语言转 SQL 查询、数据可视化和深度研究功能。

### 1.1 项目定位

- **核心能力**：通用问答、数据问答（Text2SQL）、表格问答、深度搜索、数据可视化、MCP 多智能体
- **产品特点**：开箱即用、安全可控、易于集成、越问越准

### 1.2 技术栈

| 层级 | 技术选型 |
|------|----------|
| **后端框架** | FastAPI + Uvicorn (异步 Python Web 框架) |
| **AI 框架** | LangChain / LangGraph |
| **数据库** | PostgreSQL (含 pgvector 向量)、MinIO (文件存储) |
| **前端框架** | Vue 3 + TypeScript + Vite 5 |
| **UI 组件库** | Naive UI |
| **可视化** | ECharts + AntV |
| **LLM 支持** | OpenAI / Anthropic / DeepSeek / Qwen / Ollama |

---

## 二、项目架构

### 2.1 分层架构

```
┌─────────────────────────────────────────────────────────────┐
│                      前端层 (Vue 3 + TypeScript)            │
│         views/  components/  store/  router/  api/           │
├─────────────────────────────────────────────────────────────┤
│                    API 网关层 (FastAPI)                       │
│              controllers/  common/  services/                │
├─────────────────────────────────────────────────────────────┤
│                     智能服务层                               │
│   LLM 服务  │  Text2SQL Agent  │  RAG  │  MCP 多智能体      │
├─────────────────────────────────────────────────────────────┤
│                     数据存储层                               │
│     PostgreSQL  │  MinIO  │  Neo4j  │  多种外部数据库       │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 支持的数据库类型

- **关系型数据库**：MySQL、PostgreSQL、Oracle、SQL Server、ClickHouse、达梦、Apache Doris、StarRocks
- **文件数据**：CSV、Excel

---

## 三、目录结构

```
Ai-Chat-DB/
├── serv.py                      # 应用入口 (FastAPI + Uvicorn)
├── pyproject.toml                # Python 依赖管理
├── requirements.txt              # 依赖列表
├── Makefile                      # 构建命令
│
├── controllers/                  # API 控制器
│   ├── datasource_api.py
│   ├── user_rest_api.py
│   ├── llm_chat_api.py
│   ├── db_chat_api.py
│   ├── file_chat_api.py
│   ├── aimodel_api.py
│   └── ...
│
├── services/                     # 业务服务层
│   ├── llm_service.py
│   ├── datasource_service.py
│   ├── text2_sql_service.py
│   ├── embedding_service.py
│   └── ...
│
├── model/                        # 数据模型
│   ├── db_models.py              # SQLAlchemy ORM 模型
│   ├── schemas.py                # Pydantic 数据验证
│   ├── db_connection_pool.py     # 数据库连接池
│   └── datasource_models.py      # 数据源模型
│
├── common/                       # 公共工具
│   ├── token_decorator.py         # JWT 认证（FastAPI Depends 依赖注入）
│   ├── res_decorator.py           # 统一响应 & 全局异常处理器
│   ├── permission_util.py         # 权限校验（FastAPI Depends 依赖注入）
│   ├── param_parser.py            # 参数解析工具（向后兼容）
│   ├── llm_util.py               # LLM 工具
│   ├── datasource_util.py        # 数据源工具
│   ├── minio_util.py             # MinIO 文件存储
│   ├── redis_tool.py             # Redis 缓存
│   └── ...
│
├── agent/                        # AI 智能体
│   ├── text2sql/                 # Text2SQL 智能体
│   │   ├── text2_sql_agent.py
│   │   ├── database/            # 数据库操作
│   │   ├── template/             # Prompt 模板
│   │   ├── rag/                  # 知识检索增强
│   │   ├── chart/                # 图表生成
│   │   └── ...
│   │
│   ├── excel/                    # Excel 分析智能体
│   │   ├── excel_agent.py
│   │   ├── excel_chart_generator.py
│   │   └── ...
│   │
│   └── deepagent/                # 深度研究智能体
│       ├── deep_research_agent.py
│       ├── tools/                # 工具集
│       ├── skills/               # 技能定义
│       └── AGENTS.md             # Agent 指令
│
├── web/                          # 前端项目
│   ├── src/
│   │   ├── views/                # 页面组件
│   │   │   ├── auth/             # 登录认证
│   │   │   ├── chat/             # 对话页面
│   │   │   ├── datasource/       # 数据源管理
│   │   │   ├── knowledge/        # 知识库管理
│   │   │   ├── file/             # 文件管理
│   │   │   ├── system/           # 系统设置
│   │   │   └── user/             # 用户管理
│   │   │
│   │   ├── components/          # 通用组件
│   │   ├── api/                  # API 接口定义
│   │   ├── store/                # Pinia 状态管理
│   │   ├── router/              # Vue Router 配置
│   │   ├── hooks/                # Vue Hooks
│   │   ├── utils/                # 工具函数
│   │   └── styles/               # 样式文件
│   │
│   └── vite.config.ts
│
└── docker/                       # Docker 配置
    ├── docker-compose.yaml
    ├── Dockerfile
    ├── entrypoint.sh
    └── nginx.conf.template
```

---

## 四、核心模块说明

### 4.1 后端架构

#### 4.1.1 入口文件 (`serv.py`)

- 基于 FastAPI 框架 + Uvicorn ASGI 服务器
- 支持多 Worker 部署（`uvicorn --workers N`）
- 使用 `app.include_router()` 显式注册路由
- 使用 `lifespan` 上下文管理器初始化 MinIO 等资源
- SSE 流式响应通过 `StreamingResponse` 实现
- 全局异常处理器统一错误响应格式
- 内置 OpenAPI/Swagger 文档（`/docs`）

#### 4.1.2 控制器层 (`controllers/`)

| 文件 | 功能说明 |
|------|----------|
| `llm_chat_api.py` | LLM 对话接口 |
| `db_chat_api.py` | 数据问答接口（Text2SQL） |
| `file_chat_api.py` | 文件问答接口 |
| `datasource_api.py` | 数据源管理接口 |
| `aimodel_api.py` | AI 模型管理接口 |
| `skill_api.py` | 技能中心接口 |
| `permission_api.py` | 权限管理接口 |

#### 4.1.3 服务层 (`services/`)

| 文件 | 功能说明 |
|------|----------|
| `text2_sql_service.py` | Text2SQL 核心服务 |
| `llm_service.py` | LLM 调用封装 |
| `embedding_service.py` | 向量嵌入服务 |
| `datasource_service.py` | 数据源管理服务 |
| `file_chat_service.py` | 文件对话服务 |

#### 4.1.4 数据模型 (`model/`)

- `db_models.py`：使用 SQLAlchemy ORM + pgvector 定义数据库表结构
- `schemas.py`：Pydantic 数据验证模型
- `db_connection_pool.py`：数据库连接池管理

### 4.2 AI 智能体

#### 4.2.1 Text2SQL Agent (`agent/text2sql/`)

**核心流程**：
1. 用户自然语言输入
2. LLM 意图理解 + 实体抽取
3. RAG 知识检索（Embedding + BM25 混合检索）
4. Neo4j 图谱获取表结构
5. SQL 生成与校验
6. 数据库执行
7. 可视化展示（ECharts/AntV）

**关键模块**：
- `text2_sql_agent.py`：Agent 主入口（基于 LangGraph）
- `database/db_service.py`：数据库操作
- `rag/`：知识检索增强
- `chart/generator.py`：图表生成

#### 4.2.2 Deep Research Agent (`agent/deepagent/`)

- 支持深度研究、多轮对话
- 集成 MCP 工具调用
- 内置 Skills（报告生成、Schema 探索等）

### 4.3 前端架构

#### 4.3.1 路由结构 (`web/src/router/`)

```typescript
// 主要路由
/                    → 重定向到 /chat
/login               → 登录页
/chat                → 对话主页
/chat/:id            → 具体对话
/datasource          → 数据源管理
/datasource/tables  → 数据表管理
/knowledge           → 知识库管理
/file                → 文件管理
/system              → 系统设置
```

#### 4.3.2 状态管理 (`web/src/store/`)

- 使用 Pinia 进行状态管理
- `business/index.ts`：业务状态
- `business/userStore.ts`：用户状态

#### 4.3.3 主要页面

| 页面 | 路径 | 说明 |
|------|------|------|
| 登录页 | `views/auth/login.vue` | 用户登录 |
| 对话页 | `views/chat/index.vue` | 主对话界面 |
| 数据源管理 | `views/datasource/datasource-manager.vue` | 数据源 CRUD |
| 知识库管理 | `views/knowledge/knowledge-manager.vue` | 知识库管理 |
| 系统设置 | `views/system/system-settings.vue` | 系统配置 |

---

## 五、开发规范

### 5.1 后端开发规范

#### 5.1.1 项目结构规范

```
# 新增模块时的目录结构
services/          # 业务逻辑层
├── new_service.py

controllers/       # API 入口
├── new_api.py

model/            # 数据模型
├── new_models.py
```

#### 5.1.2 代码风格

- **Python 版本**：3.11+
- **代码格式化**：Black（line-length: 88）
- **导入顺序**：
  1. 标准库
  2. 第三方库
  3. 项目内部模块
- **类型注解**：使用 Python 3.11+ 类型注解语法

#### 5.1.3 API 设计规范

- 基于 FastAPI 框架的 RESTful API
- 使用 Pydantic 进行请求/响应验证（FastAPI 原生支持）
- 使用 `Depends()` 依赖注入进行认证和权限校验
- 使用 `APIRouter` 组织路由（替代原 Sanic Blueprint）
- 统一响应格式（通过 `success_response()` 和全局异常处理器）：

```python
# 成功响应 - 使用 success_response(data)
{
    "code": 200,
    "msg": "ok",
    "data": {...}
}

# 业务错误响应 - 抛出 MyException，由全局异常处理器捕获
{
    "code": 500,
    "msg": "错误信息",
    "data": null
}
```

#### 5.1.4 认证与权限模式

```python
# 需要登录的接口：使用 Depends(get_current_user)
@router.post("/api")
async def handler(user: dict = Depends(get_current_user)):
    ...

# 需要管理员权限的接口：使用 Depends(get_admin_user)
@router.post("/admin-api")
async def admin_handler(user: dict = Depends(get_admin_user)):
    ...

# SSE 流式响应
@router.post("/stream")
async def stream_handler():
    async def generator():
        yield "data: chunk\n\n"
    return StreamingResponse(generator(), media_type="text/event-stream")
```

#### 5.1.5 数据库操作

- 使用 SQLAlchemy ORM 进行数据库操作
- 使用 pgvector 进行向量存储
- 避免直接写原始 SQL，优先使用 ORM

#### 5.1.6 LLM 调用规范

```python
# 通过 llm_service.py 统一封装
from services.llm_service import LLMService

llm_service = LLMService()
response = llm_service.chat(model_id, messages, stream=False)
```

### 5.2 前端开发规范

#### 5.2.1 项目结构

```
web/src/
├── views/           # 页面组件（按功能模块划分）
├── components/      # 通用组件
├── api/             # API 接口定义
├── store/           # Pinia 状态管理
├── router/          # 路由配置
├── hooks/           # Vue Hooks
├── utils/           # 工具函数
└── styles/          # 样式文件
```

#### 5.2.2 组件规范

- **组件命名**：使用 PascalCase（如 `DatasourceForm.vue`）
- **目录结构**：
  ```
  components/
  ├── Datasource/
  │   ├── DatasourceForm.vue
  │   ├── DatasourceList.vue
  │   └── index.ts
  ```

#### 5.2.3 API 接口定义

- 所有 API 接口定义在 `web/src/api/` 目录下
- 使用 TypeScript 进行类型定义

```typescript
// web/src/api/datasource.ts
import request from '@/utils/request'

export interface Datasource {
  id: number
  name: string
  type: string
  // ...
}

export function getDatasourceList() {
  return request.get<Datasource[]>('/datasource/list')
}
```

#### 5.2.4 样式规范

- 使用 Less 预处理器
- 使用 `web/src/styles/variables.scss` 定义全局变量
- 组件样式使用 `scoped`

### 5.3 Agent 开发规范

#### 5.3.1 Text2SQL Agent 规范

**工作流程**：
1. 意图理解 → 2. 知识检索 → 3. SQL 生成 → 4. 执行 → 5. 可视化

**安全规则**：
- 禁止执行：INSERT、UPDATE、DELETE、DROP、ALTER、TRUNCATE、CREATE
- 只允许 SELECT 查询

#### 5.3.2 Deep Research Agent 规范

**执行流程**：
1. 思考与规划（必须先输出）
2. 严格按计划执行
3. 总结与回答

**报告生成规范**：
- HTML 必须使用分隔符包裹输出
- 包含：KPI 卡片、图表、表格、深度分析、结论建议

---

## 六、部署规范

### 6.1 Docker 部署

```bash
cd docker
cp .env.template .env
docker-compose up -d
```

### 6.2 本地开发

```bash
# 1. 启动中间件
cd docker && docker-compose up -d

# 2. 安装 Python 依赖
uv venv --python 3.11
source .venv/bin/activate
uv sync

# 3. 启动后端（FastAPI + Uvicorn）
python serv.py
# 或使用 uvicorn 命令行
# uvicorn serv:app --host 0.0.0.0 --port 8088 --reload

# 4. 启动前端
cd web
npm install
npm run dev
```

### 6.3 端口配置

| 服务 | 端口 |
|------|------|
| 前端 Nginx | 18080 |
| 后端 API | 18088 |
| PostgreSQL | 15432 |
| MinIO API | 19000 |
| MinIO Console | 19001 |

---

## 七、数据库表结构

### 7.1 核心表

| 表名 | 说明 |
|------|------|
| `t_user` | 用户表 |
| `t_user_qa_record` | 问答记录表 |
| `t_ai_model` | AI 模型配置表 |
| `t_datasource` | 数据源表 |
| `t_ds_permission` | 数据权限表 |
| `t_terminology` | 术语配置表（含向量） |
| `t_data_training` | 数据训练表（含向量） |

---

## 八、关键配置

### 8.1 环境变量

```
SERVER_HOST=0.0.0.0
SERVER_PORT=8088
SERVER_WORKERS=2
UVICORN_KEEP_ALIVE_TIMEOUT=120
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
MINIO_ENDPOINT=localhost:9000
MINIO_DEFAULT_BUCKET=filedata
JWT_SECRET_KEY=550e8400-e29b-41d4-a716-446655440000
LLM_PROVIDER=openai
LLM_API_KEY=sk-xxx
```

### 8.2 依赖管理

- 使用 `uv` 进行 Python 依赖管理
- `pyproject.toml` 定义项目元数据和依赖
- 固定版本号避免依赖升级问题

---

## 九、注意事项

1. **OpenMP 兼容性问题**：设置 `KMP_DUPLICATE_LIB_OK=TRUE` 避免向量库初始化冲突
2. **多 Worker 部署**：使用 `uvicorn --workers N` 或 `gunicorn -k uvicorn.workers.UvicornWorker`
3. **SSE 超时**：DeepAgent 报告生成可能耗时较长，Nginx 需配置 `proxy_read_timeout`
4. **数据库连接池**：外部数据库连接使用连接池管理
5. **向量检索**：pgvector 用于术语和训练数据的向量相似度搜索
6. **前端 API 前缀**：前端统一使用 `/sanic` 前缀，Vite 和 Nginx 均做 rewrite 去掉前缀后转发到后端

---

## 十、附录

### 10.1 相关文档

- [README.md](./README.md) - 项目主文档
- [docs/docs/index.md](./docs/docs/index.md) - 配置说明
- [agent/deepagent/AGENTS.md](./agent/deepagent/AGENTS.md) - Agent 指令
- [agent/deepagent/skills/report-generation/SKILL.md](./agent/deepagent/skills/report-generation/SKILL.md) - 报告生成技能

### 10.2 技术文档链接

- FastAPI: https://fastapi.tiangolo.com/
- Uvicorn: https://www.uvicorn.org/
- LangChain: https://python.langchain.com/
- LangGraph: https://langchain-ai.github.io/langgraph/
- Vue 3: https://vuejs.org/
- Naive UI: https://www.naiveui.com/

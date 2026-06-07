# CLAUDE.md

本文件为 Claude Code（claude.ai/code）在本仓库中编写代码时提供的指导说明。

## Plan Mode

在 Plan Mode 下，始终将计划文件写入项目目录 `.claude/plans/`，而非默认的 `~/.claude/plans/`。文件名应基于任务主题命名（例如 `common-agent-refactor-skill-mcp.md`）。

## 构建与运行命令

```bash
# 后端 - 启动开发服务（FastAPI + Uvicorn，默认端口 8088）
python serv.py

# 后端 - 安装依赖
uv add <package> --frozen          # 添加新依赖，不升级已有依赖
uv pip freeze > requirements.txt   # 依赖变更后重新生成锁文件

# 前端 - 开发服务（需 Node.js >= 18.12）
cd web && npm install && npm run dev

# Docker
make up          # 启动服务（docker-compose）
make down        # 停止服务
make logs        # 查看日志
make build       # 构建应用镜像（约 30s，需先有基础镜像）
make build-base  # 重建基础镜像（仅依赖变更时）

# 代码格式化
black .          # line-length=88, target py312

# 测试（按功能组织在 tests/ 下，按需执行）
python -m pytest tests/<subdir>/<test_file>.py
```

## 架构

**Aix-DB** 是基于大语言模型的数据分析平台（ChatBI）。用户以自然语言提问，系统生成 SQL、执行查询并返回可视化结果。

### 后端（Python 3.12，FastAPI + Uvicorn）

```
serv.py                          # 入口 - FastAPI 应用，自动发现并注册 APIRouter
├── controllers/                 # REST API（autodiscover 自动注册）
│   ├── llm_chat_api.py         # 主聊天接口：POST /chat/answer（SSE 流式）
│   ├── db_chat_api.py          # 数据库问答相关接口
│   ├── skill_api.py            # GET /system/skill/list
│   ├── datasource_api.py       # 数据源 CRUD、表关系管理
│   ├── user_rest_api.py        # 用户登录、问答记录
│   ├── permission_api.py       # 数据源行级权限
│   ├── terminology_api.py    # 术语库
│   ├── data_training_api.py    # SQL 训练样本
│   ├── file_chat_api.py        # 文件问答
│   ├── aimodel_api.py          # 模型配置
│   └── embedding_migration_api.py  # Embedding 迁移
├── services/
│   └── llm_service.py          # 按 qa_type 路由到对应 Agent
├── agent/                       # 四套独立 Agent 系统（互不共享核心逻辑）
│   ├── common/                 # COMMON_QA - EnhancedCommonAgent（DeepAgents + Skills + MCP）
│   │   ├── enhanced_common_agent.py
│   │   └── skills/             # SKILL.md 指令文档
│   ├── text2sql/               # DATABASE_QA - Text-to-SQL（LangGraph StateGraph）
│   ├── excel/                  # FILEDATA_QA - Excel/CSV 分析（DuckDB）
│   └── deepagent/              # REPORT_QA - 深度问数（deepagents 库）
│       ├── AGENTS.md           # Agent 指令（作为 memory 加载）
│       ├── skills/             # SKILL.md 指令文档
│       └── tools/              # SQL 工具 + ToolCallManager（防循环调用）
├── model/                       # SQLAlchemy 模型 + Pydantic Schema
├── common/                      # 工具类（LLM、MinIO、加密、数据源连接等）
└── config/                      # 环境变量加载、日志配置
```

### 请求流程（聊天）

```
POST /chat/answer { query, qa_type, chat_id, datasource_id, ... }
  → llm_service.LLMRequest.exec_query()
    → 按 qa_type 路由：
      COMMON_QA   → EnhancedCommonAgent.run_agent()
      DATABASE_QA → Text2SqlAgent.run_agent()
      FILEDATA_QA → ExcelAgent.run_excel_agent()
      REPORT_QA   → DeepAgent.run_agent()
  → SSE 流式响应：data:{"data":{"messageType","content"},"dataType"}\n\n
```

> 前端通过 `/api/` 前缀访问 API（Vite/nginx 代理重写为后端路径），后端实际路由不含 `/api`。

### Agent 系统（四套独立实现，不要假设共享代码）

| Agent | 引擎 | 适用 qa_type |
| --- | --- | --- |
| **Text2SqlAgent** | LangGraph StateGraph | `DATABASE_QA` |
| **ExcelAgent** | LangGraph + DuckDB | `FILEDATA_QA` |
| **EnhancedCommonAgent** | `deepagents.create_deep_agent()` + Skills + MCP | `COMMON_QA` |
| **DeepAgent** | `deepagents.create_deep_agent()` + SQL 工具 + Skills | `REPORT_QA` |

- **Text2SqlAgent** LangGraph 流水线（`agent/text2sql/analysis/graph.py`）：

  ```
  datasource_selector
      → schema_inspector      # BM25 + FAISS 表结构混合检索
      → early_recommender     # 后台生成推荐问题
      → sql_generator         # 术语/样本 RAG + LLM 生成 SQL
      → permission_filter     # 行级权限注入
      → sql_executor          # 执行 SQL
      → parallel_collector    # 并行：图表生成 + 结果总结
      → unified_collector     # 汇总：总结 → 图表数据 → 推荐问题
      → END
  ```

  异常分支：`datasource_selector` 失败 → `error_handler` → `END`

- **DeepAgent**：多阶段追踪（PLANNING → EXECUTION → SUB_AGENT → REPORTING），用 `<details>` HTML 展示思考过程
- **EnhancedCommonAgent**：Skills + MCP + 多轮记忆，用 `<details>` HTML 展示思考过程；未配置 `MCP_HUB_COMMON_QA_GROUP_URL` 时降级为 LLM + Skill
- **ExcelAgent**：上传 Excel/CSV → MinIO 存储 → DuckDB 解析 → LangGraph SQL 分析流水线（**需 `MINIO_ENABLED=true`**）

### 前端（Vue 3 + TypeScript + Vite 6）

```
web/src/
├── views/chat/index.vue        # 主聊天界面
├── views/skill-center.vue      # 技能中心
├── api/index.ts                # 聊天 API（SSE 请求 /api/chat/answer）
├── store/business/index.ts     # Pinia 状态（qa_type、file_list、task_id）
└── components/MarkdownPreview/ # 渲染 Markdown + HTML（含 <details>）
```

### 关键模式

- **SSE 格式**：`data:{"data":{"messageType":"continue","content":"..."},"dataType":"t02"}\n\n`
- **dataType 取值**（`constants/code_enum.py` → `DataTypeEnum`）：
  - `t02` 文本答案
  - `t03` 溯源
  - `t04` 业务/图表数据
  - `t11` 任务 ID
  - `t12` 记录 ID
  - `t14` 步骤进度（Text2SQL 流水线）
  - `t15` 需要用户输入（interrupt 恢复）
  - `t99` 流结束
- **数据源支持**：MySQL、PostgreSQL、Oracle、SQL Server、ClickHouse、达梦、Doris、StarRocks（SQLAlchemy 或原生驱动）；后端还支持 Kingbase、AWS Redshift、Elasticsearch（前端表单默认隐藏）
- **CSV/Excel**：仅用于表格问答（`FILEDATA_QA`），不是 SQL 数据源类型
- **RAG（Text2SQL）**：BM25 + FAISS 表检索在 `db_service.py`；术语/训练样本 RAG 在 `agent/text2sql/rag/`；表关系来自 PostgreSQL `t_datasource.table_relation`（JSONB）
- **MCP 集成**：仅 `COMMON_QA` 使用，通过环境变量 `MCP_HUB_COMMON_QA_GROUP_URL` 连接外部 mcp-hub
- **Skills**：`SKILL.md`（含 YAML frontmatter）作为 LLM 上下文加载，非可执行工具
- **认证**：`Authorization: Bearer <token>`；`resolve_token()` / `resolve_user_payload_from_token()`（`services/auth_service.py`）统一解析登录 JWT（7 天）与永久 API Token（`aix_*`，表 `t_api_token`）；`@check_token` 将结果写入 `request.state.user_payload`，Controller/Agent 直接复用，禁止二次解析 token。Token 管理接口仅 JWT（`@check_jwt_token`）。详见 `docs/docs/api-token-guide.md`
- **LLM 配置**：所有 Agent 通过 `common/llm_util.py` 读取数据库表 `t_ai_model`，不是 `.env` 中的 API Key

### 环境变量

关键变量（详见 `.env.example` 和 `docker/docker-compose.yaml`）：

- `SQLALCHEMY_DATABASE_URI` - 应用元数据库（PostgreSQL）
- `SERVER_PORT`、`SERVER_WORKERS` - 后端服务配置
- `MINIO_ENABLED`、`MINIO_ENDPOINT`、`MINIO_ACCESS_KEY`、`MINIO_SECRET_KEY` - 文件存储（表格问答、部分 Skill 依赖）
- `MCP_HUB_COMMON_QA_GROUP_URL` - MCP 工具 Hub（仅 COMMON_QA）
- `LANGFUSE_TRACING_ENABLED`、`LANGFUSE_SECRET_KEY`、`LANGFUSE_PUBLIC_KEY`、`LANGFUSE_BASE_URL` - 链路追踪
- `VITE_ENABLE_PAGE_AGENT` - 前端 PageAgent 构建开关
- `API_TOKEN_MAX_PER_USER` - 每个管理员可创建的 API Token 数量上限（默认 10）

## graphify（可选）

若项目根目录存在 `graphify-out/` 知识图谱：

- 回答架构或代码库问题前，先读 `graphify-out/GRAPH_REPORT.md` 了解核心节点与社区结构
- 若存在 `graphify-out/wiki/index.md`，优先通过它导航，而非直接读原始文件
- 本会话中修改代码文件后，运行 `python3 -c "from graphify.watch import _rebuild_code; from pathlib import Path; _rebuild_code(Path('.'))"` 保持图谱最新

若 `graphify-out/` 不存在，忽略本节，直接阅读源码即可。

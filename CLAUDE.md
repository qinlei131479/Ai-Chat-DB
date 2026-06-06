# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Plan Mode

When in plan mode, always write plan files to the project directory `.claude/plans/` instead of the default `~/.claude/plans/`. Use descriptive filenames based on the task topic (e.g., `common-agent-refactor-skill-mcp.md`).

## Build & Run Commands

```bash
# Backend - start dev server (FastAPI + Uvicorn on port 8088)
python serv.py

# Backend - install dependencies
uv add <package> --frozen    # add new dependency without upgrading existing ones
uv pip freeze > requirements.txt  # regenerate lockfile after changes

# Frontend - dev server
cd web && pnpm install && pnpm dev

# Docker
make up          # start services (docker-compose)
make down        # stop services
make logs        # view logs
make build       # build app image (~30s, requires base image)
make build-base  # rebuild base image (only when deps change)

# Code formatting
black .          # line-length=88, target py312

# Tests (ad-hoc, organized by feature under tests/)
python -m pytest tests/<subdir>/<test_file>.py
```

## Architecture

**Aix-DB** is an LLM-powered data analysis platform (ChatBI). Users ask questions in natural language; the system generates SQL, executes it, and returns visualized results.

### Backend (Python 3.12, FastAPI + Uvicorn)

```
serv.py                          # Entry point - FastAPI app, autodiscovers APIRouter
├── controllers/                 # REST API blueprints (auto-registered via autodiscover)
│   ├── llm_chat_api.py         # Main chat endpoint: POST /dify/get_answer (SSE streaming)
│   ├── db_chat_api.py          # Database Q&A endpoints
│   ├── skill_api.py            # GET /system/skill/list
│   └── datasource_api.py       # Datasource CRUD
├── services/
│   └── llm_service.py          # Routes requests by qa_type to appropriate agent
├── agent/                       # Four independent agent systems
│   ├── common/                 # COMMON_QA - EnhancedCommonAgent (DeepAgents + Skills + MCP)
│   │   ├── enhanced_common_agent.py
│   │   └── skills/             # SKILL.md instruction documents
│   ├── text2sql/               # DATABASE_QA - Text-to-SQL (LangGraph StateGraph)
│   ├── excel/                  # FILEDATA_QA - Excel analysis (DuckDB)
│   └── deepagent/              # REPORT_QA - deep research (deepagents library)
│       ├── AGENTS.md           # Agent instructions (loaded as memory)
│       ├── skills/             # SKILL.md instruction documents
│       └── tools/              # SQL tools + ToolCallManager (loop prevention)
├── model/                       # SQLAlchemy models + Pydantic schemas
├── common/                      # Utilities (LLM, MinIO, crypto, datasource connections)
└── config/                      # Environment loading, logging config
```

### Request Flow (Chat)

```
POST /dify/get_answer { query, qa_type, chat_id, datasource_id, ... }
  → llm_service.LLMRequest.exec_query()
    → qa_type routing:
      COMMON_QA   → EnhancedCommonAgent.run_agent()
      DATABASE_QA → Text2SqlAgent.run_agent()
      FILEDATA_QA → ExcelAgent.run_excel_agent()
      REPORT_QA   → DeepAgent.run_agent()
  → SSE streaming response: data:{data:{messageType,content},dataType}\n\n
```

### Agent Systems (independent, do not share code between them)

- **Text2SqlAgent**: LangGraph StateGraph pipeline (datasource_selector → schema_inspector → sql_generator → permission_filter → sql_executor → chart_generator → summarizer)
- **DeepAgent**: `deepagents.create_deep_agent()` with skills, multi-phase tracking (PLANNING→EXECUTION→SUB_AGENT→REPORTING), `<details>` HTML for thinking visibility
- **EnhancedCommonAgent**: `deepagents.create_deep_agent()` with Skills + MCP + multi-turn memory, `<details>` HTML for thinking visibility
- **ExcelAgent**: Parses Excel to DuckDB, then SQL analysis pipeline

### Frontend (Vue 3 + TypeScript + Vite)

```
web/src/
├── views/chat/index.vue        # Main chat interface (~3700 lines)
├── views/skill-center.vue      # Skill browsing page
├── api/index.ts                # Chat API (SSE fetch to /sanic/dify/get_answer)
├── store/business/index.ts     # Pinia store (qa_type, file_list, task_id)
└── components/MarkdownPreview/ # Renders markdown + HTML (including <details>)
```

### Key Patterns

- **SSE format**: All agents stream responses as `data:{"data":{"messageType":"continue","content":"..."},"dataType":"t02"}\n\n`
- **dataType values**: `t02` (text answer), `t04` (business/chart data), `t99` (stream end)
- **Datasource support**: MySQL, PostgreSQL, Oracle, SQL Server, ClickHouse, DM, Doris, StarRocks (via SQLAlchemy or native drivers)
- **RAG (Text2SQL)**: BM25 + FAISS table retrieval in `db_service.py`; terminology/training RAG in `agent/text2sql/rag/`; table relations from PostgreSQL `datasource.table_relation` (not Neo4j)
- **Neo4j (optional)**: Datasource relation visualization only (`datasource_service.sync_table_relation_to_neo4j`); not used in Text2SQL LangGraph pipeline
- **MCP integration**: External mcp-hub service for COMMON_QA only, configured via `MCP_HUB_COMMON_QA_GROUP_URL` env var
- **Skills**: Markdown instruction documents (`SKILL.md` with YAML frontmatter) loaded as LLM context, not executable tools
- **Auth**: JWT tokens in `Authorization: Bearer <token>` header, decoded via `services/user_service.decode_jwt_token()`

### Environment

Key env vars (see `.env.example` and `docker/docker-compose.yaml`):
- `SQLALCHEMY_DATABASE_URI` - PostgreSQL connection for app metadata
- `SERVER_PORT`, `SERVER_WORKERS` - Backend server configuration
- `MINIO_ENABLED`, `MINIO_ENDPOINT`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY` - File storage
- `MCP_HUB_COMMON_QA_GROUP_URL` - MCP tool hub endpoint
- `LANGFUSE_TRACING_ENABLED`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_BASE_URL` - Observability tracing
- `VITE_ENABLE_PAGE_AGENT` - Frontend PageAgent build flag

## graphify

This project has a graphify knowledge graph at graphify-out/.

Rules:
- Before answering architecture or codebase questions, read graphify-out/GRAPH_REPORT.md for god nodes and community structure
- If graphify-out/wiki/index.md exists, navigate it instead of reading raw files
- After modifying code files in this session, run `python3 -c "from graphify.watch import _rebuild_code; from pathlib import Path; _rebuild_code(Path('.'))"` to keep the graph current
